"""add document chunks table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-02 19:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_file_path', sa.Text),
        sa.Column('file_name', sa.String(255)),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('vector_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['document_collections.id'], ondelete='CASCADE')
    )

    op.create_index('idx_chunks_collection', 'document_chunks', ['collection_id'])
    op.create_index('idx_chunks_user', 'document_chunks', ['user_id'])
    op.create_index('idx_chunks_vector', 'document_chunks', ['vector_id'])


def downgrade() -> None:
    op.drop_index('idx_chunks_vector')
    op.drop_index('idx_chunks_user')
    op.drop_index('idx_chunks_collection')
    op.drop_table('document_chunks')
