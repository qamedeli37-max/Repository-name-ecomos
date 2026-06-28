import json
import os
from dotenv import load_dotenv

load_dotenv()


class CriticResult:
    def __init__(self, selected_plan: str, score_map: dict, plan_details: dict, suggestions: list[str] = None, suggested_strategy: str = None, meta_analysis: dict = None):
        self.selected_plan = selected_plan
        self.score_map = score_map
        self.plan_details = plan_details
        self.suggestions = suggestions or []
        self.suggested_strategy = suggested_strategy
        self.meta_analysis = meta_analysis or {}

    def to_dict(self):
        result = {
            "selected_plan": self.selected_plan,
            "score_map": self.score_map,
            "suggestions": self.suggestions
        }
        if self.suggested_strategy:
            result["suggested_strategy"] = self.suggested_strategy
        if self.meta_analysis:
            result["meta_analysis"] = self.meta_analysis
        return result


class CriticAgent:
    def __init__(self):
        self._init_llm()

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def evaluate(self, goal: dict, plans: list[dict], memory=None, current_strategy=None, meta_state=None) -> CriticResult:
        if self.client:
            return self._llm_evaluate(goal, plans, memory, current_strategy, meta_state)
        return self._rule_evaluate(goal, plans, memory, current_strategy, meta_state)

    def _llm_evaluate(self, goal: dict, plans: list[dict], memory=None, current_strategy=None, meta_state=None):
        memory_context = self._build_memory_context(goal, memory)
        plans_json = json.dumps(plans, indent=2)
        strategy_context = f"Current strategy: {current_strategy.name if current_strategy else 'default'}"
        meta_context = self._build_meta_context(meta_state)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a Meta-Critic. Evaluate plans AND analyze system performance.

Analyze:
- Plan quality
- Strategy effectiveness
- Execution efficiency
- System-level performance trends

Return ONLY valid JSON:
{{
    "selected_plan": "plan_id",
    "score_map": {{"a": 0.6, "b": 0.9}},
    "suggestions": ["suggestion1"],
    "suggested_strategy": "strategy_id_or_null",
    "meta_analysis": {{
        "strategy_effective": true,
        "efficiency_trend": "improving|stable|declining",
        "system_recommendation": "recommendation"
    }}
}}

