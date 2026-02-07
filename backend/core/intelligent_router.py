"""
Intelligent Router - Performance-Based Agent Selection

Leo uses this to select the optimal agent for each task based on:
- Historical performance per category
- Current agent load
- Cost constraints
- Speed requirements

Routing Decisions:
- Primary metric: Category-specific avg score
- Secondary: Success rate
- Tertiary: Current load (don't overload high performers)

All decisions are logged for transparency and future NLP analysis.

**Cost**: Free (no LLM calls, pure algorithm)
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.performance_repository import (
    AgentPerformanceStatsModel,
    AgentPerformanceScoreModel,
    PerformanceRepository,
)
from backend.core.category_classifier import TaskCategory
from backend.core.database import get_session_maker

logger = logging.getLogger(__name__)


@dataclass
class AgentScore:
    """Score for an agent candidate"""
    agent_id: str
    nickname: str
    base_score: float  # Category performance
    success_rate: float
    load_penalty: float  # 0-1, higher = more loaded
    final_score: float  # After load adjustment
    reason: str  # Human-readable explanation


@dataclass
class RoutingDecision:
    """Complete routing decision with reasoning"""
    selected_agent_id: str
    selected_nickname: str
    task_category: TaskCategory
    all_scores: List[AgentScore]
    reason: str
    timestamp: datetime
    constraints: Dict[str, Any]


class IntelligentRouter:
    """
    Select optimal agent based on performance history

    Usage:
        router = IntelligentRouter()
        decision = await router.select_agent(
            command="@bob research quantum computing",
            category="research"
        )
        # decision.selected_agent_id = "agent_a"
    """

    # Agent specializations (default capabilities)
    AGENT_SPECIALIZATIONS = {
        "agent_a": ["research", "analysis"],      # Bob
        "agent_b": ["compliance", "analysis"],    # Sue
        "agent_c": ["analysis", "writing"],       # Rex
        "agent_d": ["planning", "analysis"],      # Kai
        "agent_e": ["planning", "chat"],          # Maya
        "agent_f": ["writing", "research"],       # Alice
        "agent_g": ["chat"],                      # Chat
    }

    AGENT_NICKNAMES = {
        "agent_a": "bob",
        "agent_b": "sue",
        "agent_c": "rex",
        "agent_d": "kai",
        "agent_e": "maya",
        "agent_f": "alice",
        "agent_g": "chat",
    }

    # Minimum tasks required before trusting stats (probation period)
    MIN_TASKS_FOR_TRUST = 5

    def __init__(self):
        self.routing_log: List[RoutingDecision] = []

    async def select_agent(
        self,
        command: str,
        category: TaskCategory,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Select optimal agent for a task

        Args:
            command: User's command
            category: Task category (from CategoryClassifier)
            constraints: Optional {"max_cost": 0.10, "max_duration": 30}

        Returns:
            RoutingDecision with selected agent and reasoning
        """
        logger.info(f"Selecting agent for category: {category.value}")

        constraints = constraints or {}

        # Get capable agents for this category
        capable_agents = self._get_capable_agents(category)

        if not capable_agents:
            # Fallback: return default agent for category
            return self._fallback_selection(category, constraints)

        # Score each agent
        session_maker = get_session_maker()
        async with session_maker() as session:
            scores = await self._score_agents(
                session=session,
                capable_agents=capable_agents,
                category=category,
                constraints=constraints
            )

        # Select best agent
        if scores:
            best_score = max(scores, key=lambda x: x.final_score)
            selected_agent_id = best_score.agent_id
            selected_nickname = best_score.nickname
            reason = self._explain_selection(best_score, scores)
        else:
            # No stats available, use default specialization
            selected_agent_id = capable_agents[0]
            selected_nickname = self.AGENT_NICKNAMES[selected_agent_id]
            reason = f"No performance data available, using default specialist ({selected_nickname})"
            scores = []

        # Create decision record
        decision = RoutingDecision(
            selected_agent_id=selected_agent_id,
            selected_nickname=selected_nickname,
            task_category=category,
            all_scores=scores,
            reason=reason,
            timestamp=datetime.utcnow(),
            constraints=constraints
        )

        # Log decision (for transparency / future NLP)
        self.routing_log.append(decision)
        logger.info(f"Selected: {selected_nickname} (score: {best_score.final_score:.2f if scores else 'N/A'})")
        logger.info(f"Reason: {reason}")

        return decision

    def _get_capable_agents(self, category: TaskCategory) -> List[str]:
        """
        Get agents capable of handling this category

        Returns:
            List of agent_ids, ordered by default specialization
        """
        capable = []

        for agent_id, specializations in self.AGENT_SPECIALIZATIONS.items():
            if category.value in specializations:
                capable.append(agent_id)

        # If no specialists, return all agents (except chat for non-chat tasks)
        if not capable and category != TaskCategory.CHAT:
            capable = [
                aid for aid in self.AGENT_SPECIALIZATIONS.keys()
                if aid != "agent_g"  # Exclude chat agent
            ]

        return capable

    async def _score_agents(
        self,
        session: AsyncSession,
        capable_agents: List[str],
        category: TaskCategory,
        constraints: Dict[str, Any]
    ) -> List[AgentScore]:
        """
        Score each capable agent based on performance history

        Scoring algorithm:
        - Base score: Category-specific avg performance (0-1)
        - Success rate: % of tasks with score >= 0.6
        - Load penalty: Current active task count

        Final score = (base_score × success_rate) × (1 - load_penalty)
        """
        scores = []

        for agent_id in capable_agents:
            nickname = self.AGENT_NICKNAMES[agent_id]

            # Get agent's performance stats
            stats = await self._get_agent_stats(session, agent_id)

            if not stats or stats.total_tasks < self.MIN_TASKS_FOR_TRUST:
                # Not enough data, skip (will use fallback)
                continue

            # Get category-specific performance
            base_score = self._get_category_score(stats, category)

            # Calculate success rate
            success_rate = stats.successful_tasks / stats.total_tasks if stats.total_tasks > 0 else 0.0

            # Get current load
            load_penalty = await self._get_load_penalty(session, agent_id)

            # Check constraints
            if not self._meets_constraints(stats, constraints):
                # Agent doesn't meet constraints, skip
                continue

            # Calculate final score
            final_score = (base_score * success_rate) * (1 - load_penalty)

            scores.append(AgentScore(
                agent_id=agent_id,
                nickname=nickname,
                base_score=base_score,
                success_rate=success_rate,
                load_penalty=load_penalty,
                final_score=final_score,
                reason=f"{nickname}: {base_score:.2f} perf × {success_rate:.2f} success × {1-load_penalty:.2f} availability"
            ))

        return scores

    async def _get_agent_stats(
        self,
        session: AsyncSession,
        agent_id: str
    ) -> Optional[AgentPerformanceStatsModel]:
        """Get aggregated stats for an agent"""
        stmt = select(AgentPerformanceStatsModel).where(
            AgentPerformanceStatsModel.agent_id == agent_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_category_score(
        self,
        stats: AgentPerformanceStatsModel,
        category: TaskCategory
    ) -> float:
        """
        Get agent's performance for specific category

        Returns:
            Score (0-1), or overall_score if category not found
        """
        if not stats.category_performance:
            return float(stats.avg_overall_score) if stats.avg_overall_score else 0.5

        category_data = stats.category_performance.get(category.value)

        if category_data:
            return category_data.get("avg_score", 0.5)

        # Category not found, use overall score
        return float(stats.avg_overall_score) if stats.avg_overall_score else 0.5

    async def _get_load_penalty(
        self,
        session: AsyncSession,
        agent_id: str
    ) -> float:
        """
        Calculate load penalty based on active tasks

        Returns:
            0.0 = no load, 0.5 = moderate load, 0.8 = heavy load
        """
        # TODO: Query active tasks from agent_tasks table
        # For now, return 0.0 (no load penalty)
        # Phase 3 enhancement: track active tasks
        return 0.0

    def _meets_constraints(
        self,
        stats: AgentPerformanceStatsModel,
        constraints: Dict[str, Any]
    ) -> bool:
        """Check if agent meets cost/speed constraints"""
        if "max_cost" in constraints:
            if stats.avg_cost_per_task and stats.avg_cost_per_task > constraints["max_cost"]:
                return False

        if "max_duration" in constraints:
            if stats.avg_duration_seconds and stats.avg_duration_seconds > constraints["max_duration"]:
                return False

        return True

    def _explain_selection(
        self,
        best: AgentScore,
        all_scores: List[AgentScore]
    ) -> str:
        """Generate human-readable explanation"""
        if len(all_scores) == 1:
            return f"{best.nickname} is the only agent with sufficient experience in this category"

        # Sort by score
        sorted_scores = sorted(all_scores, key=lambda x: x.final_score, reverse=True)

        explanation = f"{best.nickname} selected with score {best.final_score:.2f}. "

        if len(sorted_scores) > 1:
            runner_up = sorted_scores[1]
            diff = best.final_score - runner_up.final_score
            explanation += f"Runner-up: {runner_up.nickname} ({runner_up.final_score:.2f}, -{diff:.2f}). "

        explanation += f"Performance: {best.base_score:.2f}, Success rate: {best.success_rate:.2f}"

        return explanation

    def _fallback_selection(
        self,
        category: TaskCategory,
        constraints: Dict[str, Any]
    ) -> RoutingDecision:
        """
        Fallback when no performance data available

        Uses default specializations
        """
        # Map category to default agent
        default_agents = {
            TaskCategory.RESEARCH: "agent_a",  # Bob
            TaskCategory.ANALYSIS: "agent_c",  # Rex
            TaskCategory.WRITING: "agent_f",   # Alice
            TaskCategory.COMPLIANCE: "agent_b", # Sue
            TaskCategory.PLANNING: "agent_d",  # Kai
            TaskCategory.CHAT: "agent_g",      # Chat
        }

        agent_id = default_agents.get(category, "agent_a")
        nickname = self.AGENT_NICKNAMES[agent_id]

        return RoutingDecision(
            selected_agent_id=agent_id,
            selected_nickname=nickname,
            task_category=category,
            all_scores=[],
            reason=f"No performance data available, using default specialist for {category.value}: {nickname}",
            timestamp=datetime.utcnow(),
            constraints=constraints
        )

    async def save_routing_decision(
        self,
        decision: RoutingDecision,
        task_id: UUID,
        command: str
    ):
        """
        Save routing decision to database for transparency

        Stores decision log for future NLP analysis and routing optimization
        """
        session_maker = get_session_maker()

        async with session_maker() as session:
            # TODO: Create routing_decisions table to store this
            # For now, just log it
            logger.info(
                f"Routing decision for task {task_id}: "
                f"{decision.selected_nickname} (category: {decision.task_category.value})"
            )
            logger.info(f"Reason: {decision.reason}")

            # Future: Insert into routing_decisions table
            # routing_decision = RoutingDecisionModel(
            #     id=str(uuid4()),
            #     task_id=str(task_id),
            #     command=command,
            #     category=decision.task_category.value,
            #     selected_agent_id=decision.selected_agent_id,
            #     all_scores=decision.all_scores,
            #     reason=decision.reason,
            #     constraints=decision.constraints,
            #     created_at=decision.timestamp
            # )
            # session.add(routing_decision)
            # await session.commit()


# Convenience function

async def select_best_agent(
    command: str,
    category: TaskCategory,
    constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    Select best agent for a task (returns agent_id)

    Usage:
        agent_id = await select_best_agent(
            command="@bob research quantum computing",
            category=TaskCategory.RESEARCH
        )
        # agent_id = "agent_a"
    """
    router = IntelligentRouter()
    decision = await router.select_agent(command, category, constraints)
    return decision.selected_agent_id
