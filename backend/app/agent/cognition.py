from pydantic import BaseModel


class CognitionLevel(BaseModel):
    level: str  # shallow, medium, deep
    reasoning_steps: int  # 1-10
    planning_depth: str  # low, high
    description: str = ""


COGNITION_LEVELS = {
    "shallow": CognitionLevel(
        level="shallow",
        reasoning_steps=2,
        planning_depth="low",
        description="fast decisions, minimal reasoning"
    ),
    "medium": CognitionLevel(
        level="medium",
        reasoning_steps=5,
        planning_depth="medium",
        description="balanced reasoning and planning"
    ),
    "deep": CognitionLevel(
        level="deep",
        reasoning_steps=8,
        planning_depth="high",
        description="thorough analysis, comprehensive planning"
    )
}

PROFILE_COGNITION_MAP = {
    "balanced": "medium",
    "efficient_executor": "shallow",
    "safe_executor": "deep",
    "aggressive": "shallow",
    "learning": "deep"
}


def get_cognition_level(profile_id: str) -> CognitionLevel:
    level_id = PROFILE_COGNITION_MAP.get(profile_id, "medium")
    return COGNITION_LEVELS[level_id]


def get_cognition_for_level(level: str) -> CognitionLevel:
    return COGNITION_LEVELS.get(level, COGNITION_LEVELS["medium"])
