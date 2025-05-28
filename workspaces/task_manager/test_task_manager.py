import pytest
from task_manager import TaskManager, Task, TaskError

# Fixture for common setup
@pytest.fixture
def task_manager():
    return TaskManager()

def test_create_a_simple_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    assert isinstance(task, Task), "Task creation failed"
    assert task.title == "Buy groceries", "Task title is incorrect"
    assert task.status == "pending", "Task status is not 'pending'"
    assert isinstance(task.id, int), "Task ID is not unique"
    assert isinstance(task.created_at, datetime), "Task created_at timestamp is not set"

def test_complete_a_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    task_manager.complete_task(task.id)
    assert task.status == "completed", "Task status is not 'completed'"
    assert isinstance(task.completed_at, datetime), "Task completed_at timestamp is not set"
    assert task.completed_at > task.created_at, "Task completed_at is not after created_at"

def test_cannot_complete_already_completed_task(task_manager):
    task = task_manager.create_task("Buy groceries")
    task_manager.complete_task(task.id)
    with pytest.raises(TaskError) as e:
        task_manager.complete_task(task.id)
    assert str(e.value) == "Task is already completed", "Incorrect error message"
    assert task.status == "completed", "Task status changed"
    assert task.completed_at == task.completed_at, "Task completed_at timestamp changed"

def test_list_tasks_filtered_by_status(task_manager):
    task_manager.create_task("Task 1")
    task2 = task_manager.create_task("Task 2")
    task_manager.create_task("Task 3")
    task_manager.complete_task(task2.id)
    tasks = task_manager.list_tasks("pending")
    assert len(tasks) == 2, "Incorrect number of tasks returned"
    assert tasks[0].title == "Task 1" and tasks[1].title == "Task 3", "Incorrect tasks returned"