"""Initial schema with nodes, detections, queue_items, and blackout_events

Revision ID: 001_initial
Revises:
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nodes_id'), 'nodes', ['id'], unique=False)
    op.create_index(op.f('ix_nodes_node_id'), 'nodes', ['node_id'], unique=True)
    op.create_index(op.f('ix_nodes_status'), 'nodes', ['status'], unique=False)
    op.create_index(op.f('ix_nodes_last_heartbeat'), 'nodes', ['last_heartbeat'], unique=False)

    # Create detections table
    op.create_table(
        'detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude_m', sa.Float(), nullable=True),
        sa.Column('accuracy_m', sa.Float(), nullable=True),
        sa.Column('detections_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('detection_count', sa.Integer(), nullable=False),
        sa.Column('inference_time_ms', sa.Float(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detections_id'), 'detections', ['id'], unique=False)
    op.create_index(op.f('ix_detections_node_id'), 'detections', ['node_id'], unique=False)
    op.create_index(op.f('ix_detections_timestamp'), 'detections', ['timestamp'], unique=False)
    op.create_index(op.f('ix_detections_created_at'), 'detections', ['created_at'], unique=False)

    # Create queue_items table
    op.create_table(
        'queue_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_queue_items_id'), 'queue_items', ['id'], unique=False)
    op.create_index(op.f('ix_queue_items_node_id'), 'queue_items', ['node_id'], unique=False)
    op.create_index(op.f('ix_queue_items_status'), 'queue_items', ['status'], unique=False)
    op.create_index(op.f('ix_queue_items_created_at'), 'queue_items', ['created_at'], unique=False)

    # Create blackout_events table
    op.create_table(
        'blackout_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('activated_at', sa.DateTime(), nullable=False),
        sa.Column('deactivated_at', sa.DateTime(), nullable=True),
        sa.Column('activated_by', sa.String(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('detections_queued', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blackout_events_id'), 'blackout_events', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_blackout_events_id'), table_name='blackout_events')
    op.drop_table('blackout_events')

    op.drop_index(op.f('ix_queue_items_created_at'), table_name='queue_items')
    op.drop_index(op.f('ix_queue_items_status'), table_name='queue_items')
    op.drop_index(op.f('ix_queue_items_node_id'), table_name='queue_items')
    op.drop_index(op.f('ix_queue_items_id'), table_name='queue_items')
    op.drop_table('queue_items')

    op.drop_index(op.f('ix_detections_created_at'), table_name='detections')
    op.drop_index(op.f('ix_detections_timestamp'), table_name='detections')
    op.drop_index(op.f('ix_detections_node_id'), table_name='detections')
    op.drop_index(op.f('ix_detections_id'), table_name='detections')
    op.drop_table('detections')

    op.drop_index(op.f('ix_nodes_last_heartbeat'), table_name='nodes')
    op.drop_index(op.f('ix_nodes_status'), table_name='nodes')
    op.drop_index(op.f('ix_nodes_node_id'), table_name='nodes')
    op.drop_index(op.f('ix_nodes_id'), table_name='nodes')
    op.drop_table('nodes')
