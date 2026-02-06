"""
LLM-Powered Result Aggregation
Intelligently synthesizes outputs from multiple specialist agents
"""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.core.token_tracker import ExecutionMetrics, extract_token_usage_from_response


async def llm_aggregate_results(
    original_query: str,
    specialist_results: dict[str, dict[str, Any]],
    task_type: str,
    decomposition_reasoning: str | None = None,
    metrics: ExecutionMetrics | None = None
) -> str:
    """
    Use LLM to intelligently aggregate results from multiple agents

    Args:
        original_query: The original user query
        specialist_results: Dict of {agent_nickname: result_dict}
        task_type: Type of task (research, compliance, etc.)
        decomposition_reasoning: Optional reasoning from task decomposition

    Returns:
        Synthesized final response
    """
    settings = get_settings()

    # If only one agent, just return their response
    if len(specialist_results) == 1:
        agent_name = list(specialist_results.keys())[0]
        return specialist_results[agent_name]["response"]

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.openai_api_key,
        max_tokens=3000,
    )

    # TODO: Add image generation capability for complex flows
    # Use image_generate_analyze_upscale.py to create diagrams when:
    # - Explaining multi-agent workflows visually
    # - Showing data flow between specialists
    # - Illustrating complex concepts from research results
    # - Creating architecture diagrams for technical responses
    # Example: python image_generate_analyze_upscale.py generate \
    #   --prompt "Flowchart showing how bob's research flows to sue's compliance check" \
    #   --output output/workflow_diagram.png

    system_prompt = """You are Leo, the Orchestrator at Commander.ai.
Your role is to synthesize outputs from multiple specialist agents into a coherent, comprehensive final response.

Guidelines:
- Create a unified narrative that integrates all specialist insights
- Highlight key findings from each specialist
- Show how different perspectives complement each other
- Resolve any contradictions or overlaps
- Structure the response logically with clear sections
- Use markdown formatting for readability
- Credit specialists when mentioning their specific contributions
- Provide an executive summary at the top
- End with actionable recommendations or next steps

Maintain a professional, analytical tone befitting an orchestration agent."""

    # Build specialist contributions text
    contributions = []
    for agent_name, result in specialist_results.items():
        status = "✓ Success" if result.get("success") else "✗ Failed"
        response = result.get("response", "No response")
        error = result.get("error", "")

        contribution = f"""**@{agent_name}** ({status}):
{response}"""

        if error:
            contribution += f"\n\n*Error: {error}*"

        contributions.append(contribution)

    contributions_text = "\n\n" + "---\n\n".join(contributions)

    decomposition_context = ""
    if decomposition_reasoning:
        decomposition_context = f"\n\nTask Decomposition Strategy:\n{decomposition_reasoning}\n"

    user_prompt = f"""Original Query: {original_query}

Task Type: {task_type}{decomposition_context}

Specialist Contributions:
{contributions_text}

Synthesize these specialist outputs into a comprehensive final response.
Structure your response with:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (organized by theme or specialist)
3. **Integrated Analysis**
4. **Recommendations/Next Steps**

Ensure the final response directly addresses the original query."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)

        # Track token usage
        if metrics:
            prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
            metrics.add_llm_call(
                model="gpt-4o-mini",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                purpose="result_aggregation"
            )

        return response.content

    except Exception as e:
        # Fallback to simple aggregation if LLM fails
        print(f"LLM aggregation failed: {e}. Using fallback.")

        fallback = f"# Research Results\n\n"
        fallback += f"**Original Query:** {original_query}\n\n"

        for agent_name, result in specialist_results.items():
            if result.get("success"):
                fallback += f"## @{agent_name}'s Analysis\n\n"
                fallback += f"{result['response']}\n\n"
                fallback += "---\n\n"
            else:
                fallback += f"## @{agent_name} (Failed)\n\n"
                fallback += f"Error: {result.get('error', 'Unknown error')}\n\n"
                fallback += "---\n\n"

        return fallback


async def format_downloadable_output(
    final_response: str,
    metadata: dict[str, Any]
) -> dict[str, Any]:
    """
    Format the final response for downloadable output (future: .docx, .pdf, etc.)

    Args:
        final_response: The synthesized response
        metadata: Additional metadata about the task

    Returns:
        Dict with formatted output and metadata
    """
    # For now, just return markdown format
    # TODO: In future, generate actual .docx/.pdf files

    output = {
        "format": "markdown",
        "content": final_response,
        "metadata": metadata,
        "filename_suggestion": f"research_results_{metadata.get('timestamp', 'unknown')}.md"
    }

    return output
