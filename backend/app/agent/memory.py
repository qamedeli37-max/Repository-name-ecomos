from pydantic import BaseModel


class ExecutionRecord(BaseModel):
    goal: str
    success: bool
    failed_steps: list[dict] = []
    successful_plan: list[dict] = []


class PlanScoreRecord(BaseModel):
    plan_id: str
    plan_steps: list[dict]
    score: float
    result: str  # success/failed
    goal_type: str


class FailureRecord(BaseModel):
    step: str
    error_type: str
    root_cause: str
    goal_type: str
    context: dict = {}


class ExecutionMemory:
    def __init__(self):
        self.records: list[ExecutionRecord] = []
        self.plan_scores: list[PlanScoreRecord] = []
        self.failures: list[FailureRecord] = []

    def add(self, record: ExecutionRecord):
        self.records.append(record)

    def add_plan_score(self, record: PlanScoreRecord):
        self.plan_scores.append(record)

    def add_failure(self, record: FailureRecord):
        self.failures.append(record)

    def get_similar(self, goal: str) -> list[ExecutionRecord]:
        goal_lower = goal.lower()
        return [r for r in self.records if goal_lower in r.goal.lower() or r.goal.lower() in goal_lower]

    def get_successful_plans(self, goal: str) -> list[list[dict]]:
        return [r.successful_plan for r in self.get_similar(goal) if r.success and r.successful_plan]

    def get_failed_patterns(self, goal: str) -> list[dict]:
        failures = []
        for r in self.get_similar(goal):
            if not r.success:
                failures.extend(r.failed_steps)
        return failures

    def get_failures_by_type(self, error_type: str = None) -> list[FailureRecord]:
        if error_type:
            return [f for f in self.failures if f.error_type == error_type]
        return self.failures

    def get_failure_patterns(self) -> dict:
        patterns = {}
        for f in self.failures:
            key = f"{f.step}:{f.error_type}"
            if key not in patterns:
                patterns[key] = {"step": f.step, "error_type": f.error_type, "count": 0, "root_causes": []}
            patterns[key]["count"] += 1
            if f.root_cause not in patterns[key]["root_causes"]:
                patterns[key]["root_causes"].append(f.root_cause)
        return patterns

    def get_high_score_plans(self, min_score: float = 0.8, goal_type: str = None) -> list[PlanScoreRecord]:
        records = self.plan_scores
        if goal_type:
            records = [r for r in records if r.goal_type == goal_type]
        return [r for r in records if r.score >= min_score]

    def get_plan_stats(self) -> dict:
        if not self.plan_scores:
            return {"total": 0, "avg_score": 0, "high_score_count": 0}
        scores = [r.score for r in self.plan_scores]
        return {
            "total": len(scores),
            "avg_score": sum(scores) / len(scores),
            "high_score_count": sum(1 for s in scores if s >= 0.8)
        }

    def summary(self) -> dict:
        total = len(self.records)
        success = sum(1 for r in self.records if r.success)
        return {
            "total_executions": total,
            "successful": success,
            "failed": total - success,
            "plan_stats": self.get_plan_stats(),
            "failure_patterns": len(self.get_failure_patterns())
        }
