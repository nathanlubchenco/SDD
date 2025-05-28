import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

class TaskAlreadyCompletedError(Exception):
    pass

@dataclass
class Task:
    id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)
    title: str
    status: str = field(default="pending", init=False)
    created_at: datetime = field(default_factory=datetime.now, init=False)
    completed_at: Optional[datetime] = field(default=None, init=False)

    def complete(self):
        if self.status == "completed":
            raise TaskAlreadyCompletedError("Task is already completed")
        self.status = "completed"
        self.completed_at = datetime.now()

@dataclass
class TaskManager:
    tasks: List[Task] = field(default_factory=list)

    def create_task(self, title: str) -> Task:
        task = Task(title=title)
        self.tasks.append(task)
        return task

    def complete_task(self, task_id: uuid.UUID) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.complete()
                return
        raise ValueError("Task not found")

    def list_tasks(self, status: str) -> List[Task]:
        return [task for task in self.tasks if task.status == status]