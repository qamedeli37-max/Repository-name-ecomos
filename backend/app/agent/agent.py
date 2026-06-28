import re


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools

    def run(self, user_input: str):
        intent = self._decide_intent(user_input)
        tool = self.tools.get(intent)
        if not tool:
            return {"error": f"no tool: {intent}"}
        data = self._extract_data(intent, user_input)
        return tool.execute(data)

    def _decide_intent(self, text: str):
        text = text.lower()
        if "create" in text:
            return "product.create"
        if "update" in text:
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
