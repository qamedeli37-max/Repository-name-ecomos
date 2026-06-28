from pydantic import BaseModel


class ExecutionRecord(BaseModel):
    goal: str
    success: bool
    failed_steps: list[dict] = []
    successful_plan: list[dict] = []


class ExecutionMemory:
    def __init__(self):
        self.records: list[ExecutionRecord] = []

    def add(self, record: ExecutionRecord):
        self.records.append(record)

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

    def summary(self) -> dict:
        total = len(self.records)
        success = sum(1 for r in self.records if r.success)
        return {
            "total_executions": total,
            "successful": success,
            "failed": total - success
        }
