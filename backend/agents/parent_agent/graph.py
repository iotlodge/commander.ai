"""
Parent Agent Graph Implementation
Orchestrator that delegates tasks to specialist agents
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.parent_agent.state import ParentAgentState
from backend.agents.parent_agent.nodes import (
    load_memory_node,
    decompose_task_node,
    assign_specialists_node,
    delegate_to_specialists_node,
    aggregate_results_node,
    save_memory_node,
)


class ParentAgent(BaseAgent):
    """
    Orchestrator agent that coordinates complex multi-step tasks
    Delegates to specialist agents based on task decomposition
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="parent",
            nickname="leo",
            specialization="Orchestrator",
            description="Coordinates complex multi-step tasks and delegates to specialist agents",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create the orchestration graph

        Flow:
        load_memory → decompose → assign → delegate → aggregate → save → END
        """
        graph = StateGraph(ParentAgentState)

        # Add nodes
        graph.add_node("load_memory", load_memory_node)
        graph.add_node("decompose", decompose_task_node)
        graph.add_node("assign", assign_specialists_node)
        graph.add_node("delegate", delegate_to_specialists_node)
        graph.add_node("aggregate", aggregate_results_node)
        graph.add_node("save_memory", save_memory_node)

        # Define edges (linear flow for MVP)
        graph.set_entry_point("load_memory")
        graph.add_edge("load_memory", "decompose")
        graph.add_edge("decompose", "assign")
        graph.add_edge("assign", "delegate")
        graph.add_edge("delegate", "aggregate")
        graph.add_edge("aggregate", "save_memory")
        graph.add_edge("save_memory", END)

        # TODO: Fix checkpointer implementation - disabled for MVP
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """
        Execute the parent agent graph
        """
        # Prepare initial state
        initial_state: ParentAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "task_type": None,
            "subtasks": [],
            "decomposition_reasoning": None,
            "specialist_assignments": {},
            "specialist_results": {},
            "final_response": None,
            "error": None,
            "current_step": "starting",
            "requires_consultation": False,
        }

        # Execute graph
        config = {
            "configurable": {
                "thread_id": str(context.thread_id),
                "user_id": str(context.user_id),
                "agent_id": self.agent_id,
            }
        }

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            # Check for errors
            if final_state.get("error"):
                return AgentExecutionResult(
                    success=False,
                    response="",
                    error=final_state["error"],
                    final_state=final_state,
                )

            # Return successful result
            return AgentExecutionResult(
                success=True,
                response=final_state.get("final_response", "Task completed"),
                final_state=final_state,
                metadata={
                    "task_type": final_state.get("task_type"),
                    "specialists_used": list(final_state.get("specialist_results", {}).keys()),
                    "subtask_count": len(final_state.get("subtasks", [])),
                },
            )

        except Exception as e:
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Graph execution failed: {str(e)}",
            )
