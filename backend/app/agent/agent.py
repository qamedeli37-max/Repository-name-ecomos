import json
import os
import re
from dotenv import load_dotenv

load_dotenv()


class Agent:
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

    def run(self, user_input: str):
        if self.client:
            return self._run_llm(user_input)
        return self._run_rules(user_input)

    # ========== LLM Mode (multi-step) ==========

    def _run_llm(self, user_input: str):
        plan = self._llm_decide(user_input)
        results = []
        for step in plan.get("steps", []):
            tool = self.tools.get(step.get("tool"))
            if not tool:
                results.append({"error": f"no tool: {step.get('tool')}"})
                continue
            result = tool.execute(step.get("args", {}))
            results.append(result)
        return results

    def _llm_decide(self, user_input: str):
        tool_list = "\n".join(self.tools.keys())

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a tool calling engine.

Return ONLY valid JSON:
{{
    "steps": [
        {{
            "tool": "tool.name",
            "args": {{}}
        }}
    ]
}}

Available tools:
{tool_list}

You may use multiple steps if needed."""
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        content = response.choices[0].message.content
        return json.loads(content)

    # ========== Rule Mode (fallback) ==========

    def _run_rules(self, user_input: str):
        steps = self._rule_plan(user_input)
        results = []
        for step in steps:
            tool = self.tools.get(step.get("tool"))
            if not tool:
                results.append({"error": f"no tool: {step.get('tool')}"})
                continue
            result = tool.execute(step.get("args", {}))
            results.append(result)
        return results

    def _rule_plan(self, text: str):
        text_lower = text.lower()
        steps = []

        # create
        if "create" in text_lower or "创建" in text_lower:
            steps.append({
                "tool": "product.create",
                "args": self._parse_product_create(text)
            })

        # update
        if "update" in text_lower or "修改" in text_lower:
            steps.append({
                "tool": "product.update",
                "args": self._parse_product_update(text)
            })

        # list
        if "list" in text_lower or "show all" in text_lower or "查看所有" in text_lower:
            steps.append({
                "tool": "product.list",
                "args": {}
            })
        elif "get" in text_lower or "show" in text_lower or "查看" in text_lower:
            steps.append({
                "tool": "product.get",
                "args": {}
            })

        if not steps:
            steps.append({"tool": "product.get", "args": {}})

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
