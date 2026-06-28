import json
import os
from dotenv import load_dotenv

load_dotenv()


class CriticResult:
    def __init__(self, score: float, suggestions: list[str] = None, approved: bool = True):
        self.score = score
        self.suggestions = suggestions or []
        self.approved = approved

    def to_dict(self):
        return {
            "score": self.score,
            "suggestions": self.suggestions,
            "approved": self.approved
        }


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

    def evaluate(self, goal: dict, plan: list[dict], memory=None, cognition_config=None) -> CriticResult:
        if cognition_config and cognition_config.verification_level == "none":
            return CriticResult(score=1.0, suggestions=["verification skipped"], approved=True)

        if self.client:
            return self._llm_evaluate(goal, plan, memory, cognition_config)
        return self._rule_evaluate(goal, plan, memory, cognition_config)

    def _llm_evaluate(self, goal: dict, plan: list[dict], memory=None, cognition_config=None):
        plan_json = json.dumps(plan, indent=2)
        memory_context = self._build_memory_context(goal, memory)
        cog_context = f"Verification: {cognition_config.verification_level}" if cognition_config else ""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a Critic. Evaluate this plan.
Return ONLY valid JSON:
{{
    "score": 0.85,
    "suggestions": ["suggestion1"],
    "approved": true
}}
{cog_context}
{memory_context}"""
                },
                {"role": "user", "content": f"Goal: {json.dumps(goal)}\nPlan: {plan_json}"}
            ]
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return CriticResult(
            score=data.get("score", 0.5),
            suggestions=data.get("suggestions", []),
            approved=data.get("approved", True)
        )

    def _rule_evaluate(self, goal: dict, plan: list[dict], memory=None, cognition_config=None):
        score = 1.0
        suggestions = []
        goal_text = goal.get("goal", "").lower()
        plan_tools = [s.get("tool") for s in plan]

        if not plan:
            return CriticResult(score=0.0, suggestions=["empty plan"], approved=False)

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

        if cognition_config and len(plan) > cognition_config.max_steps:
            score -= 0.3
            suggestions.append(f"plan has {len(plan)} steps but max is {cognition_config.max_steps}")

        for tool in plan_tools:
            if tool in avoid_steps:
                score -= 0.3
                suggestions.append(f"tool {tool} has failed before")

        if "create" in goal_text or "创建" in goal_text:
            if "product.create" not in plan_tools:
                score -= 0.3
                suggestions.append("create goal but no create tool")

        if "list" in goal_text or "show" in goal_text or "查看" in goal_text:
            if "product.list" not in plan_tools and "product.get" not in plan_tools:
                score -= 0.3
                suggestions.append("list goal but no list/get tool")

        if high_score_tools and any(t in high_score_tools for t in plan_tools):
            score += 0.1

        score = min(1.0, max(0.0, score))
        approved = score >= 0.5

        if not suggestions:
            suggestions.append("plan looks good")

        return CriticResult(score=score, suggestions=suggestions, approved=approved)

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        parts = []
        failed = memory.get_failed_patterns(goal.get("goal", ""))
        if failed:
            parts.append(f"Past failures: {json.dumps(failed[:3])}")
        high_score = memory.get_high_score_plans(min_score=0.8)
        if high_score:
            patterns = [{"tools": [s["tool"] for s in r.plan_steps], "score": r.score} for r in high_score[:3]]
            parts.append(f"High-score patterns: {json.dumps(patterns)}")
        return "\n".join(parts) if parts else ""
