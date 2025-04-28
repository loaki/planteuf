from logging import Logger

from mongodb.collections import Collections
from mongodb.mongodb import (
    MongoDBClient,
    MongoDBClientError,
)
from task.model import (
    Task,
    TaskEvent,
    TaskStatus,
)
from settings import (
    LOGGING_FILENAME,
    LOGGING_LEVEL,
)
from task.task_queue import TaskQueue
from utils.log import get_logger


class TaskOrchestratorError(Exception):
    pass


class TaskOrchestrator:
    logging: Logger
    task_queue: TaskQueue
    mongo_client: MongoDBClient

    def __init__(self, task_queue: TaskQueue, mongo_client: MongoDBClient) -> None:
        self.logging = get_logger(name=__name__, log_level=LOGGING_LEVEL, filename=LOGGING_FILENAME)
        self.task_queue = task_queue
        self.mongo_client = mongo_client

        self.refresh_queue()

    def refresh_queue(self) -> None:
        self.logging.info("Refreshing task queue")
        task_ids = self.mongo_client.find(
            collection_name=Collections.TASK,
            filter={"status": {"$nin": [TaskStatus.COMPLETED, TaskStatus.FAILED]}},
            projection={"task_id": 1},
            sort=[("created_at", 1)],
        )
        for task_id in task_ids:
            self.task_queue.enqueue(task_id)

    def create_task(self, task: Task) -> None:
        self.logging.info("Creating task", extra={"task": task})
        task.status = TaskStatus.PENDING
        task.history = [TaskStatus.PENDING]
        task.log = []
        try:
            task_id = self.mongo_client.insert_one(collection_name=Collections.TASK, document=task)
            self.task_queue.enqueue(task_id)
            self.logging.info("Task created", extra={"task_id": task_id})
        except MongoDBClientError:
            self.logging.exception("Failed to create task")
            raise TaskOrchestratorError(f"Failed to create task {task.task_id}")

    def update_task(self, task_id: str, status: TaskStatus, log: str) -> None:
        self.logging.info("Updating task", extra={"task_id": task_id})
        try:
            task = self.mongo_client.find_one(
                collection_name=Collections.TASK,
                filter={"task_id": task_id},
            )
            if not task:
                raise TaskOrchestratorError(f"Task with ID {task_id} not found")
            task.status = status
            task.log.append(log)
            task.history.append(status)
            self.mongo_client.update_one(
                collection_name=Collections.TASK,
                filter={"task_id": task_id},
                update={"$set": {"status": status, "log": task.log, "history": task.history}},
            )
            self.logging.info("Task updated with ID: {task_id}")
        except MongoDBClientError:
            self.logging.exception("Failed to update task")
            raise TaskOrchestratorError(f"Failed to update task {task_id}")
