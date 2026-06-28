from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService
from app.tools.product import ProductCreateTool, ProductUpdateTool, ProductGetTool
from app.tools.registry import ToolRegistry
from app.supervisor.supervisor import Supervisor
from app.supervisor.task import Task

router = APIRouter(tags=["Execute"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_supervisor(db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    service = ProductService(repo)

    registry = ToolRegistry()
    registry.register(ProductCreateTool(service))
    registry.register(ProductUpdateTool(service))
    registry.register(ProductGetTool(service))

    return Supervisor(registry)


@router.post("/execute")
def execute(task: Task, supervisor: Supervisor = Depends(get_supervisor)):
    return supervisor.execute_task(task)
