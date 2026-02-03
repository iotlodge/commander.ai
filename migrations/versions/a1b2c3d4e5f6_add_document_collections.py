"""add document collections table

Revision ID: a1b2c3d4e5f6
Revises: 812ba4d72478
Create Date: 2026-02-02 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '812ba4d72478'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_name', sa.String(255), nullable=False),
        sa.Column('qdrant_collection_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('chunk_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.UniqueConstraint('user_id', 'collection_name', name='uq_user_collection_name'),
        sa.UniqueConstraint('qdrant_collection_name', name='uq_qdrant_collection_name')
    )

    op.create_index('idx_collections_user', 'document_collections', ['user_id'])
    op.create_index('idx_collections_created_at', 'document_collections', ['created_at'], postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    op.drop_index('idx_collections_created_at')
    op.drop_index('idx_collections_user')
    op.drop_table('document_collections')
