from pydantic import BaseModel


class CognitionConfig(BaseModel):
    level: str  # shallow, medium, deep
    max_steps: int
    allow_replan: bool
    verification_level: str  # none, light, strict
    description: str = ""


COGNITION_CONFIGS = {
    "shallow": CognitionConfig(
        level="shallow",
        max_steps=1,
        allow_replan=False,
        verification_level="none",
        description="fast decisions, no verification"
    ),
    "medium": CognitionConfig(
        level="medium",
        max_steps=5,
        allow_replan=True,
        verification_level="light",
        description="balanced reasoning with light validation"
    ),
    "deep": CognitionConfig(
        level="deep",
        max_steps=10,
        allow_replan=True,
        verification_level="strict",
        description="thorough analysis, full critic + retry"
    )
}

PROFILE_COGNITION_MAP = {
    "balanced": "medium",
    "efficient_executor": "shallow",
    "safe_executor": "deep",
    "aggressive": "shallow",
    "learning": "deep"
}


def get_cognition_config(profile_id: str) -> CognitionConfig:
    level = PROFILE_COGNITION_MAP.get(profile_id, "medium")
    return COGNITION_CONFIGS[level]


def get_cognition_config_by_level(level: str) -> CognitionConfig:
    return COGNITION_CONFIGS.get(level, COGNITION_CONFIGS["medium"])
