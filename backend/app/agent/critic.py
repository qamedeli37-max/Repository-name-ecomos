import json
import os
from dotenv import load_dotenv

load_dotenv()


class CriticResult:
    def __init__(self, score: float, issues: list[str], approved: bool):
        self.score = score
        self.issues = issues
        self.approved = approved

    def to_dict(self):
        return {
            "score": self.score,
            "issues": self.issues,
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

    def evaluate(self, goal: dict, plan: list[dict], memory=None) -> CriticResult:
        if self.client:
            return self._llm_evaluate(goal, plan, memory)
        return self._rule_evaluate(goal, plan, memory)

    def _llm_evaluate(self, goal: dict, plan: list[dict], memory=None):
        memory_context = self._build_memory_context(goal, memory)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a plan critic. Evaluate if the plan achieves the goal.

Return ONLY valid JSON:
{{
    "score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "approved": true/false
}}

Rules:
- score >= 0.7 and no critical issues → approved
- score < 0.7 or critical issues → not approved

{memory_context}"""
                },
                {
                    "role": "user",
                    "content": f"Goal: {json.dumps(goal)}\nPlan: {json.dumps(plan)}"
                }
            ]
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return CriticResult(
            score=data.get("score", 0),
            issues=data.get("issues", []),
            approved=data.get("approved", False)
        )

    def _rule_evaluate(self, goal: dict, plan: list[dict], memory=None):
        issues = []
        score = 1.0

        if not plan:
            issues.append("empty plan")
            score = 0.0

        goal_text = goal.get("goal", "").lower()
        plan_tools = [s.get("tool") for s in plan]

        if "create" in goal_text or "创建" in goal_text:
            if "product.create" not in plan_tools:
                issues.append("goal requires create but plan missing product.create")
                score -= 0.3

        if "list" in goal_text or "show" in goal_text or "查看" in goal_text:
            if "product.list" not in plan_tools and "product.get" not in plan_tools:
                issues.append("goal requires list/get but plan missing")
                score -= 0.3

        if memory:
            failed = memory.get_failed_patterns(goal_text)
            for f in failed:
                if f.get("tool") in plan_tools:
                    issues.append(f"plan includes previously failed tool: {f.get('tool')}")
                    score -= 0.2

        score = max(0.0, score)
        approved = score >= 0.7 and not any("critical" in i.lower() for i in issues)

        return CriticResult(score=score, issues=issues, approved=approved)

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        goal_text = goal.get("goal", "")
        failed = memory.get_failed_patterns(goal_text)
        if failed:
            return f"Past failures to avoid: {json.dumps(failed[:3])}"
        return ""
