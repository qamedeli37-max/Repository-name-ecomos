from app.tools.registry import build_tools

MAX_RETRY = 2


class ExecuteResult:
    def __init__(self, steps: list[dict], requires_replan: bool = False, feedback: dict = None):
        self.steps = steps
        self.requires_replan = requires_replan
        self.feedback = feedback or {}


class ExecutorAgent:
    def __init__(self, tools: dict):
        self.tools = tools
        self._init_llm()

    def _init_llm(self):
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = None
        except Exception:
            self.client = None

    def execute_plan(self, plan: list[dict], profile=None) -> ExecuteResult:
        results = []
        retry_enabled = profile.retry_enabled if profile else True
        auto_fix = profile.auto_fix if profile else True

        for step in plan:
            result = self._execute_with_retry(step, retry_enabled, auto_fix)
            results.append(result)

        has_failure = any(r.get("status") == "failed" for r in results)
        failed_step = next((r for r in results if r.get("status") == "failed"), None)

        return ExecuteResult(
            steps=results,
            requires_replan=has_failure,
            feedback=failed_step if failed_step else {}
        )

    def _execute_with_retry(self, step: dict, retry_enabled: bool, auto_fix: bool) -> dict:
        result = self.execute_step(step)

        if result["status"] == "failed" and retry_enabled:
            for attempt in range(MAX_RETRY):
                if auto_fix:
                    fixed_step = self.fix_step(step, result.get("error", ""))
                    result = self.execute_step(fixed_step)
                else:
                    result = self.execute_step(step)

                if result["status"] == "success":
                    break

        return result

    def execute_step(self, step: dict) -> dict:
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        tool = self.tools.get(tool_name)

        if not tool:
            return {"tool": tool_name, "status": "failed", "error": f"tool {tool_name} not found"}

        try:
            result = tool.execute(args)
            return {"tool": tool_name, "status": "success", "result": result}
        except Exception as e:
            return {"tool": tool_name, "status": "failed", "error": str(e)}

    def fix_step(self, step: dict, error: str) -> dict:
        if self.client:
            return self._llm_fix(step, error)
        return self._rule_fix(step, error)

    def _llm_fix(self, step: dict, error: str) -> dict:
        import json
        import os

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""Fix the failed tool call. Return ONLY valid JSON:
{{
    "tool": "tool.name",
    "args": {{}}
}}"""
                },
                {
                    "role": "user",
                    "content": f"Step: {json.dumps(step)}\nError: {error}\nFix the args to make it work."
                }
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _rule_fix(self, step: dict, error: str) -> dict:
        tool_name = step.get("tool", "")
        args = step.get("args", {})

        if tool_name == "product.create":
            if "not found" in error.lower():
                return {"tool": "product.list", "args": {}}
            if not args.get("title"):
                args["title"] = "Untitled"
            if not args.get("price"):
                args["price"] = 0
            return {"tool": tool_name, "args": args}

        if tool_name == "product.update":
            if "not found" in error.lower():
                return {"tool": "product.list", "args": {}}

        return step
