"""
Kai (Reflexion Specialist) Agent Implementation
Self-reflective reasoning with iterative improvement based on Reflexion paper
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_f.state import ReflexionAgentState
from backend.core.config import get_settings
from backend.core.token_tracker import extract_token_usage_from_response
from backend.core.llm_factory import ModelConfig, create_llm, DEFAULT_CONFIGS


async def initial_reasoning_node(state: ReflexionAgentState) -> dict:
    """
    Generate initial reasoning attempt for the problem
    """
    if callback := state.get("task_callback"):
        await callback.on_progress_update(20, "initial_reasoning")

    # Use provided config or default to agent_f config
    config = state.get("model_config") or DEFAULT_CONFIGS["agent_f"]
    llm = create_llm(config, temperature=0.3)

    system_prompt = """You are Kai, a Reflexion Specialist at Commander.ai.
Your role is to solve problems through self-reflective reasoning.

For this initial attempt:
- Analyze the problem carefully
- Break it down into components
- Provide your reasoning step-by-step
- Arrive at a solution or answer
- Be explicit about your thought process"""

    user_prompt = f"""Problem/Task:
{state['query']}

Provide your initial reasoning and solution."""

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
            purpose="initial_reasoning"
        )

        # Broadcast metrics update in real-time
        if callback := state.get("task_callback"):
            await callback.update_metadata({
                "execution_metrics": metrics.to_dict(include_details=True)
            })

    # Store in trace
    reasoning_trace = state.get("reasoning_trace", [])
    reasoning_trace.append({
        "iteration": 1,
        "type": "initial_attempt",
        "content": response.content
    })

    return {
        **state,
        "initial_attempt": response.content,
        "reasoning_trace": reasoning_trace,
        "iteration": 1,
        "current_step": "initial_reasoned",
    }


async def self_critique_node(state: ReflexionAgentState) -> dict:
    """
    Perform self-critique of the reasoning
    """
    settings = get_settings()

    if callback := state.get("task_callback"):
        progress = 20 + (state.get("iteration", 1) * 20)
        await callback.on_progress_update(min(progress, 80), "self_critiquing")

    # Use provided config or default to agent_f config
    config = state.get("model_config") or DEFAULT_CONFIGS["agent_f"]
    llm = create_llm(config, temperature=0.2)

    # Get current reasoning to critique
    current_reasoning = state.get("refined_reasoning") or state.get("initial_attempt")

    system_prompt = """You are Kai, performing self-critique on your own reasoning.

Be brutally honest and identify:
1. **Logical flaws**: Errors in reasoning, invalid assumptions
2. **Missing information**: Gaps in analysis or understanding
3. **Alternative perspectives**: Other viewpoints not considered
4. **Weak arguments**: Unsupported claims or weak evidence
5. **Improvement opportunities**: How reasoning could be stronger

Output JSON:
{
    "overall_quality": "poor" | "fair" | "good" | "excellent",
    "flaws": ["list", "of", "specific", "flaws"],
    "strengths": ["what", "worked", "well"],
    "should_iterate": true/false,
    "improvement_strategy": "How to improve in next iteration"
}"""

    user_prompt = f"""Original problem:
{state['query']}

Current reasoning (iteration {state.get('iteration', 1)}):
{current_reasoning}

Perform self-critique in JSON format."""

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
                model="gpt-4o-mini",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                purpose=f"self_critique_iteration_{state.get('iteration', 1)}"
            )

            # Broadcast metrics update in real-time
            if callback := state.get("task_callback"):
                await callback.update_metadata({
                    "execution_metrics": metrics.to_dict(include_details=True)
                })

        # Parse JSON
        import json
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        critique = json.loads(content)

        flaws = critique.get("flaws", [])
        should_iterate = critique.get("should_iterate", False)
        improvement_strategy = critique.get("improvement_strategy", "")

        # Don't iterate if we've hit max iterations
        iteration = state.get("iteration", 1)
        max_iterations = state.get("max_iterations", 3)
        should_iterate = should_iterate and iteration < max_iterations

    except Exception as e:
        print(f"Failed to parse critique JSON: {e}")
        flaws = ["Unable to parse structured critique"]
        should_iterate = False
        improvement_strategy = "No strategy available"

    # Store in trace
    reasoning_trace = state.get("reasoning_trace", [])
    reasoning_trace.append({
        "iteration": state.get("iteration", 1),
        "type": "self_critique",
        "content": response.content,
        "should_iterate": should_iterate
    })

    return {
        **state,
        "self_critique": response.content,
        "identified_flaws": flaws,
        "improvement_strategy": improvement_strategy,
        "reasoning_trace": reasoning_trace,
        "should_iterate": should_iterate,
        "current_step": "critiqued",
    }


async def refine_reasoning_node(state: ReflexionAgentState) -> dict:
    """
    Generate improved reasoning based on self-critique
    """
    settings = get_settings()

    if callback := state.get("task_callback"):
        await callback.on_progress_update(70, "refining_reasoning")

    # Use provided config or default to agent_f config
    config = state.get("model_config") or DEFAULT_CONFIGS["agent_f"]
    llm = create_llm(config, temperature=0.3)

    # Get previous reasoning
    previous_reasoning = state.get("refined_reasoning") or state.get("initial_attempt")

    # Format flaws
    flaws_text = "\n".join(f"- {flaw}" for flaw in state.get("identified_flaws", []))

    system_prompt = """You are Kai, refining your reasoning based on self-critique.

