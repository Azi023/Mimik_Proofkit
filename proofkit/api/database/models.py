"""SQLAlchemy database models."""

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from . import Base


def generate_id(prefix: str) -> str:
    """Generate prefixed unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class User(Base):
    """User model for API authentication."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: generate_id("usr"))
    email = Column(String, unique=True, nullable=False, index=True)
    api_key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    audits = relationship("Audit", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Audit(Base):
    """Audit record model."""
    __tablename__ = "audits"

    id = Column(String, primary_key=True, default=lambda: generate_id("aud"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    mode = Column(String, default="fast")
    status = Column(String, default="queued", index=True)
    business_type = Column(String, nullable=True)
    conversion_goal = Column(String, nullable=True)
    generate_concept = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Results
    scorecard = Column(JSON, nullable=True)
    finding_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)

    # Store full results as JSON
    raw_data_path = Column(String, nullable=True)
    report_data = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audits")

    def __repr__(self):
        return f"<Audit {self.id} - {self.url}>"


class WebhookLog(Base):
    """Log of webhook delivery attempts."""
    __tablename__ = "webhook_logs"

    id = Column(String, primary_key=True, default=lambda: generate_id("whk"))
    audit_id = Column(String, ForeignKey("audits.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<WebhookLog {self.id} - {self.audit_id}>"
