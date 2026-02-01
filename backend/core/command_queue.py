"""
Command Queue - Async queue for managing incoming commands
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel


class CommandPriority(int, Enum):
    """Priority levels for commands"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass(order=True)
class QueuedCommand:
    """A command in the queue with priority"""

    priority: int  # Higher = processed first
    timestamp: datetime
    command_id: UUID
    user_id: UUID
    thread_id: UUID
    command_text: str
    target_agent_id: str
    metadata: dict[str, Any]

    def __init__(
        self,
        command_text: str,
        user_id: UUID,
        thread_id: UUID,
        target_agent_id: str,
        priority: CommandPriority = CommandPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ):
        self.priority = -priority.value  # Negative for heap (lower = higher priority)
        self.timestamp = datetime.now()
        self.command_id = uuid4()
        self.user_id = user_id
        self.thread_id = thread_id
        self.command_text = command_text
        self.target_agent_id = target_agent_id
        self.metadata = metadata or {}


class CommandQueue:
    """
    Async priority queue for commands
    """

    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=maxsize)
        self._active_commands: dict[UUID, QueuedCommand] = {}

    async def enqueue(self, command: QueuedCommand) -> None:
        """Add command to queue"""
        await self._queue.put(command)

    async def dequeue(self) -> QueuedCommand:
        """Get next command from queue"""
        command = await self._queue.get()
        self._active_commands[command.command_id] = command
        return command

    def mark_complete(self, command_id: UUID) -> None:
        """Mark command as complete"""
        self._active_commands.pop(command_id, None)

    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()

    def get_active_commands(self) -> list[QueuedCommand]:
        """Get currently processing commands"""
        return list(self._active_commands.values())
