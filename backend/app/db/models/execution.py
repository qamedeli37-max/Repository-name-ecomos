from sqlalchemy import Column, String, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from app.db.database import Base


class ExecutionLogORM(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=True)
    goal = Column(Text, nullable=False)
    status = Column(String, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    steps = Column(JSON, default=[])
    result = Column(Text, nullable=True)
    error = Column(JSON, nullable=True)
    strategy = Column(String, nullable=True)
    profile = Column(String, nullable=True)
    cognition = Column(String, nullable=True)
    replans = Column(String, default=0)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
