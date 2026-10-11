"""Google Gemini AI service layer for Café Companion.

Implements generative AI capabilities using Google GenAI SDK (Gemini 2.5/1.5 Flash)
for conversational ordering, flavor recommendations, communal icebreakers,
dynamic wait predictions, and ambient room sentiment synthesis.
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from app.config import GEMINI_API_KEY, GEMINI_MODEL

# Configure logger
logger = logging.getLogger("cafe_companion.gemini")


def get_genai_client(api_key: Optional[str] = None):
    """Retrieve an authenticated Google GenAI client instance.

    Args:
        api_key: Optional Gemini API key override. If not supplied,
            falls back to the configured environment variable.

    Returns:
        genai.Client or None: Authenticated client if key is present.
    """
    if not GENAI_AVAILABLE:
        return None

    active_key = api_key or GEMINI_API_KEY
    if not active_key:
        return None

    try:
        return genai.Client(api_key=active_key)
    except Exception as exc:
        logger.warning("Failed to initialize Google GenAI client: %s", exc)
        return None


def chat_with_barista(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    menu_items: List[Dict[str, Any]],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Provide intelligent conversational ordering assistance.

    Interprets natural language customer requests, recommends matching
    menu items, respects dietary preferences, and extracts suggested items
    to populate the customer's digital order cart.

    Args:
        user_message: The text input from the café customer.
        conversation_history: Prior chat messages with role and content.
        menu_items: Catalog of available menu items for reference.
        api_key: Optional API key override.

    Returns:
        dict: Contains conversational 'reply', 'suggested_items', and 'used_live_api'.
    """
    client = get_genai_client(api_key)

    # Simplified menu summary for LLM context
    catalog_context = "\n".join(
        [
            f"- {item['name']} (${item['price']:.2f}): {item['description']} "
            f"(Tags: {', '.join(item['tags'])})"
            for item in menu_items
        ]
    )

    system_instruction = (
        "You are 'Aura', the intelligent café companion and master barista at "
        "'The Artisan Roast & Byte'. You are warm, knowledgeable, and passionate "
        "about specialty coffee, brewing notes, and customer wellbeing.\n"
        "Your goals:\n"
        "1. Welcome the guest and recommend items tailored to their mood, dietary "
        "preferences, or work focus.\n"
        "2. If they want to order, naturally confirm their choices and customize milk/sweetness.\n"
        "3. Always reference items from the real menu catalog.\n"
        "4. Output your response as valid JSON with two fields:\n"
        "   - 'reply': Your friendly, concise barista reply (markdown supported).\n"
        "   - 'suggested_items': A list of objects [{'name': 'Item Name', 'quantity': 1, 'notes': 'extra oat milk'}] "
        "matching items the customer requested or you strongly recommended.\n\n"
        f"Café Menu Catalog:\n{catalog_context}"
    )

    if client:
        try:
            # Build conversation prompt
            history_text = "\n".join(
                [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation_history[-6:]]
            )
            full_prompt = (
                f"{system_instruction}\n\n"
                f"Conversation History:\n{history_text}\n"
                f"User: {user_message}\n\n"
                "Respond ONLY with a valid JSON object with keys 'reply' and 'suggested_items'."
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )

            raw_text = response.text.strip()
            parsed = json.loads(raw_text)
            return {
                "reply": parsed.get("reply", "I'd love to craft that for you!"),
                "suggested_items": parsed.get("suggested_items", []),
                "used_live_api": True,
            }
        except Exception as exc:
            logger.error("Gemini API call failed, using intelligent simulation: %s", exc)

    # Intelligent Fallback Simulation Engine
    lower_msg = user_message.lower()
    matched_items = []
    reply_lines = []

    if any(k in lower_msg for k in ["iced", "cold", "refreshing", "summer"]):
        matched_items.append({"name": "Nitro Vanilla Cloud Cold Brew", "quantity": 1, "notes": "Chilled & velvety"})
        reply_lines.append(
            "For a crisp and energizing sip, our **Nitro Vanilla Cloud Cold Brew** is unmatched! "
            "It has a velvety cold foam with single-origin Colombian cold drip."
        )
    elif any(k in lower_msg for k in ["oat", "dairy-free", "lactose", "vegan"]):
        matched_items.append({"name": "Velvet Honey Flat White", "quantity": 1, "notes": "Steamed oat milk"})
        reply_lines.append(
            "I'd love to prepare our **Velvet Honey Flat White** for you with our house organic oat milk! "
            "It has gentle wildflower honey and cinnamon that pairs beautifully with oat milk's natural creaminess."
        )
    elif any(k in lower_msg for k in ["matcha", "tea", "calm", "relax", "l-theanine"]):
        matched_items.append({"name": "Ceremonial Uji Matcha Latte", "quantity": 1, "notes": "Whisked fresh"})
        reply_lines.append(
            "The **Ceremonial Uji Matcha Latte** is perfect right now. Stone-ground green tea brings a smooth, "
            "jitter-free cognitive flow with calming L-theanine."
        )
    elif any(k in lower_msg for k in ["sweet", "pastry", "croissant", "eat", "food", "snack"]):
        matched_items.append({"name": "Brown Butter Almond Croissant", "quantity": 1, "notes": "Warm & flaky"})
        reply_lines.append(
            "You cannot go wrong with our **Brown Butter Almond Croissant** fresh from the morning bake. "
            "Golden, twice-baked, and stuffed with nutty frangipane!"
        )
    else:
        matched_items.append({"name": "Velvet Honey Flat White", "quantity": 1, "notes": "Standard roast"})
        reply_lines.append(
            "Welcome! If you're settling in for work or relaxing, I highly recommend our signature "
            "**Velvet Honey Flat White** or a **Brown Butter Almond Croissant**. Let me know if you prefer "
            "dairy-free milk or a bold single-origin drip!"
        )

    return {
        "reply": "\n\n".join(reply_lines),
        "suggested_items": matched_items,
        "used_live_api": False,
    }


