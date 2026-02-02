"""Database models for agent graph visualizations"""
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from backend.repositories.task_repository import Base


class AgentGraphModel(Base):
    """Stores agent graph visualizations"""
    __tablename__ = "agent_graphs"

    agent_id = Column(String, primary_key=True)  # e.g., "agent_a", "parent"
    agent_nickname = Column(String, nullable=False)  # e.g., "bob", "leo"
    mermaid_diagram = Column(Text, nullable=False)
    graph_schema = Column(JSONB, nullable=True)  # Optional full schema
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
