from app.models.product import Product, ProductCreate
from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    def create(self, data) -> Product:
        product_data = ProductCreate(**data) if isinstance(data, dict) else data
        return self.repo.create(product_data)

    def update(self, data):
        product_id = data.get("id") or data.get("product_id")
        if not product_id:
            return {"error": "missing id"}
        existing = self.repo.get(str(product_id))
        if not existing:
            return {"error": "product not found"}
        return {"status": "updated", "id": product_id, "data": data}

    def get(self, data):
        product_id = data.get("id") or data.get("product_id")
        if not product_id:
            return {"error": "missing id"}
        product = self.repo.get(str(product_id))
        if not product:
            return {"error": "product not found"}
        return product.model_dump()

    def list(self) -> list[Product]:
        return self.repo.list()

    def delete(self, product_id: str) -> bool:
        return self.repo.delete(product_id)
