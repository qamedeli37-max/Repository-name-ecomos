from app.models.product import Product, ProductCreate
from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    def create_product(self, data: ProductCreate) -> Product:
        return self.repo.create(data)

    def get_product(self, product_id: str) -> Product | None:
        return self.repo.get(product_id)

    def list_products(self) -> list[Product]:
        return self.repo.list()

    def delete_product(self, product_id: str) -> bool:
        return self.repo.delete(product_id)
