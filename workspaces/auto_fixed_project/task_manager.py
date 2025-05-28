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

class TaskManager:
    def __init__(self):
        self.tasks = []

    def create_task(self, title: str) -> Task:
        """Create a new task with the given title."""
        task = Task(title=title)
        self.tasks.append(task)
        return task

    def complete_task(self, task_id: uuid.UUID) -> Task:
        """Mark a task as complete."""
        task = self.get_task_by_id(task_id)
        if task.status == "completed":
            raise TaskAlreadyCompletedError("Task is already completed")
        task.status = "completed"
        task.completed_at = datetime.now()
        return task

    def get_task_by_id(self, task_id: uuid.UUID) -> Task:
        """Retrieve a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError("Task not found")

    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        """List all tasks, optionally filtered by status."""
        if status is None:
            return self.tasks
        return [task for task in self.tasks if task.status == status]