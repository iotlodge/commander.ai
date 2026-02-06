"""
Chat Assistant Agent Implementation
Simple conversational agent for interactive chat
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_g.state import ChatAgentState
from backend.agents.specialized.agent_g.llm_chat import llm_generate_chat_response


async def receive_message_node(state: ChatAgentState) -> dict:
    """
    Receive and prepare the user's message
    """
    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(30, "receiving_message")

    # Extract conversation history from context if available
    conversation_history = state.get("messages", [])

    return {
        **state,
        "messages": conversation_history,
        "current_step": "message_received",
    }


async def generate_response_node(state: ChatAgentState) -> dict:
    """
    Generate chat response using LLM with web search capability
    """
    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(60, "generating_response")

    query = state["query"]
    user_id = state["user_id"]
    conversation_history = state.get("messages", [])

    # Generate response using LLM with TavilyToolset web search
    response = await llm_generate_chat_response(
        current_message=query,
        user_id=user_id,
        conversation_history=conversation_history,
        metrics=state.get("metrics")
    )

    # Update conversation history
    updated_messages = conversation_history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": response},
    ]

    return {
        **state,
        "response": response,
        "messages": updated_messages,
        "current_step": "completed",
    }


class ChatAgent(BaseAgent):
    """
    Chat Assistant - Interactive LLM conversation agent
    Simple agent for real-time chat interactions
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_g",
            nickname="chat",
            specialization="Chat Assistant",
            description="Interactive chat interface with LLM",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create simple chat graph

        Flow:
        receive_message → generate_response → END
        """
        graph = StateGraph(ChatAgentState)

        # Add nodes
        graph.add_node("receive_message", receive_message_node)
        graph.add_node("generate_response", generate_response_node)

        # Define flow
        graph.set_entry_point("receive_message")
        graph.add_edge("receive_message", "generate_response")
        graph.add_edge("generate_response", END)

        # No checkpointer needed for stateless chat
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute chat graph"""
        # Extract conversation history from context if available
        conversation_history = []
        if context.conversation_context and context.conversation_context.recent_conversation:
            # Convert ConversationMessage objects to simple dict format
            conversation_history = [
                {"role": msg.role.value, "content": msg.content}
                for msg in context.conversation_context.recent_conversation
            ]

        initial_state: ChatAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump(mode='json')
                if context.conversation_context
                else {}
            ),
            "messages": conversation_history,
            "response": None,
            "error": None,
            "current_step": "starting",
            "task_callback": context.task_callback,
            "metrics": context.metrics,
        }

        # Build config with execution tracker callbacks
        config = self._build_graph_config(context)

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            if not final_state:
                return AgentExecutionResult(
                    success=False,
                    response="",
                    error="Graph returned empty state",
                    final_state={},
                )

            return AgentExecutionResult(
                success=True,
                response=final_state.get("response", "Chat completed"),
                final_state=final_state,
                metadata={
                    "conversation_length": len(final_state.get("messages", [])),
                },
            )

        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Chat failed: {error_details}",
            )
