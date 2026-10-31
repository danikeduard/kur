"""Database models for users, tutoring interactions, and research data."""

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(UserMixin, db.Model):
    __tablename__ = "app_user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    self_level = db.Column(db.String(2), nullable=False)
    daily_cap_override = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    @property
    def daily_cap(self) -> int:
        from flask import current_app

        return self.daily_cap_override or current_app.config["DAILY_MESSAGE_CAP"]


class SkillRating(db.Model):
    __tablename__ = "app_skill_rating"

    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), primary_key=True)
    skill = db.Column(db.String(20), primary_key=True)
    rating = db.Column(db.Float, nullable=False)
    n_updates = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Message(db.Model):
    __tablename__ = "app_message"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ts = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    is_valid_for_rating = db.Column(db.Boolean, default=False, nullable=False)
    msg_index = db.Column(db.Integer, nullable=True)


class RatingEvent(db.Model):
    __tablename__ = "app_rating_event"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("app_message.id"), nullable=False)
    skill = db.Column(db.String(20), nullable=False)
    rating_before = db.Column(db.Float, nullable=False)
    rating_after = db.Column(db.Float, nullable=False)
    observed_level = db.Column(db.String(2), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    ts = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ErrorLog(db.Model):
    __tablename__ = "app_error_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("app_message.id"), nullable=True)
    topic = db.Column(db.String(80), nullable=False)
    error_type = db.Column(db.String(30), nullable=False)
    original = db.Column(db.Text, nullable=False)
    corrected = db.Column(db.Text, nullable=False)
    ts = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ApiMetric(db.Model):
    __tablename__ = "app_api_metric"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=True)
    kind = db.Column(db.String(20), nullable=False)
    latency_ms = db.Column(db.Float, nullable=False)
    tokens_in = db.Column(db.Integer, nullable=True)
    tokens_out = db.Column(db.Integer, nullable=True)
    est_cost_usd = db.Column(db.Float, nullable=True)
    ts = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Feedback(db.Model):
    __tablename__ = "app_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=False, index=True)
    sus_answers = db.Column(db.JSON, nullable=False)
    free_text = db.Column(db.Text, nullable=True)
    ts = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
