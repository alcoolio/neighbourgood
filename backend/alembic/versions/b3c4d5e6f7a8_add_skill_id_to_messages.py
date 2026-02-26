"""add skill_id to messages

Revision ID: b3c4d5e6f7a8
Revises: 72f9e65d40b8
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = '72f9e65d40b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('skill_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_messages_skill_id', 'skills', ['skill_id'], ['id'])
        batch_op.create_index(batch_op.f('ix_messages_skill_id'), ['skill_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_messages_skill_id'))
        batch_op.drop_constraint('fk_messages_skill_id', type_='foreignkey')
        batch_op.drop_column('skill_id')
