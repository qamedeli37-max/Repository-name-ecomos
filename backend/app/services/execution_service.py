from app.repositories.execution_repository import ExecutionRepository
from app.db.database import SessionLocal
from datetime import datetime


class ExecutionService:
    def __init__(self):
        self.session = SessionLocal()
        self.repo = ExecutionRepository(self.session)

    def log_start(self, execution_id: str, goal: str, tenant_id: str = None, strategy: str = None, profile: str = None, cognition: str = None):
        return self.repo.create({
            "execution_id": execution_id,
            "tenant_id": tenant_id,
            "goal": goal,
            "status": "running",
            "started_at": datetime.utcnow(),
            "strategy": strategy,
            "profile": profile,
            "cognition": cognition
        })

    def log_step(self, execution_id: str, step: dict):
        log = self.repo.get(execution_id)
        if log:
            steps = log.steps or []
            serializable = self._serialize_step(step)
            steps.append(serializable)
            self.repo.update(execution_id, {"steps": steps})

    def _serialize_step(self, step: dict) -> dict:
        result = step.get("result")
        if result is not None:
            if hasattr(result, "model_dump"):
                step = {**step, "result": result.model_dump()}
            elif hasattr(result, "dict"):
                step = {**step, "result": result.dict()}
        return step

    def log_complete(self, execution_id: str, status: str, result: str = None, error: dict = None, score: float = 0.0, replans: int = 0):
        return self.repo.update(execution_id, {
            "status": status,
            "finished_at": datetime.utcnow(),
            "result": result,
            "error": error,
            "score": score,
            "replans": replans
        })

    def get(self, execution_id: str):
        return self.repo.get(execution_id)

    def list_by_tenant(self, tenant_id: str, limit: int = 50, offset: int = 0):
        return self.repo.list_by_tenant(tenant_id, limit, offset)

    def list_all(self, limit: int = 50, offset: int = 0):
        return self.repo.list_all(limit, offset)
