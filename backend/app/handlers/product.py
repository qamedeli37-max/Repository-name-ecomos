from app.services.product_service import ProductService


class ProductCreateHandler:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def handle(self, data):
        return self.product_service.create(data)


class ProductUpdateHandler:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def handle(self, data):
        return self.product_service.update(data)


class ProductGetHandler:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def handle(self, data):
        return self.product_service.get(data)
