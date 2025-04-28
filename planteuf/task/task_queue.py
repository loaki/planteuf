from collections import deque
from typing import (
    Deque,
    List,
)


class TaskQueue:
    queue: Deque[str]

    def __init__(self) -> None:
        self.queue = deque()

    def enqueue(self, task_id: str) -> bool:
        if task_id in self.queue:
            return False
        self.queue.append(task_id)
        return True

    def dequeue(self, task_id: str) -> bool:
        if task_id in self.queue:
            self.queue.remove(task_id)
            return True
        return False

    def list_queue(self) -> List[str]:
        return list(self.queue)
