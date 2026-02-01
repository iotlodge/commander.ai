"""
Rex (Data Analyst) Agent Implementation
Performs data analysis, visualization, and statistical insights
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_c.state import DataAgentState


async def identify_analysis_type_node(state: DataAgentState) -> dict:
    """
    Determine type of data analysis needed
    """
    query_lower = state["query"].lower()

    if any(kw in query_lower for kw in ["visualize", "chart", "graph", "plot"]):
        analysis_type = "visualization"
    elif any(kw in query_lower for kw in ["statistics", "mean", "median", "correlation"]):
        analysis_type = "statistical"
    else:
        analysis_type = "descriptive"

    return {
        **state,
        "analysis_type": analysis_type,
        "current_step": "analysis_type_identified",
    }


async def analyze_data_node(state: DataAgentState) -> dict:
    """
    Perform data analysis
    TODO: Integrate pandas, matplotlib in production
    """
    findings = []

    # Placeholder analysis
    if state["analysis_type"] == "visualization":
        findings.append("Generated bar chart showing data distribution")
        findings.append("Created trend line for time series data")

    elif state["analysis_type"] == "statistical":
        findings.append("Mean: 42.5, Median: 40.0, Std Dev: 5.2")
        findings.append("Strong positive correlation detected (r=0.85)")

    else:
        findings.append("Dataset contains 1,000 records across 5 variables")
        findings.append("No missing values detected")
        findings.append("Data appears normally distributed")

    return {
        **state,
        "findings": findings,
        "current_step": "analyzed",
    }


async def finalize_analysis_node(state: DataAgentState) -> dict:
    """
    Create final analysis report
    """
    response_parts = []

    response_parts.append(f"**Data Analysis Report** ({state['analysis_type'].title()})\n")
    response_parts.append("**Findings:**")

    for i, finding in enumerate(state["findings"], 1):
        response_parts.append(f"{i}. {finding}")

    response_parts.append("\n*Note: This is a placeholder analysis. Production version will use pandas and matplotlib.*")

    final_response = "\n".join(response_parts)

    return {
        **state,
        "final_response": final_response,
        "current_step": "completed",
    }


class DataAgent(BaseAgent):
    """
    Rex - Data Analyst
    Performs data analysis, visualization, and statistical insights
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_c",
            nickname="rex",
            specialization="Data Analyst",
            description="Performs data analysis, visualization, and statistical insights",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create data analysis graph

        Flow:
        identify_analysis_type → analyze → finalize → END
        """
        graph = StateGraph(DataAgentState)

        # Add nodes
        graph.add_node("identify", identify_analysis_type_node)
        graph.add_node("analyze", analyze_data_node)
        graph.add_node("finalize", finalize_analysis_node)

        # Define flow
        graph.set_entry_point("identify")
        graph.add_edge("identify", "analyze")
        graph.add_edge("analyze", "finalize")
        graph.add_edge("finalize", END)

        # TODO: Fix checkpointer implementation - disabled for MVP
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute Rex's data analysis graph"""
        initial_state: DataAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "data_source": None,
            "analysis_type": None,
            "findings": [],
            "final_response": None,
            "error": None,
            "current_step": "starting",
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

            return AgentExecutionResult(
                success=True,
                response=final_state.get("final_response", "Data analysis completed"),
                final_state=final_state,
                metadata={
                    "analysis_type": final_state.get("analysis_type"),
                    "findings_count": len(final_state.get("findings", [])),
                },
            )

        except Exception as e:
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Data analysis failed: {str(e)}",
            )
