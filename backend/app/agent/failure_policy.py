from enum import Enum


class FailureAction(Enum):
    RETRY = "retry"
    REPLAN = "replan"
    RETRY_ONCE = "retry_once"
    STOP = "stop"


class FailurePolicy:
    POLICIES = {
        "tool_error": FailureAction.RETRY,
        "validation_error": FailureAction.REPLAN,
        "timeout": FailureAction.RETRY_ONCE,
        "connection_error": FailureAction.RETRY_ONCE,
        "not_found": FailureAction.REPLAN,
        "permission_error": FailureAction.STOP,
        "critical_error": FailureAction.STOP,
        "unknown_error": FailureAction.RETRY
    }

    def __init__(self):
        self._retry_once_used: dict[str, bool] = {}

    def decide(self, error_type: str, step: str, retry_count: int, max_retry: int) -> FailureAction:
        action = self.POLICIES.get(error_type, FailureAction.RETRY)

        if action == FailureAction.RETRY and retry_count >= max_retry:
            return FailureAction.REPLAN

        if action == FailureAction.RETRY_ONCE:
            key = f"{step}:{error_type}"
            if self._retry_once_used.get(key):
                return FailureAction.REPLAN
            self._retry_once_used[key] = True
            return FailureAction.RETRY

        return action

    def reset(self):
        self._retry_once_used.clear()

    def classify_error(self, error: str) -> str:
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
        if "critical" in error_lower or "fatal" in error_lower:
            return "critical_error"
        return "tool_error"
