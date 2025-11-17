"""Add duration_seconds and detections_transmitted to blackout_events

Revision ID: 003_blackout_columns
Revises: 002_next_attempt
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_blackout_columns'
down_revision = '002_next_attempt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add duration_seconds column to blackout_events
    op.add_column('blackout_events', sa.Column('duration_seconds', sa.Integer(), nullable=True))

    # Add detections_transmitted column to blackout_events
    op.add_column('blackout_events', sa.Column('detections_transmitted', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove columns
    op.drop_column('blackout_events', 'detections_transmitted')
    op.drop_column('blackout_events', 'duration_seconds')
