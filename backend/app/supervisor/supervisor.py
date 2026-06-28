from app.models.product import ProductCreate
from app.services.product_service import ProductService
from app.supervisor.task import Task


class Supervisor:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def execute_task(self, task: Task):
        if task.intent == "create_product":
            data = ProductCreate(**task.data)
            return self.product_service.create_product(data)
        else:
            raise ValueError(f"Unknown intent: {task.intent}")
