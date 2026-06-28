import json
import os
import re
from dotenv import load_dotenv

load_dotenv()


class PlannerAgent:
    def __init__(self):
        self._init_llm()

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def plan(self, goal: dict, tools: dict, memory=None) -> dict:
        if self.client:
            return self._llm_plan(goal, tools, memory)
        return {"plans": [{"id": "a", "steps": self._rule_plan(goal, memory)}]}

    def refine_plan(self, goal: dict, tools: dict, feedback: dict, memory=None) -> dict:
        if self.client:
            return self._llm_refine(goal, tools, feedback, memory)
        return {"plans": [{"id": "a", "steps": self._rule_refine(goal, feedback, memory)}]}

    def _llm_plan(self, goal: dict, tools: dict, memory=None):
        tool_list = "\n".join(tools.keys())
        memory_context = self._build_memory_context(goal, memory)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner. Generate 2-3 different plans.

Return ONLY valid JSON:
{{
    "plans": [
        {{
            "id": "a",
            "steps": [{{"tool": "tool.name", "args": {{}}}}]
        }}
    ]
}}

Available tools:
{tool_list}

{memory_context}"""
                },
                {"role": "user", "content": json.dumps(goal)}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _llm_refine(self, goal: dict, tools: dict, feedback: dict, memory=None):
        tool_list = "\n".join(tools.keys())
        memory_context = self._build_memory_context(goal, memory)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner. A previous plan failed.

Generate 2-3 NEW plans that avoid the error.

Return ONLY valid JSON:
{{
    "plans": [
        {{
            "id": "a",
            "steps": [{{"tool": "tool.name", "args": {{}}}}]
        }}
    ]
}}

Available tools:
{tool_list}

{memory_context}"""
                },
                {
                    "role": "user",
                    "content": f"Goal: {json.dumps(goal)}\nFailed step: {json.dumps(feedback.get('failed_step'))}\nError: {feedback.get('error')}"
                }
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        goal_text = goal.get("goal", "")
        successful = memory.get_successful_plans(goal_text)
        failed = memory.get_failed_patterns(goal_text)
        parts = []
        if successful:
            parts.append(f"Past successful plans: {json.dumps(successful[:2])}")
        if failed:
            parts.append(f"Past failed steps to avoid: {json.dumps(failed[:2])}")
        return "\n".join(parts) if parts else ""

    def _rule_plan(self, goal: dict, memory=None):
        text = goal.get("goal", "").lower()
        steps = []
        if "create" in text or "创建" in text:
            steps.append({"tool": "product.create", "args": self._parse_product_create(text)})
        if "update" in text or "修改" in text:
            steps.append({"tool": "product.update", "args": self._parse_product_update(text)})
        if "list" in text or "show all" in text or "查看所有" in text:
            steps.append({"tool": "product.list", "args": {}})
        elif "get" in text or "show" in text or "查看" in text:
            steps.append({"tool": "product.get", "args": {}})
        if not steps:
            steps.append({"tool": "product.list", "args": {}})
        return steps

    def _rule_refine(self, goal: dict, feedback: dict, memory=None):
        failed_step = feedback.get("failed_step", {})
        tool_name = failed_step.get("tool", "")
        if tool_name == "product.create":
            return [{"tool": "product.list", "args": {}}]
        return self._rule_plan(goal, memory)

    def _parse_product_create(self, text: str):
        price_match = re.search(r'(\d+(?:\.\d+)?)', text)
        price = float(price_match.group(1)) if price_match else 0
        cleaned = re.sub(r'create\s+(a\s+)?product\s*', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'帮我创建', '', cleaned)
        cleaned = re.sub(r'\d+(?:\.\d+)?', '', cleaned).strip()
        title = cleaned if cleaned else "Untitled"
        return {"title": title, "price": price}

    def _parse_product_update(self, text: str):
        price_match = re.search(r'(\d+(?:\.\d+)?)', text)
        return {"id": "", "price": float(price_match.group(1)) if price_match else 0}
