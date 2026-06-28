from pydantic import BaseModel
from typing import Literal


class ExecutionState(BaseModel):
    execution_id: str
    goal: str
    plan: list[dict] = []
    status: Literal["running", "paused", "done"] = "running"
    current_step: int = 0
    history: list[dict] = []


class StateStore:
    def __init__(self):
        self._states: dict[str, ExecutionState] = {}

    def save(self, state: ExecutionState):
        self._states[state.execution_id] = state

    def get(self, execution_id: str) -> ExecutionState | None:
        return self._states.get(execution_id)

    def delete(self, execution_id: str):
        self._states.pop(execution_id, None)
