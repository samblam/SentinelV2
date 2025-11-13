"""Add next_attempt_at to queue_items

Revision ID: 002_next_attempt
Revises: 001_initial
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_next_attempt'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add next_attempt_at column to queue_items
    op.add_column('queue_items', sa.Column('next_attempt_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_queue_items_next_attempt_at'), 'queue_items', ['next_attempt_at'], unique=False)


def downgrade() -> None:
    # Remove next_attempt_at column
    op.drop_index(op.f('ix_queue_items_next_attempt_at'), table_name='queue_items')
    op.drop_column('queue_items', 'next_attempt_at')
