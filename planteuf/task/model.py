import enum
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import BaseModel


class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskEvent(enum.Enum):
    TEST = "test"


class Task(BaseModel):
    event: TaskEvent
    status: TaskStatus
    data: Dict[str, Any]
    author: str
    history: List[TaskStatus]
    log: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
