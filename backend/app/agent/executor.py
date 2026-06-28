import os
from dotenv import load_dotenv

load_dotenv()


class ExecuteResult:
    def __init__(self, steps: list[dict], requires_replan: bool = False, feedback: list[str] = None):
        self.steps = steps
        self.requires_replan = requires_replan
        self.feedback = feedback or []


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

    def execute_plan(self, plan: list[dict], profile=None, cognition_config=None, guard=None) -> ExecuteResult:
        steps = []
        feedback = []
        max_retry = 2
        retry_enabled = True
        auto_fix = True

        if profile:
            retry_enabled = profile.retry_enabled
            auto_fix = profile.auto_fix

        for step in plan:
            tool_name = step.get("tool", "")
            args = step.get("args", {})

            if guard and not guard.can_step():
                steps.append({"tool": tool_name, "status": "failed", "error": "max_steps exceeded"})
                feedback.append("max_steps exceeded")
                return ExecuteResult(steps=steps, requires_replan=True, feedback=feedback)

            if guard:
                guard.step_used()

            result = self.execute_step(step)

            if result.get("status") == "failed" and retry_enabled:
                for retry in range(max_retry):
                    if guard and not guard.can_retry():
                        break
                    if guard:
                        guard.retry_used()

                    if auto_fix and self.client:
                        args = self.fix_step(step, result.get("error", ""))
                    result = self.execute_step({"tool": tool_name, "args": args})
                    if result.get("status") == "success":
                        break

            steps.append(result)

            if result.get("status") == "failed":
                feedback.append(f"{tool_name}: {result.get('error', 'unknown')}")

        has_failure = any(s.get("status") == "failed" for s in steps)
        return ExecuteResult(
            steps=steps,
            requires_replan=has_failure and len(feedback) > 0,
            feedback=feedback
        )

    def execute_step(self, step: dict) -> dict:
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        tool = self.tools.get(tool_name)
        if not tool:
            return {"tool": tool_name, "status": "failed", "error": f"tool not found: {tool_name}"}
        try:
            result = tool.execute(args)
            return {"tool": tool_name, "status": "success", "result": result}
        except Exception as e:
            return {"tool": tool_name, "status": "failed", "error": str(e)}

    def fix_step(self, step: dict, error: str) -> dict:
        if not self.client:
            return step.get("args", {})

        tool_name = step.get("tool", "")
        args = step.get("args", {})

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Fix the arguments for tool '{tool_name}'. Error: {error}. Return ONLY valid JSON args."
                },
                {
                    "role": "user",
                    "content": f"Current args: {args}"
                }
            ]
        )
        content = response.choices[0].message.content
        import json
        return json.loads(content)
