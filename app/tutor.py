"""Adaptive tutor prompt construction and Groq response generation."""

import time
from typing import Any

from .models import ApiMetric, ErrorLog, Message, SkillRating
from .rating import rating_to_level

STYLE_GUIDE = {
    "A1": "Use very short sentences, common words, and one idea at a time.",
    "A2": "Use everyday vocabulary, short explanations, and simple past/future examples.",
    "B1": "Use clear paragraphs, practical idioms, and explain useful grammar briefly.",
    "B2": "Use varied sentence structures, nuanced vocabulary, and ask follow-up questions.",
    "C1": "Use precise, flexible language and discuss abstract ideas naturally.",
    "C2": "Use sophisticated nuance, register, collocations, and subtle distinctions.",
}


def build_system_prompt(user_id: int, db: Any) -> str:
    """Build a prompt from current ratings and recent weak topics."""
    ratings = {row.skill: rating_to_level(row.rating) for row in db.session.scalars(db.select(SkillRating).filter_by(user_id=user_id))}
    errors = db.session.scalars(
        db.select(ErrorLog.topic).filter_by(user_id=user_id).order_by(ErrorLog.ts.desc()).limit(5)
    ).all()
    overall = ratings.get("writing", "B1")
    style = STYLE_GUIDE[overall]
    topics = ", ".join(dict.fromkeys(errors)) or "none recorded yet"
    return f"""You are a friendly English tutor. Skill levels: {ratings}. {style}
Weak topics to revisit: {topics}.
Use the Socratic method: hints before direct answers; give the direct answer after two failed hints
or when explicitly requested. Correct at most two mistakes per reply, then continue naturally.
Occasionally give a short exercise about a weak topic. Use a few emojis, and stay under 120 words
for A1-A2 or 200 words for other levels unless asked."""


def tutor_reply(client: Any, model: str, user_id: int, content: str, history: list[Message], db: Any) -> str:
    """Generate a tutor response using only the latest twelve stored messages."""
    messages = [{"role": "system", "content": build_system_prompt(user_id, db)}]
    messages.extend({"role": row.role, "content": row.content} for row in history[-12:])
    messages.append({"role": "user", "content": content})
    started = time.perf_counter()
    response = client.chat.completions.create(model=model, temperature=0.4, messages=messages)
    reply = response.choices[0].message.content
    db.session.add(ApiMetric(user_id=user_id, kind="tutor", latency_ms=(time.perf_counter() - started) * 1000))
    db.session.commit()
    return reply
