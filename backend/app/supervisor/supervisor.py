from app.models.product import ProductCreate
from app.services.product_service import ProductService
from app.supervisor.task import Task


class Supervisor:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def execute_task(self, task: Task):
        intent = task.intent
        data = task.data

        # ========== PRODUCT ==========
        if intent == "product.create":
            return self.product_service.create(data)

        if intent == "product.update":
            return self.product_service.update(data)

        if intent == "product.get":
            return self.product_service.get(data)

        # ========== ORDER（先占位） ==========
        if intent == "order.create":
            return {"status": "not implemented yet"}

        # ========== fallback ==========
        return {"error": f"unknown intent: {intent}"}
