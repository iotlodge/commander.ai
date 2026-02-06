# Copyright 2025 George Liu (eva2000) and commander.ai contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
FastAPI application entry point
"""

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.memory.memory_service import get_memory_service
from backend.agents.base.agent_registry import initialize_default_agents
from backend.api.websocket import get_ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    settings = get_settings()

    # Initialize memory service
    memory_service = await get_memory_service()

    # Initialize and register agents
    await initialize_default_agents()

    print("🚀 commander.ai started successfully")

    yield

    # Shutdown
    await memory_service.shutdown()

    # Close database connections
    from backend.core.database import close_db_connections
    await close_db_connections()

    print("👋 commander.ai shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="commander.ai API",
    description="Interactive interface for delegating work to AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "commander.ai",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    memory_service = await get_memory_service()

    return {
        "status": "healthy",
        "memory_service": "connected" if memory_service._initialized else "disconnected",
    }


# WebSocket endpoint for real-time task updates
@app.websocket("/ws/{user_id}")
async def task_websocket(websocket: WebSocket, user_id: str, token: str = None):
    """
    WebSocket endpoint for real-time task updates

    Development: Accepts user_id path parameter (MVP user bypass)
    Production: Requires authentication via token query parameter: /ws/{user_id}?token=<jwt_token>
    """
    from backend.auth.security import decode_token
    from backend.auth.dependencies import MVP_USER_ID
    from jose import JWTError

    ws_manager = get_ws_manager()

    # Development bypass: Allow MVP_USER_ID without token
    if user_id == str(MVP_USER_ID) and not token:
        try:
            parsed_user_id = UUID(user_id)
            await ws_manager.connect(websocket, parsed_user_id)

            try:
                while True:
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")
            except WebSocketDisconnect:
                ws_manager.disconnect(parsed_user_id)
            return
        except ValueError:
            await websocket.close(code=1008, reason="Invalid user_id format")
            return

    # Production: Require JWT token
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        # Decode and validate JWT token
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token")
            return

        token_user_id = UUID(payload.get("sub"))

        # Verify path user_id matches token user_id
        if user_id != str(token_user_id):
            await websocket.close(code=1008, reason="User ID mismatch")
            return

        # Accept connection after successful authentication
        await ws_manager.connect(websocket, token_user_id)

        try:
            while True:
                # Keep connection alive with heartbeat
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(token_user_id)

    except (JWTError, ValueError) as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
        return


# Import and include routers
from backend.api.routes import tasks, commands, graphs, agents, chat
from backend.auth.routes import router as auth_router

# Public routes (no auth required)
app.include_router(auth_router)

# Protected routes (auth required)
app.include_router(tasks.router)
app.include_router(commands.router)
app.include_router(graphs.router)
app.include_router(agents.router)
app.include_router(chat.router)
