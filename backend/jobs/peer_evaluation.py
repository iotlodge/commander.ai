"""
Peer Evaluation Job

Background job that runs after task completion to get peer reviews from:
- Kai (critical thinking, reflexion)
- Maya (holistic reflection)

These agents evaluate the quality of other agents' work, providing
diverse perspectives for comprehensive performance assessment.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.core.config import get_settings
from backend.repositories.performance_repository import PerformanceRepository
from backend.core.database import get_session_maker

logger = logging.getLogger(__name__)


# Peer Evaluation Prompts

KAI_EVALUATION_PROMPT = """You are Kai, the reflexion and critical thinking specialist.

You've been asked to evaluate another agent's work. Be thorough, critical, and constructive.

Original Task: {original_command}
Agent: {agent_name}
Output: {agent_output}

Evaluate this work on the following criteria (0.0-1.0 scale):

1. **Accuracy**: Are the facts and reasoning correct? Any logical errors?
2. **Depth**: How thorough is the analysis? Surface-level or deep?
3. **Critical Thinking**: Does it consider multiple perspectives? Edge cases?
4. **Evidence Quality**: Are claims well-supported?

Provide your evaluation as JSON:
{{
  "accuracy": 0.0-1.0,
  "depth": 0.0-1.0,
  "critical_thinking": 0.0-1.0,
  "evidence_quality": 0.0-1.0,
  "overall": 0.0-1.0,
  "feedback": "Your detailed critique and suggestions for improvement..."
}}

Be honest and constructive. Focus on helping this agent improve."""


MAYA_EVALUATION_PROMPT = """You are Maya, the reflective and holistic thinking specialist.

You've been asked to evaluate another agent's work. Consider the big picture and user value.

Original Task: {original_command}
Agent: {agent_name}
Output: {agent_output}

Evaluate this work on the following criteria (0.0-1.0 scale):

1. **Relevance**: Does it actually answer what was asked?
2. **Usefulness**: Would this genuinely help the user?
3. **Completeness**: Are there important gaps or missing pieces?
4. **User Experience**: Is it easy to understand and actionable?

Provide your evaluation as JSON:
{{
  "relevance": 0.0-1.0,
  "usefulness": 0.0-1.0,
  "completeness": 0.0-1.0,
  "user_experience": 0.0-1.0,
  "overall": 0.0-1.0,
  "feedback": "Your holistic assessment and suggestions..."
}}

Be empathetic but honest. Focus on the user's perspective."""


