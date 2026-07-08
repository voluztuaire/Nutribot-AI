"""
LLM Service - Groq Backend
Preserves the original function signatures used by routes/chat.py but routes
all generation through Groq (https://console.groq.com). Optional RAG context
from the local food database is still applied when available.
"""

import os
import json
import re
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
SUMMARIZATION_MODEL = os.getenv("GROQ_SUMMARIZATION_MODEL", "llama-3.1-8b-instant")
ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

# Optional food-db context
try:
    from services.food_database import search_foods
    FOOD_DB_AVAILABLE = True
except Exception:
    FOOD_DB_AVAILABLE = False

# Lazy import groq SDK – fall back to raw HTTP if not installed
try:
    from groq import Groq  # type: ignore
    _client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    _USE_SDK = True
except Exception:
    import requests
    _client = None
    _USE_SDK = False


NUTRIBOT_SYSTEM_PROMPT = """You are NutriBot, a smart, friendly AI Meal & Diet Planner.

Personality:
- Friendly, supportive, conversational.
- Always reply in English, regardless of the user's input language.

STRICT SCOPE — you MUST only answer questions related to:
- Meal planning & diet
- Nutrition (calories, protein, carbs, fat, vitamins, minerals)
- Healthy recipes
- Diet tips (weight loss/gain, muscle gain, etc.)
- Foods for specific conditions (with medical disclaimer)

If the user asks anything off-topic (politics, tech, sports unrelated to diet,
entertainment, math, history, etc.), politely decline and steer back to meal
planning.

Rules:
1. NEVER give medical diagnosis.
2. Ask for missing info (age, weight, height, goal, activity) when needed.
3. Always use clean Markdown structure.
4. When RAG <context>...</context> is provided, prioritize those exact values
   over your trained knowledge.
"""


def _chat_completion(messages: List[Dict[str, str]], model: str, temperature: float = 0.7,
                     max_tokens: int = 1500) -> str:
    """Call Groq chat completions."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not configured. Add it to backend-flask/.env"
        )

    if _USE_SDK and _client is not None:
        resp = _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    # HTTP fallback
    import requests
    r = requests.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _build_rag_context(message: str) -> str:
    """Pull a tiny food-DB snippet if available."""
    if not (ENABLE_RAG and FOOD_DB_AVAILABLE):
        return ""
    try:
        # crude keyword scrape
        tokens = re.findall(r"[A-Za-z]{4,}", message)
        query = " ".join(tokens[:3]) if tokens else message[:40]
        foods = search_foods(query, limit=3)
        if not foods:
            return ""
        lines = []
        for f in foods:
            n = f.get("nutrients", {}) or {}
            lines.append(
                f"- {f.get('description', 'food')}: "
                f"{n.get('calories', '?')} kcal, "
                f"P {n.get('protein', '?')}g / C {n.get('carbs', '?')}g / F {n.get('fat', '?')}g"
            )
        return "<context>\n" + "\n".join(lines) + "\n</context>\n"
    except Exception:
        return ""


def _build_messages(message: str, context: Optional[Dict] = None,
                    history: Optional[List[Dict]] = None) -> List[Dict[str, str]]:
    sys = NUTRIBOT_SYSTEM_PROMPT
    if context:
        sys += "\n\nUser profile:\n" + json.dumps(context, ensure_ascii=False)

    msgs: List[Dict[str, str]] = [{"role": "system", "content": sys}]
    for h in (history or [])[-12:]:
        role = h.get("sender") or h.get("role") or "user"
        if role == "ai":
            role = "assistant"
        content = h.get("message") or h.get("content") or ""
        if content:
            msgs.append({"role": role, "content": content})

    rag = _build_rag_context(message)
    user_content = (rag + message) if rag else message
    msgs.append({"role": "user", "content": user_content})
    return msgs


# -------------------- Public API (same names as before) --------------------

def send_message(message: str, context: Optional[Dict] = None,
                 model: Optional[str] = None) -> str:
    return _chat_completion(_build_messages(message, context), model or CHAT_MODEL)


def chat_with_history(message: str, history: List[Dict],
                      context: Optional[Dict] = None,
                      model: Optional[str] = None) -> str:
    return _chat_completion(
        _build_messages(message, context, history), model or CHAT_MODEL
    )


def generate_meal_plan(user_data: Dict) -> str:
    prompt = (
        "Build a detailed, realistic 3-day meal plan in English "
        f"for a user with the following profile: {json.dumps(user_data, ensure_ascii=False)}.\n"
        "Include Breakfast/Lunch/Dinner/Snack, estimated calories per item, "
        "total daily calories, and a short shopping list. Use clean Markdown formatting. "
        "Reply only in English."
    )
    return send_message(prompt, context=user_data)


def summarize_meal_plan(meal_plan_text: str,
                        user_context: Optional[Dict] = None) -> str:
    prompt = f"""Write a CONCISE summary of the meal plan / nutrition conversation below.
Reply only in English. Must include (clean Markdown):
1. **Total Daily Calories & Macros (average)**
2. **Main Menu Items** (2-3 examples)
3. **Diet Notes** (high-protein / low-carb / balanced)
4. **Shopping List** (5-7 key ingredients)

Do not repeat the raw content, only the summary.

-- START --
{meal_plan_text}
-- END --
"""
    msgs = [
        {"role": "system", "content": "You are a concise nutrition summarizer."},
        {"role": "user", "content": prompt},
    ]
    try:
        return _chat_completion(msgs, SUMMARIZATION_MODEL, temperature=0.4, max_tokens=600)
    except Exception as e:
        print(f"summarize_meal_plan error: {e}")
        return "Summary unavailable."


def extract_meal_calendar(meal_plan_text: str) -> List[Dict[str, Any]]:
    """Ask the LLM to extract a structured meal calendar as JSON."""
    prompt = (
        "Extract a structured meal calendar from the following text. "
        "Return ONLY a JSON array, no prose. Each item has: "
        "{day:string, meal:string, name:string, calories:number}.\n\n" + meal_plan_text
    )
    try:
        out = _chat_completion(
            [
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            SUMMARIZATION_MODEL,
            temperature=0.1,
            max_tokens=800,
        )
        match = re.search(r"\[.*\]", out, re.S)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"extract_meal_calendar error: {e}")
    return []
