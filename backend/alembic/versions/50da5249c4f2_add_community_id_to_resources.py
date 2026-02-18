"""add community_id to resources

Revision ID: 50da5249c4f2
Revises: db58f8fb093e
Create Date: 2026-02-18 13:01:47.828737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50da5249c4f2'
down_revision: Union[str, None] = 'db58f8fb093e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('community_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_resources_community_id'), ['community_id'], unique=False)
        batch_op.create_foreign_key('fk_resources_community_id', 'communities', ['community_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.drop_constraint('fk_resources_community_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_resources_community_id'))
        batch_op.drop_column('community_id')
