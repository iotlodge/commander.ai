"""add agent_model_configs table

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-06 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_model_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('nickname', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('temperature', sa.Float, nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer, nullable=False, server_default='2000'),
        sa.Column('model_params', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Create indexes for efficient lookups
    op.create_index('idx_agent_model_configs_agent', 'agent_model_configs', ['agent_id', 'active'])
    op.create_index('idx_agent_model_configs_version', 'agent_model_configs', ['agent_id', 'version'])

    # Seed data with default configurations for all 8 agents
    op.execute("""
        INSERT INTO agent_model_configs
        (agent_id, nickname, provider, model_name, temperature, max_tokens, version, active)
        VALUES
        -- Parent Agent (Leo - Orchestrator)
        ('parent', 'leo', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent A (Bob - Research)
        ('agent_a', 'bob', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent B (Sue - Compliance)
        ('agent_b', 'sue', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent C (Rex - Data Analysis)
        ('agent_c', 'rex', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent D (Maya - Reflection)
        ('agent_d', 'maya', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent E (Kai - Reflexion)
        ('agent_e', 'kai', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent F (Alice - Documents)
        ('agent_f', 'alice', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE),

        -- Agent G (Chat)
        ('agent_g', 'chat', 'openai', 'gpt-4o-mini', 0.7, 2000, 1, TRUE)
    """)


def downgrade() -> None:
    op.drop_index('idx_agent_model_configs_version')
    op.drop_index('idx_agent_model_configs_agent')
    op.drop_table('agent_model_configs')