{strategy_context}
{meta_context}
{memory_context}"""
                },
                {
                    "role": "user",
                    "content": f"Goal: {json.dumps(goal)}\nPlans: {plans_json}"
                }
            ]
        )
        content = response.choices[0].message.content
        data = json.loads(content)

        selected_id = data.get("selected_plan", plans[0].get("id", "a"))
        score_map = data.get("score_map", {})
        suggestions = data.get("suggestions", [])
        suggested_strategy = data.get("suggested_strategy")
        meta_analysis = data.get("meta_analysis", {})
        plan_details = {p["id"]: p for p in plans}

        return CriticResult(
            selected_plan=selected_id,
            score_map=score_map,
            plan_details=plan_details,
            suggestions=suggestions,
            suggested_strategy=suggested_strategy,
            meta_analysis=meta_analysis
        )

    def _rule_evaluate(self, goal: dict, plans: list[dict], memory=None, current_strategy=None, meta_state=None):
        score_map = {}
        suggestions = []
        suggested_strategy = None
        meta_analysis = {}
        goal_text = goal.get("goal", "").lower()

        high_score_plans = memory.get_high_score_plans() if memory else []
        high_score_tools = set()
        for record in high_score_plans:
            for step in record.plan_steps:
                high_score_tools.add(step.get("tool", ""))

        failure_patterns = memory.get_failure_patterns() if memory else {}
        avoid_steps = set()
        for key, pattern in failure_patterns.items():
            if pattern["count"] >= 2:
                avoid_steps.add(pattern["step"])

        strategy_effective = True
        efficiency_trend = "stable"

        if meta_state:
            perf = meta_state.performance
            if perf.total_executions >= 3:
                if perf.success_rate < 0.7:
                    strategy_effective = False
                    efficiency_trend = "declining"
                    suggestions.append(f"success rate {perf.success_rate:.0%} is low - consider strategy change")
                elif perf.success_rate > 0.9:
                    efficiency_trend = "improving"

                if perf.avg_replans > 1.5:
                    strategy_effective = False
                    suggestions.append(f"high avg replans ({perf.avg_replans:.1f}) indicates planning issues")

            if len(failure_patterns) >= 3:
                suggested_strategy = "safe_mode"
                suggestions.append("multiple failure patterns - switch to safe_mode")

            strategy_stats = {}
            for entry in meta_state.recent_goals:
                s = entry["strategy"]
                if s not in strategy_stats:
                    strategy_stats[s] = {"total": 0, "success": 0}
                strategy_stats[s]["total"] += 1
                if entry["success"]:
                    strategy_stats[s]["success"] += 1

            for s, stats in strategy_stats.items():
                if stats["total"] >= 2:
                    sr = stats["success"] / stats["total"]
                    if sr < 0.5:
                        strategy_effective = False
                        suggestions.append(f"strategy '{s}' has {sr:.0%} success rate")

        meta_analysis = {
            "strategy_effective": strategy_effective,
            "efficiency_trend": efficiency_trend,
            "system_recommendation": "continue current strategy" if strategy_effective else "consider strategy adjustment"
        }

        for plan in plans:
            score = 1.0
            plan_id = plan.get("id", "a")
            steps = plan.get("steps", [])
            plan_tools = [s.get("tool") for s in steps]

            if not steps:
                score = 0.0

            if current_strategy:
                if current_strategy.avoid_tools:
                    for tool in plan_tools:
                        if tool in current_strategy.avoid_tools:
                            score -= 0.3

                if len(steps) > current_strategy.max_steps:
                    score -= 0.1

            if "create" in goal_text or "创建" in goal_text:
                if "product.create" not in plan_tools:
                    score -= 0.3

            if "list" in goal_text or "show" in goal_text or "查看" in goal_text:
                if "product.list" not in plan_tools and "product.get" not in plan_tools:
                    score -= 0.3

            for tool in plan_tools:
                if tool in avoid_steps:
                    score -= 0.3

            if high_score_tools and any(t in high_score_tools for t in plan_tools):
                score += 0.1

            if len(set(plan_tools)) < len(plan_tools):
                score -= 0.1

            score_map[plan_id] = min(1.0, max(0.0, score))

        if not suggestions:
            suggestions.append("no structural issues detected")

        selected_id = max(score_map, key=score_map.get)
        plan_details = {p["id"]: p for p in plans}

        return CriticResult(
            selected_plan=selected_id,
            score_map=score_map,
            plan_details=plan_details,
            suggestions=suggestions,
            suggested_strategy=suggested_strategy,
            meta_analysis=meta_analysis
        )

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        goal_text = goal.get("goal", "")
        parts = []

        failed = memory.get_failed_patterns(goal_text)
        if failed:
            parts.append(f"Past failures to avoid: {json.dumps(failed[:3])}")

        high_score = memory.get_high_score_plans(min_score=0.8)
        if high_score:
            patterns = [{"tools": [s["tool"] for s in r.plan_steps], "score": r.score} for r in high_score[:3]]
            parts.append(f"High-score plan patterns: {json.dumps(patterns)}")

        failure_patterns = memory.get_failure_patterns()
        if failure_patterns:
            avoid_list = [{"step": v["step"], "error": v["error_type"], "count": v["count"]} for v in failure_patterns.values()]
            parts.append(f"Failure patterns: {json.dumps(avoid_list)}")

        return "\n".join(parts) if parts else ""

    def _build_meta_context(self, meta_state) -> str:
        if not meta_state:
            return ""
        parts = []

        parts.append(f"Current strategy: {meta_state.current_strategy}")
        parts.append(f"Strategy history: {json.dumps(meta_state.strategy_history)}")

        perf = meta_state.performance
        parts.append(f"Performance: success_rate={perf.success_rate:.2f}, avg_steps={perf.avg_steps:.1f}, avg_replans={perf.avg_replans:.1f}, avg_score={perf.avg_score:.2f}")

        if meta_state.recent_goals:
            parts.append(f"Recent goals: {json.dumps(meta_state.recent_goals[-3:])}")

        return "\n".join(parts) if parts else ""
