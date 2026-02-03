"""
Agent listing API endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.base.agent_registry import AgentRegistry


router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentResponse(BaseModel):
    """Agent information response"""

    id: str
    nickname: str
    specialization: str
    description: str
    avatar_url: str | None = None


@router.get("", response_model=list[AgentResponse])
async def list_agents():
    """
    Get all registered agents

    Returns list of all agents registered in the system
    with their metadata (id, nickname, specialization, etc.)
    """
    all_agents = AgentRegistry.get_all_agents()

    return [
        AgentResponse(
            id=agent.agent_id,
            nickname=agent.nickname,
            specialization=agent.metadata.specialization,
            description=agent.metadata.description,
            avatar_url=agent.metadata.avatar_url,
        )
        for agent in all_agents.values()
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get specific agent by ID"""
    agent = AgentRegistry.get_agent(agent_id)

    if not agent:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return AgentResponse(
        id=agent.agent_id,
        nickname=agent.nickname,
        specialization=agent.metadata.specialization,
        description=agent.metadata.description,
        avatar_url=agent.metadata.avatar_url,
    )


@router.get("/nickname/{nickname}", response_model=AgentResponse)
async def get_agent_by_nickname(nickname: str):
    """Get specific agent by nickname"""
    agent = AgentRegistry.get_by_nickname(nickname)

    if not agent:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Agent @{nickname} not found")

    return AgentResponse(
        id=agent.agent_id,
        nickname=agent.nickname,
        specialization=agent.metadata.specialization,
        description=agent.metadata.description,
        avatar_url=agent.metadata.avatar_url,
    )
