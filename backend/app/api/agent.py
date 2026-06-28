from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.registry import build_tools
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.db.database import SessionLocal
from app.agent.agent import Agent
from app.agent.responses import format_agent_response, error_response

router = APIRouter()

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        session = SessionLocal()
        repo = ProductRepository(session)
        service = ProductService(repo)
        tools = build_tools(service)
        _agent = Agent(tools)
    return _agent


class AgentRequest(BaseModel):
    input: str = None
    goal: str = None
    constraints: list = []
    context: dict = {}


@router.post("/agent")
def run_agent(req: AgentRequest):
    try:
        agent = get_agent()
        user_input = req.goal or req.input or ""
        if not user_input:
            return error_response("validation_error", "input or goal is required")

        raw = agent.run(user_input)
        return format_agent_response(raw)
    except Exception as e:
        return error_response("internal_error", str(e))


@router.post("/resume")
def resume_agent(execution_id: str):
    try:
        agent = get_agent()
        raw = agent.resume(execution_id)
        if "error" in raw:
            return error_response("not_found", raw["error"])
        return format_agent_response(raw)
    except Exception as e:
        return error_response("internal_error", str(e))
