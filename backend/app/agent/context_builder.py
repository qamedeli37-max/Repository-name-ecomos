from pydantic import BaseModel
from typing import Optional


class PlannerContext(BaseModel):
    goal: str
    goal_type: str
    constraints: list[str] = []
    history: list[dict] = []
    policy: dict = {}
    critic_feedback: Optional[dict] = None


class ContextBuilder:
    def build(self, goal: dict, profile, strategy, cognition_config, memory, critic_feedback=None) -> PlannerContext:
        goal_text = goal.get("goal", "")
        goal_type = self._detect_goal_type(goal_text)

        constraints = list(goal.get("constraints", []))
        constraints.extend(self._profile_constraints(profile))
        constraints.extend(self._strategy_constraints(strategy))
        constraints.extend(self._cognition_constraints(cognition_config))

        history = self._build_history(goal_text, memory)

        policy = {
            "max_steps": cognition_config.max_steps if cognition_config else 5,
            "allow_replan": cognition_config.allow_replan if cognition_config else True,
            "tool_priority": strategy.tool_priority if strategy else [],
            "avoid_tools": strategy.avoid_tools if strategy else [],
            "planner_style": profile.planner_style if profile else "adaptive"
        }

        return PlannerContext(
            goal=goal_text,
            goal_type=goal_type,
            constraints=constraints,
            history=history,
            policy=policy,
            critic_feedback=critic_feedback
        )

    def _detect_goal_type(self, goal: str) -> str:
        goal_lower = goal.lower()
        if "create" in goal_lower or "创建" in goal_lower:
            return "product_create"
        if "update" in goal_lower or "修改" in goal_lower:
            return "product_update"
        if "list" in goal_lower or "show" in goal_lower or "查看" in goal_lower:
            return "product_list"
        return "unknown"

    def _profile_constraints(self, profile) -> list[str]:
        if not profile:
            return []
        constraints = []
        if profile.planner_style == "minimal_steps":
            constraints.append("keep plan minimal, max 2 steps")
        elif profile.planner_style == "thorough":
            constraints.append("include fallback steps")
        return constraints

    def _strategy_constraints(self, strategy) -> list[str]:
        if not strategy:
            return []
        constraints = []
        if strategy.avoid_tools:
            constraints.append(f"avoid tools: {', '.join(strategy.avoid_tools)}")
        constraints.append(f"max {strategy.max_steps} steps")
        return constraints

    def _cognition_constraints(self, cognition_config) -> list[str]:
        if not cognition_config:
            return []
        return [f"cognition level: {cognition_config.level}, max {cognition_config.max_steps} steps"]

    def _build_history(self, goal_text: str, memory) -> list[dict]:
        if not memory:
            return []
        history = []
        failed = memory.get_failed_patterns(goal_text)
        if failed:
            history.append({"type": "failures", "data": failed[:3]})
        high_score = memory.get_high_score_plans(min_score=0.8)
        if high_score:
            patterns = [{"tools": [s["tool"] for s in r.plan_steps], "score": r.score} for r in high_score[:3]]
            history.append({"type": "success_patterns", "data": patterns})
        return history
