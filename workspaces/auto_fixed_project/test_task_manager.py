import pytest
import uuid
from datetime import datetime
from task_manager import TaskAlreadyCompletedError, Task, TaskManager

# Fixture for common setup
@pytest.fixture
def task_manager():
    return TaskManager()

def test_create_a_simple_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    assert isinstance(task, Task), "Task creation failed"
    assert task.title == "Buy groceries", "Task title is incorrect"
    assert task.status == "pending", "Task status is incorrect"
    assert task.id is not None, "Task ID is not set"
    assert task.created_at is not None, "Task created_at is not set"

def test_complete_a_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    task_manager.complete_task(task.id)
    assert task.status == "completed", "Task status is not completed"
    assert task.completed_at is not None, "Task completed_at is not set"
    assert task.completed_at > task.created_at, "Task completed_at is not after created_at"

def test_cannot_complete_already_completed_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    task_manager.complete_task(task.id)
    with pytest.raises(TaskAlreadyCompletedError) as e:
        task_manager.complete_task(task.id)
    assert str(e.value) == "Task is already completed", "Error message is incorrect"
    assert task.status == "completed", "Task status is not completed"
    assert task.completed_at is not None, "Task completed_at is not set"

def test_list_tasks_filtered_by_status(task_manager):
    task_manager.create_task("Task 1")
    task2 = task_manager.create_task("Task 2")
    task_manager.create_task("Task 3")
    task_manager.complete_task(task2.id)
    tasks = task_manager.list_tasks("pending")
    assert len(tasks) == 2, "Incorrect number of tasks returned"
    assert tasks[0].title == "Task 1" and tasks[1].title == "Task 3", "Incorrect tasks returned"