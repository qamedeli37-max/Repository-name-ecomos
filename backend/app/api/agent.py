from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService
from app.tools.registry import build_tools
from app.agent.agent import Agent

router = APIRouter(tags=["Agent"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_agent(db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    service = ProductService(repo)
    tools = build_tools(service)
    return Agent(tools)


@router.post("/agent")
def run_agent(payload: dict, agent: Agent = Depends(get_agent)):
    user_input = payload.get("input", "")
    return agent.run(user_input)
