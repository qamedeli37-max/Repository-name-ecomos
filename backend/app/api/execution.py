from fastapi import APIRouter
from app.services.execution_service import ExecutionService
from app.agent.responses import error_response

router = APIRouter()

_service = None


def get_service():
    global _service
    if _service is None:
        _service = ExecutionService()
    return _service


@router.get("/executions/{execution_id}")
def get_execution(execution_id: str):
    service = get_service()
    log = service.get(execution_id)
    if not log:
        return error_response("not_found", "execution not found")

    return {
        "execution_id": log.id,
        "tenant_id": log.tenant_id,
        "goal": log.goal,
        "status": log.status,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "finished_at": log.finished_at.isoformat() if log.finished_at else None,
        "steps": log.steps or [],
        "result": log.result,
        "error": log.error,
        "strategy": log.strategy,
        "profile": log.profile,
        "cognition": log.cognition,
        "replans": log.replans,
        "score": log.score,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "updated_at": log.updated_at.isoformat() if log.updated_at else None
    }


@router.get("/executions")
def list_executions(tenant_id: str = None, limit: int = 50, offset: int = 0):
    service = get_service()
    if tenant_id:
        logs = service.list_by_tenant(tenant_id, limit, offset)
    else:
        logs = service.list_all(limit, offset)

    return {
        "executions": [
            {
                "execution_id": log.id,
                "tenant_id": log.tenant_id,
                "goal": log.goal,
                "status": log.status,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "score": log.score,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ],
        "total": len(logs)
    }
