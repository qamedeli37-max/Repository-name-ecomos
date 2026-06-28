from pydantic import BaseModel
from typing import Any


class Task(BaseModel):
    intent: str
    data: dict[str, Any] = {}
