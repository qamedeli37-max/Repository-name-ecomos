from app.tools.base import Tool
from app.tools.product import ProductCreateTool, ProductUpdateTool, ProductGetTool
from app.services.product_service import ProductService


def build_tools(product_service: ProductService) -> dict[str, Tool]:
    tools = [
        ProductCreateTool(product_service),
        ProductUpdateTool(product_service),
        ProductGetTool(product_service),
    ]
    return {tool.name: tool for tool in tools}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [tool.to_schema() for tool in self._tools.values()]
