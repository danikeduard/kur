import json
from types import SimpleNamespace

import pytest

from app.evaluator import Evaluation, evaluate_message
from app.extensions import db
from app.learning import topic_recommendations, update_topic_mastery
from app.models import ApiMetric, User


def ensure_user():
    user = User(email="evaluator@example.com", self_level="B1")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()
    return user


def response_for(payload):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


def valid_payload():
    return {
        "is_english": True,
        "skills": {
            "grammar": {"level": "B1", "confidence": 0.8},
            "vocab": {"level": "B1", "confidence": 0.7},
            "writing": {"level": "A2", "confidence": 0.4},
        },
        "errors": [
            {
                "topic": "articles",
                "type": "article",
                "original": "some advice",
                "corrected": "advice",
            },
            {
                "topic": "unknown_topic",
                "type": "article",
                "original": "not present",
                "corrected": "fixed",
            },
        ],
        "strengths": [],
    }


def test_evaluation_requires_exact_skill_set():
    payload = valid_payload()
    payload["skills"].pop("writing")
    with pytest.raises(ValueError):
        Evaluation.model_validate(payload)


def test_evaluator_filters_untrusted_error_evidence(app):
    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return response_for(valid_payload())

    with app.app_context():
        user = ensure_user()
        result = evaluate_message(
            FakeClient(),
            "test-model",
            "I need some advice about my studies.",
            user.id,
            db,
        )

    assert result is not None
    assert len(result.errors) == 1
    assert result.errors[0].topic == "articles"


def test_evaluator_retries_invalid_json_and_records_failure(app):
    class BrokenClient:
        class chat:
            class completions:
                calls = 0

                @classmethod
                def create(cls, **kwargs):
                    cls.calls += 1
                    return response_for({"invalid": True})

    with app.app_context():
        user = ensure_user()
        result = evaluate_message(
            BrokenClient(),
            "test-model",
            "I need some advice about my studies.",
            user.id,
            db,
        )
        metric = db.session.scalar(db.select(ApiMetric).order_by(ApiMetric.id.desc()))

    assert result is None
    assert BrokenClient.chat.completions.calls == 2
    assert metric.status == "failure"
    assert metric.retry_count == 1


def test_topic_mastery_tracks_errors_and_strengths(app):
    class Observation:
        def __init__(self, topic, severity=0.6):
            self.topic = topic
            self.severity = severity

    with app.app_context():
        user = ensure_user()
        update_topic_mastery(
            db,
            user.id,
            [Observation("articles", 1.0)],
            [Observation("collocations")],
        )
        rows = topic_recommendations(db, user.id)

    assert [row.topic for row in rows] == ["articles", "collocations"]
    assert rows[0].mastery < 0.5
    assert rows[1].mastery > 0.5