Address all identified flaws and:
- Fix logical errors
- Fill information gaps
- Consider alternative perspectives
- Strengthen weak arguments
- Provide more thorough analysis

Build on what worked well from the previous attempt."""

    user_prompt = f"""Original problem:
{state['query']}

Previous reasoning:
{previous_reasoning}

Identified flaws:
{flaws_text}

Improvement strategy:
{state.get('improvement_strategy', 'Improve overall quality')}

Generate refined reasoning that addresses these issues."""

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
            purpose=f"refine_reasoning_iteration_{state.get('iteration', 1)}"
        )

        # Broadcast metrics update in real-time
        if callback := state.get("task_callback"):
            await callback.update_metadata({
                "execution_metrics": metrics.to_dict(include_details=True)
            })

    # Update iteration counter
    new_iteration = state.get("iteration", 1) + 1

    # Store in trace
    reasoning_trace = state.get("reasoning_trace", [])
    reasoning_trace.append({
        "iteration": new_iteration,
        "type": "refined_reasoning",
        "content": response.content
    })

    return {
        **state,
        "refined_reasoning": response.content,
        "reasoning_trace": reasoning_trace,
        "iteration": new_iteration,
        "current_step": "refined",
    }


async def finalize_reflexion_node(state: ReflexionAgentState) -> dict:
    """
    Create final reflexion report showing reasoning evolution
    """
    if callback := state.get("task_callback"):
        await callback.on_progress_update(90, "finalizing")

    # Calculate improvement score
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)
    improvement_score = min(1.0, iteration / max_iterations)

    # Build final report
    final_report = f"""# Reflexion Report by @kai

## Problem
{state['query']}

## Iterations: {iteration}/{max_iterations}
## Improvement Score: {improvement_score:.2f}/1.00

---

"""

    # Show reasoning evolution
    reasoning_trace = state.get("reasoning_trace", [])
    for entry in reasoning_trace:
        iter_num = entry.get("iteration", 0)
        entry_type = entry.get("type", "unknown")
        content = entry.get("content", "No content")

        if entry_type == "initial_attempt":
            final_report += f"### 🔷 Iteration {iter_num}: Initial Reasoning\n\n{content}\n\n---\n\n"
        elif entry_type == "self_critique":
            final_report += f"### 🔍 Iteration {iter_num}: Self-Critique\n\n{content}\n\n---\n\n"
        elif entry_type == "refined_reasoning":
            final_report += f"### ✨ Iteration {iter_num}: Refined Reasoning\n\n{content}\n\n---\n\n"

    # Add final answer
    final_answer = state.get("refined_reasoning") or state.get("initial_attempt")
    final_report += f"\n## Final Answer\n\n{final_answer}\n"

    return {
        **state,
        "final_response": final_report,
        "improvement_score": improvement_score,
        "current_step": "completed",
    }


def should_iterate_again(state: ReflexionAgentState) -> str:
    """Router: decide if another iteration is needed"""
    return "yes" if state.get("should_iterate", False) else "no"


class ReflexionAgent(BaseAgent):
    """
    Kai - Reflexion Specialist
    Self-reflective reasoning with iterative improvement
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_f",
            nickname="kai",
            specialization="Reflexion Specialist",
            description="Solves problems through self-reflective reasoning and iterative improvement",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create reflexion graph with iteration loop

        Flow:
        initial → critique → [iterate?] → refine → critique → ... → finalize → END
        """
        graph = StateGraph(ReflexionAgentState)

        # Add nodes
        graph.add_node("initial", initial_reasoning_node)
        graph.add_node("critique", self_critique_node)
        graph.add_node("refine", refine_reasoning_node)
        graph.add_node("finalize", finalize_reflexion_node)

        # Define flow
        graph.set_entry_point("initial")
        graph.add_edge("initial", "critique")

        # Conditional: iterate or finalize
        graph.add_conditional_edges(
            "critique",
            should_iterate_again,
            {"yes": "refine", "no": "finalize"},
        )

        # After refining, critique again
        graph.add_edge("refine", "critique")
        graph.add_edge("finalize", END)

        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute Kai's reflexion graph"""
        initial_state: ReflexionAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "iteration": 0,
            "max_iterations": 3,
            "reasoning_trace": [],
            "initial_attempt": None,
            "self_critique": None,
            "identified_flaws": [],
            "improvement_strategy": None,
            "refined_reasoning": None,
            "final_response": None,
            "improvement_score": None,
            "error": None,
            "current_step": "starting",
            "should_iterate": True,
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
                response=final_state.get("final_response", "Reflexion completed"),
                final_state=final_state,
                metadata={
                    "iterations": final_state.get("iteration", 0),
                    "improvement_score": final_state.get("improvement_score"),
                },
            )

        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Reflexion failed: {error_details}",
            )
