from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from uuid import uuid4
import time
import functools
from pydantic import BaseModel, validator
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import asyncio

# Custom Exceptions
class TaskAlreadyCompletedError(Exception):
    pass

# Pydantic Models for Input Validation
class TaskCreateModel(BaseModel):
    title: str

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title must not be empty')
        return v

# Dataclass for Task Entity
@dataclass
class Task:
    title: str
    status: str = "pending"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Task Manager
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def timing_decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
            return result
        return wrapper

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

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Dummy token validation
    if token != "valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])