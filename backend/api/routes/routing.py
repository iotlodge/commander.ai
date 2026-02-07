"""
API routes for intelligent routing and agent selection insights
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.task_repository import get_db_session
from backend.core.category_classifier import CategoryClassifier, TaskCategory
from backend.core.intelligent_router import IntelligentRouter


router = APIRouter(prefix="/api/routing", tags=["routing"])


# Pydantic Models

class ClassifyRequest(BaseModel):
    """Request to classify a command"""
    command: str


class ClassifyResponse(BaseModel):
    """Classification result"""
    command: str
    category: str
    confidence: str = "high"  # high/medium/low


class AgentScoreInfo(BaseModel):
    """Agent scoring info"""
    agent_id: str
    nickname: str
    base_score: float
    success_rate: float
    load_penalty: float
    final_score: float
    reason: str


class RoutingRecommendationResponse(BaseModel):
    """Routing recommendation with reasoning"""
    command: str
    category: str
    selected_agent_id: str
    selected_nickname: str
    reason: str
    all_scores: list[AgentScoreInfo]
    constraints: dict


class AgentCapabilitiesResponse(BaseModel):
    """Agent capabilities profile"""
    agent_id: str
    nickname: str
    specializations: list[str]
    category_performance: dict  # {"research": {"count": 10, "avg_score": 0.87}}
    total_tasks: int
    avg_overall_score: float
    rank: Optional[int]


# API Endpoints

@router.post("/classify", response_model=ClassifyResponse)
async def classify_command(request: ClassifyRequest):
    """
    Classify a user command into a task category

    Uses LLM to detect task objective (research, analysis, writing, etc.)

    Cost: ~$0.00002 per classification (GPT-4o-mini)

    Example:
        POST /api/routing/classify
        {"command": "@bob research quantum computing"}

        Response:
        {"command": "...", "category": "research"}
    """
    try:
        classifier = CategoryClassifier()
        category = await classifier.classify(request.command)

        return ClassifyResponse(
            command=request.command,
            category=category.value
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/recommend-agent", response_model=RoutingRecommendationResponse)
async def recommend_agent(
    request: ClassifyRequest,
    max_cost: Optional[float] = Query(None, description="Maximum cost constraint"),
    max_duration: Optional[float] = Query(None, description="Maximum duration in seconds")
):
    """
    Get agent recommendation for a command

    1. Classifies the command
    2. Scores all capable agents
    3. Returns best agent with reasoning

    Cost: ~$0.00002 per recommendation (1 LLM call for classification)

    Example:
        POST /api/routing/recommend-agent?max_cost=0.10
        {"command": "@bob research quantum computing"}

        Response:
        {
            "selected_agent_id": "agent_a",
            "selected_nickname": "bob",
            "category": "research",
            "reason": "bob selected with score 0.87...",
            "all_scores": [...]
        }
    """
    try:
        # Step 1: Classify command
        classifier = CategoryClassifier()
        category = await classifier.classify(request.command)

        # Step 2: Build constraints
        constraints = {}
        if max_cost is not None:
            constraints["max_cost"] = max_cost
        if max_duration is not None:
            constraints["max_duration"] = max_duration

        # Step 3: Get routing recommendation
        router_instance = IntelligentRouter()
        decision = await router_instance.select_agent(
            command=request.command,
            category=category,
            constraints=constraints
        )

        # Convert to response format
        all_scores = [
            AgentScoreInfo(
                agent_id=score.agent_id,
                nickname=score.nickname,
                base_score=score.base_score,
                success_rate=score.success_rate,
                load_penalty=score.load_penalty,
                final_score=score.final_score,
                reason=score.reason
            )
            for score in decision.all_scores
        ]

        return RoutingRecommendationResponse(
            command=request.command,
            category=decision.task_category.value,
            selected_agent_id=decision.selected_agent_id,
            selected_nickname=decision.selected_nickname,
            reason=decision.reason,
            all_scores=all_scores,
            constraints=constraints
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Routing recommendation failed: {str(e)}"
        )


@router.get("/agent-capabilities/{agent_id}", response_model=AgentCapabilitiesResponse)
async def get_agent_capabilities(
    agent_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Get capability profile for a specific agent

    Returns:
    - Specializations (default categories)
    - Category performance (historical data)
    - Overall stats and rank

    Example:
        GET /api/routing/agent-capabilities/agent_a
    """
    try:
        from backend.repositories.performance_repository import PerformanceRepository

        router_instance = IntelligentRouter()

        # Get default specializations
        specializations = router_instance.AGENT_SPECIALIZATIONS.get(agent_id, [])
        nickname = router_instance.AGENT_NICKNAMES.get(agent_id, agent_id)

        # Get performance stats
        repo = PerformanceRepository(session)
        stats = await repo.get_agent_stats(agent_id)

        if stats:
            return AgentCapabilitiesResponse(
                agent_id=agent_id,
                nickname=nickname,
                specializations=specializations,
                category_performance=stats.category_performance or {},
                total_tasks=stats.total_tasks,
                avg_overall_score=float(stats.avg_overall_score) if stats.avg_overall_score else 0.0,
                rank=stats.overall_rank
            )
        else:
            # No stats yet
            return AgentCapabilitiesResponse(
                agent_id=agent_id,
                nickname=nickname,
                specializations=specializations,
                category_performance={},
                total_tasks=0,
                avg_overall_score=0.0,
                rank=None
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch agent capabilities: {str(e)}"
        )


@router.get("/best-agents-by-category")
async def get_best_agents_by_category(
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Get best performing agents for each category

    Returns:
        Dict mapping categories to top agents

    Example:
        GET /api/routing/best-agents-by-category

        Response:
        {
            "research": [
                {"agent_id": "agent_a", "nickname": "bob", "avg_score": 0.87, "count": 50},
                {"agent_id": "agent_f", "nickname": "alice", "avg_score": 0.82, "count": 30}
            ],
            "analysis": [...]
        }
    """
    try:
        from backend.repositories.performance_repository import PerformanceRepository

        repo = PerformanceRepository(session)
        router_instance = IntelligentRouter()

        # Get all agent stats
        from sqlalchemy import select
        from backend.repositories.performance_repository import AgentPerformanceStatsModel

        stmt = select(AgentPerformanceStatsModel)
        result = await session.execute(stmt)
        all_stats = list(result.scalars().all())

        # Group by category
        categories_map = {}

        for stats in all_stats:
            if not stats.category_performance:
                continue

            nickname = router_instance.AGENT_NICKNAMES.get(stats.agent_id, stats.nickname)

            for category, perf_data in stats.category_performance.items():
                if category not in categories_map:
                    categories_map[category] = []

                categories_map[category].append({
                    "agent_id": stats.agent_id,
                    "nickname": nickname,
                    "avg_score": perf_data.get("avg_score", 0.0),
                    "count": perf_data.get("count", 0)
                })

        # Sort each category by avg_score
        for category in categories_map:
            categories_map[category].sort(key=lambda x: x["avg_score"], reverse=True)

        return categories_map

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch best agents by category: {str(e)}"
        )
