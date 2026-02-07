"""
API routes for background jobs and maintenance tasks
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.task_repository import get_db_session
from backend.jobs.model_deprecation_checker import (
    ModelDeprecationChecker,
    check_model_deprecations,
)


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class DeprecationCheckResponse(BaseModel):
    """Response from deprecation check"""
    timestamp: str
    summary: dict
    deprecated_models: list[dict]
    suggested_updates: list[dict]


class ApplyUpdatesRequest(BaseModel):
    """Request to apply suggested updates"""
    auto_approve: bool = False


class ApplyUpdatesResponse(BaseModel):
    """Response from applying updates"""
    status: str
    applied: list[dict]
    failed: list[dict]
    total_suggestions: int
    applied_count: int
    failed_count: int


@router.post("/check-deprecated-models", response_model=DeprecationCheckResponse)
async def check_deprecated_models(
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Check all approved models for deprecation

    This endpoint:
    1. Queries each provider API to test model availability
    2. Detects deprecated models (404 errors)
    3. Suggests replacement models
    4. Returns a comprehensive report

    Returns:
        DeprecationCheckResponse with results and suggestions
    """
    try:
        report = await check_model_deprecations(session)
        return DeprecationCheckResponse(**report.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check model deprecations: {str(e)}"
        )


@router.post("/apply-model-updates", response_model=ApplyUpdatesResponse)
async def apply_model_updates(
    request: ApplyUpdatesRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Apply suggested model updates to the database

    This endpoint:
    1. Re-runs the deprecation check
    2. Applies suggested updates (if auto_approve=True)
    3. Marks deprecated models in the database
    4. Returns summary of applied changes

    Args:
        request: ApplyUpdatesRequest with auto_approve flag

    Returns:
        ApplyUpdatesResponse with applied/failed updates
    """
    try:
        # Run deprecation check
        checker = ModelDeprecationChecker(session)
        report = await checker.check_all_models()

        # Apply updates
        result = await checker.apply_suggested_updates(
            report,
            auto_approve=request.auto_approve
        )

        return ApplyUpdatesResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply model updates: {str(e)}"
        )


@router.get("/deprecation-report", response_model=DeprecationCheckResponse)
async def get_deprecation_report(
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Get a quick deprecation report (alias for check-deprecated-models)

    Returns:
        DeprecationCheckResponse with current status
    """
    return await check_deprecated_models(session)


# v0.5.0 Performance System Jobs

class StatsAggregationResponse(BaseModel):
    """Response from stats aggregation job"""
    status: str
    updated_agents: list[str]
    updated_count: int
    duration_seconds: float
    timestamp: str


@router.post("/aggregate-stats", response_model=StatsAggregationResponse)
async def run_stats_aggregation_job():
    """
    Manually trigger stats aggregation job

    This job:
    1. Aggregates performance data for all agents
    2. Calculates average scores, cost metrics, speed
    3. Updates agent_performance_stats table
    4. Calculates rankings (overall and per-category)

    Normally runs hourly via scheduler, but can be triggered manually.

    Returns:
        StatsAggregationResponse with summary of updates
    """
    try:
        from backend.jobs.stats_aggregation import run_stats_aggregation

        result = await run_stats_aggregation()
        return StatsAggregationResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run stats aggregation: {str(e)}"
        )
