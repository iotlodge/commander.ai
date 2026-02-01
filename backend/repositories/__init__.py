"""
Repository layer for data access
"""

from backend.repositories.task_repository import TaskRepository, get_task_repository

__all__ = ["TaskRepository", "get_task_repository"]
