import enum
from typing import List

from pydantic import BaseModel


class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskEvent(enum.Enum):
    TEST = "test"


class Task(BaseModel):
    task_id: str
    event: TaskEvent
    status: TaskStatus
    data: dict
    author: str
    history: List[TaskStatus]
    log: List[str]
    created_at: str
    updated_at: str
