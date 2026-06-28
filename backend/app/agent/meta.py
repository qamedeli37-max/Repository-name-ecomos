from pydantic import BaseModel


class PerformanceMetrics(BaseModel):
    success_rate: float = 0.0
    avg_steps: float = 0.0
    total_executions: int = 0
    avg_replans: float = 0.0
    avg_score: float = 0.0


class MetaState(BaseModel):
    current_strategy: str = "default"
    strategy_history: list[str] = ["default"]
    performance: PerformanceMetrics = PerformanceMetrics()
    recent_goals: list[dict] = []


class MetaStateManager:
    def __init__(self):
        self.state = MetaState()
        self.execution_log: list[dict] = []

    def record_execution(self, goal: str, strategy: str, success: bool, steps_count: int, replans: int, score: float):
        self.execution_log.append({
            "goal": goal,
            "strategy": strategy,
            "success": success,
            "steps_count": steps_count,
            "replans": replans,
            "score": score
        })

        if strategy != self.state.current_strategy:
            self.state.current_strategy = strategy
            if strategy not in self.state.strategy_history:
                self.state.strategy_history.append(strategy)

        self._update_performance()
        self._update_recent_goals(goal, strategy, success)

    def _update_performance(self):
        if not self.execution_log:
            return

        total = len(self.execution_log)
        successes = sum(1 for e in self.execution_log if e["success"])
        avg_steps = sum(e["steps_count"] for e in self.execution_log) / total
        avg_replans = sum(e["replans"] for e in self.execution_log) / total
        avg_score = sum(e["score"] for e in self.execution_log) / total

        self.state.performance = PerformanceMetrics(
            success_rate=successes / total,
            avg_steps=avg_steps,
            total_executions=total,
            avg_replans=avg_replans,
            avg_score=avg_score
        )

    def _update_recent_goals(self, goal: str, strategy: str, success: bool):
        self.state.recent_goals.append({
            "goal": goal[:50],
            "strategy": strategy,
            "success": success
        })
        if len(self.state.recent_goals) > 10:
            self.state.recent_goals = self.state.recent_goals[-10:]

    def get_state(self) -> MetaState:
        return self.state

    def get_strategy_effectiveness(self) -> dict:
        strategy_stats = {}
        for entry in self.execution_log:
            s = entry["strategy"]
            if s not in strategy_stats:
                strategy_stats[s] = {"total": 0, "success": 0, "avg_steps": 0, "avg_score": 0}
            strategy_stats[s]["total"] += 1
            if entry["success"]:
                strategy_stats[s]["success"] += 1
            strategy_stats[s]["avg_steps"] += entry["steps_count"]
            strategy_stats[s]["avg_score"] += entry["score"]

        for s, stats in strategy_stats.items():
            stats["success_rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            stats["avg_steps"] = stats["avg_steps"] / stats["total"] if stats["total"] > 0 else 0
            stats["avg_score"] = stats["avg_score"] / stats["total"] if stats["total"] > 0 else 0

        return strategy_stats
