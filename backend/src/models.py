"""Database models for Sentinel v2 Backend API."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

# Use JSONB for PostgreSQL, JSON for other databases
JSONType = JSONB().with_variant(JSON(), "sqlite")


class Node(Base):
    """Edge node registry."""
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False, index=True)  # online, offline, covert
    last_heartbeat = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    detections = relationship("Detection", back_populates="node", cascade="all, delete-orphan")
    queue_items = relationship("QueueItem", back_populates="node", cascade="all, delete-orphan")
    blackout_events = relationship("BlackoutEvent", back_populates="node", cascade="all, delete-orphan")


class Detection(Base):
    """Detection records with full metadata."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=True)
    accuracy_m = Column(Float, nullable=True)
    detections_json = Column(JSONType, nullable=False)  # JSONB for PostgreSQL, JSON for SQLite
    detection_count = Column(Integer, nullable=False)
    inference_time_ms = Column(Float, nullable=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    node = relationship("Node", back_populates="detections")


class QueueItem(Base):
    """Pending transmissions during network issues."""
    __tablename__ = "queue_items"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    payload = Column(JSONType, nullable=False)  # JSONB for PostgreSQL, JSON for SQLite
    status = Column(String, nullable=False, index=True)  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    node = relationship("Node", back_populates="queue_items")


class BlackoutEvent(Base):
    """Blackout activation/deactivation log."""
    __tablename__ = "blackout_events"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    activated_at = Column(DateTime, nullable=False)
    deactivated_at = Column(DateTime, nullable=True)
    activated_by = Column(String, nullable=True)  # operator ID
    reason = Column(Text, nullable=True)
    detections_queued = Column(Integer, default=0)

    # Relationships
    node = relationship("Node", back_populates="blackout_events")
