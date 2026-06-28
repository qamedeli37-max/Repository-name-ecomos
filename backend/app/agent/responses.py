from pydantic import BaseModel
from typing import Any, Optional


class ErrorDetail(BaseModel):
    type: str
    message: str
    step: Optional[int] = None


class ToolResult(BaseModel):
    tool: str
    status: str
    result: Optional[Any] = None
    error: Optional[ErrorDetail] = None


class AgentResponse(BaseModel):
    execution_id: str
    status: str
    goal: str
    result: Optional[str] = None
    steps: list[ToolResult]
    score: float = 0
    replans: int = 0
    strategy: str = "default"
    profile: str = "balanced"
    cognition: str = "medium"
    error: Optional[ErrorDetail] = None
    tenant_id: Optional[str] = None
    timeline: Optional[dict] = None
    debug: Optional[dict] = None


class ErrorResponse(BaseModel):
    status: str = "failed"
    error: ErrorDetail


def format_tool_result(step_result: dict) -> ToolResult:
    if step_result.get("status") == "success":
        return ToolResult(
            tool=step_result.get("tool", ""),
            status="success",
            result=step_result.get("result"),
            error=None
        )
    else:
        return ToolResult(
            tool=step_result.get("tool", ""),
            status="failed",
            result=None,
            error=ErrorDetail(
                type="tool_error",
                message=step_result.get("error", "unknown error"),
                step=None
            )
        )


def format_agent_response(raw: dict) -> AgentResponse:
    steps = raw.get("steps", [])
    formatted_steps = []
    for i, step in enumerate(steps):
        formatted = format_tool_result(step)
        if formatted.error:
            formatted.error.step = i + 1
        formatted_steps.append(formatted)

    has_failure = any(s.get("status") == "failed" for s in steps)
    status = "failed" if has_failure else "success"

    result_text = None
    if not has_failure and formatted_steps:
        last = formatted_steps[-1]
        if last.result:
            result_text = str(last.result)

    error = None
    if has_failure:
        failed_step = next((s for s in formatted_steps if s.status == "failed"), None)
        if failed_step and failed_step.error:
            error = failed_step.error

    return AgentResponse(
        execution_id=raw.get("execution_id", ""),
        status=status,
        goal=raw.get("goal", ""),
        result=result_text,
        steps=formatted_steps,
        score=raw.get("score", 0),
        replans=raw.get("replans", 0),
        strategy=raw.get("strategy", "default"),
        profile=raw.get("profile", "balanced"),
        cognition=raw.get("cognition", "medium"),
        error=error,
        tenant_id=raw.get("tenant_id"),
        timeline=raw.get("timeline"),
        debug=raw.get("debug")
    )


def error_response(error_type: str, message: str, step: int = None) -> ErrorResponse:
    return ErrorResponse(
        status="failed",
        error=ErrorDetail(
            type=error_type,
            message=message,
            step=step
        )
    )
