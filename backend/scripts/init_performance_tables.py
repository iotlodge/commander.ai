"""
Initialize performance tracking tables

Run this script to create the new tables for agent performance tracking:
- agent_performance_scores
- agent_peer_evaluations
- agent_node_performance
- agent_performance_stats
- objective_templates

Usage:
    python -m backend.scripts.init_performance_tables
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from backend.core.config import get_settings
from backend.models.base import Base
from backend.repositories.performance_repository import (
    AgentPerformanceScoreModel,
    AgentPeerEvaluationModel,
    AgentNodePerformanceModel,
    AgentPerformanceStatsModel,
    ObjectiveTemplateModel,
)


async def init_performance_tables():
    """Create performance tracking tables"""
    settings = get_settings()

    print("🔧 Initializing performance tracking tables...")
    print(f"📍 Database: {settings.database_url.split('@')[1]}")

    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,  # Show SQL commands
    )

    # Create tables
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from backend.repositories.performance_repository import (
            AgentPerformanceScoreModel,
            AgentPeerEvaluationModel,
            AgentNodePerformanceModel,
            AgentPerformanceStatsModel,
            ObjectiveTemplateModel,
        )

        # Create only the performance tables (not all Base tables)
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    AgentPerformanceScoreModel.__table__,
                    AgentPeerEvaluationModel.__table__,
                    AgentNodePerformanceModel.__table__,
                    AgentPerformanceStatsModel.__table__,
                    ObjectiveTemplateModel.__table__,
                ],
                checkfirst=True  # Only create if doesn't exist
            )
        )

    print("✅ Performance tracking tables created successfully!")
    print("\nCreated tables:")
    print("  - agent_performance_scores")
    print("  - agent_peer_evaluations")
    print("  - agent_node_performance")
    print("  - agent_performance_stats")
    print("  - objective_templates")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_performance_tables())
