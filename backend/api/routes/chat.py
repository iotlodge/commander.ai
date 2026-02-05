"""
Direct chat API endpoint - bypasses task creation for real-time chat
"""
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.base.agent_registry import AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext
from backend.memory.schemas import ConversationContext
from backend.core.token_tracker import ExecutionMetrics

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    user_id: UUID
    message: str
    thread_id: UUID | None = None


class ChatResponse(BaseModel):
    """Response from chat agent"""
    response: str
    metrics: dict
    thread_id: UUID


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Send a message to the chat agent and get immediate response.
    Does NOT create a task - for use in chat sessions only.
    """
    # Get chat agent
    chat_agent = AgentRegistry.get_by_nickname("chat")
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not available")

    # Use provided thread_id or create new one
    thread_id = request.thread_id or uuid4()

    # Create execution context
    metrics = ExecutionMetrics()
    context = AgentExecutionContext(
        user_id=request.user_id,
        thread_id=thread_id,
        command=request.message,  # Add the required command field
        conversation_context=ConversationContext(
            graph_state={},
            recent_conversation=[],
            relevant_memories=[],
            thread_id=thread_id,
            user_id=request.user_id,
            agent_id="agent_g",
        ),
        task_callback=None,
        metrics=metrics,
    )

    # Execute agent directly
    try:
        result = await chat_agent._execute_graph(request.message, context)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Chat agent failed: {result.error}"
            )

        # Return response with metrics
        return ChatResponse(
            response=result.response,
            metrics={
                "llm_calls": metrics.llm_calls,
                "tokens": {
                    "total": metrics.token_usage.total_tokens,
                    "prompt": metrics.token_usage.prompt_tokens,
                    "completion": metrics.token_usage.completion_tokens,
                },
            },
            thread_id=thread_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )
