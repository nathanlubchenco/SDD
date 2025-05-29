import pytest
from datetime import datetime
from task_management_system import TaskManager, TaskAlreadyCompletedError

@pytest.fixture
def task_manager():
    return TaskManager()

def test_create_a_simple_task(task_manager):
    # Action: Create a task with title "Buy groceries"
    task = task_manager.create_task(title="Buy groceries")
    
    # Assertions
    assert task.title == "Buy groceries", "Task title should be 'Buy groceries'"
    assert task.status == "pending", "Task status should be 'pending'"
    assert isinstance(task.id, int), "Task should have a unique ID"
    assert isinstance(task.created_at, datetime), "Task should have a created_at timestamp"

def test_complete_a_task(task_manager):
    # Setup: Create a task with title "Buy groceries" and status "pending"
    task = task_manager.create_task(title="Buy groceries")
    
    # Action: Mark the task as complete
    task_manager.complete_task(task.id)
    
    # Assertions
    assert task.status == "completed", "Task status should be 'completed'"
    assert isinstance(task.completed_at, datetime), "Task should have a completed_at timestamp"
    assert task.completed_at > task.created_at, "completed_at should be after created_at"

def test_cannot_complete_already_completed_task(task_manager):
    # Setup: Create a task with status "completed"
    task = task_manager.create_task(title="Buy groceries")
    task_manager.complete_task(task.id)
    original_completed_at = task.completed_at
    
    # Action: Try to mark the task as complete again
    with pytest.raises(TaskAlreadyCompletedError, match="Task is already completed"):
        task_manager.complete_task(task.id)
    
    # Assertions
    assert task.status == "completed", "Task status should remain 'completed'"
    assert task.completed_at == original_completed_at, "The original completed_at should not change"

def test_list_tasks_filtered_by_status(task_manager):
    # Setup: Create tasks with different statuses
    task1 = task_manager.create_task(title="Task 1")
    task2 = task_manager.create_task(title="Task 2")
    task3 = task_manager.create_task(title="Task 3")
    task_manager.complete_task(task2.id)
    
    # Action: List tasks with status "pending"
    pending_tasks = task_manager.list_tasks_by_status("pending")
    
    # Assertions
    assert len(pending_tasks) == 2, "There should be exactly 2 pending tasks"
    pending_titles = [task.title for task in pending_tasks]
    assert "Task 1" in pending_titles, "Task 1 should be in the pending tasks"
    assert "Task 3" in pending_titles, "Task 3 should be in the pending tasks"