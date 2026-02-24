"""add inventory fields to resources and triage fields to emergency_tickets

Revision ID: a1b2c3d4e5f6
Revises: 50da5249c4f2
Create Date: 2026-02-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '50da5249c4f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Resource inventory fields ──────────────────────────────────
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quantity_total', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('quantity_available', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('reorder_threshold', sa.Integer(), nullable=True))

    # ── EmergencyTicket triage field ───────────────────────────────
    with op.batch_alter_table('emergency_tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('due_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('emergency_tickets', schema=None) as batch_op:
        batch_op.drop_column('due_at')

    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.drop_column('reorder_threshold')
        batch_op.drop_column('quantity_available')
        batch_op.drop_column('quantity_total')
