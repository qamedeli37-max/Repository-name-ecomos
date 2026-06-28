from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.tools.registry import build_tools
from app.agent.agent import Agent
from app.db.database import SessionLocal

router = APIRouter(tags=["Agent"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    return ProductService(repo)


def get_agent(service: ProductService = Depends(get_service)):
    tools = build_tools(service)
    return Agent(tools)


@router.post("/agent")
def run_agent(body: dict, agent: Agent = Depends(get_agent)):
    user_input = body.get("input") or body.get("goal") or body
    return agent.run(user_input)
