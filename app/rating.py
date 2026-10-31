"""Pure adaptive CEFR rating functions.

Ratings are on a 0-2000 scale with CEFR centres spaced by 200 points.
"""

import re

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
CENTERS = {"A1": 600.0, "A2": 800.0, "B1": 1000.0, "B2": 1200.0, "C1": 1400.0, "C2": 1600.0}
ALPHA = 0.12
MAX_STEP = 80.0
SKILL_WEIGHTS = {"grammar": 0.4, "vocab": 0.3, "writing": 0.3}


def level_to_rating(level: str) -> float:
    """Return the centre rating for a CEFR level."""
    normalized = level.upper()
    if normalized not in CENTERS:
        raise ValueError(f"Unknown CEFR level: {level}")
    return CENTERS[normalized]


def rating_to_level(rating: float) -> str:
    """Return the label for a rating using the specified boundaries."""
    if rating < 700:
        return "A1"
    if rating < 900:
        return "A2"
    if rating < 1100:
        return "B1"
    if rating < 1300:
        return "B2"
    if rating < 1500:
        return "C1"
    return "C2"


def initial_ratings(level: str) -> dict[str, float]:
    """Initialize all skills at the declared level centre."""
    center = level_to_rating(level)
    return {skill: center for skill in SKILL_WEIGHTS}


def is_valid_message(content: str) -> bool:
    """Return whether text is eligible for rating updates."""
    text = content.strip()
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    if text.startswith("/") or len(words) < 4:
        return False
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    return sum(char.isascii() for char in letters) / len(letters) >= 0.7


def update_rating(rating: float, observed_level: str, confidence: float, valid_index: int) -> tuple[float, float]:
    """Apply one observation and return (new rating, applied weight)."""
    weight = 2.0 if valid_index <= 5 else 1.0
    if confidence < 0.3:
        return rating, weight
    confidence = max(0.0, min(1.0, confidence))
    delta = ALPHA * weight * confidence * (level_to_rating(observed_level) - rating)
    delta = max(-MAX_STEP, min(MAX_STEP, delta))
    return rating + delta, weight


def displayed_level(rating: float, previous_level: str | None) -> str:
    """Apply 25-point hysteresis when changing a displayed label."""
    candidate = rating_to_level(rating)
    if previous_level is None or candidate == previous_level:
        return candidate
    if LEVELS.index(candidate) > LEVELS.index(previous_level):
        boundary = level_to_rating(candidate) - 100
        return candidate if rating >= boundary + 25 else previous_level
    boundary = level_to_rating(previous_level) - 100
    return candidate if rating <= boundary - 25 else previous_level


def overall_rating(ratings: dict[str, float]) -> float:
    """Return the weighted overall rating."""
    return sum(ratings[skill] * weight for skill, weight in SKILL_WEIGHTS.items())
