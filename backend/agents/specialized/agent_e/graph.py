"""
Maya (Reflection Specialist) Agent Implementation
Reviews and critiques outputs, providing constructive feedback
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_e.state import ReflectionAgentState
from backend.core.config import get_settings
from backend.core.token_tracker import extract_token_usage_from_response
from backend.core.llm_factory import ModelConfig, create_llm, DEFAULT_CONFIGS


async def analyze_content_node(state: ReflectionAgentState) -> dict:
    """
    Perform initial analysis of the content to review
    """
    if callback := state.get("task_callback"):
        await callback.on_progress_update(25, "analyzing")

    # Use provided config or default to agent_e config
    config = state.get("model_config") or DEFAULT_CONFIGS["agent_e"]
    llm = create_llm(config, temperature=0.2)

    system_prompt = """You are Maya, a Reflection Specialist at Commander.ai.
Your role is to critically analyze content and provide constructive feedback.

For any content you review:
1. Identify strengths and weaknesses
2. Check for clarity, accuracy, and completeness
3. Evaluate logical flow and structure
4. Assess quality and professionalism
5. Consider the intended audience

Provide a balanced, objective analysis."""

    user_prompt = f"""Analyze this content:

{state['query']}

Provide your initial analysis covering:
- Overall quality assessment
- Key strengths
- Areas for improvement
- Clarity and coherence
- Completeness"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics := state.get("metrics"):
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model=config.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="content_analysis"
        )

    return {
        **state,
        "initial_analysis": response.content,
        "current_step": "analyzed",
    }


async def identify_issues_node(state: ReflectionAgentState) -> dict:
    """
    Identify specific issues and improvement opportunities
    """
    if callback := state.get("task_callback"):
        await callback.on_progress_update(50, "identifying_issues")

    # Use provided config or default to agent_e config
    config = state.get("model_config") or DEFAULT_CONFIGS["agent_e"]
    llm = create_llm(config, temperature=0)

    system_prompt = """You are Maya, identifying specific issues in content.

Categorize issues by:
- **Critical**: Must be fixed (factual errors, major gaps)
- **Important**: Should be fixed (clarity issues, weak arguments)
- **Minor**: Nice to fix (style improvements, polish)

Output JSON array:
[
    {
        "severity": "critical" | "important" | "minor",
        "issue": "Description of the problem",
        "location": "Where it occurs",
        "suggestion": "How to fix it"
    }
]"""

    user_prompt = f"""Original content:
{state['query']}

Initial analysis:
{state.get('initial_analysis', '')}

Identify specific issues in JSON format."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)

        # Track token usage
        if metrics := state.get("metrics"):
            prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
            metrics.add_llm_call(
                model=config.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                purpose="identify_issues"
            )

        # Parse JSON
        import json
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        issues = json.loads(content)

    except Exception as e:
        print(f"Failed to parse issues JSON: {e}")
        issues = [{
            "severity": "unknown",
            "issue": "Unable to parse structured issues",
            "location": "general",
            "suggestion": response.content
        }]

    # Extract suggestions
    suggestions = [issue.get("suggestion", "") for issue in issues]

    return {
        **state,
        "identified_issues": issues,
        "suggested_improvements": suggestions,
        "current_step": "issues_identified",
    }


async def generate_improvements_node(state: ReflectionAgentState) -> dict:
    """
    Generate an improved version incorporating feedback
    """
    settings = get_settings()

    if callback := state.get("task_callback"):
        await callback.on_progress_update(75, "generating_improvements")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.openai_api_key,
        max_tokens=2000,
    )

    # Format issues for prompt
    issues_text = "\n".join([
        f"- [{issue.get('severity', 'unknown').upper()}] {issue.get('issue', '')} → {issue.get('suggestion', '')}"
        for issue in state.get("identified_issues", [])
    ])

    system_prompt = """You are Maya, refining content based on identified issues.

Create an improved version that:
- Addresses all critical and important issues
- Maintains the original intent and voice
- Enhances clarity and professionalism
- Improves structure and flow
- Adds necessary details or context

Do not completely rewrite - improve strategically."""

    user_prompt = f"""Original content:
{state['query']}

Identified issues:
{issues_text}

Generate an improved version that addresses these issues while maintaining the core message."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics := state.get("metrics"):
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="generate_improvements"
        )

    return {
        **state,
        "refined_output": response.content,
        "current_step": "improvements_generated",
    }


async def finalize_reflection_node(state: ReflectionAgentState) -> dict:
    """
    Create final reflection report with score
    """
    if callback := state.get("task_callback"):
        await callback.on_progress_update(90, "finalizing")

    issues = state.get("identified_issues", [])

    # Calculate reflection score based on issue severity
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    important_count = sum(1 for i in issues if i.get("severity") == "important")
    minor_count = sum(1 for i in issues if i.get("severity") == "minor")

    # Score: 1.0 (perfect) down to 0.0 (many critical issues)
    score = max(0.0, 1.0 - (critical_count * 0.3 + important_count * 0.15 + minor_count * 0.05))

    # Build final report
    final_report = f"""# Reflection Report by @maya

## Quality Score: {score:.2f}/1.00

## Initial Analysis
{state.get('initial_analysis', 'No analysis available')}

## Identified Issues ({len(issues)} total)
"""

    for issue in issues:
        severity_emoji = {"critical": "🔴", "important": "🟡", "minor": "🟢"}.get(
            issue.get("severity", "unknown"), "⚪"
        )
        final_report += f"\n{severity_emoji} **{issue.get('severity', 'Unknown').title()}**: {issue.get('issue', 'No description')}\n"
        final_report += f"   - *Location*: {issue.get('location', 'Not specified')}\n"
        final_report += f"   - *Suggestion*: {issue.get('suggestion', 'No suggestion')}\n"

    final_report += f"\n## Refined Version\n\n{state.get('refined_output', 'No refined version generated')}\n"

    return {
        **state,
        "final_response": final_report,
        "reflection_score": score,
        "current_step": "completed",
    }


class ReflectionAgent(BaseAgent):
    """
    Maya - Reflection Specialist
    Reviews and critiques outputs with constructive feedback
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_e",
            nickname="maya",
            specialization="Reflection Specialist",
            description="Reviews and critiques content, providing constructive feedback and improvements",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create reflection graph

        Flow:
        analyze → identify_issues → generate_improvements → finalize → END
        """
        graph = StateGraph(ReflectionAgentState)

        # Add nodes
        graph.add_node("analyze", analyze_content_node)
        graph.add_node("identify_issues", identify_issues_node)
        graph.add_node("generate_improvements", generate_improvements_node)
        graph.add_node("finalize", finalize_reflection_node)

        # Define flow
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "identify_issues")
        graph.add_edge("identify_issues", "generate_improvements")
        graph.add_edge("generate_improvements", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute Maya's reflection graph"""
        initial_state: ReflectionAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "initial_analysis": None,
            "identified_issues": [],
            "suggested_improvements": [],
            "refined_output": None,
            "final_response": None,
            "reflection_score": None,
            "error": None,
            "current_step": "starting",
            "task_callback": context.task_callback,
            "metrics": context.metrics,
            "model_config": self.model_config,
        }

        # Build config with execution tracker callbacks
        config = self._build_graph_config(context)

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            return AgentExecutionResult(
                success=True,
                response=final_state.get("final_response", "Reflection completed"),
                final_state=final_state,
                metadata={
                    "reflection_score": final_state.get("reflection_score"),
                    "issues_count": len(final_state.get("identified_issues", [])),
                },
            )

        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Reflection failed: {error_details}",
            )
