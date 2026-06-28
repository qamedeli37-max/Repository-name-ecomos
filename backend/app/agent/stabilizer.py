from pydantic import BaseModel
from typing import Optional


class CriticIssue(BaseModel):
    type: str  # logic, safety, efficiency
    severity: str  # low, medium, high
    message: str


class StabilizedCriticResult(BaseModel):
    score: float
    approved: bool
    issues: list[CriticIssue] = []
    suggestions: list[str] = []


class CriticStabilizer:
    THRESHOLD = 0.7

    def stabilize(self, raw_score: float, raw_suggestions: list[str], plan: list[dict], cognition_config=None) -> StabilizedCriticResult:
        score = max(0.0, min(1.0, raw_score))
        issues = self._extract_issues(raw_suggestions, plan, cognition_config)
        approved = self._decide_approval(score, issues)
        clean_suggestions = self._clean_suggestions(raw_suggestions)

        return StabilizedCriticResult(
            score=score,
            approved=approved,
            issues=issues,
            suggestions=clean_suggestions
        )

    def _decide_approval(self, score: float, issues: list[CriticIssue]) -> bool:
        has_high = any(i.severity == "high" for i in issues)
        if has_high:
            return False
        return score >= self.THRESHOLD

    def _extract_issues(self, suggestions: list[str], plan: list[dict], cognition_config) -> list[CriticIssue]:
        issues = []
        plan_tools = [s.get("tool") for s in plan]

        if not plan:
            issues.append(CriticIssue(type="logic", severity="high", message="empty plan"))
            return issues

        if cognition_config and len(plan) > cognition_config.max_steps:
            issues.append(CriticIssue(
                type="efficiency",
                severity="medium",
                message=f"plan has {len(plan)} steps but max is {cognition_config.max_steps}"
            ))

        if len(set(plan_tools)) < len(plan_tools):
            issues.append(CriticIssue(type="efficiency", severity="low", message="duplicate tools in plan"))

        for s in suggestions:
            s_lower = s.lower()
            if "fail" in s_lower or "error" in s_lower:
                issues.append(CriticIssue(type="safety", severity="high", message=s))
            elif "avoid" in s_lower:
                issues.append(CriticIssue(type="safety", severity="medium", message=s))

        return issues

    def _clean_suggestions(self, suggestions: list[str]) -> list[str]:
        seen = set()
        clean = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                clean.append(s)
        return clean[:5]
