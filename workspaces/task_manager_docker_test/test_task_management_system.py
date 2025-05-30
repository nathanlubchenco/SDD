import pytest
from datetime import datetime
from task_management_system import TaskManager, TaskAlreadyCompletedError

@pytest.fixture
def task_manager():
    return TaskManager()

def test_create_a_simple_task(task_manager):
    # Action: Create a task with title "Buy groceries"
    task = task_manager.create_task(title="Buy groceries")
    
    # Verify: A task should exist with title "Buy groceries"
    assert task.title == "Buy groceries", "Task title does not match"
    
    # Verify: The task should have status "pending"
    assert task.status == "pending", "Task status is not 'pending'"
    
    # Verify: The task should have a unique ID
    assert isinstance(task.id, int), "Task ID is not an integer"
    
    # Verify: The task should have a created_at timestamp
    assert isinstance(task.created_at, datetime), "Task created_at is not a datetime object"

def test_complete_a_task(task_manager):
    # Setup: A task exists with title "Buy groceries" and status "pending"
    task = task_manager.create_task(title="Buy groceries")
    
    # Action: Mark the task as complete
    task_manager.complete_task(task.id)
    
    # Verify: Task status is "completed"
    assert task.status == "completed", "Task status is not 'completed'"
    
    # Verify: The task should have a completed_at timestamp
    assert isinstance(task.completed_at, datetime), "Task completed_at is not a datetime object"
    
    # Verify: The completed_at should be after created_at
    assert task.completed_at > task.created_at, "completed_at is not after created_at"

def test_cannot_complete_already_completed_task(task_manager):
    # Setup: A task exists with status "completed"
    task = task_manager.create_task(title="Buy groceries")
    task_manager.complete_task(task.id)
    original_completed_at = task.completed_at
    
    # Action: Try to mark the task as complete again
    with pytest.raises(TaskAlreadyCompletedError, match="Task is already completed"):
        task_manager.complete_task(task.id)
    
    # Verify: The task status should remain "completed"
    assert task.status == "completed", "Task status changed from 'completed'"
    
    # Verify: The original completed_at should not change
    assert task.completed_at == original_completed_at, "completed_at timestamp changed"

def test_list_tasks_filtered_by_status(task_manager):
    # Setup: Create tasks with different statuses
    task1 = task_manager.create_task(title="Task 1")
    task2 = task_manager.create_task(title="Task 2")
    task3 = task_manager.create_task(title="Task 3")
    task_manager.complete_task(task2.id)
    
    # Action: List tasks with status "pending"
    pending_tasks = task_manager.list_tasks(status="pending")
    
    # Verify: I should see exactly 2 tasks
    assert len(pending_tasks) == 2, "Number of pending tasks is not 2"
    
    # Verify: The tasks should be "Task 1" and "Task 3"
    pending_titles = {task.title for task in pending_tasks}
    assert pending_titles == {"Task 1", "Task 3"}, "Pending tasks do not match expected titles"