from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional
from app.tools.registry import build_tools
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.db.database import SessionLocal
from app.agent.agent import Agent
from app.agent.tenant import TenantManager
from app.agent.responses import format_agent_response, error_response

router = APIRouter()

_agent = None
_tenant_manager = None


def get_agent():
    global _agent
    if _agent is None:
        session = SessionLocal()
        repo = ProductRepository(session)
        service = ProductService(repo)
        tools = build_tools(service)
        _agent = Agent(tools)
    return _agent


def get_tenant_manager():
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager


class AgentRequest(BaseModel):
    input: str = None
    goal: str = None
    constraints: list = []
    context: dict = {}


@router.post("/agent")
def run_agent(req: AgentRequest, x_api_key: Optional[str] = Header(None), debug: bool = Query(False)):
    tenant_manager = get_tenant_manager()
    tenant = None
    tenant_id = "default"

    if x_api_key:
        tenant = tenant_manager.get_by_api_key(x_api_key)
        if not tenant:
            return error_response("authentication_error", "invalid api key")
        tenant_id = tenant.id

        if not tenant_manager.check_rate_limit(tenant_id):
            return error_response("rate_limit_error", "rate limit exceeded")

    try:
        agent = get_agent()
        user_input = req.goal or req.input or ""
        if not user_input:
            return error_response("validation_error", "input or goal is required")

        raw = agent.run(user_input, tenant_id=tenant_id, debug=debug)
        return format_agent_response(raw)
    except Exception as e:
        return error_response("internal_error", str(e))


@router.post("/resume")
def resume_agent(execution_id: str, x_api_key: Optional[str] = Header(None)):
    tenant_manager = get_tenant_manager()
    tenant_id = "default"

    if x_api_key:
        tenant = tenant_manager.get_by_api_key(x_api_key)
        if not tenant:
            return error_response("authentication_error", "invalid api key")
        tenant_id = tenant.id

    try:
        agent = get_agent()
        raw = agent.resume(execution_id, tenant_id=tenant_id)
        if "error" in raw:
            return error_response("not_found", raw["error"])
        return format_agent_response(raw)
    except Exception as e:
        return error_response("internal_error", str(e))


@router.get("/tenants")
def list_tenants():
    tenant_manager = get_tenant_manager()
    return {"tenants": tenant_manager.list_tenants()}


@router.post("/tenants/{tenant_id}/api-key")
def create_api_key(tenant_id: str):
    tenant_manager = get_tenant_manager()
    key = tenant_manager.create_api_key(tenant_id)
    if not key:
        return error_response("not_found", "tenant not found")
    return {"tenant_id": tenant_id, "api_key": key}
