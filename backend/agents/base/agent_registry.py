"""
Agent Registry - Central registry for all agents in the system
Manages agent instances and nickname mappings
"""

from typing import Dict

from backend.agents.base.agent_interface import BaseAgent, AgentMetadata


class AgentRegistry:
    """
    Singleton registry for all agents
    Manages agent instances and provides lookup by ID or nickname
    """

    _instance: "AgentRegistry | None" = None
    _agents: Dict[str, BaseAgent] = {}
    _nickname_map: Dict[str, str] = {}  # nickname -> agent_id

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """Register an agent in the registry"""
        instance = cls()
        instance._agents[agent.agent_id] = agent
        instance._nickname_map[agent.nickname.lower()] = agent.agent_id

    @classmethod
    def get_agent(cls, agent_id: str) -> BaseAgent | None:
        """Get agent by ID"""
        instance = cls()
        return instance._agents.get(agent_id)

    @classmethod
    def get_by_nickname(cls, nickname: str) -> BaseAgent | None:
        """Get agent by nickname (case-insensitive)"""
        instance = cls()
        agent_id = instance._nickname_map.get(nickname.lower())
        if agent_id:
            return instance._agents.get(agent_id)
        return None

    @classmethod
    def get_specialist(cls, agent_id: str) -> BaseAgent | None:
        """Alias for get_agent (used in consultation patterns)"""
        return cls.get_agent(agent_id)

    @classmethod
    def get_all_agents(cls) -> Dict[str, BaseAgent]:
        """Get all registered agents"""
        instance = cls()
        return instance._agents.copy()

    @classmethod
    def get_all_nicknames(cls) -> list[str]:
        """Get all registered nicknames"""
        instance = cls()
        return list(instance._nickname_map.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents (useful for testing)"""
        instance = cls()
        instance._agents.clear()
        instance._nickname_map.clear()


# Initialize default agents (to be populated during app startup)
async def initialize_default_agents() -> None:
    """
    Initialize and register default agents
    This will be called during application startup
    """
    # Import agent implementations here to avoid circular imports
    from backend.agents.parent_agent.graph import ParentAgent
    from backend.agents.specialized.agent_a.graph import ResearchAgent
    from backend.agents.specialized.agent_b.graph import ComplianceAgent
    from backend.agents.specialized.agent_c.graph import DataAgent
    from backend.agents.specialized.agent_d.graph import DocumentManagerAgent
    from backend.agents.specialized.agent_e.graph import ReflectionAgent
    from backend.agents.specialized.agent_f.graph import ReflexionAgent

    # Create and register Parent Agent (Orchestrator)
    parent_agent = ParentAgent()
    AgentRegistry.register(parent_agent)
    await parent_agent.initialize()

    # Create and register specialist agents
    bob = ResearchAgent()
    AgentRegistry.register(bob)
    await bob.initialize()

    sue = ComplianceAgent()
    AgentRegistry.register(sue)
    await sue.initialize()

    rex = DataAgent()
    AgentRegistry.register(rex)
    await rex.initialize()

    alice = DocumentManagerAgent()
    AgentRegistry.register(alice)
    await alice.initialize()

    maya = ReflectionAgent()
    AgentRegistry.register(maya)
    await maya.initialize()

    kai = ReflexionAgent()
    AgentRegistry.register(kai)
    await kai.initialize()
