import json
import os
from dotenv import load_dotenv

load_dotenv()


class CriticResult:
    def __init__(self, selected_plan: str, score_map: dict, plan_details: dict):
        self.selected_plan = selected_plan
        self.score_map = score_map
        self.plan_details = plan_details

    def to_dict(self):
        return {
            "selected_plan": self.selected_plan,
            "score_map": self.score_map
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

    def evaluate(self, goal: dict, plans: list[dict], memory=None) -> CriticResult:
        if self.client:
            return self._llm_evaluate(goal, plans, memory)
        return self._rule_evaluate(goal, plans, memory)

    def _llm_evaluate(self, goal: dict, plans: list[dict], memory=None):
        memory_context = self._build_memory_context(goal, memory)
        plans_json = json.dumps(plans, indent=2)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a plan critic. Evaluate and select the best plan.

Return ONLY valid JSON:
{{
    "selected_plan": "plan_id",
    "score_map": {{"a": 0.6, "b": 0.9}},
    "reasoning": "why selected"
}}

Rules:
- Choose the plan most likely to succeed
- Consider past high-score patterns
- Consider past failures

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
        plan_details = {p["id"]: p for p in plans}

        return CriticResult(
            selected_plan=selected_id,
            score_map=score_map,
            plan_details=plan_details
        )

    def _rule_evaluate(self, goal: dict, plans: list[dict], memory=None):
        score_map = {}
        goal_text = goal.get("goal", "").lower()

        high_score_plans = memory.get_high_score_plans() if memory else []
        high_score_tools = set()
        for record in high_score_plans:
            for step in record.plan_steps:
                high_score_tools.add(step.get("tool", ""))

        for plan in plans:
            score = 1.0
            plan_id = plan.get("id", "a")
            steps = plan.get("steps", [])
            plan_tools = [s.get("tool") for s in steps]

            if not steps:
                score = 0.0

            if "create" in goal_text or "创建" in goal_text:
                if "product.create" not in plan_tools:
                    score -= 0.3

            if "list" in goal_text or "show" in goal_text or "查看" in goal_text:
                if "product.list" not in plan_tools and "product.get" not in plan_tools:
                    score -= 0.3

            if memory:
                failed = memory.get_failed_patterns(goal_text)
                for f in failed:
                    if f.get("tool") in plan_tools:
                        score -= 0.2

            if high_score_tools and any(t in high_score_tools for t in plan_tools):
                score += 0.1

            score_map[plan_id] = min(1.0, max(0.0, score))

        selected_id = max(score_map, key=score_map.get)
        plan_details = {p["id"]: p for p in plans}

        return CriticResult(
            selected_plan=selected_id,
            score_map=score_map,
            plan_details=plan_details
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

        return "\n".join(parts) if parts else ""
