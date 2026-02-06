"""
Prompt Management REST API
Provides CRUD operations for agent prompts with search, filtering, and testing
"""

import logging
from typing import Annotated, List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.prompt_models import AgentPrompt, PromptCreate, PromptUpdate
from backend.repositories.task_repository import get_db_session
from backend.repositories.prompt_repository import PromptRepository
from backend.auth.dependencies import get_current_active_user
from backend.auth.models import User
from backend.core.prompt_engineer import get_prompt_engineer, PromptEngineerError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Response models
class PromptListResponse(BaseModel):
    """Response for list prompts endpoint"""
    prompts: List[AgentPrompt]
    total: int
    limit: int
    offset: int


class PromptTestRequest(BaseModel):
    """Request to test a prompt"""
    agent_id: str = Field(..., description="Agent identifier")
    prompt_text: str = Field(..., description="System prompt to test")
    prompt_type: str = Field(default="system", description="Prompt type")
    test_query: str = Field(..., description="Test query to run")
    test_context: dict = Field(default_factory=dict, description="Optional task context")


class PromptTestResponse(BaseModel):
    """Response from prompt testing"""
    generated_response: str = Field(..., description="LLM response using the prompt")
    metrics: dict = Field(..., description="Token and performance metrics")
    compiled_messages: List[dict] = Field(..., description="Full message list sent to LLM")


class PromptCloneRequest(BaseModel):
    """Request to clone a prompt with modifications"""
    description: str = Field(..., description="Description for the cloned prompt")
    modifications: dict = Field(default_factory=dict, description="Changes to apply")


