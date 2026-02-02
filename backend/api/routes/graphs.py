"""API routes for agent graph visualizations"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.task_repository import get_db_session
from backend.repositories.graph_repository import GraphRepository
from pydantic import BaseModel

router = APIRouter(prefix="/api/graphs", tags=["graphs"])


class AgentGraphResponse(BaseModel):
    """Response model for agent graph visualization"""
    agent_id: str
    agent_nickname: str
    mermaid_diagram: str
    node_count: int
    edge_count: int
    last_updated: str


@router.get("", response_model=list[AgentGraphResponse])
async def get_all_graphs(session: AsyncSession = Depends(get_db_session)):
    """Get all agent graph visualizations"""
    repo = GraphRepository(session)
    graphs = await repo.get_all_graphs()

    return [
        AgentGraphResponse(
            agent_id=g.agent_id,
            agent_nickname=g.agent_nickname,
            mermaid_diagram=g.mermaid_diagram,
            node_count=g.node_count,
            edge_count=g.edge_count,
            last_updated=g.last_updated.isoformat()
        )
        for g in graphs
    ]


@router.get("/{agent_id}", response_model=AgentGraphResponse)
async def get_graph(agent_id: str, session: AsyncSession = Depends(get_db_session)):
    """Get graph visualization for specific agent"""
    repo = GraphRepository(session)
    graph = await repo.get_graph(agent_id)

    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph not found for agent: {agent_id}")

    return AgentGraphResponse(
        agent_id=graph.agent_id,
        agent_nickname=graph.agent_nickname,
        mermaid_diagram=graph.mermaid_diagram,
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        last_updated=graph.last_updated.isoformat()
    )
