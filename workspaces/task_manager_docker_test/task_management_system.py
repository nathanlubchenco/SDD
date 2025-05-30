from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import asyncio
import logging
from functools import wraps
from time import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Exceptions
class TaskAlreadyCompletedError(Exception):
    pass

# Timing Decorator
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time()
        result = await func(*args, **kwargs)
        end_time = time()
        logger.info(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Task Data Model
@dataclass
class Task:
    title: str
    status: str = "pending"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Pydantic Model for Input Validation
class TaskCreateModel(BaseModel):
    title: str

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title must not be empty')
        return v

# Task Manager
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

# FastAPI Application
app = FastAPI()
task_manager = TaskManager()
security = HTTPBearer()

# JWT Token Validation
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Placeholder for JWT validation logic
    if credentials.credentials != "valid-token":
        raise HTTPException(status_code=403, detail="Invalid token")

@app.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreateModel, credentials: HTTPAuthorizationCredentials = Depends(validate_token)):
    return await task_manager.create_task(task_data)

@app.post("/tasks/{task_id}/complete", response_model=Task)
async def complete_task(task_id: str, credentials: HTTPAuthorizationCredentials = Depends(validate_token)):
    try:
        return await task_manager.complete_task(task_id)
    except TaskAlreadyCompletedError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks", response_model=List[Task])
async def list_tasks(status: str, credentials: HTTPAuthorizationCredentials = Depends(validate_token)):
    return await task_manager.list_tasks(status)

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}