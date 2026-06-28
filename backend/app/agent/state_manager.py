from uuid import uuid4
from app.agent.state import ExecutionState, StateStore
from app.agent.memory import ExecutionMemory, ExecutionRecord


class StateManager:
    def __init__(self):
        self.store = StateStore()
        self.memory = ExecutionMemory()

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

    def mark_done(self, state: ExecutionState, success: bool = True):
        state.status = "done"
        self.store.save(state)

        failed_steps = [s for s in state.history if s.get("status") == "failed"]
        successful_plan = [s for s in state.history if s.get("status") == "success"]

        record = ExecutionRecord(
            goal=state.goal,
            success=success and len(failed_steps) == 0,
            failed_steps=failed_steps,
            successful_plan=successful_plan
        )
        self.memory.add(record)

    def append_result(self, state: ExecutionState, result: dict):
        state.history.append(result)
        state.current_step += 1
        self.store.save(state)

    def get_memory(self):
        return self.memory
