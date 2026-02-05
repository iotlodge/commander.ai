"""
LLM-Powered Chat Utilities for Chat Assistant
Uses OpenAI GPT-4o-mini for conversational interactions
"""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from backend.core.config import get_settings
from backend.core.token_tracker import ExecutionMetrics, extract_token_usage_from_response


async def llm_generate_chat_response(
    current_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    metrics: ExecutionMetrics | None = None
) -> str:
    """
    Generate chat response using LLM based on conversation history

    Args:
        current_message: Current user message
        conversation_history: Previous messages in format [{role: "user/assistant", content: "..."}]
        metrics: Optional execution metrics tracker

    Returns:
        Generated response string
    """
    settings = get_settings()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.openai_api_key,
        max_tokens=2000,
    )

    system_prompt = """You are a helpful AI assistant in the Commander.ai system.
Your role is to have natural, informative conversations with users.

Guidelines:
- Be conversational and friendly
- Provide clear, helpful responses
- Ask clarifying questions when needed
- Use markdown formatting for better readability
- Be concise but thorough
- Admit when you don't know something"""

    # Build message list
    messages = [SystemMessage(content=system_prompt)]

    # Add conversation history if available
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=current_message))

    # Generate response
    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics:
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="chat_response"
        )

    return response.content
