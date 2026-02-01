"""add agent tasks table

Revision ID: 9077b9149369
Revises: 
Create Date: 2026-01-31 20:20:44.879154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9077b9149369'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('agent_nickname', sa.String(50), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('command_text', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('progress_percentage', sa.Integer, server_default='0'),
        sa.Column('current_node', sa.String(100)),
        sa.Column('consultation_target_id', sa.String(50)),
        sa.Column('consultation_target_nickname', sa.String(50)),
        sa.Column('result', sa.Text),
        sa.Column('error_message', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.CheckConstraint("status IN ('queued', 'in_progress', 'tool_call', 'completed', 'failed')", name='valid_status'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='valid_progress')
    )

    op.create_index('idx_agent_tasks_user_id', 'agent_tasks', ['user_id'])
    op.create_index('idx_agent_tasks_status', 'agent_tasks', ['status'])
    op.create_index('idx_agent_tasks_created_at', 'agent_tasks', ['created_at'], postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    op.drop_index('idx_agent_tasks_created_at')
    op.drop_index('idx_agent_tasks_status')
    op.drop_index('idx_agent_tasks_user_id')
    op.drop_table('agent_tasks')
