"""Repository for agent graph visualizations"""
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.graph_models import AgentGraphModel
from sqlalchemy import select


class GraphRepository:
    """Data access layer for agent graphs"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_graph(
        self,
        agent_id: str,
        agent_nickname: str,
        mermaid_diagram: str,
        graph_schema: dict | None = None,
        node_count: int = 0,
        edge_count: int = 0
    ) -> AgentGraphModel:
        """Create or update agent graph visualization"""
        # Try to get existing
        result = await self.session.execute(
            select(AgentGraphModel).where(AgentGraphModel.agent_id == agent_id)
        )
        graph = result.scalar_one_or_none()

        if graph:
            # Update existing
            graph.agent_nickname = agent_nickname
            graph.mermaid_diagram = mermaid_diagram
            graph.graph_schema = graph_schema
            graph.node_count = node_count
            graph.edge_count = edge_count
        else:
            # Create new
            graph = AgentGraphModel(
                agent_id=agent_id,
                agent_nickname=agent_nickname,
                mermaid_diagram=mermaid_diagram,
                graph_schema=graph_schema,
                node_count=node_count,
                edge_count=edge_count
            )
            self.session.add(graph)

        await self.session.commit()
        await self.session.refresh(graph)
        return graph

    async def get_graph(self, agent_id: str) -> AgentGraphModel | None:
        """Get graph visualization for an agent"""
        result = await self.session.execute(
            select(AgentGraphModel).where(AgentGraphModel.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_all_graphs(self) -> list[AgentGraphModel]:
        """Get all agent graph visualizations"""
        result = await self.session.execute(select(AgentGraphModel))
        return list(result.scalars().all())
