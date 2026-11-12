"""Adaptive tutor prompt construction and Groq response generation."""

import time
from typing import Any

from .models import ErrorLog, Message, SkillRating
from .providers import call_with_fallback, response_usage, reasoning_usage
from .rating import rating_to_level

STYLE_GUIDE = {
    "A1": "Use very short sentences, common words, and one idea at a time.",
    "A2": "Use everyday vocabulary, short explanations, and simple past/future examples.",
    "B1": "Use clear paragraphs, practical idioms, and explain useful grammar briefly.",
    "B2": "Use varied sentence structures, nuanced vocabulary, and ask follow-up questions.",
    "C1": "Use precise, flexible language and discuss abstract ideas naturally.",
    "C2": "Use sophisticated nuance, register, collocations, and subtle distinctions.",
}


def build_system_prompt(ratings: dict[str, str], errors: list[str], settings: dict, plan: dict | None = None) -> str:
    """Build a prompt from preloaded request data."""
    overall = ratings.get("writing", "B1")
    style = STYLE_GUIDE[overall]
    topics = ", ".join(dict.fromkeys(errors)) or "none recorded yet"
    reply_length = settings.get("reply_length", "balanced")
    use_emojis = settings.get("use_emojis", True)
    length_limits = {"concise": "under 80 words", "balanced": "under 160 words", "detailed": "under 260 words"}
    emoji_rule = "Use occasional emojis." if use_emojis else "Do not use emojis."
    plan = plan or {
        "target_skill": None,
        "target_topic": None,
        "action": "diagnostic_conversation",
        "difficulty": overall,
    }
    return f"""You are a friendly English tutor. Skill levels: {ratings}. {style}
Reply in English, and keep learner examples and target-language exercises in English.
Weak topics to revisit: {topics}.
Learning plan: target skill={plan["target_skill"] or "all"}, target topic={plan["target_topic"] or "none"},
action={plan["action"]}, difficulty={plan["difficulty"]}.
Follow this action when natural: a diagnostic conversation asks an open question, targeted diagnostic
checks one uncertain topic, micro_exercise gives one short task, and spaced_review revisits one known
weak topic. Do not expose internal scores or policy names to the learner.
Use the Socratic method: hints before direct answers; give the direct answer after two failed hints
or when explicitly requested. Correct at most two mistakes per reply, then continue naturally.
Occasionally give a short exercise about a weak topic. {emoji_rule} Keep the reply {length_limits[reply_length]}."""


def tutor_reply(client: Any, model: str, content: str, history: list[dict], ratings: dict[str, str],
                errors: list[str], settings: dict, plan: dict, max_tokens: int,
                provider: str = "unknown", fallbacks: list[str] | None = None,
                reasoning: dict[str, str] | None = None) -> dict:
    """Generate a database-free tutor result."""
    messages = [{"role": "system", "content": build_system_prompt(ratings, errors, settings, plan)}]
    messages.extend({"role": row["role"], "content": row["content"]} for row in history[-12:])
    messages.append({"role": "user", "content": content})
    started = time.perf_counter()
    response, answered_model, fallback_used = call_with_fallback(
        client, model, fallbacks or [],
        {"temperature": 0.4, "max_tokens": max_tokens, "messages": messages, **(reasoning or {})}
    )
    reply = response.choices[0].message.content
    tokens_in, tokens_out = response_usage(response)
    return {
        "reply": reply, "latency_ms": (time.perf_counter() - started) * 1000,
        "tokens_in": tokens_in, "tokens_out": tokens_out,
        "reasoning_tokens": reasoning_usage(response), "model": answered_model,
        "provider": provider, "status": "success", "retry_count": 0,
        "fallback_used": fallback_used,
    }
