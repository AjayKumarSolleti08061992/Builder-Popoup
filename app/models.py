"""SQLAlchemy database models for Café Companion.

Defines schemas for menu catalog items, customer orders, communal
co-working patrons, and ambient room feedback.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

# Declarative base class for SQLAlchemy models
Base = declarative_base()


class MenuItem(Base):
    """Represents a café food or beverage item in the catalog."""

    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String(255), default="")  # Comma-separated tags
    image_url = Column(String(255), nullable=True)
    prep_time_minutes = Column(Integer, default=3)
    in_stock = Column(Boolean, default=True)

    def to_dict(self):
        """Serialize menu item attributes into a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "description": self.description,
            "tags": [tag.strip() for tag in self.tags.split(",") if tag.strip()],
            "image_url": self.image_url,
            "prep_time_minutes": self.prep_time_minutes,
            "in_stock": self.in_stock,
        }


class Order(Base):
    """Represents a customer order placed in the café."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(20), unique=True, index=True)
    customer_name = Column(String(100), nullable=False)
    table_number = Column(String(20), nullable=False)
    items_json = Column(Text, nullable=False)  # JSON-encoded order lines
    special_notes = Column(Text, default="")
    total_price = Column(Float, default=0.0)
    status = Column(
        String(30), default="placed", index=True
    )  # placed, brewing, ready, served
    estimated_wait_minutes = Column(Integer, default=5)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize order record to dictionary format."""
        try:
            parsed_items = json.loads(self.items_json)
        except Exception:
            parsed_items = []

        return {
            "id": self.id,
            "order_code": self.order_code,
            "customer_name": self.customer_name,
            "table_number": self.table_number,
            "items": parsed_items,
            "special_notes": self.special_notes,
            "total_price": round(self.total_price, 2),
            "status": self.status,
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }


class CommunalPatron(Base):
    """Represents an opt-in café patron open to connecting with others."""

    __tablename__ = "communal_patrons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    table_number = Column(String(20), nullable=False)
    focus_topic = Column(Text, nullable=False)
    open_for = Column(
        String(60), default="Casual Chat"
    )  # e.g., "Casual Chat", "Silent Co-working", "Brainstorming"
    skills_interests = Column(String(255), default="")
    avatar_emoji = Column(String(10), default="☕")
    active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Serialize patron card for communal display."""
        return {
            "id": self.id,
            "name": self.name,
            "table_number": self.table_number,
            "focus_topic": self.focus_topic,
            "open_for": self.open_for,
            "skills_interests": [
                s.strip() for s in self.skills_interests.split(",") if s.strip()
            ],
            "avatar_emoji": self.avatar_emoji,
            "active": self.active,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }


class RoomFeedback(Base):
    """Represents live ambient feedback submitted by café visitors."""

    __tablename__ = "room_feedback"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String(20), nullable=False)
    sentiment_score = Column(Integer, default=5)  # 1 to 5 scale
    noise_rating = Column(String(30), default="Ideal Buzz")  # Quiet, Buzz, Loud
    temperature_rating = Column(String(30), default="Just Right")
    vibe_tag = Column(String(50), default="Focus Friendly")
    customer_comment = Column(Text, default="")
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Serialize feedback record into dictionary format."""
        return {
            "id": self.id,
            "table_number": self.table_number,
            "sentiment_score": self.sentiment_score,
            "noise_rating": self.noise_rating,
            "temperature_rating": self.temperature_rating,
            "vibe_tag": self.vibe_tag,
            "customer_comment": self.customer_comment,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
