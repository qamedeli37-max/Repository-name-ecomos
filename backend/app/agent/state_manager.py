from uuid import uuid4
from app.agent.state import ExecutionState, StateStore


class StateManager:
    def __init__(self):
        self.store = StateStore()

    def create(self, goal: str, plan: list[dict]) -> ExecutionState:
        state = ExecutionState(
            execution_id=str(uuid4()),
            goal=goal,
            plan=plan,
            status="running",
            current_step=0,
            history=[]
        )
        self.store.save(state)
        return state

    def get(self, execution_id: str) -> ExecutionState | None:
        return self.store.get(execution_id)

    def save(self, state: ExecutionState):
        self.store.save(state)

    def mark_done(self, state: ExecutionState):
        state.status = "done"
        self.store.save(state)

    def append_result(self, state: ExecutionState, result: dict):
        state.history.append(result)
        state.current_step += 1
        self.store.save(state)
