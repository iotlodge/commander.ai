"""add agent prompts table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-02 19:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('nickname', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('prompt_text', sa.Text, nullable=False),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('prompt_type', sa.String(50), nullable=False, server_default="'system'"),
        sa.Column('variables', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('agent_id', 'description', name='uq_agent_prompt_description')
    )

    op.create_index('idx_prompts_agent', 'agent_prompts', ['agent_id', 'active'])


def downgrade() -> None:
    op.drop_index('idx_prompts_agent')
    op.drop_table('agent_prompts')
