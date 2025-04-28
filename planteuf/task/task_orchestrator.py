from logging import Logger
from typing import (
    Any,
    Dict,
)

from planteuf.mongodb.collections import Collections
from planteuf.mongodb.mongodb import (
    MongoDBClient,
    MongoDBClientError,
)
from planteuf.settings import (
    LOGGING_FILENAME,
    LOGGING_LEVEL,
)
from planteuf.task.model import (
    Task,
    TaskEvent,
    TaskStatus,
)
from planteuf.task.task_queue import TaskQueue
from planteuf.utils.log import get_logger


class TaskOrchestratorError(Exception):
    pass


class TaskOrchestrator:
    logging: Logger
    task_queue: TaskQueue
    mongo_client: MongoDBClient

    def __init__(self, task_queue: TaskQueue, mongo_client: MongoDBClient) -> None:
        self.logging = get_logger(name=__name__, level=LOGGING_LEVEL, filename=LOGGING_FILENAME)
        self.task_queue = task_queue
        self.mongo_client = mongo_client

        self.refresh_queue()

    def refresh_queue(self) -> None:
        self.logging.info("Refreshing task queue")
        tasks = self.mongo_client.find(
            collection_name=Collections.TASK,
            query={"status": {"$nin": [TaskStatus.COMPLETED, TaskStatus.FAILED]}},
            projection={"task_id": 1},
        )
        if tasks:
            for task in tasks:
                self.task_queue.enqueue(task["_id"])

    def create_task(self, event: TaskEvent, data: Dict[str, Any], author: str) -> None:
        self.logging.info("Creating task")
        task = Task(
            event=event,
            status=TaskStatus.PENDING,
            data=data,
            author=author,
            history=[TaskStatus.PENDING],
            log=[],
        )
        try:
            task_id = self.mongo_client.insert_one(collection_name=Collections.TASK, document=task)
            if task_id is None:
                raise TaskOrchestratorError("Failed to create task")
            self.task_queue.enqueue(task_id)
            self.logging.info("Task created", extra={"task_id": task_id})
        except MongoDBClientError:
            self.logging.exception("Failed to create task")
            raise TaskOrchestratorError(f"Failed to create task {task_id}")
