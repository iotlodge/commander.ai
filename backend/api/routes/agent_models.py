"""
API routes for agent model configuration management
Allows dynamic switching of LLM models per agent
"""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.task_repository import get_session_factory, get_db_session
from backend.repositories.agent_model_repository import AgentModelRepository
from backend.models.agent_model_models import (
    AgentModelUpdate,
    ModelConfigResponse,
    ApprovedModelsResponse,
)
from backend.agents.base.agent_registry import AgentRegistry
from backend.core.llm_factory import ModelConfig

router = APIRouter(prefix="/api/agents", tags=["agent-models"])


async def get_agent_model_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> AgentModelRepository:
    """Dependency to get agent model repository"""
    return AgentModelRepository(session)


@router.get("/{agent_id}/model", response_model=ModelConfigResponse)
async def get_agent_model_config(
    agent_id: str,
    repo: Annotated[AgentModelRepository, Depends(get_agent_model_repo)]
):
    """
    Get the current model configuration for an agent

    Args:
        agent_id: Agent identifier (e.g., 'agent_a', 'parent')

    Returns:
        Current model configuration including provider, model name, and parameters
    """
    # Get config from database
    config = await repo.get_agent_model_config(agent_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"No model configuration found for agent {agent_id}"
        )

    # Get model details from approved models
    model_details = await repo.get_model_details(config.provider, config.model_name)

    return ModelConfigResponse(
        agent_id=config.agent_id,
        nickname=config.nickname,
        provider=config.provider,
        model_name=config.model_name,
        model_display_name=model_details.model_display_name if model_details else None,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        model_params=config.model_params,
        version=config.version,
        supports_function_calling=model_details.supports_function_calling if model_details else False,
        context_window=model_details.context_window if model_details else None,
    )


@router.get("/models/approved", response_model=ApprovedModelsResponse)
async def get_approved_models(
    repo: Annotated[AgentModelRepository, Depends(get_agent_model_repo)],
    provider: str | None = Query(None, description="Filter by provider (openai, anthropic)")
):
    """
    Get list of approved LLM models

    Args:
        provider: Optional filter by provider

    Returns:
        List of approved models with metadata
    """
    models = await repo.get_approved_models(provider=provider)

    return ApprovedModelsResponse(
        models=models,
        total=len(models)
    )


@router.patch("/{agent_id}/model", response_model=ModelConfigResponse)
async def update_agent_model_config(
    agent_id: str,
    update: AgentModelUpdate,
    repo: Annotated[AgentModelRepository, Depends(get_agent_model_repo)]
):
    """
    Update an agent's model configuration and reload the agent

    This endpoint:
    1. Validates no active tasks are running on the agent
    2. Checks that the model is approved
    3. Saves the new configuration to the database
    4. Reloads the agent with the new model
    5. Rolls back if reload fails

    Args:
        agent_id: Agent identifier
        update: New model configuration

    Returns:
        Updated model configuration

    Raises:
        409: If agent has active tasks
        400: If model is not approved
        500: If agent reload fails
    """
    # Step 1: Check for active tasks
    active_tasks = await _check_active_tasks(agent_id)
    if active_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"Agent {agent_id} has {active_tasks} active task(s). "
                   "Wait for completion or cancel tasks before changing model."
        )

    # Step 2: Validate model is approved
    is_approved = await repo.is_model_approved(update.provider, update.model_name)
    if not is_approved:
        raise HTTPException(
            status_code=400,
            detail=f"Model {update.provider}/{update.model_name} is not approved"
        )

    # Step 3: Get current config for rollback
    current_config = await repo.get_agent_model_config(agent_id)
    if not current_config:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_id} not found"
        )

    # Step 4: Save new configuration
    new_config = await repo.save_agent_model_config(
        agent_id=agent_id,
        nickname=current_config.nickname,
        model_update=update,
        user_id=None  # TODO: Get from JWT token
    )

    # Step 5: Reload agent with new model
    try:
        await _reload_agent_with_new_model(agent_id, new_config)
    except Exception as e:
        # Rollback on failure
        print(f"Agent reload failed, rolling back: {e}")
        await repo.rollback_agent_model_config(agent_id)

        # Re-initialize agent with old config
        try:
            await _reload_agent_with_new_model(agent_id, current_config)
        except Exception as rollback_error:
            print(f"Rollback also failed: {rollback_error}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload agent with new model: {str(e)}"
        )

    # Step 6: Broadcast update via WebSocket
    # TODO: Add WebSocket broadcast when WebSocket manager is ready

    # Get model details for response
    model_details = await repo.get_model_details(new_config.provider, new_config.model_name)

    return ModelConfigResponse(
        agent_id=new_config.agent_id,
        nickname=new_config.nickname,
        provider=new_config.provider,
        model_name=new_config.model_name,
        model_display_name=model_details.model_display_name if model_details else None,
        temperature=new_config.temperature,
        max_tokens=new_config.max_tokens,
        model_params=new_config.model_params,
        version=new_config.version,
        supports_function_calling=model_details.supports_function_calling if model_details else False,
        context_window=model_details.context_window if model_details else None,
    )


async def _check_active_tasks(agent_id: str) -> int:
    """
    Check if agent has any active tasks

    Returns:
        Number of active tasks
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        from backend.repositories.task_repository import TaskRepository
        from sqlalchemy import select, func
        from backend.repositories.task_repository import AgentTaskModel

        repo = TaskRepository(session)

        # Count tasks with status IN_PROGRESS or QUEUED
        stmt = select(func.count()).select_from(AgentTaskModel).where(
            AgentTaskModel.agent_id == agent_id,
            AgentTaskModel.status.in_(["PENDING", "IN_PROGRESS"])
        )
        result = await session.execute(stmt)
        count = result.scalar_one()

        return count


async def _reload_agent_with_new_model(agent_id: str, config) -> None:
    """
    Reload agent with new model configuration

    Args:
        agent_id: Agent identifier
        config: New AgentModelConfig

    Raises:
        Exception if agent not found or reload fails
    """
    # Get agent from registry
    if agent_id == "parent":
        agent = AgentRegistry.get_orchestrator()
    else:
        agent = AgentRegistry.get_specialist(agent_id)

    if not agent:
        raise ValueError(f"Agent {agent_id} not found in registry")

    # Update agent's model_config attribute
    agent.model_config = ModelConfig(
        provider=config.provider,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        model_params=config.model_params,
    )

    # Recreate graph with new config
    # The graph will use agent.model_config when creating LLM instances
    agent.graph = agent.create_graph()

    print(f"Agent {agent_id} ({agent.nickname}) reloaded with {config.provider}/{config.model_name}")
