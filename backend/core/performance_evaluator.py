"""
Performance Evaluator - LLM-based Quality Scoring

Uses GPT-4o to evaluate task outputs on multiple quality dimensions:
- Accuracy: Did it correctly answer the question?
- Relevance: Was it on-topic and helpful?
- Completeness: Did it cover all aspects?
- Clarity: Was it well-structured and clear?

This provides objective quality metrics for agent optimization.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PerformanceScores:
    """Quality scores for a task output"""
    accuracy: float  # 0-1 scale
    relevance: float
    completeness: float
    clarity: float
    overall: float  # Weighted average

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for storage"""
        return {
            "accuracy_score": self.accuracy,
            "relevance_score": self.relevance,
            "completeness_score": self.completeness,
            "overall_score": self.overall,
            # Note: clarity is used in calculation but not stored separately (yet)
        }


class PerformanceEvaluator:
    """
    Evaluates task outputs using LLM-based scoring

    Uses GPT-4o-mini for cost-effective evaluation (meta-reasoning)
    """

    # Scoring weights for overall calculation
    WEIGHTS = {
        "accuracy": 0.35,
        "relevance": 0.25,
        "completeness": 0.25,
        "clarity": 0.15,
    }

    def __init__(self):
        settings = get_settings()

        # Use GPT-4o-mini for cost-effective evaluation
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,  # Deterministic scoring
            api_key=settings.openai_api_key
        )

    async def evaluate_task(
        self,
        original_command: str,
        agent_output: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceScores:
        """
        Evaluate a completed task output

        Args:
            original_command: User's original command/query
            agent_output: Agent's final result/response
            agent_name: Name of the agent that executed the task
            metadata: Optional execution metadata (tokens, duration, etc.)

        Returns:
            PerformanceScores with quality ratings
        """
        logger.info(f"Evaluating task output from {agent_name}")

        try:
            # Get individual dimension scores
            accuracy = await self._evaluate_accuracy(original_command, agent_output)
            relevance = await self._evaluate_relevance(original_command, agent_output)
            completeness = await self._evaluate_completeness(original_command, agent_output)
            clarity = await self._evaluate_clarity(agent_output)

            # Calculate weighted overall score
            overall = self._calculate_overall(
                accuracy=accuracy,
                relevance=relevance,
                completeness=completeness,
                clarity=clarity
            )

            scores = PerformanceScores(
                accuracy=accuracy,
                relevance=relevance,
                completeness=completeness,
                clarity=clarity,
                overall=overall
            )

            logger.info(f"Task evaluation complete: {overall:.2f} overall")
            return scores

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            # Return default scores on error
            return PerformanceScores(
                accuracy=0.5,
                relevance=0.5,
                completeness=0.5,
                clarity=0.5,
                overall=0.5
            )

    async def _evaluate_accuracy(self, query: str, output: str) -> float:
        """
        Evaluate accuracy: Did it correctly answer the question?

        Returns:
            Score from 0.0 to 1.0
        """
        prompt = f"""You are an expert evaluator assessing the accuracy of AI agent responses.

Original Query: {query}

Agent Response: {output}

Evaluate the ACCURACY of this response on a 0.0-1.0 scale:
- 1.0 = Perfectly accurate, all facts correct
- 0.8 = Mostly accurate, minor errors
- 0.6 = Partially accurate, some errors
- 0.4 = Mostly inaccurate, significant errors
- 0.2 = Completely inaccurate or wrong

Consider:
- Factual correctness
- Logical consistency
- Absence of hallucinations

Respond with ONLY a number between 0.0 and 1.0 (e.g., "0.85")"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))  # Clamp to 0-1
        except Exception as e:
            logger.warning(f"Accuracy evaluation failed: {e}")
            return 0.5

    async def _evaluate_relevance(self, query: str, output: str) -> float:
        """
        Evaluate relevance: Was it on-topic and helpful?

        Returns:
            Score from 0.0 to 1.0
        """
        prompt = f"""You are an expert evaluator assessing the relevance of AI agent responses.

Original Query: {query}

Agent Response: {output}

Evaluate the RELEVANCE of this response on a 0.0-1.0 scale:
- 1.0 = Perfectly relevant, directly addresses the query
- 0.8 = Mostly relevant, minor tangents
- 0.6 = Partially relevant, some off-topic content
- 0.4 = Mostly irrelevant, significant off-topic content
- 0.2 = Completely irrelevant or unrelated

Consider:
- Does it answer what was asked?
- Is the information useful for the query?
- Does it stay on-topic?

Respond with ONLY a number between 0.0 and 1.0 (e.g., "0.90")"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Relevance evaluation failed: {e}")
            return 0.5

    async def _evaluate_completeness(self, query: str, output: str) -> float:
        """
        Evaluate completeness: Did it cover all aspects?

        Returns:
            Score from 0.0 to 1.0
        """
        prompt = f"""You are an expert evaluator assessing the completeness of AI agent responses.

Original Query: {query}

Agent Response: {output}

Evaluate the COMPLETENESS of this response on a 0.0-1.0 scale:
- 1.0 = Fully complete, all aspects covered
- 0.8 = Mostly complete, minor gaps
- 0.6 = Partially complete, some aspects missing
- 0.4 = Mostly incomplete, significant gaps
- 0.2 = Very incomplete, barely addressed the query

Consider:
- Are all parts of the query addressed?
- Is sufficient detail provided?
- Are there obvious gaps?

Respond with ONLY a number between 0.0 and 1.0 (e.g., "0.75")"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Completeness evaluation failed: {e}")
            return 0.5

    async def _evaluate_clarity(self, output: str) -> float:
        """
        Evaluate clarity: Was it well-structured and clear?

        Returns:
            Score from 0.0 to 1.0
        """
        prompt = f"""You are an expert evaluator assessing the clarity of AI agent responses.

Agent Response: {output}

Evaluate the CLARITY of this response on a 0.0-1.0 scale:
- 1.0 = Perfectly clear, well-structured, easy to understand
- 0.8 = Mostly clear, minor organization issues
- 0.6 = Partially clear, some confusion
- 0.4 = Mostly unclear, hard to follow
- 0.2 = Very unclear, confusing or poorly structured

Consider:
- Organization and structure
- Writing quality
- Ease of understanding
- Use of formatting (bullets, headers, etc.)

Respond with ONLY a number between 0.0 and 1.0 (e.g., "0.80")"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Clarity evaluation failed: {e}")
            return 0.5

    def _calculate_overall(
        self,
        accuracy: float,
        relevance: float,
        completeness: float,
        clarity: float
    ) -> float:
        """
        Calculate weighted overall score

        Weights:
        - Accuracy: 35%
        - Relevance: 25%
        - Completeness: 25%
        - Clarity: 15%
        """
        overall = (
            accuracy * self.WEIGHTS["accuracy"] +
            relevance * self.WEIGHTS["relevance"] +
            completeness * self.WEIGHTS["completeness"] +
            clarity * self.WEIGHTS["clarity"]
        )

        return round(overall, 2)