async def get_prompt_repo(session: AsyncSession = Depends(get_db_session)) -> PromptRepository:
    """Dependency to get PromptRepository"""
    return PromptRepository(session)


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    prompt_type: str | None = Query(None, description="Filter by prompt type"),
    active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in description/text"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List prompts with optional filtering and search

    Supports filtering by:
    - agent_id: Specific agent (e.g., "agent_a", "parent")
    - prompt_type: Type of prompt ("system", "human", "ai")
    - active: Active status (true/false)
    - search: Keyword search in description and prompt_text
    """
    try:
        # For MVP, just get prompts for the specified agent
        # TODO: Implement full search/filter functionality
        if agent_id:
            prompts = await repo.get_active_prompts(agent_id)

            # Apply filters
            if prompt_type:
                prompts = [p for p in prompts if p.prompt_type == prompt_type]

            if active is not None:
                prompts = [p for p in prompts if p.active == active]

            if search:
                search_lower = search.lower()
                prompts = [
                    p for p in prompts
                    if search_lower in p.description.lower()
                    or search_lower in p.prompt_text.lower()
                ]

            # Apply pagination
            total = len(prompts)
            prompts = prompts[offset:offset + limit]

            return PromptListResponse(
                prompts=prompts,
                total=total,
                limit=limit,
                offset=offset
            )
        else:
            # No agent_id filter - return empty for now
            # TODO: Implement cross-agent listing
            return PromptListResponse(
                prompts=[],
                total=0,
                limit=limit,
                offset=offset
            )

    except Exception as e:
        logger.error(f"Failed to list prompts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/{prompt_id}", response_model=AgentPrompt)
async def get_prompt(
    prompt_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
    include_versions: bool = Query(False, description="Include version history"),
):
    """
    Get a single prompt by ID

    Optionally includes version history if include_versions=true
    """
    try:
        prompt = await repo.get_prompt(prompt_id)

        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # TODO: Add version history when include_versions=true
        # For now, just return the prompt

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("", response_model=AgentPrompt, status_code=201)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
):
    """
    Create a new prompt

    Creates a prompt and stores it in the database.
    The prompt will be available immediately for use by PromptEngineer.
    """
    try:
        # Create prompt in database
        prompt = await repo.create_prompt(prompt_data)

        logger.info(
            f"Created prompt {prompt.id} for agent {prompt.agent_id} "
            f"by user {current_user.email}"
        )

        # Invalidate PromptEngineer cache for this agent
        try:
            prompt_engineer = get_prompt_engineer()
            prompt_engineer.clear_cache(prompt.agent_id)
            logger.info(f"Cleared PromptEngineer cache for {prompt.agent_id}")
        except RuntimeError:
            # PromptEngineer not initialized yet - that's OK
            pass

        return prompt

    except Exception as e:
        logger.error(f"Failed to create prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create prompt: {str(e)}")


@router.patch("/{prompt_id}", response_model=AgentPrompt)
async def update_prompt(
    prompt_id: UUID,
    prompt_update: PromptUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
):
    """
    Update an existing prompt

    Updates prompt text, active status, or variables.
    Automatically invalidates PromptEngineer cache.
    """
    try:
        # Get existing prompt first
        existing = await repo.get_prompt(prompt_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # Update prompt
        updated_prompt = await repo.update_prompt(prompt_id, prompt_update)

        logger.info(
            f"Updated prompt {prompt_id} for agent {existing.agent_id} "
            f"by user {current_user.email}"
        )

        # Invalidate PromptEngineer cache
        try:
            prompt_engineer = get_prompt_engineer()
            prompt_engineer.clear_cache(existing.agent_id)
            logger.info(f"Cleared PromptEngineer cache for {existing.agent_id}")
        except RuntimeError:
            pass

        return updated_prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt {prompt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
):
    """
    Delete a prompt (soft delete - sets active=false)

    Preserves the prompt in the database for version history,
    but marks it as inactive so it won't be used.
    """
    try:
        # Get existing prompt
        existing = await repo.get_prompt(prompt_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # Soft delete by setting active=false
        await repo.update_prompt(
            prompt_id,
            PromptUpdate(active=False)
        )

        logger.info(
            f"Deactivated prompt {prompt_id} for agent {existing.agent_id} "
            f"by user {current_user.email}"
        )

        # Invalidate cache
        try:
            prompt_engineer = get_prompt_engineer()
            prompt_engineer.clear_cache(existing.agent_id)
        except RuntimeError:
            pass

        return {
            "message": "Prompt deactivated successfully",
            "prompt_id": str(prompt_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt {prompt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete prompt: {str(e)}")


@router.post("/test", response_model=PromptTestResponse)
async def test_prompt(
    test_request: PromptTestRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Test a prompt with a sample query

    Generates a response using the provided prompt and test query.
    Returns the response, metrics, and compiled message list for debugging.

    Useful for:
    - Testing new prompts before saving
    - Comparing prompt variants
    - Debugging prompt issues
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from backend.core.config import get_settings
        from backend.core.token_tracker import extract_token_usage_from_response
        import time

        settings = get_settings()

        # Create LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=settings.openai_api_key,
        )

        # Build messages
        messages = [
            SystemMessage(content=test_request.prompt_text),
            HumanMessage(content=test_request.test_query)
        ]

        # Time the request
        start_time = time.time()
        response = await llm.ainvoke(messages)
        response_time_ms = int((time.time() - start_time) * 1000)

        # Extract token usage
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        total_tokens = prompt_tokens + completion_tokens

        # Build response
        return PromptTestResponse(
            generated_response=response.content,
            metrics={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "response_time_ms": response_time_ms
            },
            compiled_messages=[
                {"role": "system", "content": test_request.prompt_text},
                {"role": "user", "content": test_request.test_query}
            ]
        )

    except Exception as e:
        logger.error(f"Failed to test prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to test prompt: {str(e)}")


@router.post("/{prompt_id}/clone", response_model=AgentPrompt, status_code=201)
async def clone_prompt(
    prompt_id: UUID,
    clone_request: PromptCloneRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
):
    """
    Clone a prompt with modifications

    Creates a new prompt based on an existing one, applying specified modifications.
    Useful for creating prompt variants for A/B testing.
    """
    try:
        # Get source prompt
        source = await repo.get_prompt(prompt_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # Create new prompt with modifications
        new_prompt_data = PromptCreate(
            agent_id=source.agent_id,
            nickname=source.nickname,
            description=clone_request.description,
            prompt_text=clone_request.modifications.get("prompt_text", source.prompt_text),
            active=True,
            prompt_type=source.prompt_type,
            variables=clone_request.modifications.get("variables", source.variables)
        )

        # Create in database
        cloned = await repo.create_prompt(new_prompt_data)

        logger.info(
            f"Cloned prompt {prompt_id} to {cloned.id} "
            f"by user {current_user.email}"
        )

        return cloned

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone prompt {prompt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clone prompt: {str(e)}")


@router.get("/{prompt_id}/metrics")
async def get_prompt_metrics(
    prompt_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: PromptRepository = Depends(get_prompt_repo),
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
):
    """
    Get performance metrics for a prompt

    Returns usage statistics, success rates, and performance trends.

    TODO: Implement metrics tracking and aggregation
    Currently returns placeholder data.
    """
    try:
        # Verify prompt exists
        prompt = await repo.get_prompt(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # TODO: Query prompt_metrics table and aggregate
        # For now, return placeholder data

        return {
            "prompt_id": str(prompt_id),
            "time_period": f"{days} days",
            "metrics": {
                "total_uses": 0,
                "success_rate": 0.0,
                "avg_tokens": {
                    "prompt": 0,
                    "completion": 0,
                    "total": 0
                },
                "avg_response_time_ms": 0,
                "user_satisfaction": None,
                "comparison_to_baseline": {
                    "tokens_saved": 0,
                    "response_time_improvement_ms": 0
                }
            },
            "usage_over_time": [],
            "note": "Metrics tracking not yet implemented. This is placeholder data."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for prompt {prompt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
