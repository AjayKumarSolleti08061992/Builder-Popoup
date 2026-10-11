"""Database engine setup, session handling, and initial seed data.

Provides SQLAlchemy session dependency and populates initial specialty
menu items, communal co-working patron cards, and ambient room metrics.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL, CLOUD_SQL_CONNECTION_NAME
from app.models import Base, MenuItem, CommunalPatron, RoomFeedback, Order

# Database engine configuration
# For SQLite, check_same_thread needs to be False for FastAPI multi-threading
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for standalone database operations outside web requests."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def seed_initial_data(db):
    """Seed specialty menu items, communal table cards, and ambient records."""
    # Check if menu items already exist
    existing_items_count = db.query(MenuItem).count()
    if existing_items_count == 0:
        sample_items = [
            MenuItem(
                name="Velvet Honey Flat White",
                category="Espresso & Lattes",
                price=5.40,
                description=(
                    "Double ristretto of Ethiopian Yirgacheffe with micro-foamed "
                    "oat milk infused with raw local wildflower honey and cinnamon."
                ),
                tags="oat milk, low acidity, floral, specialty roast",
                image_url="/static/images/artisan_latte.jpg",
                prep_time_minutes=3,
                in_stock=True,
            ),
            MenuItem(
                name="Nitro Vanilla Cloud Cold Brew",
                category="Cold Brews",
                price=5.90,
                description=(
                    "24-hour steeped single-origin Colombian cold brew topped "
                    "with silky Madagascar vanilla sweet foam and cocoa nib dust."
                ),
                tags="high caffeine, iced, smooth, vegan foam available",
                image_url="/static/images/coldbrew_pastry.jpg",
                prep_time_minutes=2,
                in_stock=True,
            ),
            MenuItem(
                name="Cardamom Rose Cortado",
                category="Espresso & Lattes",
                price=4.80,
                description=(
                    "Equal parts intense espresso and textured whole or almond milk, "
                    "scented with freshly crushed green cardamom and Damascus rose water."
                ),
                tags="balanced, aromatic, short drink, traditional",
                image_url="/static/images/artisan_latte.jpg",
                prep_time_minutes=3,
                in_stock=True,
            ),
            MenuItem(
                name="Kyoto Slow-Drip Pour Over",
                category="Cold Brews",
                price=6.20,
                description=(
                    "Artisanal glass tower drip extraction over 8 hours, yielding "
                    "a clean, tea-like body with vibrant jasmine, bergamot, and peach notes."
                ),
                tags="single origin, delicate, high clarity, light roast",
                image_url="/static/images/artisan_latte.jpg",
                prep_time_minutes=2,
                in_stock=True,
            ),
            MenuItem(
                name="Ceremonial Uji Matcha Latte",
                category="Artisanal Teas",
                price=5.75,
                description=(
                    "Stone-ground first-harvest Japanese green tea whisked with "
                    "creamy organic oat milk and subtle Madagascar agave."
                ),
                tags="antioxidant, calm focus, L-theanine, dairy-free",
                image_url="/static/images/artisan_latte.jpg",
                prep_time_minutes=3,
                in_stock=True,
            ),
            MenuItem(
                name="Brown Butter Almond Croissant",
                category="Bakery & Treats",
                price=4.95,
                description=(
                    "Freshly baked flaky twice-cooked viennoiserie stuffed with rich "
                    "frangipane almond cream and toasted almond flakes."
                ),
                tags="pastry, sweet, warm, pairs with espresso",
                image_url="/static/images/coldbrew_pastry.jpg",
                prep_time_minutes=2,
                in_stock=True,
            ),
            MenuItem(
                name="Smashed Avocado & Whipped Feta Tartine",
                category="Light Bites",
                price=8.50,
                description=(
                    "Toasted artisan sourdough with Hass avocado, whipped Greek feta, "
                    "pickled shallots, dukkah crunch, and organic microgreens."
                ),
                tags="savory, high protein, vegetarian, sourdough",
                image_url="/static/images/coldbrew_pastry.jpg",
                prep_time_minutes=5,
                in_stock=True,
            ),
            MenuItem(
                name="Sparkling Cascara Hibiscus Spritz",
                category="Artisanal Teas",
                price=5.25,
                description=(
                    "Sun-dried coffee cherry cascara tea brewed with Egyptian hibiscus, "
                    "sparkling mineral water, and fresh blood orange slice."
                ),
                tags="low caffeine, refreshing, fruity, upcycled coffee",
                image_url="/static/images/coldbrew_pastry.jpg",
                prep_time_minutes=2,
                in_stock=True,
            ),
        ]
        db.add_all(sample_items)
        db.commit()

    # Seed initial communal table patrons if empty
    if db.query(CommunalPatron).count() == 0:
        sample_patrons = [
            CommunalPatron(
                name="Elena Vance",
                table_number="Table 4 (Window Bar)",
                focus_topic="Training edge vision models on Raspberry Pi & Google Coral",
                open_for="Brainstorming & Tech Chat",
                skills_interests="Computer Vision, TinyML, Python, Sci-Fi novels",
                avatar_emoji="🚀",
                active=True,
            ),
            CommunalPatron(
                name="Marcus Chen",
                table_number="Table 2 (Big Oak Table)",
                focus_topic="Polishing the UI design system for a sustainable fashion brand",
                open_for="Silent Co-working & Coffee Breaks",
                skills_interests="UI/UX, Figma, Typography, Pour-over extraction",
                avatar_emoji="🎨",
                active=True,
            ),
            CommunalPatron(
                name="Dr. Priya Nair",
                table_number="Table 7 (Bookshelf Nook)",
                focus_topic="Writing a chapter on cognitive psychology and ambient soundscapes",
                open_for="Book Discussion & Quiet Exchange",
                skills_interests="Neuroscience, Ambient Music, Specialty Tea",
                avatar_emoji="📚",
                active=True,
            ),
        ]
        db.add_all(sample_patrons)
        db.commit()

    # Seed ambient room feedback sample
    if db.query(RoomFeedback).count() == 0:
        sample_feedbacks = [
            RoomFeedback(
                table_number="Table 2",
                sentiment_score=5,
                noise_rating="Ideal Buzz",
                temperature_rating="Just Right",
                vibe_tag="Focus Friendly",
                customer_comment="The lo-fi background jazz is at the absolute perfect volume for deep focus work.",
            ),
            RoomFeedback(
                table_number="Table 5",
                sentiment_score=4,
                noise_rating="Ideal Buzz",
                temperature_rating="Just Right",
                vibe_tag="Cozy Sanctuary",
                customer_comment="In love with the velvet flat white and natural lighting.",
            ),
        ]
        db.add_all(sample_feedbacks)
        db.commit()


def init_database():
    """Create all database tables and seed starting data."""
    Base.metadata.create_all(bind=engine)
    with get_db_context() as db:
        seed_initial_data(db)