class PeerEvaluationJob:
    """
    Background job to collect peer evaluations from Kai and Maya

    Usage:
        job = PeerEvaluationJob()
        await job.evaluate_task(task_id, agent_id, original_command, output)
    """

    def __init__(self):
        settings = get_settings()

        # Use GPT-4o-mini for cost-effective peer evaluation
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,  # Slight creativity for feedback
            api_key=settings.openai_api_key
        )

    async def evaluate_task(
        self,
        task_id: UUID,
        agent_id: str,
        agent_name: str,
        original_command: str,
        agent_output: str
    ) -> Dict[str, Any]:
        """
        Run peer evaluations from Kai and Maya

        Args:
            task_id: Task UUID
            agent_id: Agent identifier (e.g., "agent_a")
            agent_name: Human-readable agent name (e.g., "Bob")
            original_command: User's original command
            agent_output: Agent's result

        Returns:
            Dict with both evaluations
        """
        logger.info(f"Starting peer evaluation for task {task_id} (agent: {agent_name})")

        try:
            # Get evaluations from both agents in parallel
            import asyncio

            kai_eval_task = self._get_kai_evaluation(
                original_command, agent_name, agent_output
            )
            maya_eval_task = self._get_maya_evaluation(
                original_command, agent_name, agent_output
            )

            kai_eval, maya_eval = await asyncio.gather(
                kai_eval_task,
                maya_eval_task,
                return_exceptions=True
            )

            # Handle evaluation failures gracefully
            if isinstance(kai_eval, Exception):
                logger.error(f"Kai evaluation failed: {kai_eval}")
                kai_eval = self._default_evaluation("agent_kai")

            if isinstance(maya_eval, Exception):
                logger.error(f"Maya evaluation failed: {maya_eval}")
                maya_eval = self._default_evaluation("agent_maya")

            # Save to database
            await self._save_evaluations(task_id, agent_id, kai_eval, maya_eval)

            logger.info(f"Peer evaluations saved for task {task_id}")

            return {
                "kai": kai_eval,
                "maya": maya_eval
            }

        except Exception as e:
            logger.error(f"Peer evaluation job failed: {e}", exc_info=True)
            return {
                "kai": self._default_evaluation("agent_kai"),
                "maya": self._default_evaluation("agent_maya")
            }

    async def _get_kai_evaluation(
        self,
        original_command: str,
        agent_name: str,
        agent_output: str
    ) -> Dict[str, Any]:
        """Get critical evaluation from Kai"""
        prompt = KAI_EVALUATION_PROMPT.format(
            original_command=original_command,
            agent_name=agent_name,
            agent_output=agent_output[:2000]  # Limit output length
        )

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            # Parse JSON response
            import json
            eval_data = json.loads(response.content.strip())

            return {
                "evaluator_id": "agent_kai",
                "evaluator_name": "Kai",
                "score": eval_data.get("overall", 0.5),
                "criteria": {
                    "accuracy": eval_data.get("accuracy", 0.5),
                    "depth": eval_data.get("depth", 0.5),
                    "critical_thinking": eval_data.get("critical_thinking", 0.5),
                    "evidence_quality": eval_data.get("evidence_quality", 0.5),
                },
                "feedback": eval_data.get("feedback", "No feedback provided"),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Kai's evaluation JSON: {e}")
            # Try to extract score from text
            return self._extract_score_from_text(response.content, "agent_kai")
        except Exception as e:
            logger.error(f"Kai evaluation failed: {e}")
            raise

    async def _get_maya_evaluation(
        self,
        original_command: str,
        agent_name: str,
        agent_output: str
    ) -> Dict[str, Any]:
        """Get holistic evaluation from Maya"""
        prompt = MAYA_EVALUATION_PROMPT.format(
            original_command=original_command,
            agent_name=agent_name,
            agent_output=agent_output[:2000]  # Limit output length
        )

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            # Parse JSON response
            import json
            eval_data = json.loads(response.content.strip())

            return {
                "evaluator_id": "agent_maya",
                "evaluator_name": "Maya",
                "score": eval_data.get("overall", 0.5),
                "criteria": {
                    "relevance": eval_data.get("relevance", 0.5),
                    "usefulness": eval_data.get("usefulness", 0.5),
                    "completeness": eval_data.get("completeness", 0.5),
                    "user_experience": eval_data.get("user_experience", 0.5),
                },
                "feedback": eval_data.get("feedback", "No feedback provided"),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Maya's evaluation JSON: {e}")
            return self._extract_score_from_text(response.content, "agent_maya")
        except Exception as e:
            logger.error(f"Maya evaluation failed: {e}")
            raise

    def _extract_score_from_text(self, text: str, evaluator_id: str) -> Dict[str, Any]:
        """
        Fallback: Extract score from text if JSON parsing fails

        Looks for patterns like "0.85" or "overall: 0.75"
        """
        import re

        # Look for decimal numbers between 0 and 1
        matches = re.findall(r'0\.\d+|1\.0+', text)

        if matches:
            score = float(matches[0])
        else:
            score = 0.5  # Default

        return {
            "evaluator_id": evaluator_id,
            "evaluator_name": "Kai" if "kai" in evaluator_id else "Maya",
            "score": score,
            "criteria": {},
            "feedback": text[:500]  # Use raw text as feedback
        }

    def _default_evaluation(self, evaluator_id: str) -> Dict[str, Any]:
        """Default evaluation when evaluation fails"""
        return {
            "evaluator_id": evaluator_id,
            "evaluator_name": "Kai" if "kai" in evaluator_id else "Maya",
            "score": 0.5,
            "criteria": {},
            "feedback": "Evaluation unavailable"
        }

    async def _save_evaluations(
        self,
        task_id: UUID,
        agent_id: str,
        kai_eval: Dict[str, Any],
        maya_eval: Dict[str, Any]
    ):
        """Save peer evaluations to database"""
        session_maker = get_session_maker()

        async with session_maker() as session:
            repo = PerformanceRepository(session)

            # Save Kai's evaluation
            await repo.save_peer_evaluation(
                task_id=task_id,
                evaluated_agent_id=agent_id,
                evaluator_agent_id=kai_eval["evaluator_id"],
                evaluation_score=kai_eval["score"],
                evaluation_feedback=kai_eval["feedback"],
                evaluation_criteria=kai_eval["criteria"]
            )

            # Save Maya's evaluation
            await repo.save_peer_evaluation(
                task_id=task_id,
                evaluated_agent_id=agent_id,
                evaluator_agent_id=maya_eval["evaluator_id"],
                evaluation_score=maya_eval["score"],
                evaluation_feedback=maya_eval["feedback"],
                evaluation_criteria=maya_eval["criteria"]
            )

            await session.commit()


# Convenience function for background execution

async def run_peer_evaluation(
    task_id: UUID,
    agent_id: str,
    agent_name: str,
    original_command: str,
    agent_output: str
) -> Dict[str, Any]:
    """
    Run peer evaluation job

    Usage:
        # After task completes
        await run_peer_evaluation(task_id, agent_id, agent_name, command, output)
    """
    job = PeerEvaluationJob()
    return await job.evaluate_task(
        task_id=task_id,
        agent_id=agent_id,
        agent_name=agent_name,
        original_command=original_command,
        agent_output=agent_output
    )
