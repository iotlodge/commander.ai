"""add web cache indexes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2024-02-05 12:15:00.000000

Add indexes for web cache performance optimization:
- Index on created_at for staleness queries
- GIN index on metadata JSONB for fast lookups
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add indexes for web cache optimization

    1. created_at index - for staleness detection queries
    2. GIN index on metadata JSONB - for fast metadata filtering
    """
    # Add index on created_at for efficient staleness queries
    op.create_index(
        'ix_document_chunks_created_at',
        'document_chunks',
        ['created_at'],
        unique=False
    )

    # Add GIN index on metadata JSONB for fast metadata lookups
    # This enables efficient queries on metadata keys like:
    # - metadata->>'source_type' = 'web'
    # - metadata->>'content_hash'
    # - metadata->>'fetched_at'
    op.execute("""
        CREATE INDEX ix_document_chunks_metadata_gin
        ON document_chunks USING GIN (metadata)
    """)

    # Add index on metadata->>'content_hash' for deduplication
    op.execute("""
        CREATE INDEX ix_document_chunks_content_hash
        ON document_chunks ((metadata->>'content_hash'))
        WHERE metadata->>'content_hash' IS NOT NULL
    """)

    # Add index on metadata->>'source_type' for filtering web content
    op.execute("""
        CREATE INDEX ix_document_chunks_source_type
        ON document_chunks ((metadata->>'source_type'))
        WHERE metadata->>'source_type' = 'web'
    """)


def downgrade() -> None:
    """Remove web cache indexes"""
    # Drop indexes in reverse order
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_source_type")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_content_hash")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_metadata_gin")
    op.drop_index('ix_document_chunks_created_at', table_name='document_chunks')
