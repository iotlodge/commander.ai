"""
Parent Agent Graph Nodes
Individual node functions for the orchestration workflow
"""

from typing import Any
from uuid import UUID

from backend.agents.parent_agent.state import ParentAgentState
from backend.agents.base.agent_registry import AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext, AgentExecutionResult
from backend.agents.parent_agent.llm_reasoning import llm_decompose_task
from backend.agents.parent_agent.llm_aggregation import llm_aggregate_results


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
    Analyze query using LLM and determine task type and decomposition
    Uses GPT-4o-mini for intelligent task breakdown
    """
    query = state["query"]

    # Use LLM-powered decomposition
    try:
        decomposition = await llm_decompose_task(
            query=query,
            user_context=state.get("conversation_context"),
            metrics=state.get("metrics")
        )

        task_type = decomposition.get("task_type", "research")
        subtasks = decomposition.get("subtasks", [])
        reasoning = decomposition.get("reasoning", "LLM-based decomposition")

        # Ensure subtasks have required fields
        for subtask in subtasks:
            if "query" not in subtask:
                subtask["query"] = query
            if "assigned_to" not in subtask:
                subtask["assigned_to"] = "bob"  # Default to bob
            if "type" not in subtask:
                subtask["type"] = task_type

        return {
            **state,
            "task_type": task_type,
            "subtasks": subtasks,
            "decomposition_reasoning": reasoning,
            "current_step": "decomposed",
            "requires_consultation": len(subtasks) > 1,
        }

    except Exception as e:
        # Fallback to simple pattern matching if LLM fails
        print(f"LLM decomposition failed, using fallback: {e}")

        query_lower = query.lower()

        if any(kw in query_lower for kw in ["research", "find", "investigate", "study"]):
            task_type = "research"
            subtasks = [{"type": "research", "query": query, "assigned_to": "bob"}]
        elif any(kw in query_lower for kw in ["compliance", "gdpr", "policy", "regulation"]):
            task_type = "compliance"
            subtasks = [{"type": "compliance", "query": query, "assigned_to": "sue"}]
        elif any(kw in query_lower for kw in ["data", "statistics", "visualize"]):
            task_type = "data_analysis"
            subtasks = [{"type": "data_analysis", "query": query, "assigned_to": "rex"}]
        else:
            task_type = "research"
            subtasks = [{"type": "research", "query": query, "assigned_to": "bob"}]

        return {
            **state,
            "task_type": task_type,
            "subtasks": subtasks,
            "decomposition_reasoning": "Fallback pattern matching",
            "current_step": "decomposed",
            "requires_consultation": False,
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
    Execute subtasks by invoking specialist agents IN PARALLEL
    Uses asyncio.gather() for concurrent execution
    """
    import asyncio
    from backend.core.token_tracker import ExecutionMetrics

    async def execute_agent(agent_nickname: str, subtask_query: str) -> tuple[str, dict]:
        """Execute single agent and return results"""
        # Get agent from registry
        agent = AgentRegistry.get_by_nickname(agent_nickname)

        if not agent:
            return agent_nickname, {
                "success": False,
                "error": f"Agent {agent_nickname} not found",
            }

        # Create child execution context with fresh metrics
        child_metrics = ExecutionMetrics()
        context = AgentExecutionContext(
            user_id=state["user_id"],
            thread_id=state["thread_id"],
            command=subtask_query,
            conversation_context=state.get("conversation_context"),
            metrics=child_metrics,
        )

        # Execute specialist agent
        try:
            result: AgentExecutionResult = await agent.execute(subtask_query, context)

            # Track agent call in parent metrics
            if parent_metrics := state.get("metrics"):
                parent_metrics.add_agent_call(
                    agent_id=agent.agent_id,
                    agent_nickname=agent_nickname,
                    success=result.success,
                    child_metrics=result.metrics
                )

            return agent_nickname, {
                "success": result.success,
                "response": result.response,
                "error": result.error,
                "metadata": result.metadata,
            }
        except Exception as e:
            return agent_nickname, {
                "success": False,
                "error": str(e),
            }

    # Create tasks for parallel execution
    tasks = [
        execute_agent(agent_nickname, subtask_query)
        for agent_nickname, subtask_query in state["specialist_assignments"].items()
    ]

    # Execute all agents in parallel
    agent_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results
    results = {}
    for item in agent_results:
        if isinstance(item, Exception):
            # Handle exception from gather
            results["unknown"] = {
                "success": False,
                "error": f"Agent execution exception: {str(item)}",
            }
        else:
            agent_nickname, result = item
            results[agent_nickname] = result

    return {
        **state,
        "specialist_results": results,
        "current_step": "delegated",
    }


async def aggregate_results_node(state: ParentAgentState) -> dict[str, Any]:
    """
    Use LLM to intelligently aggregate results from all specialist agents
    """
    results = state["specialist_results"]

    # Check if ANY specialist succeeded
    successful = [name for name, result in results.items() if result.get("success")]

    if not successful:
        # All specialists failed
        error_msg = "All specialists failed to complete their tasks"
        error_details = "\n".join([
            f"- @{name}: {result.get('error', 'Unknown error')}"
            for name, result in results.items()
        ])

        return {
            **state,
            "error": f"{error_msg}\n\n{error_details}",
            "final_response": None,
            "current_step": "failed",
        }

    # Use LLM to aggregate results (handles both single and multiple specialists)
    try:
        final_response = await llm_aggregate_results(
            original_query=state["query"],
            specialist_results=results,
            task_type=state.get("task_type", "unknown"),
            decomposition_reasoning=state.get("decomposition_reasoning"),
            metrics=state.get("metrics")
        )

        # Add disclaimer if some specialists failed
        failed = [name for name, result in results.items() if not result.get("success")]
        if failed:
            disclaimer = f"\n\n---\n\n⚠️ **Note:** Some specialists encountered issues: {', '.join(f'@{name}' for name in failed)}"
            final_response += disclaimer

        return {
            **state,
            "final_response": final_response,
            "current_step": "completed",
        }

    except Exception as e:
        # If aggregation fails, fall back to simple concatenation
        print(f"LLM aggregation failed: {e}. Using fallback.")

        aggregated = []
        for agent_name, result in results.items():
            if result.get("success"):
                aggregated.append(f"## @{agent_name}'s Analysis\n\n{result['response']}\n")

        final_response = "\n---\n\n".join(aggregated)

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
