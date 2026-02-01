"""
Parent Agent Graph Nodes
Individual node functions for the orchestration workflow
"""

from typing import Any
from uuid import UUID

from backend.agents.parent_agent.state import ParentAgentState
from backend.agents.base.agent_registry import AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext, AgentExecutionResult


async def load_memory_node(state: ParentAgentState) -> dict[str, Any]:
    """Load conversation context and relevant memories"""
    # Memory loading handled by execute() method
    # This node just marks the step
    return {
        **state,
        "current_step": "memory_loaded",
    }


async def decompose_task_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Analyze query and determine task type and decomposition
    """
    query = state["query"].lower()

    # Simple keyword-based routing for MVP
    # TODO: Use LLM for smarter decomposition in production

    if any(kw in query for kw in ["research", "find", "investigate", "study", "analyze"]):
        task_type = "research"
        subtasks = [{"type": "research", "query": state["query"], "assigned_to": "bob"}]

    elif any(
        kw in query
        for kw in ["compliance", "gdpr", "policy", "regulation", "legal", "privacy"]
    ):
        task_type = "compliance"
        subtasks = [{"type": "compliance", "query": state["query"], "assigned_to": "sue"}]

    elif any(kw in query for kw in ["data", "statistics", "visualize", "chart", "graph"]):
        task_type = "data_analysis"
        subtasks = [{"type": "data_analysis", "query": state["query"], "assigned_to": "rex"}]

    elif any(kw in query for kw in ["and", "also", "both", ","]):
        # Multi-specialist task
        task_type = "multi_specialist"
        subtasks = []

        if any(kw in query for kw in ["research", "find"]):
            subtasks.append({"type": "research", "query": state["query"], "assigned_to": "bob"})

        if any(kw in query for kw in ["compliance", "policy"]):
            subtasks.append(
                {"type": "compliance", "query": state["query"], "assigned_to": "sue"}
            )

        if any(kw in query for kw in ["data", "statistics"]):
            subtasks.append(
                {"type": "data_analysis", "query": state["query"], "assigned_to": "rex"}
            )

    else:
        # Default to Bob for general queries
        task_type = "research"
        subtasks = [{"type": "research", "query": state["query"], "assigned_to": "bob"}]

    return {
        **state,
        "task_type": task_type,
        "subtasks": subtasks,
        "current_step": "decomposed",
        "requires_consultation": len(subtasks) > 1,
    }


async def assign_specialists_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Create specialist assignments from subtasks
    """
    assignments = {}
    for subtask in state["subtasks"]:
        agent_nickname = subtask["assigned_to"]
        assignments[agent_nickname] = subtask["query"]

    return {
        **state,
        "specialist_assignments": assignments,
        "current_step": "assigned",
    }


async def delegate_to_specialists_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Execute subtasks by invoking specialist agents
    """
    results = {}

    for agent_nickname, subtask_query in state["specialist_assignments"].items():
        # Get agent from registry
        agent = AgentRegistry.get_by_nickname(agent_nickname)

        if not agent:
            results[agent_nickname] = {
                "success": False,
                "error": f"Agent {agent_nickname} not found",
            }
            continue

        # Create execution context
        context = AgentExecutionContext(
            user_id=state["user_id"],
            thread_id=state["thread_id"],
            command=subtask_query,
            conversation_context=state.get("conversation_context"),
        )

        # Execute specialist agent
        try:
            result: AgentExecutionResult = await agent.execute(subtask_query, context)
            results[agent_nickname] = {
                "success": result.success,
                "response": result.response,
                "error": result.error,
            }
        except Exception as e:
            results[agent_nickname] = {
                "success": False,
                "error": str(e),
            }

    return {
        **state,
        "specialist_results": results,
        "current_step": "delegated",
    }


async def aggregate_results_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Combine results from all specialist agents into final response
    """
    results = state["specialist_results"]

    # Check if any specialist failed
    failed = [name for name, result in results.items() if not result.get("success")]

    if failed:
        error_msg = f"Some specialists failed: {', '.join(failed)}"
        return {
            **state,
            "error": error_msg,
            "final_response": None,
            "current_step": "failed",
        }

    # Single specialist - just return their response
    if len(results) == 1:
        agent_name = list(results.keys())[0]
        response = results[agent_name]["response"]

        return {
            **state,
            "final_response": response,
            "current_step": "completed",
        }

    # Multiple specialists - aggregate responses
    aggregated = []
    for agent_name, result in results.items():
        aggregated.append(f"**{agent_name.title()}'s Analysis:**\n{result['response']}\n")

    final_response = "\n".join(aggregated)

    return {
        **state,
        "final_response": final_response,
        "current_step": "completed",
    }


async def save_memory_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Save interaction to memory
    Memory saving handled by execute() method
    """
    return {
        **state,
        "current_step": "saved",
    }
