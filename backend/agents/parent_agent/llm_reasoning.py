"""
LLM-Powered Task Reasoning
Intelligent task decomposition using OpenAI GPT-4o-mini
"""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.core.token_tracker import ExecutionMetrics, extract_token_usage_from_response


async def llm_decompose_task(query: str, user_context: dict[str, Any] | None = None, metrics: ExecutionMetrics | None = None) -> dict[str, Any]:
    """
    Use LLM to intelligently decompose a research task into subtasks

    Args:
        query: The user's research request
        user_context: Optional context about conversation history

    Returns:
        dict containing:
            - task_type: str
            - subtasks: list[dict] with agent assignments and refined prompts
            - reasoning: str explaining the decomposition
    """
    settings = get_settings()

    # Initialize GPT-4o-mini for cost-effective reasoning
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.openai_api_key,
    )

    system_prompt = """You are an intelligent task orchestrator for Commander.ai.
Your job is to analyze research requests and decompose them into targeted subtasks.

Available specialist agents:
- bob (Research Specialist): Conducts web research, information gathering, synthesis
- sue (Compliance Specialist): Reviews for legal/regulatory compliance, privacy, GDPR
- rex (Data Analyst): Analyzes data, creates visualizations, statistical analysis
- alice (Document Manager): Manages documents, PDFs, creates collections

For research tasks, you should:
1. Identify the main investigation areas
2. Create 1-5 focused subtasks (prefer 3-4 for balance)
3. Assign each subtask to the most appropriate agent(s)
4. Refine each subtask into a clear, specific prompt
5. Consider parallel execution when subtasks are independent

Output format (JSON):
{
    "task_type": "research" | "compliance" | "data_analysis" | "multi_specialist",
    "reasoning": "Brief explanation of decomposition strategy",
    "subtasks": [
        {
            "type": "research",
            "assigned_to": "bob",
            "query": "Specific refined prompt for this subtask",
            "investigation_area": "Brief label for this area"
        }
    ]
}

Example:
Query: "Research quantum computing applications in cryptography"
Output:
{
    "task_type": "research",
    "reasoning": "This requires technical research on quantum computing and security analysis for cryptography. Bob can handle both areas with focused prompts.",
    "subtasks": [
        {
            "type": "research",
            "assigned_to": "bob",
            "query": "Research current state of quantum computing hardware and algorithms, focusing on qubit stability and error correction",
            "investigation_area": "quantum computing fundamentals"
        },
        {
            "type": "research",
            "assigned_to": "bob",
            "query": "Research quantum algorithms (Shor's, Grover's) and their implications for breaking current encryption methods (RSA, ECC)",
            "investigation_area": "cryptographic vulnerabilities"
        },
        {
            "type": "research",
            "assigned_to": "bob",
            "query": "Research post-quantum cryptography solutions and NIST standardization efforts",
            "investigation_area": "quantum-resistant solutions"
        }
    ]
}
"""

    user_prompt = f"""Analyze this research request and decompose it into subtasks:

REQUEST: {query}

Provide your decomposition in JSON format."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        # Get LLM response
        response = await llm.ainvoke(messages)

        # Track token usage
        if metrics:
            prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
            metrics.add_llm_call(
                model="gpt-4o-mini",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                purpose="task_decomposition"
            )

        # Parse JSON response
        import json
        content = response.content

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        # Validate structure
        if not result.get("subtasks"):
            result["subtasks"] = [
                {
                    "type": "research",
                    "assigned_to": "bob",
                    "query": query,
                    "investigation_area": "general research"
                }
            ]

        return result

    except Exception as e:
        # Fallback to simple decomposition on error
        print(f"LLM decomposition failed: {e}. Using fallback.")
        return {
            "task_type": "research",
            "reasoning": f"Fallback decomposition due to error: {e}",
            "subtasks": [
                {
                    "type": "research",
                    "assigned_to": "bob",
                    "query": query,
                    "investigation_area": "general research"
                }
            ]
        }
