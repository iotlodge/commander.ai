"""add approved_models_provider table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'approved_models_provider',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_display_name', sa.String(150), nullable=True),
        sa.Column('mode', sa.String(50), nullable=True),
        sa.Column('context_window', sa.Integer, nullable=True),
        sa.Column('supports_function_calling', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('approved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('deprecated', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('replacement_model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_per_1k_input', sa.Numeric(10, 6), nullable=True),
        sa.Column('cost_per_1k_output', sa.Numeric(10, 6), nullable=True),
        sa.Column('default_params', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('provider', 'model_name', 'version', name='uq_provider_model_version')
    )

    # Seed data with initial approved models
    op.execute("""
        INSERT INTO approved_models_provider
        (provider, model_name, model_display_name, mode, approved, context_window, supports_function_calling, description)
        VALUES
        -- OpenAI Models
        ('openai', 'gpt-4o-mini', 'GPT-4o Mini', 'reasoning', TRUE, 128000, TRUE, 'Fast and cost-effective model for most tasks'),
        ('openai', 'gpt-4o', 'GPT-4o', 'reasoning', TRUE, 128000, TRUE, 'Most capable OpenAI model for complex reasoning'),
        ('openai', 'gpt-4-turbo', 'GPT-4 Turbo', 'reasoning', TRUE, 128000, TRUE, 'Previous generation flagship model'),
        ('openai', 'gpt-3.5-turbo', 'GPT-3.5 Turbo', 'chat', TRUE, 16385, TRUE, 'Fast and economical for simple tasks'),

        -- Anthropic Models
        ('anthropic', 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'reasoning', TRUE, 200000, TRUE, 'Most intelligent Claude model, excellent for complex tasks'),
        ('anthropic', 'claude-3-5-haiku-20241022', 'Claude 3.5 Haiku', 'chat', TRUE, 200000, TRUE, 'Fastest Claude model, great for simple tasks'),
        ('anthropic', 'claude-3-opus-20240229', 'Claude 3 Opus', 'reasoning', TRUE, 200000, TRUE, 'Previous generation flagship Claude model')
    """)


def downgrade() -> None:
    op.drop_table('approved_models_provider')
