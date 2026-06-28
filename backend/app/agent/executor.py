import json
import os
from dotenv import load_dotenv

load_dotenv()

MAX_RETRY = 2


class ExecuteResult:
    def __init__(self):
        self.steps: list[dict] = []
        self.requires_replan = False
        self.feedback: dict = {}

    def add_step(self, result: dict):
        self.steps.append(result)

    def request_replan(self, failed_step: dict, error: str):
        self.requires_replan = True
        self.feedback = {
            "failed_step": failed_step,
            "error": error
        }


class ExecutorAgent:
    def __init__(self, tools: dict):
        self.tools = tools
        self._init_llm()

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def execute_plan(self, plan: list[dict]) -> ExecuteResult:
        result = ExecuteResult()

        for step in plan:
            step_result = self.execute_step(step)
            result.add_step(step_result)

            if step_result.get("status") == "failed":
                result.request_replan(step, step_result.get("error", "unknown"))
                break

        return result

    def execute_step(self, step: dict) -> dict:
        tool = self.tools.get(step.get("tool"))
        if not tool:
            return {
                "tool": step.get("tool"),
                "status": "failed",
                "error": f"tool not found: {step.get('tool')}"
            }

        attempt = 0
        success = False
        last_error = None

        while attempt < MAX_RETRY and not success:
            try:
                result = tool.execute(step.get("args", {}))
                success = True
            except Exception as e:
                attempt += 1
                last_error = str(e)
                if attempt < MAX_RETRY and self.client:
                    step = self.fix_step(step, last_error)

        if success:
            return {
                "tool": step.get("tool"),
                "status": "success",
                "result": result
            }
        else:
            return {
                "tool": step.get("tool"),
                "status": "failed",
                "error": last_error
            }

    def fix_step(self, step: dict, error: str):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """This tool call failed. Fix the arguments.
Return ONLY valid JSON with corrected args."""
                },
                {
                    "role": "user",
                    "content": f"Step: {json.dumps(step)}\nError: {error}"
                }
            ]
        )
        content = response.choices[0].message.content
        fixed = json.loads(content)
        step["args"] = fixed.get("args", step.get("args", {}))
        return step
