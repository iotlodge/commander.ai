"""
Initialize scheduled commands tables

Run this script to create the new tables for NLP command scheduling:
- scheduled_commands
- scheduled_command_executions

Usage:
    python -m backend.scripts.init_scheduled_commands_tables
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from backend.core.config import get_settings
from backend.models.base import Base
from backend.repositories.scheduled_command_repository import (
    ScheduledCommandModel,
    ScheduledCommandExecutionModel,
)


async def init_scheduled_commands_tables():
    """Create scheduled commands tables"""
    settings = get_settings()

    print("🔧 Initializing scheduled commands tables...")
    print(f"📍 Database: {settings.database_url.split('@')[1]}")

    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,  # Show SQL commands
    )

    # Create tables
    async with engine.begin() as conn:
        # Import models to ensure they're registered
        from backend.repositories.scheduled_command_repository import (
            ScheduledCommandModel,
            ScheduledCommandExecutionModel,
        )

        # Create only the scheduled commands tables (not all Base tables)
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    ScheduledCommandModel.__table__,
                    ScheduledCommandExecutionModel.__table__,
                ],
                checkfirst=True  # Only create if doesn't exist
            )
        )

    print("✅ Scheduled commands tables created successfully!")
    print("\nCreated tables:")
    print("  - scheduled_commands")
    print("  - scheduled_command_executions")
    print("\nIndexes created:")
    print("  - idx_scheduled_commands_user (user_id, enabled)")
    print("  - idx_scheduled_commands_next_run (next_run_at) WHERE enabled = true")
    print("  - idx_executions_scheduled_command (scheduled_command_id, triggered_at DESC)")
    print("  - idx_executions_status (status, triggered_at)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_scheduled_commands_tables())
