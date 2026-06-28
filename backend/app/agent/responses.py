from pydantic import BaseModel
from typing import Any, Optional


class ErrorDetail(BaseModel):
    type: str  # tool_error, validation_error, internal_error, not_found
    message: str
    step: Optional[int] = None


class ToolResult(BaseModel):
    tool: str
    status: str  # success, failed
    result: Optional[Any] = None
    error: Optional[ErrorDetail] = None


class AgentMeta(BaseModel):
    profile: str
    cognition: str
    strategy: str
    replans: int


class AgentResponse(BaseModel):
    execution_id: str
    status: str  # success, failed
    goal: str
    result: Optional[str] = None
    steps: list[ToolResult]
    meta: AgentMeta
    error: Optional[ErrorDetail] = None


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

    meta = AgentMeta(
        profile=raw.get("profile", "balanced"),
        cognition=raw.get("cognition", {}).get("level", "medium"),
        strategy=raw.get("strategy", "default"),
        replans=raw.get("replans", 0)
    )

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
        meta=meta,
        error=error
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
