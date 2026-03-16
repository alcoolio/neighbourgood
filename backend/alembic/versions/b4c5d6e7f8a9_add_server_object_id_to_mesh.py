"""add server_object_id to mesh_synced_messages

Revision ID: b4c5d6e7f8a9
Revises: a2b3c4d5e6f7
Create Date: 2026-03-16 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('mesh_synced_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('server_object_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('mesh_synced_messages', schema=None) as batch_op:
        batch_op.drop_column('server_object_id')
