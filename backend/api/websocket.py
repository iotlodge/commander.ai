"""
WebSocket manager for real-time task updates
"""
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class TaskWebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"✅ WebSocket connected: user {user_id}")

    def disconnect(self, user_id: UUID):
        """Remove connection"""
        self.active_connections.pop(user_id, None)
        print(f"❌ WebSocket disconnected: user {user_id}")

    async def send_to_user(self, user_id: UUID, message: dict):
        """Send message to specific user"""
        if connection := self.active_connections.get(user_id):
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_task_event(self, event: BaseModel):
        """Broadcast task event to all connected users"""
        message = event.model_dump(mode='json')
        print(f"📤 Broadcasting event: {event.type} to {len(self.active_connections)} connections")

        # Send to all connections
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
                print(f"  ✅ Sent to user {user_id}")
            except Exception as e:
                print(f"  ❌ Failed to send to user {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up failed connections
        for user_id in disconnected:
            self.disconnect(user_id)


# Singleton instance
_ws_manager: TaskWebSocketManager | None = None


def get_ws_manager() -> TaskWebSocketManager:
    """Get or create WebSocket manager singleton"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = TaskWebSocketManager()
    return _ws_manager
