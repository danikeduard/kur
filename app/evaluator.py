"""Groq evaluator integration and response validation."""

import json
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .models import ApiMetric


class SkillObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = Field(pattern=r"^[ABC][12]$")
    confidence: float = Field(ge=0, le=1)


class ErrorObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str
    type: str
    original: str
    corrected: str


class Evaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_english: bool
    skills: dict[str, SkillObservation]
    errors: list[ErrorObservation] = []


SYSTEM_PROMPT = """Evaluate the learner's English message. Return only strict JSON with is_english,
skills for grammar, vocab, writing (each level A1-C2 and confidence 0..1), and errors.
Do not include markdown or extra keys."""


def evaluate_message(client: Any, model: str, content: str, user_id: int, db: Any) -> Evaluation | None:
    """Call Groq once, retry invalid JSON once, and record API timing."""
    for attempt in range(2):
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": content}],
            )
            raw = response.choices[0].message.content
            result = Evaluation.model_validate(json.loads(raw))
            _record_metric(db, ApiMetric(user_id=user_id, kind="evaluator", latency_ms=(time.perf_counter() - started) * 1000))
            return result
        except (json.JSONDecodeError, ValidationError, KeyError, TypeError, AttributeError):
            if attempt == 1:
                _record_metric(db, ApiMetric(user_id=user_id, kind="evaluator", latency_ms=(time.perf_counter() - started) * 1000))
                return None
    return None


def _record_metric(db: Any, metric: ApiMetric) -> None:
    db.session.add(metric)
    db.session.commit()
