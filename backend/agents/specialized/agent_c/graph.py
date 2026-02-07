"""
Rex (Data Analyst) Agent Implementation
Performs data analysis, visualization, and statistical insights
"""

import numpy as np
import pandas as pd
from langgraph.graph import END, StateGraph

from backend.agents.base.agent_interface import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentMetadata,
    BaseAgent,
)
from backend.agents.specialized.agent_c.state import DataAgentState
from backend.core.config import get_settings
from backend.core.token_tracker import ExecutionMetrics
from backend.tools.data_analysis import ChartGenerator, StatisticsAnalyzer


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
    Perform data analysis using tools
    """
    findings = []
    chart_paths = []
    metrics = state.get("metrics") or ExecutionMetrics()

    try:
        # Initialize tools
        stats_tool = StatisticsAnalyzer()
        chart_tool = ChartGenerator(output_dir=get_settings().chart_output_dir)

        # Load data (from state or create sample)
        if state.get("dataframe"):
            df = pd.DataFrame(state["dataframe"])
        elif state.get("data_source"):
            # Future: load from CSV, Excel, database
            df = pd.read_csv(state["data_source"])
        else:
            # Sample data for testing
            df = pd.DataFrame(
                {
                    "x": np.arange(1, 51),
                    "y": np.random.randn(50).cumsum(),
                    "category": np.random.choice(["A", "B", "C"], 50),
                }
            )

        # Validate data
        if df.empty:
            return {
                **state,
                "error": "Data source is empty",
                "findings": [],
                "metrics": metrics,
                "current_step": "analyzed",
            }

        # Route based on analysis type
        if state["analysis_type"] == "statistical":
            # Descriptive statistics
            metrics.add_tool_call("StatisticsAnalyzer.describe_dataframe", success=True)
            desc = await stats_tool.describe_dataframe(df)
            findings.append(f"Dataset: {desc['shape'][0]} rows × {desc['shape'][1]} columns")

            # Get numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) > 0:
                # Calculate statistics for first numeric column
                metrics.add_tool_call("StatisticsAnalyzer.calculate_statistics", success=True)
                stats = await stats_tool.calculate_statistics(
                    df[numeric_cols[0]], metrics=["mean", "median", "std", "min", "max"]
                )

                for stat in stats:
                    findings.append(f"{numeric_cols[0]} - {stat.metric}: {stat.value:.2f}")

                # Correlation matrix if multiple numeric columns
                if len(numeric_cols) >= 2:
                    metrics.add_tool_call("StatisticsAnalyzer.correlation_matrix", success=True)
                    corr = await stats_tool.correlation_matrix(df[numeric_cols], method="pearson")

                    if corr["strong_correlations"]:
                        findings.append(
                            f"Strong correlations detected: {len(corr['strong_correlations'])} pairs"
                        )
            else:
                findings.append("No numeric columns available for statistical analysis")

        elif state["analysis_type"] == "visualization":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) >= 2:
                # Scatter plot
                metrics.add_tool_call("ChartGenerator.scatter_plot", success=True)
                scatter_result = await chart_tool.scatter_plot(
                    data=df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    hue="category" if "category" in df.columns else None,
                    title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    save=True,
                    return_base64=False,
                )
                findings.append(f"Created scatter plot: {scatter_result.file_path}")
                chart_paths.append(scatter_result.file_path)

                # Line plot for trends
                metrics.add_tool_call("ChartGenerator.line_plot", success=True)
                line_result = await chart_tool.line_plot(
                    data=df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title="Trend Analysis",
                    markers=True,
                    save=True,
                )
                findings.append(f"Created line plot: {line_result.file_path}")
                chart_paths.append(line_result.file_path)

                # Histogram
                metrics.add_tool_call("ChartGenerator.histogram", success=True)
                hist_result = await chart_tool.histogram(
                    data=df,
                    column=numeric_cols[1],
                    kde=True,
                    bins="auto",
                    title=f"Distribution of {numeric_cols[1]}",
                    save=True,
                )
                findings.append(f"Created histogram: {hist_result.file_path}")
                chart_paths.append(hist_result.file_path)
            else:
                findings.append("Insufficient numeric columns for visualization")

        else:  # descriptive
            metrics.add_tool_call("StatisticsAnalyzer.describe_dataframe", success=True)
            desc = await stats_tool.describe_dataframe(df)

            findings.append(f"Shape: {desc['shape'][0]} rows × {desc['shape'][1]} columns")
            findings.append(f"Columns: {', '.join(desc['columns'])}")
            findings.append(f"Data types: {len(desc['dtypes'])} columns analyzed")

            if desc["missing_values"]:
                total_missing = sum(desc["missing_values"].values())
                findings.append(f"Missing values: {total_missing} total")

        return {
            **state,
            "findings": findings,
            "chart_paths": chart_paths,
            "metrics": metrics,
            "current_step": "analyzed",
        }

    except Exception as e:
        metrics.add_tool_call("data_analysis", success=False)
        return {
            **state,
            "findings": [f"Analysis failed: {str(e)}"],
            "error": str(e),
            "chart_paths": [],
            "metrics": metrics,
            "current_step": "analyzed",
        }


async def finalize_analysis_node(state: DataAgentState) -> dict:
    """Create final analysis report"""
    response_parts = []

    response_parts.append(f"**Data Analysis Report** ({state['analysis_type'].title()})\n")
    response_parts.append("**Findings:**")

    for i, finding in enumerate(state["findings"], 1):
        response_parts.append(f"{i}. {finding}")

    # Include chart paths if any were generated
    if state.get("chart_paths"):
        response_parts.append("\n**Generated Charts:**")
        for path in state["chart_paths"]:
            response_parts.append(f"- {path}")

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
            "chart_paths": [],
            "dataframe": None,
            "metrics": None,
            "final_response": None,
            "error": None,
            "current_step": "starting",
            "model_config": self.model_config,
        }

        # Build config with execution tracker callbacks
        config = self._build_graph_config(context)

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            return AgentExecutionResult(
                success=True,
                response=final_state.get("final_response", "Data analysis completed"),
                final_state=final_state,
                metadata={
                    "analysis_type": final_state.get("analysis_type"),
                    "findings_count": len(final_state.get("findings", [])),
                    "chart_count": len(final_state.get("chart_paths", [])),
                },
            )

        except Exception as e:
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Data analysis failed: {str(e)}",
            )
