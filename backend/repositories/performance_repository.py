"""
Performance tracking repository for agent evaluation and scoring
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional

from sqlalchemy import select, update, desc, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, JSON

from backend.models.base import Base


# SQLAlchemy Models

class AgentPerformanceScoreModel(Base):
    """Core performance tracking for each task"""

    __tablename__ = "agent_performance_scores"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)

    # Objective Classification
    objective_category = Column(String(50), nullable=True, index=True)
    task_complexity = Column(Integer, nullable=True)  # 1-5 scale

    # Quality Scores (0-1 scale)
    accuracy_score = Column(Numeric(3, 2), nullable=True)
    relevance_score = Column(Numeric(3, 2), nullable=True)
    completeness_score = Column(Numeric(3, 2), nullable=True)
    efficiency_score = Column(Numeric(3, 2), nullable=True)
    overall_score = Column(Numeric(3, 2), nullable=True)  # Weighted average

    # User Feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Cost Metrics
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(10, 6), nullable=True)
    cost_per_quality_point = Column(Numeric(10, 6), nullable=True)

    # Execution Metadata
    model_used = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    duration_seconds = Column(Numeric(10, 2), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default="NOW()")


class AgentPeerEvaluationModel(Base):
    """Peer evaluations - agents rating each other"""

    __tablename__ = "agent_peer_evaluations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    evaluated_agent_id = Column(String(50), nullable=False, index=True)
    evaluator_agent_id = Column(String(50), nullable=False, index=True)

    evaluation_score = Column(Numeric(3, 2), nullable=True)
    evaluation_feedback = Column(Text, nullable=True)  # For future NLP analysis
    evaluation_criteria = Column(JSONB, nullable=True)  # {"clarity": 0.9, "depth": 0.8}

    created_at = Column(DateTime, nullable=False, server_default="NOW()")


class AgentNodePerformanceModel(Base):
    """Node-level performance tracking within agents"""

    __tablename__ = "agent_node_performance"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    node_name = Column(String(100), nullable=False, index=True)

    # Node Metrics
    execution_time_seconds = Column(Numeric(10, 2), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)

    # Quality (if evaluable)
    output_quality_score = Column(Numeric(3, 2), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default="NOW()")


class AgentPerformanceStatsModel(Base):
    """Aggregated agent statistics (updated hourly)"""

    __tablename__ = "agent_performance_stats"

    agent_id = Column(String(50), primary_key=True)
    nickname = Column(String(50), nullable=False)

    # Agent Lifecycle
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    days_active = Column(Integer, nullable=True)

    # Overall Stats
    total_tasks = Column(Integer, nullable=False, server_default="0")
    successful_tasks = Column(Integer, nullable=False, server_default="0")
    failed_tasks = Column(Integer, nullable=False, server_default="0")
    avg_overall_score = Column(Numeric(3, 2), nullable=True)
    avg_user_rating = Column(Numeric(3, 2), nullable=True)

    # Cost Efficiency
    total_cost = Column(Numeric(10, 2), nullable=True)
    avg_cost_per_task = Column(Numeric(10, 6), nullable=True)
    cost_efficiency_score = Column(Numeric(3, 2), nullable=True)

    # Speed
    avg_duration_seconds = Column(Numeric(10, 2), nullable=True)

    # Task Category Performance (JSONB for flexibility)
    category_performance = Column(JSONB, nullable=True)

    # Model Performance (track when LLM changes)
    model_performance = Column(JSONB, nullable=True)

    # Rankings
    overall_rank = Column(Integer, nullable=True)
    category_ranks = Column(JSONB, nullable=True)

    last_updated = Column(DateTime, nullable=False, server_default="NOW()")


class ObjectiveTemplateModel(Base):
    """Templates for task objective classification"""

    __tablename__ = "objective_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    category = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    evaluation_criteria = Column(JSONB, nullable=True)
    recommended_agents = Column(ARRAY(String), nullable=True)


# Repository Class

class PerformanceRepository:
    """Data access layer for performance tracking"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Performance Scores

    async def save_performance_score(
        self,
        task_id: UUID,
        agent_id: str,
        scores: dict,
        metadata: dict = None
    ) -> AgentPerformanceScoreModel:
        """
        Save performance score for a completed task

        Args:
            task_id: Task UUID
            agent_id: Agent identifier (e.g., "agent_a")
            scores: Dict with quality scores (accuracy, relevance, etc.)
            metadata: Optional execution metadata (tokens, cost, duration)

        Returns:
            Created performance score record
        """
        score_record = AgentPerformanceScoreModel(
            id=str(uuid4()),
            task_id=str(task_id),
            agent_id=agent_id,
            objective_category=scores.get("objective_category"),
            task_complexity=scores.get("task_complexity"),
            accuracy_score=scores.get("accuracy_score"),
            relevance_score=scores.get("relevance_score"),
            completeness_score=scores.get("completeness_score"),
            efficiency_score=scores.get("efficiency_score"),
            overall_score=scores.get("overall_score"),
            user_rating=scores.get("user_rating"),
            user_feedback=scores.get("user_feedback"),
            user_id=str(scores.get("user_id")) if scores.get("user_id") else None,
            total_tokens=metadata.get("total_tokens") if metadata else None,
            estimated_cost=metadata.get("estimated_cost") if metadata else None,
            cost_per_quality_point=metadata.get("cost_per_quality_point") if metadata else None,
            model_used=metadata.get("model_used") if metadata else None,
            temperature=metadata.get("temperature") if metadata else None,
            duration_seconds=metadata.get("duration_seconds") if metadata else None,
            created_at=datetime.utcnow()
        )

        self.session.add(score_record)
        await self.session.flush()
        return score_record

    async def update_user_feedback(
        self,
        task_id: UUID,
        user_rating: int,
        user_feedback: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Update user feedback for an existing performance score

        Args:
            task_id: Task UUID
            user_rating: 1-5 star rating
            user_feedback: Optional text feedback
            user_id: Optional user UUID

        Returns:
            True if updated, False if not found
        """
        stmt = (
            update(AgentPerformanceScoreModel)
            .where(AgentPerformanceScoreModel.task_id == str(task_id))
            .values(
                user_rating=user_rating,
                user_feedback=user_feedback,
                user_id=str(user_id) if user_id else None
            )
        )

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def get_performance_score(self, task_id: UUID) -> Optional[AgentPerformanceScoreModel]:
        """Get performance score for a specific task"""
        stmt = select(AgentPerformanceScoreModel).where(
            AgentPerformanceScoreModel.task_id == str(task_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agent_scores(
        self,
        agent_id: str,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentPerformanceScoreModel]:
        """Get recent performance scores for an agent"""
        stmt = select(AgentPerformanceScoreModel).where(
            AgentPerformanceScoreModel.agent_id == agent_id
        )

        if category:
            stmt = stmt.where(AgentPerformanceScoreModel.objective_category == category)

        stmt = stmt.order_by(desc(AgentPerformanceScoreModel.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Peer Evaluations

    async def save_peer_evaluation(
        self,
        task_id: UUID,
        evaluated_agent_id: str,
        evaluator_agent_id: str,
        evaluation_score: float,
        evaluation_feedback: Optional[str] = None,
        evaluation_criteria: Optional[dict] = None
    ) -> AgentPeerEvaluationModel:
        """Save peer evaluation from one agent about another's work"""
        evaluation = AgentPeerEvaluationModel(
            id=str(uuid4()),
            task_id=str(task_id),
            evaluated_agent_id=evaluated_agent_id,
            evaluator_agent_id=evaluator_agent_id,
            evaluation_score=evaluation_score,
            evaluation_feedback=evaluation_feedback,
            evaluation_criteria=evaluation_criteria,
            created_at=datetime.utcnow()
        )

        self.session.add(evaluation)
        await self.session.flush()
        return evaluation

    async def get_peer_evaluations(
        self,
        task_id: Optional[UUID] = None,
        evaluated_agent_id: Optional[str] = None
    ) -> List[AgentPeerEvaluationModel]:
        """Get peer evaluations for a task or agent"""
        stmt = select(AgentPeerEvaluationModel)

        if task_id:
            stmt = stmt.where(AgentPeerEvaluationModel.task_id == str(task_id))

        if evaluated_agent_id:
            stmt = stmt.where(AgentPeerEvaluationModel.evaluated_agent_id == evaluated_agent_id)

        stmt = stmt.order_by(desc(AgentPeerEvaluationModel.created_at))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Node Performance

    async def save_node_performance(
        self,
        task_id: UUID,
        agent_id: str,
        node_name: str,
        execution_time_seconds: float,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        output_quality_score: Optional[float] = None
    ) -> AgentNodePerformanceModel:
        """Save node-level performance metrics"""
        node_perf = AgentNodePerformanceModel(
            id=str(uuid4()),
            task_id=str(task_id),
            agent_id=agent_id,
            node_name=node_name,
            execution_time_seconds=execution_time_seconds,
            tokens_used=tokens_used,
            success=success,
            error_message=error_message,
            output_quality_score=output_quality_score,
            created_at=datetime.utcnow()
        )

        self.session.add(node_perf)
        await self.session.flush()
        return node_perf

    # Agent Stats

    async def get_agent_stats(self, agent_id: str) -> Optional[AgentPerformanceStatsModel]:
        """Get aggregated stats for an agent"""
        stmt = select(AgentPerformanceStatsModel).where(
            AgentPerformanceStatsModel.agent_id == agent_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_leaderboard(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentPerformanceStatsModel]:
        """
        Get agent leaderboard rankings

        Args:
            category: Optional category filter (e.g., "research")
            limit: Number of agents to return

        Returns:
            List of agent stats ordered by rank
        """
        stmt = select(AgentPerformanceStatsModel)

        # TODO: Add category filtering once we implement category_ranks
        # For now, just order by overall_rank

        stmt = stmt.order_by(AgentPerformanceStatsModel.overall_rank).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_agent_stats(
        self,
        agent_id: str,
        nickname: str,
        stats: dict
    ) -> AgentPerformanceStatsModel:
        """
        Create or update agent statistics

        Args:
            agent_id: Agent identifier
            nickname: Agent nickname (e.g., "bob")
            stats: Dict with stats to update

        Returns:
            Updated or created stats record
        """
        # Try to get existing record
        existing = await self.get_agent_stats(agent_id)

        if existing:
            # Update existing record
            update_stmt = (
                update(AgentPerformanceStatsModel)
                .where(AgentPerformanceStatsModel.agent_id == agent_id)
                .values(
                    **stats,
                    last_updated=datetime.utcnow()
                )
            )
            await self.session.execute(update_stmt)
            await self.session.flush()

            # Fetch updated record
            return await self.get_agent_stats(agent_id)
        else:
            # Create new record
            new_stats = AgentPerformanceStatsModel(
                agent_id=agent_id,
                nickname=nickname,
                **stats,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            self.session.add(new_stats)
            await self.session.flush()
            return new_stats
