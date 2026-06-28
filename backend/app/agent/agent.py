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

    # ========== LLM Mode ==========

    def _run_llm(self, user_input: str):
        result = self._llm_decide(user_input)
        tool_name = result.get("tool")
        args = result.get("args", {})
        tool = self.tools.get(tool_name)
        if not tool:
            return {"error": f"no tool: {tool_name}"}
        return tool.execute(args)

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
    "tool": "tool.name",
    "args": {{}}
}}

Available tools:
{tool_list}"""
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
        intent = self._decide_intent(user_input)
        tool = self.tools.get(intent)
        if not tool:
            return {"error": f"no tool: {intent}"}
        data = self._extract_data(intent, user_input)
        return tool.execute(data)

    def _decide_intent(self, text: str):
        text = text.lower()
        if "create" in text or "创建" in text:
            return "product.create"
        if "update" in text or "修改" in text:
            return "product.update"
        if "get" in text or "show" in text or "list" in text or "查看" in text:
            return "product.get"
        return "product.get"

    def _extract_data(self, intent: str, text: str):
        if intent == "product.create":
            return self._parse_product_create(text)
        if intent == "product.update":
            return self._parse_product_update(text)
        if intent == "product.get":
            return {}
        return {}

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
