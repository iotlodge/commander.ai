"""
Stats Aggregation Job

Scheduled job (hourly) that aggregates performance data and calculates rankings.

Updates agent_performance_stats table with:
- Total tasks, success rate
- Average scores (overall, user rating)
- Cost metrics (total, avg per task, efficiency)
- Category performance (research, analysis, etc.)
- Model performance (which models work best)
- Rankings (overall and per-category)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.performance_repository import (
    AgentPerformanceScoreModel,
    AgentPeerEvaluationModel,
    AgentPerformanceStatsModel,
    PerformanceRepository,
)
from backend.core.database import get_session_maker

logger = logging.getLogger(__name__)


class StatsAggregationJob:
    """
    Aggregate performance data and calculate rankings

    Run this hourly to keep stats fresh:
        job = StatsAggregationJob()
        await job.run()
    """

    def __init__(self):
        self.agent_nicknames = {
            "agent_parent": "leo",
            "agent_a": "bob",
            "agent_b": "sue",
            "agent_c": "rex",
            "agent_d": "kai",
            "agent_e": "maya",
            "agent_f": "alice",
            "agent_g": "chat",
        }

    async def run(self) -> Dict[str, Any]:
        """
        Run stats aggregation job

        Returns:
            Dict with summary of updates
        """
        logger.info("Starting stats aggregation job...")
        start_time = datetime.utcnow()

        session_maker = get_session_maker()

        async with session_maker() as session:
            # Aggregate stats for each agent
            updated_agents = []

            for agent_id, nickname in self.agent_nicknames.items():
                try:
                    stats = await self._aggregate_agent_stats(session, agent_id, nickname)

                    if stats:
                        updated_agents.append(agent_id)
                        logger.info(f"Updated stats for {nickname}: {stats['total_tasks']} tasks")

                except Exception as e:
                    logger.error(f"Failed to aggregate stats for {agent_id}: {e}", exc_info=True)

            # Calculate rankings after all agents updated
            await self._calculate_rankings(session)

            await session.commit()

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "status": "completed",
            "updated_agents": updated_agents,
            "updated_count": len(updated_agents),
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Stats aggregation complete: {len(updated_agents)} agents updated in {duration:.2f}s")

        return result

    async def _aggregate_agent_stats(
        self,
        session: AsyncSession,
        agent_id: str,
        nickname: str
    ) -> Dict[str, Any] | None:
        """
        Aggregate stats for a single agent

        Returns:
            Dict with aggregated stats, or None if no data
        """
        # Get all performance scores for this agent
        stmt = select(AgentPerformanceScoreModel).where(
            AgentPerformanceScoreModel.agent_id == agent_id
        )
        result = await session.execute(stmt)
        scores = list(result.scalars().all())

        if not scores:
            return None

        # Calculate aggregated metrics
        total_tasks = len(scores)
        successful_tasks = sum(1 for s in scores if s.overall_score and s.overall_score >= 0.6)
        failed_tasks = total_tasks - successful_tasks

        # Average scores
        overall_scores = [s.overall_score for s in scores if s.overall_score]
        avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0

        user_ratings = [s.user_rating for s in scores if s.user_rating]
        avg_user_rating = sum(user_ratings) / len(user_ratings) if user_ratings else None

        # Cost metrics
        total_cost = sum(s.estimated_cost for s in scores if s.estimated_cost) or 0.0
        avg_cost_per_task = total_cost / total_tasks if total_tasks > 0 else 0.0

        # Cost efficiency (quality per dollar)
        if total_cost > 0 and avg_overall_score > 0:
            cost_efficiency_score = avg_overall_score / (total_cost / total_tasks)
            cost_efficiency_score = min(cost_efficiency_score, 1.0)  # Cap at 1.0
        else:
            cost_efficiency_score = 0.0

        # Speed
        durations = [s.duration_seconds for s in scores if s.duration_seconds]
        avg_duration_seconds = sum(durations) / len(durations) if durations else 0.0

        # Category performance
        category_performance = await self._calculate_category_performance(session, agent_id)

        # Model performance
        model_performance = await self._calculate_model_performance(session, agent_id)

        # Agent age (days since first task)
        first_task_date = min(s.created_at for s in scores)
        days_active = (datetime.utcnow() - first_task_date).days

        # Upsert stats
        repo = PerformanceRepository(session)
        stats_data = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "avg_overall_score": round(avg_overall_score, 2),
            "avg_user_rating": round(avg_user_rating, 2) if avg_user_rating else None,
            "total_cost": round(total_cost, 2),
            "avg_cost_per_task": round(avg_cost_per_task, 6),
            "cost_efficiency_score": round(cost_efficiency_score, 2),
            "avg_duration_seconds": round(avg_duration_seconds, 2),
            "category_performance": category_performance,
            "model_performance": model_performance,
            "days_active": days_active,
        }

        await repo.upsert_agent_stats(agent_id, nickname, stats_data)

        return stats_data

    async def _calculate_category_performance(
        self,
        session: AsyncSession,
        agent_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance by category (research, analysis, etc.)

        Returns:
            Dict like: {"research": {"count": 10, "avg_score": 0.85}, ...}
        """
        stmt = select(AgentPerformanceScoreModel).where(
            and_(
                AgentPerformanceScoreModel.agent_id == agent_id,
                AgentPerformanceScoreModel.objective_category.isnot(None)
            )
        )
        result = await session.execute(stmt)
        scores = list(result.scalars().all())

        # Group by category
        categories = defaultdict(list)
        for score in scores:
            if score.objective_category and score.overall_score:
                categories[score.objective_category].append(score.overall_score)

        # Calculate averages
        category_stats = {}
        for category, score_list in categories.items():
            category_stats[category] = {
                "count": len(score_list),
                "avg_score": round(sum(score_list) / len(score_list), 2)
            }

        return category_stats

    async def _calculate_model_performance(
        self,
        session: AsyncSession,
        agent_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance by model used

        Returns:
            Dict like: {"gpt-4o": {"count": 5, "avg_score": 0.88, "since": "2026-02-01"}, ...}
        """
        stmt = select(AgentPerformanceScoreModel).where(
            and_(
                AgentPerformanceScoreModel.agent_id == agent_id,
                AgentPerformanceScoreModel.model_used.isnot(None)
            )
        )
        result = await session.execute(stmt)
        scores = list(result.scalars().all())

        # Group by model
        models = defaultdict(lambda: {"scores": [], "first_used": None})
        for score in scores:
            if score.model_used and score.overall_score:
                model_data = models[score.model_used]
                model_data["scores"].append(score.overall_score)

                # Track when this model was first used
                if model_data["first_used"] is None or score.created_at < model_data["first_used"]:
                    model_data["first_used"] = score.created_at

        # Calculate averages
        model_stats = {}
        for model_name, data in models.items():
            model_stats[model_name] = {
                "count": len(data["scores"]),
                "avg_score": round(sum(data["scores"]) / len(data["scores"]), 2),
                "since": data["first_used"].isoformat() if data["first_used"] else None
            }

        return model_stats

    async def _calculate_rankings(self, session: AsyncSession):
        """
        Calculate overall rankings based on aggregated stats

        Ranking algorithm:
        - Primary: Overall quality score (avg_overall_score)
        - Secondary: Total tasks (activity level)
        - Tertiary: Cost efficiency
        """
        # Get all agent stats
        stmt = select(AgentPerformanceStatsModel).order_by(
            AgentPerformanceStatsModel.avg_overall_score.desc(),
            AgentPerformanceStatsModel.total_tasks.desc(),
            AgentPerformanceStatsModel.cost_efficiency_score.desc()
        )
        result = await session.execute(stmt)
        all_stats = list(result.scalars().all())

        # Assign ranks
        for rank, stat in enumerate(all_stats, start=1):
            stat.overall_rank = rank

        # TODO: Category-specific rankings
        # For now, we'll store overall rank in category_ranks as well
        for stat in all_stats:
            if stat.category_performance:
                category_ranks = {}
                for category in stat.category_performance.keys():
                    # Simplified: use overall rank for now
                    # Phase 3 will calculate per-category ranks
                    category_ranks[category] = stat.overall_rank
                stat.category_ranks = category_ranks

        await session.flush()


# Convenience function for scheduled execution

async def run_stats_aggregation() -> Dict[str, Any]:
    """
    Run stats aggregation job

    Usage (in scheduled job):
        from backend.jobs.stats_aggregation import run_stats_aggregation
        result = await run_stats_aggregation()
    """
    job = StatsAggregationJob()
    return await job.run()
