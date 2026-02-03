"""
Bob (Research Specialist) Agent Implementation
Conducts research with conditional Sue (Compliance) consultation
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_a.state import ResearchAgentState
from backend.agents.specialized.agent_a.llm_research import (
    llm_web_search,
    llm_synthesize_research,
    llm_check_compliance_keywords,
)
from backend.memory.schemas import MemoryType


async def search_node(state: ResearchAgentState) -> dict:
    """
    Perform web search using Tavily API or LLM knowledge
    """
    query = state["query"]

    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(25, "searching")

    # Use LLM-powered web search
    search_results = await llm_web_search(query)

    return {
        **state,
        "search_results": search_results,
        "current_step": "searched",
    }


async def synthesize_node(state: ResearchAgentState) -> dict:
    """
    Synthesize search results into coherent response using LLM
    """
    query = state["query"]
    results = state["search_results"]

    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(50, "synthesizing")

    # Use LLM to synthesize research
    synthesis = await llm_synthesize_research(
        query=query,
        search_results=results,
        context=state.get("conversation_context")
    )

    return {
        **state,
        "synthesis": synthesis,
        "current_step": "synthesized",
    }


async def check_compliance_need_node(state: ResearchAgentState) -> dict:
    """
    Use LLM to intelligently check if research involves compliance concerns
    """
    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(70, "checking_compliance")

    # Combine query and synthesis for analysis
    text_to_check = f"{state['query']}\n\n{state.get('synthesis', '')}"

    # Use LLM-powered compliance detection
    needs_review, concerns = await llm_check_compliance_keywords(text_to_check)

    return {
        **state,
        "needs_compliance_review": needs_review,
        "compliance_keywords_found": concerns,
        "current_step": "compliance_checked",
    }


async def consult_sue_node(state: ResearchAgentState) -> dict:
    """
    Consult Sue (Compliance Specialist) for review
    """
    # For MVP, just mark as consulted
    # TODO: Actually invoke Sue agent when implemented

    compliance_review = (
        f"Compliance review: The research discusses {', '.join(state['compliance_keywords_found'])}. "
        f"Please ensure compliance with relevant data protection regulations."
    )

    return {
        **state,
        "sue_consulted": True,
        "compliance_review": compliance_review,
        "current_step": "sue_consulted",
    }


async def finalize_response_node(state: ResearchAgentState) -> dict:
    """
    Create final response, including compliance review if needed
    """
    # Report progress if callback exists
    if callback := state.get("task_callback"):
        await callback.on_progress_update(90, "finalizing")

    response = state["synthesis"]

    if state.get("sue_consulted") and state.get("compliance_review"):
        response += f"\n\n⚠️ **Compliance Note:**\n{state['compliance_review']}"

    return {
        **state,
        "final_response": response,
        "current_step": "completed",
    }


def should_consult_sue(state: ResearchAgentState) -> str:
    """Router function: decide if Sue consultation needed"""
    return "yes" if state.get("needs_compliance_review") else "no"


class ResearchAgent(BaseAgent):
    """
    Bob - Research Specialist
    Conducts research and synthesis with conditional compliance consultation
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_a",
            nickname="bob",
            specialization="Research Specialist",
            description="Conducts research, synthesis, and information gathering",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create research graph with conditional Sue consultation

        Flow:
        search → synthesize → check_compliance → [consult_sue?] → finalize → END
        """
        graph = StateGraph(ResearchAgentState)

        # Add nodes
        graph.add_node("search", search_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("check_compliance", check_compliance_need_node)
        graph.add_node("consult_sue", consult_sue_node)
        graph.add_node("finalize", finalize_response_node)

        # Define flow
        graph.set_entry_point("search")
        graph.add_edge("search", "synthesize")
        graph.add_edge("synthesize", "check_compliance")

        # Conditional edge: consult Sue if needed
        graph.add_conditional_edges(
            "check_compliance",
            should_consult_sue,
            {"yes": "consult_sue", "no": "finalize"},
        )

        graph.add_edge("consult_sue", "finalize")
        graph.add_edge("finalize", END)

        # TODO: Fix checkpointer implementation - disabled for MVP
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute Bob's research graph"""
        initial_state: ResearchAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "search_results": [],
            "synthesis": None,
            "needs_compliance_review": False,
            "compliance_keywords_found": [],
            "sue_consulted": False,
            "compliance_review": None,
            "final_response": None,
            "error": None,
            "current_step": "starting",
            "task_callback": context.task_callback,  # Pass through callback
        }

        config = {
            "configurable": {
                "thread_id": str(context.thread_id),
                "user_id": str(context.user_id),
                "agent_id": self.agent_id,
            }
        }

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
                response=final_state.get("final_response", "Research completed"),
                final_state=final_state,
                metadata={
                    "sue_consulted": final_state.get("sue_consulted", False),
                    "compliance_keywords": final_state.get("compliance_keywords_found", []),
                },
            )

        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Research failed: {error_details}",
            )
