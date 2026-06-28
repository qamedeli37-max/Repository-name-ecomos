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

    def plan(self, goal: dict, tools: dict) -> dict:
        if self.client:
            return self._llm_plan(goal, tools)
        return {"plan": self._rule_plan(goal)}

    def _llm_plan(self, goal: dict, tools: dict):
        tool_list = "\n".join(tools.keys())
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner.

Given a goal, create a plan with steps.

Return ONLY valid JSON:
{{
    "goal": "the goal description",
    "plan": [
        {{
            "tool": "tool.name",
            "args": {{}}
        }}
    ]
}}

Available tools:
{tool_list}"""
                },
                {"role": "user", "content": json.dumps(goal)}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _rule_plan(self, goal: dict):
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
