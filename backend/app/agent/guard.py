import time
from app.agent.cognition import CognitionConfig


class ExecutionGuard:
    def __init__(self, max_steps: int = 10, max_retry: int = 2, timeout_ms: int = 5000):
        self.max_steps = max_steps
        self.max_retry = max_retry
        self.timeout_ms = timeout_ms
        self._step_count = 0
        self._retry_count = 0
        self._start_time = 0

    def reset(self, cognition_config: CognitionConfig = None):
        self._step_count = 0
        self._retry_count = 0
        self._start_time = time.time()
        if cognition_config:
            self.max_steps = cognition_config.max_steps

    def can_step(self) -> bool:
        return self._step_count < self.max_steps

    def step_used(self) -> int:
        self._step_count += 1
        return self._step_count

    def can_retry(self) -> bool:
        return self._retry_count < self.max_retry

    def retry_used(self) -> int:
        self._retry_count += 1
        return self._retry_count

    def is_timeout(self) -> bool:
        if self._start_time == 0:
            return False
        elapsed_ms = (time.time() - self._start_time) * 1000
        return elapsed_ms > self.timeout_ms

    def elapsed_ms(self) -> float:
        if self._start_time == 0:
            return 0
        return (time.time() - self._start_time) * 1000

    def status(self) -> dict:
        return {
            "steps_used": self._step_count,
            "max_steps": self.max_steps,
            "retries_used": self._retry_count,
            "max_retry": self.max_retry,
            "elapsed_ms": round(self.elapsed_ms(), 2),
            "timeout_ms": self.timeout_ms
        }
