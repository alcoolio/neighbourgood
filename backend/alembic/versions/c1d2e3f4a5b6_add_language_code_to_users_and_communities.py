"""add language_code to users and primary_language to communities

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── User language preference ────────────────────────────────────
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language_code', sa.String(10), nullable=False, server_default='en'))

    # ── Community primary language ──────────────────────────────────
    with op.batch_alter_table('communities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('primary_language', sa.String(10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('communities', schema=None) as batch_op:
        batch_op.drop_column('primary_language')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('language_code')
