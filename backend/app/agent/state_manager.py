from uuid import uuid4
from app.agent.state import ExecutionState, StateStore
from app.agent.memory import ExecutionMemory, ExecutionRecord, PlanScoreRecord, FailureRecord


class TenantState:
    def __init__(self):
        self.store = StateStore()
        self.memory = ExecutionMemory()


class StateManager:
    def __init__(self):
        self.tenant_states: dict[str, TenantState] = {}
        self.default = TenantState()

    def _get_tenant_state(self, tenant_id: str = None) -> TenantState:
        if not tenant_id:
            return self.default
        if tenant_id not in self.tenant_states:
            self.tenant_states[tenant_id] = TenantState()
        return self.tenant_states[tenant_id]

    def create(self, goal: str, plan: list[dict], tenant_id: str = None) -> ExecutionState:
        ts = self._get_tenant_state(tenant_id)
        state = ExecutionState(
            execution_id=str(uuid4()),
            goal=goal,
            plan=plan,
            status="running",
            current_step=0,
            history=[]
        )
        state.tenant_id = tenant_id
        ts.store.save(state)
        return state

    def get(self, execution_id: str, tenant_id: str = None) -> ExecutionState | None:
        ts = self._get_tenant_state(tenant_id)
        return ts.store.get(execution_id)

    def save(self, state: ExecutionState, tenant_id: str = None):
        ts = self._get_tenant_state(tenant_id)
        ts.store.save(state)

    def mark_done(self, state: ExecutionState, success: bool = True, tenant_id: str = None):
        state.status = "done"
        ts = self._get_tenant_state(tenant_id)
        ts.store.save(state)

        failed_steps = [s for s in state.history if s.get("status") == "failed"]
        successful_plan = [s for s in state.history if s.get("status") == "success"]

        record = ExecutionRecord(
            goal=state.goal,
            success=success and len(failed_steps) == 0,
            failed_steps=failed_steps,
            successful_plan=successful_plan
        )
        ts.memory.add(record)

    def record_plan_score(self, plan_id: str, plan_steps: list[dict], score: float, success: bool, goal_type: str, tenant_id: str = None):
        ts = self._get_tenant_state(tenant_id)
        record = PlanScoreRecord(
            plan_id=plan_id,
            plan_steps=plan_steps,
            score=score,
            result="success" if success else "failed",
            goal_type=goal_type
        )
        ts.memory.add_plan_score(record)

    def record_failure(self, step: str, error: str, goal_type: str, context: dict = None, tenant_id: str = None):
        ts = self._get_tenant_state(tenant_id)
        error_type = self._classify_error(error)
        root_cause = self._infer_root_cause(step, error, error_type)

        record = FailureRecord(
            step=step,
            error_type=error_type,
            root_cause=root_cause,
            goal_type=goal_type,
            context=context or {}
        )
        ts.memory.add_failure(record)

    def _classify_error(self, error: str) -> str:
        error_lower = error.lower()
        if "not found" in error_lower or "不存在" in error_lower:
            return "not_found"
        if "validation" in error_lower or "required" in error_lower:
            return "validation_error"
        if "timeout" in error_lower:
            return "timeout"
        if "connection" in error_lower:
            return "connection_error"
        if "permission" in error_lower or "denied" in error_lower:
            return "permission_error"
        return "unknown_error"

    def _infer_root_cause(self, step: str, error: str, error_type: str) -> str:
        if error_type == "not_found":
            return "resource_does_not_exist_or_invalid_id"
        if error_type == "validation_error":
            return "missing_or_invalid_required_field"
        if error_type == "timeout":
            return "operation_took_too_long"
        if error_type == "connection_error":
            return "service_unavailable"
        if error_type == "permission_error":
            return "insufficient_access_rights"
        return f"error_in_{step}"

    def append_result(self, state: ExecutionState, result: dict, tenant_id: str = None):
        state.history.append(result)
        state.current_step += 1
        ts = self._get_tenant_state(tenant_id)
        ts.store.save(state)

    def get_memory(self, tenant_id: str = None):
        ts = self._get_tenant_state(tenant_id)
        return ts.memory
