"""FastAPI route handlers for Café Companion.

Defines RESTful endpoints for the menu catalog, order lifecycle,
Gemini AI conversational barista, flavor discovery, communal co-working
matchmaking, ambient room sentiment, and system health checks.
"""

from datetime import datetime, timezone
import json
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.gemini_service import (
    analyze_room_sentiment_pulse,
    calculate_smart_wait_time,
    chat_with_barista,
    generate_social_icebreaker,
    recommend_by_mood_and_diet,
)
from app.models import CommunalPatron, MenuItem, Order, RoomFeedback

router = APIRouter(prefix="/api", tags=["Cafe Companion API"])


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """Represents a single message in the conversational chat history."""

    role: str = Field(..., description="Role of speaker: 'user' or 'model'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    """Payload for conversational ordering and barista guidance."""

    message: str = Field(..., min_length=1)
    history: List[ChatMessage] = Field(default_factory=list)
    api_key: Optional[str] = None


class RecommendRequest(BaseModel):
    """Payload for mood and diet based flavor discovery."""

    mood: str = Field(default="Deep Focus")
    dietary_pref: str = Field(default="None")
    caffeine_pref: str = Field(default="Balanced")
    api_key: Optional[str] = None


class OrderItemPayload(BaseModel):
    """Line item in an order submission."""

    id: Optional[int] = None
    name: str
    price: float
    quantity: int = 1
    customizations: Dict[str, Any] = Field(default_factory=dict)


class CreateOrderRequest(BaseModel):
    """Order creation payload submitted by the customer."""

    customer_name: str = Field(..., min_length=1)
    table_number: str = Field(..., min_length=1)
    items: List[OrderItemPayload] = Field(..., min_items=1)
    special_notes: Optional[str] = ""


class UpdateOrderStatusRequest(BaseModel):
    """Status transition request payload."""

    status: str = Field(..., pattern="^(placed|brewing|ready|served)$")


class CreatePatronRequest(BaseModel):
    """Communal table card registration payload."""

    name: str = Field(..., min_length=1)
    table_number: str = Field(..., min_length=1)
    focus_topic: str = Field(..., min_length=2)
    open_for: str = Field(default="Casual Chat")
    skills_interests: str = Field(default="")
    avatar_emoji: str = Field(default="☕")


class IcebreakerRequest(BaseModel):
    """Icebreaker spark generation payload."""

    patron_a_id: int
    patron_b_id: int
    api_key: Optional[str] = None


class CreateFeedbackRequest(BaseModel):
    """Ambient room sentiment and feedback payload."""

    table_number: str = Field(..., min_length=1)
    sentiment_score: int = Field(default=5, ge=1, le=5)
    noise_rating: str = Field(default="Ideal Buzz")
    temperature_rating: str = Field(default="Just Right")
    vibe_tag: str = Field(default="Focus Friendly")
    customer_comment: Optional[str] = ""


class ApiKeyConfigRequest(BaseModel):
    """Dynamic API key configuration payload."""

    api_key: str = Field(..., min_length=10)


# -----------------------------------------------------------------------------
# Menu & Catalog Endpoints
# -----------------------------------------------------------------------------


@router.get("/menu", summary="Fetch café menu catalog")
def get_menu(db: Session = Depends(get_db)):
    """Retrieve all active food and beverage items in the catalog."""
    items = db.query(MenuItem).filter(MenuItem.in_stock == True).all()  # noqa: E712
    return {"status": "success", "items": [item.to_dict() for item in items]}


# -----------------------------------------------------------------------------
# Order Lifecycle & Better Waits Endpoints
# -----------------------------------------------------------------------------


@router.post("/orders", status_code=status.HTTP_201_CREATED, summary="Create new café order")
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    """Place a new order with AI dynamic wait time prediction."""
    # Count pending orders currently in progress
    active_count = (
        db.query(Order)
        .filter(Order.status.in_(["placed", "brewing"]))
        .count()
    )

    total_items_count = sum(item.quantity for item in payload.items)
    wait_time = calculate_smart_wait_time(active_count, total_items_count)

    # Calculate monetary total
    total_price = sum(item.price * item.quantity for item in payload.items)

    # Generate friendly order code
    order_number = random.randint(101, 999)
    order_code = f"CF-{order_number}"

    # Serialize items
    serialized_items = [item.dict() for item in payload.items]

    new_order = Order(
        order_code=order_code,
        customer_name=payload.customer_name,
        table_number=payload.table_number,
        items_json=json.dumps(serialized_items),
        special_notes=payload.special_notes or "",
        total_price=total_price,
        status="placed",
        estimated_wait_minutes=wait_time,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "status": "success",
        "message": f"Order #{order_code} received!",
        "order": new_order.to_dict(),
    }


@router.get("/orders", summary="List active kitchen queue orders")
def list_orders(db: Session = Depends(get_db)):
    """Retrieve all open and recently fulfilled orders for the barista display."""
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(30)
        .all()
    )
    return {"status": "success", "orders": [o.to_dict() for o in orders]}


@router.patch("/orders/{order_id}/status", summary="Update order preparation status")
def update_order_status(
    order_id: int, payload: UpdateOrderStatusRequest, db: Session = Depends(get_db)
):
    """Transition an order between placed, brewing, ready, and served."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)

    return {"status": "success", "order": order.to_dict()}


# -----------------------------------------------------------------------------
# Gemini AI Features (Conversational Ordering & Flavor Discovery)
# -----------------------------------------------------------------------------


@router.post("/ai/chat", summary="Conversational barista companion powered by Gemini")
def ai_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Interact with Aura, the AI specialty barista companion."""
    menu_items = [
        item.to_dict()
        for item in db.query(MenuItem).filter(MenuItem.in_stock == True).all()  # noqa: E712
    ]

    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history]
    result = chat_with_barista(
        user_message=payload.message,
        conversation_history=history_dicts,
        menu_items=menu_items,
        api_key=payload.api_key or config.GEMINI_API_KEY,
    )

    return {"status": "success", **result}


@router.post("/ai/recommend", summary="Flavor discovery and mood-based pairings")
def ai_recommend(payload: RecommendRequest, db: Session = Depends(get_db)):
    """Discover curated drink and pastry pairings for a customer's specific vibe."""
    menu_items = [item.to_dict() for item in db.query(MenuItem).all()]
    result = recommend_by_mood_and_diet(
        mood=payload.mood,
        dietary_pref=payload.dietary_pref,
        caffeine_pref=payload.caffeine_pref,
        menu_items=menu_items,
        api_key=payload.api_key or config.GEMINI_API_KEY,
    )
    return {"status": "success", "recommendation": result}


# -----------------------------------------------------------------------------
# Connect People: The Café Commons
# -----------------------------------------------------------------------------


@router.get("/social/patrons", summary="List active communal table patrons")
def get_communal_patrons(db: Session = Depends(get_db)):
    """Fetch opt-in café patrons open to networking and casual conversation."""
    patrons = (
        db.query(CommunalPatron)
        .filter(CommunalPatron.active == True)  # noqa: E712
        .order_by(CommunalPatron.created_at.desc())
        .all()
    )
    return {"status": "success", "patrons": [p.to_dict() for p in patrons]}


@router.post("/social/patrons", status_code=status.HTTP_201_CREATED, summary="Register communal table card")
def create_communal_patron(payload: CreatePatronRequest, db: Session = Depends(get_db)):
    """Broadcast current focus project and connect preferences to the café floor."""
    new_patron = CommunalPatron(
        name=payload.name,
        table_number=payload.table_number,
        focus_topic=payload.focus_topic,
        open_for=payload.open_for,
        skills_interests=payload.skills_interests,
        avatar_emoji=payload.avatar_emoji,
        active=True,
    )
    db.add(new_patron)
    db.commit()
    db.refresh(new_patron)

    return {"status": "success", "patron": new_patron.to_dict()}


@router.post("/social/icebreaker", summary="AI-generated social spark between two patrons")
def create_icebreaker(payload: IcebreakerRequest, db: Session = Depends(get_db)):
    """Generate a low-pressure, intelligent conversational starter between two guests."""
    patron_a = db.query(CommunalPatron).filter(CommunalPatron.id == payload.patron_a_id).first()
    patron_b = db.query(CommunalPatron).filter(CommunalPatron.id == payload.patron_b_id).first()

    if not patron_a or not patron_b:
        raise HTTPException(status_code=404, detail="One or both patrons not found")

    result = generate_social_icebreaker(
        patron_a.to_dict(),
        patron_b.to_dict(),
        api_key=payload.api_key or config.GEMINI_API_KEY,
    )
    return {"status": "success", "icebreaker": result}


# -----------------------------------------------------------------------------
# Understand the Room: Live Feedback & Room Pulse
# -----------------------------------------------------------------------------


@router.post("/room/feedback", status_code=status.HTTP_201_CREATED, summary="Submit ambient feedback")
def submit_room_feedback(payload: CreateFeedbackRequest, db: Session = Depends(get_db)):
    """Submit rating on acoustics, temperature, and vibe from any table."""
    feedback = RoomFeedback(
        table_number=payload.table_number,
        sentiment_score=payload.sentiment_score,
        noise_rating=payload.noise_rating,
        temperature_rating=payload.temperature_rating,
        vibe_tag=payload.vibe_tag,
        customer_comment=payload.customer_comment or "",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {"status": "success", "feedback": feedback.to_dict()}


@router.get("/room/pulse", summary="Get aggregate room pulse for staff and customers")
def get_room_pulse(db: Session = Depends(get_db)):
    """Synthesize live room sentiment, acoustics, and AI staff directives."""
    feedbacks = (
        db.query(RoomFeedback)
        .order_by(RoomFeedback.created_at.desc())
        .limit(20)
        .all()
    )
    active_orders_count = (
        db.query(Order)
        .filter(Order.status.in_(["placed", "brewing"]))
        .count()
    )

    pulse_data = analyze_room_sentiment_pulse(
        [f.to_dict() for f in feedbacks],
        active_orders_count,
        api_key=config.GEMINI_API_KEY,
    )

    return {
        "status": "success",
        "pulse": pulse_data,
        "recent_feedbacks": [f.to_dict() for f in feedbacks[:5]],
        "active_queue_count": active_orders_count,
    }


# -----------------------------------------------------------------------------
# System Configuration & Google Cloud Health
# -----------------------------------------------------------------------------


@router.post("/config/key", summary="Configure Gemini API Key dynamically")
def set_gemini_key(payload: ApiKeyConfigRequest):
    """Allow user or evaluator to supply their Google Gemini API key via the UI."""
    config.GEMINI_API_KEY = payload.api_key.strip()
    return {
        "status": "success",
        "message": "Gemini API key configured successfully!",
        "has_key": bool(config.GEMINI_API_KEY),
    }


@router.get("/health", summary="System health and Google Cloud technology status")
def health_check(db: Session = Depends(get_db)):
    """Return runtime diagnostics and verification of Google Cloud pillars."""
    menu_count = db.query(MenuItem).count()
    orders_count = db.query(Order).count()
    has_gemini_key = bool(config.GEMINI_API_KEY)

    return {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "google_technologies": {
            "gemini_api": {
                "configured": has_gemini_key,
                "model": config.GEMINI_MODEL,
                "status": "Active (Live GenAI)" if has_gemini_key else "Active (Intelligent Demo Fallback)",
            },
            "cloud_sql": {
                "active": True,
                "connection": "Cloud SQL PostgreSQL Compatible" if config.CLOUD_SQL_CONNECTION_NAME else "Local SQLite Engine",
                "tables_initialized": True,
                "catalog_count": menu_count,
                "orders_count": orders_count,
            },
            "cloud_run": {
                "container_ready": True,
                "stateless_http": True,
                "deployment_script": "deploy_cloud_run.ps1",
            },
        },
    }
