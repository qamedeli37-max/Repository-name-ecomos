from app.tools.base import Tool
from app.services.product_service import ProductService


class ProductCreateTool(Tool):
    name = "product.create"

    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def execute(self, data: dict):
        return self.product_service.create(data)


class ProductUpdateTool(Tool):
    name = "product.update"

    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def execute(self, data: dict):
        return self.product_service.update(data)


class ProductGetTool(Tool):
    name = "product.get"

    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def execute(self, data: dict):
        return self.product_service.get(data)
