"""merge model config migrations

Revision ID: dd9efeb26360
Revises: 333e1493b071, a7b8c9d0e1f2
Create Date: 2026-02-06 16:38:54.337932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd9efeb26360'
down_revision: Union[str, None] = ('333e1493b071', 'a7b8c9d0e1f2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
