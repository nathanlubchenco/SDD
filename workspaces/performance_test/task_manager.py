from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, validator
import uuid
import asyncio
import time
from functools import wraps

# Custom Exceptions
class TaskAlreadyCompletedError(Exception):
    pass

# Timing Decorator
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Data Models
@dataclass
class Task:
    title: str
    status: str = "pending"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Pydantic Models
class TaskCreateModel(BaseModel):
    title: str

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title must not be empty')
        return v

# Manager Class
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    @timing_decorator
    async def create_task(self, task_data: TaskCreateModel) -> Task:
        task = Task(title=task_data.title)
        self.tasks[task.id] = task
        return task

    @timing_decorator
    async def complete_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status == "completed":
            raise TaskAlreadyCompletedError("Task is already completed")
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        return task

    @timing_decorator
    async def list_tasks(self, status: str) -> List[Task]:
        return [task for task in self.tasks.values() if task.status == status]

# FastAPI Setup
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
task_manager = TaskManager()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Placeholder for JWT validation
    return {"username": "test_user"}

@app.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreateModel, user: dict = Depends(get_current_user)):
    return await task_manager.create_task(task_data)

@app.post("/tasks/{task_id}/complete", response_model=Task)
async def complete_task(task_id: str, user: dict = Depends(get_current_user)):
    try:
        return await task_manager.complete_task(task_id)
    except TaskAlreadyCompletedError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks", response_model=List[Task])
async def list_tasks(status: str, user: dict = Depends(get_current_user)):
    return await task_manager.list_tasks(status)

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Simulate async I/O operations
async def simulate_io():
    await asyncio.sleep(0.01)