def recommend_by_mood_and_diet(
    mood: str,
    dietary_pref: str,
    caffeine_pref: str,
    menu_items: List[Dict[str, Any]],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate tailored beverage and culinary pairings based on mood and diet.

    Args:
        mood: The customer's emotional or work state (e.g., Deep Focus, Social Chill).
        dietary_pref: Vegan, Gluten-Free, Dairy-Free, None.
        caffeine_pref: High Caffeine, Low/Decaf, Medium.
        menu_items: Active café menu items.
        api_key: Optional API key override.

    Returns:
        dict: Recommendation details including drink, pastry pairing, and tasting notes.
    """
    client = get_genai_client(api_key)

    if client:
        try:
            catalog_summary = "\n".join(
                [f"- {m['name']} ({m['category']}): {m['description']} [{m['tags']}]" for m in menu_items]
            )
            prompt = (
                f"You are the Flavor Discovery AI at 'The Artisan Roast & Byte'.\n"
                f"Customer Context:\n"
                f"- Current Vibe/Mood: {mood}\n"
                f"- Dietary Restriction: {dietary_pref}\n"
                f"- Caffeine Preference: {caffeine_pref}\n\n"
                f"Available Menu:\n{catalog_summary}\n\n"
                "Recommend the single best beverage and an ideal food pairing from the menu. "
                "Explain the sensory chemistry and why it fits this mood.\n"
                "Return JSON with keys:\n"
                "- 'drink_name': string\n"
                "- 'pairing_name': string\n"
                "- 'pairing_rationale': string (1-2 sentences)\n"
                "- 'tasting_notes': list of 3 flavor strings (e.g. ['Honey Blossom', 'Toasted Almond', 'Citrus'])\n"
                "- 'barista_tip': string"
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.6,
                ),
            )
            data = json.loads(response.text.strip())
            data["used_live_api"] = True
            return data
        except Exception as exc:
            logger.warning("Gemini recommendation fallback triggered: %s", exc)

    # Heuristic recommendations based on mood
    mood_profiles = {
        "Deep Focus": {
            "drink_name": "Kyoto Slow-Drip Pour Over",
            "pairing_name": "Brown Butter Almond Croissant",
            "pairing_rationale": "High clarity single-origin extraction provides clean cognitive stamina without mid-day jitters, balanced by comforting buttery pastry notes.",
            "tasting_notes": ["White Peach", "Jasmine Blossom", "Bergamot"],
            "barista_tip": "Sip slowly at room temperature to let the floral origin notes bloom.",
        },
        "Social Buzz": {
            "drink_name": "Nitro Vanilla Cloud Cold Brew",
            "pairing_name": "Smashed Avocado & Whipped Feta Tartine",
            "pairing_rationale": "Energizing nitro effervescence paired with savory whipped feta and crunchy dukkah keeps conversation lively and palate refreshed.",
            "tasting_notes": ["Madagascar Vanilla", "Dark Cacao", "Creamy Foam"],
            "barista_tip": "Don't use a straw—drink directly from the lip to get both foam and cold brew together.",
        },
        "Calm & Mindful": {
            "drink_name": "Ceremonial Uji Matcha Latte",
            "pairing_name": "Brown Butter Almond Croissant",
            "pairing_rationale": "Rich L-theanine promotes alpha brainwaves for creative reading or reflective journals, harmonizing with warm nutty aromas.",
            "tasting_notes": ["Sweet Umami", "Steamed Oat Cream", "Stone Grass"],
            "barista_tip": "Ask for light sweetness to savor the vegetal purity of first-harvest Uji leaves.",
        },
        "Cozy Comfort": {
            "drink_name": "Velvet Honey Flat White",
            "pairing_name": "Brown Butter Almond Croissant",
            "pairing_rationale": "The delicate spice of cinnamon and honey warmth wraps around you like a soft wool blanket on a breezy afternoon.",
            "tasting_notes": ["Wildflower Honey", "Ceylon Cinnamon", "Velvety Crema"],
            "barista_tip": "Paired best with Table 4 by the sunlit window nook.",
        },
    }

    selected = mood_profiles.get(mood, mood_profiles["Deep Focus"])
    selected["used_live_api"] = False
    return selected


def generate_social_icebreaker(
    patron_a: Dict[str, Any],
    patron_b: Dict[str, Any],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an AI-powered conversational spark between two café patrons.

    Finds shared intersections, complementary skills, or fun coffee prompts
    without friction or awkwardness.

    Args:
        patron_a: Profile of the initiator patron.
        patron_b: Profile of the peer patron at the café.
        api_key: Optional API key override.

    Returns:
        dict: Icebreaker question, common thread explanation, and vibe rating.
    """
    client = get_genai_client(api_key)

    if client:
        try:
            prompt = (
                f"You are the Café Social Matchmaker AI at 'The Artisan Roast & Byte'.\n"
                f"Patron A ({patron_a.get('name')} at {patron_a.get('table_number')}):\n"
                f"- Working on: {patron_a.get('focus_topic')}\n"
                f"- Open for: {patron_a.get('open_for')}\n"
                f"- Interests: {patron_a.get('skills_interests')}\n\n"
                f"Patron B ({patron_b.get('name')} at {patron_b.get('table_number')}):\n"
                f"- Working on: {patron_b.get('focus_topic')}\n"
                f"- Open for: {patron_b.get('open_for')}\n"
                f"- Interests: {patron_b.get('skills_interests')}\n\n"
                "Create a clever, natural, zero-awkwardness conversational icebreaker to connect them. "
                "Keep it polite, engaging, and relevant to their work or café context.\n"
                "Return JSON with:\n"
                "- 'shared_thread': string (1 concise sentence explaining what connects them)\n"
                "- 'icebreaker_prompt': string (A fun, respectful opening line or question)\n"
                "- 'suggested_activity': string (e.g. '10-minute coffee walk', 'Quick feedback exchange')"
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            data = json.loads(response.text.strip())
            data["used_live_api"] = True
            return data
        except Exception as exc:
            logger.warning("Gemini icebreaker fallback triggered: %s", exc)

    # Simulation fallback
    return {
        "shared_thread": (
            f"Both {patron_a.get('name', 'You')} and {patron_b.get('name', 'they')} "
            "are deeply immersed in creative problem-solving and love artisan café energy!"
        ),
        "icebreaker_prompt": (
            f"\"Hey {patron_b.get('name')}, noticed you're exploring {patron_b.get('focus_topic', 'an intriguing project')}—"
            f"I'm at {patron_a.get('table_number')} working on {patron_a.get('focus_topic', 'something similar')}. "
            "How's the coffee treating your workflow today?\""
        ),
        "suggested_activity": "5-minute coffee recharge & idea ping-pong",
        "used_live_api": False,
    }


def analyze_room_sentiment_pulse(
    feedback_entries: List[Dict[str, Any]],
    active_orders_count: int,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Synthesize ambient room feedback into actionable insights for café staff.

    Args:
        feedback_entries: Collection of recent customer ratings and comments.
        active_orders_count: Number of orders currently in the kitchen queue.
        api_key: Optional API key override.

    Returns:
        dict: Barista executive pulse summary, vibe index, and staff action recommendations.
    """
    total_reviews = len(feedback_entries)
    if total_reviews == 0:
        avg_score = 4.8
    else:
        avg_score = sum(f.get("sentiment_score", 5) for f in feedback_entries) / total_reviews

    client = get_genai_client(api_key)

    if client and total_reviews > 0:
        try:
            feedback_text = "\n".join(
                [
                    f"- Table {f.get('table_number')}: Score {f.get('sentiment_score')}/5, "
                    f"Noise: {f.get('noise_rating')}, Temp: {f.get('temperature_rating')}, "
                    f"Vibe: {f.get('vibe_tag')}, Note: '{f.get('customer_comment', '')}'"
                    for f in feedback_entries[-10:]
                ]
            )

            prompt = (
                f"You are the Café Intelligence Analyst for the Barista Kitchen Screen.\n"
                f"Active Kitchen Queue: {active_orders_count} orders in preparation.\n"
                f"Recent Customer Feedback:\n{feedback_text}\n\n"
                "Synthesize this into a concise room status for the floor manager.\n"
                "Return JSON with:\n"
                "- 'pulse_summary': string (1-2 sentences summarizing overall customer atmosphere)\n"
                "- 'room_vibe_label': string (e.g. 'Cozy & High Focus', 'Energetic Rush', 'Slightly Noisy')\n"
                "- 'staff_actions': list of 3 short actionable directives for baristas/floor staff\n"
                "- 'overall_sentiment_pct': integer between 50 and 99"
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            data = json.loads(response.text.strip())
            data["average_rating"] = round(avg_score, 1)
            data["used_live_api"] = True
            return data
        except Exception as exc:
            logger.warning("Gemini room pulse analysis fallback: %s", exc)

    # Heuristic staff analysis
    sentiment_pct = int(min(98, max(60, avg_score * 19.2)))
    vibe_label = "Deep Work & Creative Harmony" if sentiment_pct > 80 else "Steady Café Flow"

    return {
        "pulse_summary": (
            f"The room is radiating a {vibe_label.lower()} vibe with {sentiment_pct}% patron satisfaction. "
            f"Acoustics and lighting are well-calibrated; {active_orders_count} orders currently in the queue."
        ),
        "room_vibe_label": vibe_label,
        "staff_actions": [
            "Maintain current chill playlist tempo (lo-fi acoustic jazz)",
            "Verify oat milk stock on steam wand station 2",
            "Offer table water top-ups to patrons working over 1 hour",
        ],
        "overall_sentiment_pct": sentiment_pct,
        "average_rating": round(avg_score, 1),
        "used_live_api": False,
    }


def calculate_smart_wait_time(
    active_orders_count: int,
    item_count: int,
    current_hour: Optional[int] = None,
) -> int:
    """Predict realistic wait time for a new order based on barista load.

    Args:
        active_orders_count: Number of queued unserved orders.
        item_count: Number of items in the new order.
        current_hour: Current hour of day (0-23) for peak hour weighting.

    Returns:
        int: Estimated wait time in minutes.
    """
    if current_hour is None:
        current_hour = datetime.now().hour

    # Peak rush hour multiplier (8-10 AM morning rush, 2-3 PM afternoon rush)
    is_rush_hour = (8 <= current_hour <= 10) or (14 <= current_hour <= 15)
    rush_multiplier = 1.25 if is_rush_hour else 1.0

    base_minutes = 3.0
    queue_impact = active_orders_count * 2.2
    complexity_impact = (item_count - 1) * 1.5 if item_count > 1 else 0

    total_wait = (base_minutes + queue_impact + complexity_impact) * rush_multiplier
    return max(3, min(25, round(total_wait)))
