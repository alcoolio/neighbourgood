"""add ticket_comments table

Revision ID: 72f9e65d40b8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-25 19:51:05.627810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72f9e65d40b8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ticket_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['ticket_id'], ['emergency_tickets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ticket_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ticket_comments_author_id'), ['author_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ticket_comments_ticket_id'), ['ticket_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('ticket_comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ticket_comments_ticket_id'))
        batch_op.drop_index(batch_op.f('ix_ticket_comments_author_id'))

    op.drop_table('ticket_comments')
