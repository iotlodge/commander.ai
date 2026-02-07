"""
API routes for agent performance tracking and leaderboards
"""

from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.task_repository import get_db_session
from backend.repositories.performance_repository import PerformanceRepository


router = APIRouter(prefix="/api/performance", tags=["performance"])


# Pydantic Models

class TaskFeedbackRequest(BaseModel):
    """User feedback for a completed task"""
    user_rating: int = Field(..., ge=1, le=5, description="Star rating (1-5)")
    user_feedback: Optional[str] = Field(None, description="Optional text feedback")
    user_id: Optional[UUID] = Field(None, description="User UUID")


class TaskFeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool
    message: str


class AgentRanking(BaseModel):
    """Agent ranking for leaderboard"""
    agent_id: str
    nickname: str
    rank: int
    total_tasks: int
    avg_overall_score: float
    avg_user_rating: Optional[float]
    total_cost: Optional[float]
    cost_efficiency_score: Optional[float]
    days_active: Optional[int]


class LeaderboardResponse(BaseModel):
    """Leaderboard response"""
    rankings: List[AgentRanking]
    category: Optional[str] = None
    last_updated: str


# API Endpoints

@router.post("/tasks/{task_id}/feedback", response_model=TaskFeedbackResponse)
async def submit_task_feedback(
    task_id: UUID,
    feedback: TaskFeedbackRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Submit user feedback for a completed task

    This endpoint allows users to rate task outputs and provide optional text feedback.
    Feedback is stored in the performance tracking system for agent evaluation.

    Args:
        task_id: UUID of the completed task
        feedback: User rating (1-5 stars) and optional text feedback

    Returns:
        Success confirmation

    Example:
        POST /api/tasks/123e4567-e89b-12d3-a456-426614174000/feedback
        {
            "user_rating": 5,
            "user_feedback": "Excellent research, very thorough!",
            "user_id": "user-uuid"
        }
    """
    try:
        repo = PerformanceRepository(session)

        # Update or create performance score with user feedback
        updated = await repo.update_user_feedback(
            task_id=task_id,
            user_rating=feedback.user_rating,
            user_feedback=feedback.user_feedback,
            user_id=feedback.user_id
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"No performance record found for task {task_id}"
            )

        await session.commit()

        return TaskFeedbackResponse(
            success=True,
            message="Feedback submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_agent_leaderboard(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category: Optional[str] = None,
    limit: int = 10
):
    """
    Get agent performance leaderboard

    Returns ranked list of agents based on performance metrics.
    Can filter by objective category (research, analysis, etc.)

    Args:
        category: Optional category filter (e.g., "research")
        limit: Maximum number of agents to return (default: 10)

    Returns:
        Leaderboard with agent rankings and stats

    Example:
        GET /api/agents/leaderboard?category=research&limit=5
    """
    try:
        repo = PerformanceRepository(session)

        # Get leaderboard data
        stats = await repo.get_leaderboard(category=category, limit=limit)

        # Convert to response format
        rankings = []
        for stat in stats:
            rankings.append(AgentRanking(
                agent_id=stat.agent_id,
                nickname=stat.nickname,
                rank=stat.overall_rank or 999,  # Default rank if not set
                total_tasks=stat.total_tasks,
                avg_overall_score=float(stat.avg_overall_score) if stat.avg_overall_score else 0.0,
                avg_user_rating=float(stat.avg_user_rating) if stat.avg_user_rating else None,
                total_cost=float(stat.total_cost) if stat.total_cost else None,
                cost_efficiency_score=float(stat.cost_efficiency_score) if stat.cost_efficiency_score else None,
                days_active=stat.days_active
            ))

        return LeaderboardResponse(
            rankings=rankings,
            category=category,
            last_updated=stats[0].last_updated.isoformat() if stats else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )


@router.get("/agents/{agent_id}")
async def get_agent_performance(
    agent_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category: Optional[str] = None,
    limit: int = 100
):
    """
    Get performance history for a specific agent

    Returns recent performance scores for the agent, optionally filtered by category.

    Args:
        agent_id: Agent identifier (e.g., "agent_a")
        category: Optional category filter
        limit: Maximum number of scores to return (default: 100)

    Returns:
        List of performance scores with timestamps
    """
    try:
        repo = PerformanceRepository(session)

        # Get agent stats
        stats = await repo.get_agent_stats(agent_id)

        # Get recent scores
        scores = await repo.get_agent_scores(
            agent_id=agent_id,
            category=category,
            limit=limit
        )

        return {
            "agent_id": agent_id,
            "stats": {
                "total_tasks": stats.total_tasks if stats else 0,
                "avg_overall_score": float(stats.avg_overall_score) if stats and stats.avg_overall_score else None,
                "avg_user_rating": float(stats.avg_user_rating) if stats and stats.avg_user_rating else None,
                "rank": stats.overall_rank if stats else None
            },
            "recent_scores": [
                {
                    "task_id": str(score.task_id),
                    "overall_score": float(score.overall_score) if score.overall_score else None,
                    "user_rating": score.user_rating,
                    "category": score.objective_category,
                    "created_at": score.created_at.isoformat()
                }
                for score in scores
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch agent performance: {str(e)}"
        )
