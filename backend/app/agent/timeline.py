import time
from pydantic import BaseModel
from typing import Optional


class TimelineEntry(BaseModel):
    phase: str  # planning, critic, executing, retry, replan
    step: Optional[str] = None
    duration_ms: float
    started_at: float
    finished_at: float
    metadata: dict = {}


class ExecutionTimeline:
    def __init__(self):
        self.entries: list[TimelineEntry] = []
        self._start: float = 0

    def start(self):
        self._start = time.time()
        self.entries = []

    def record(self, phase: str, step: str = None, metadata: dict = None) -> float:
        now = time.time()
        duration = (now - self._start) * 1000 if self._start else 0
        entry = TimelineEntry(
            phase=phase,
            step=step,
            duration_ms=round(duration, 2),
            started_at=self._start,
            finished_at=now,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        self._start = now
        return duration

    def get_summary(self) -> dict:
        total = sum(e.duration_ms for e in self.entries)
        phases = {}
        for e in self.entries:
            if e.phase not in phases:
                phases[e.phase] = {"count": 0, "total_ms": 0}
            phases[e.phase]["count"] += 1
            phases[e.phase]["total_ms"] += e.duration_ms

        return {
            "total_ms": round(total, 2),
            "phases": {k: {**v, "total_ms": round(v["total_ms"], 2)} for k, v in phases.items()},
            "entries": [e.model_dump() for e in self.entries]
        }

    def to_list(self) -> list[dict]:
        return [e.model_dump() for e in self.entries]
