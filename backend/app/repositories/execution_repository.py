from app.db.models.execution import ExecutionLogORM
from sqlalchemy.orm import Session
from datetime import datetime


class ExecutionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: dict) -> ExecutionLogORM:
        log = ExecutionLogORM(
            id=data["execution_id"],
            tenant_id=data.get("tenant_id"),
            goal=data.get("goal", ""),
            status=data.get("status", "running"),
            started_at=data.get("started_at", datetime.utcnow()),
            steps=data.get("steps", []),
            result=data.get("result"),
            error=data.get("error"),
            strategy=data.get("strategy"),
            profile=data.get("profile"),
            cognition=data.get("cognition"),
            replans=data.get("replans", 0),
            score=data.get("score", 0.0)
        )
        self.session.add(log)
        self.session.commit()
        return log

    def update(self, execution_id: str, data: dict) -> ExecutionLogORM | None:
        log = self.session.query(ExecutionLogORM).filter(ExecutionLogORM.id == execution_id).first()
        if not log:
            return None
        for key, value in data.items():
            if hasattr(log, key):
                setattr(log, key, value)
        log.updated_at = datetime.utcnow()
        self.session.commit()
        return log

    def get(self, execution_id: str) -> ExecutionLogORM | None:
        return self.session.query(ExecutionLogORM).filter(ExecutionLogORM.id == execution_id).first()

    def list_by_tenant(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[ExecutionLogORM]:
        return (
            self.session.query(ExecutionLogORM)
            .filter(ExecutionLogORM.tenant_id == tenant_id)
            .order_by(ExecutionLogORM.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def list_all(self, limit: int = 50, offset: int = 0) -> list[ExecutionLogORM]:
        return (
            self.session.query(ExecutionLogORM)
            .order_by(ExecutionLogORM.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete(self, execution_id: str) -> bool:
        log = self.session.query(ExecutionLogORM).filter(ExecutionLogORM.id == execution_id).first()
        if not log:
            return False
        self.session.delete(log)
        self.session.commit()
        return True
