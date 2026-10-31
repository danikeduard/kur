"""Public pages and chat API."""

import csv
import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from groq import Groq

from .evaluator import evaluate_message
from .extensions import db, limiter
from .models import ApiMetric, ErrorLog, Feedback, Message, RatingEvent, SkillRating, User
from .rating import is_valid_message, rating_to_level, update_rating

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/chat")
@login_required
def chat():
    return render_template("chat.html")


@main_bp.get("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.get("/progress")
@login_required
def progress():
    events = db.session.scalars(
        db.select(RatingEvent).where(RatingEvent.user_id == current_user.id).order_by(RatingEvent.ts)
    ).all()
    errors = db.session.execute(
        db.select(ErrorLog.topic, db.func.count(ErrorLog.id)).where(ErrorLog.user_id == current_user.id)
        .group_by(ErrorLog.topic).order_by(db.func.count(ErrorLog.id).desc()).limit(5)
    ).all()
    ratings = {row.skill: rating_to_level(row.rating) for row in db.session.scalars(
        db.select(SkillRating).filter_by(user_id=current_user.id)
    )}
    return render_template("progress.html", events=events, weak_topics=errors, levels=ratings,
                           total_messages=db.session.scalar(db.select(db.func.count(Message.id)).filter_by(user_id=current_user.id)))


@main_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        answers = [request.form.get(f"q{i}", "") for i in range(1, 11)]
        if not all(answer in {"1", "2", "3", "4", "5"} for answer in answers):
            flash("Please answer all ten questions.", "error")
        else:
            db.session.add(Feedback(user_id=current_user.id, sus_answers=answers,
                                    free_text=request.form.get("free_text", "")[:4000]))
            db.session.commit()
            flash("Thank you for your feedback!", "success")
            return redirect(url_for("main.chat"))
    return render_template("feedback.html")


@main_bp.post("/account/delete")
@login_required
def delete_account():
    user_id = current_user.id
    for model in (RatingEvent, ErrorLog, Message, SkillRating, ApiMetric, Feedback):
        db.session.execute(db.delete(model).where(model.user_id == user_id))
    db.session.execute(db.delete(User).where(User.id == user_id))
    db.session.commit()
    from flask_login import logout_user
    logout_user()
    flash("Your account and stored data have been deleted.", "success")
    return redirect(url_for("main.index"))


@main_bp.get("/admin/export")
@login_required
def admin_export():
    if not current_user.is_admin:
        return jsonify(error="Not found"), 404
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["dataset", "user_hash", "kind", "skill", "rating_before", "rating_after",
                     "latency_ms", "tokens_in", "tokens_out", "est_cost_usd", "ts"])
    for event in db.session.scalars(db.select(RatingEvent)):
        writer.writerow(["rating_event", _hash_user(event.user_id), "", event.skill, event.rating_before,
                         event.rating_after, "", "", "", "", event.ts.isoformat()])
    for metric in db.session.scalars(db.select(ApiMetric)):
        writer.writerow(["api_metric", _hash_user(metric.user_id), metric.kind, "", "", "",
                         metric.latency_ms, metric.tokens_in, metric.tokens_out, metric.est_cost_usd,
                         metric.ts.isoformat()])
    for item in db.session.scalars(db.select(Feedback)):
        writer.writerow(["feedback", _hash_user(item.user_id), "", "", "", "", "", "", "", "", item.ts.isoformat()])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=linguapath-export.csv"})


def _hash_user(user_id: int | None) -> str:
    return hashlib.sha256(f"{current_app.config['SECRET_KEY']}:{user_id}".encode()).hexdigest()[:16]


@main_bp.post("/api/chat")
@login_required
@limiter.limit(lambda: current_app.config["RATE_LIMIT_CHAT"])
def api_chat():
    payload = request.get_json(silent=True) or {}
    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip() or len(content) > 4000:
        return jsonify(error="Please send a message under 4,000 characters."), 400
    today = datetime.now(UTC).date()
    sent_today = db.session.scalar(
        db.select(db.func.count(Message.id)).where(
            Message.user_id == current_user.id, Message.role == "user", db.func.date(Message.ts) == today
        )
    )
    if sent_today >= current_user.daily_cap:
        return jsonify(error="Your daily message limit has been reached. Please try again tomorrow."), 429

    valid = is_valid_message(content)
    message = Message(user_id=current_user.id, role="user", content=content, is_valid_for_rating=valid)
    db.session.add(message)
    db.session.flush()
    valid_index = db.session.scalar(
        db.select(db.func.count(Message.id)).where(
            Message.user_id == current_user.id, Message.role == "user", Message.is_valid_for_rating.is_(True)
        )
    ) if valid else 0
    message.msg_index = valid_index if valid else None
    db.session.commit()

    if not current_app.config.get("GROQ_API_KEY"):
        return jsonify(error="The tutor is not configured yet."), 503
    app = current_app._get_current_object()
    client = Groq(api_key=current_app.config["GROQ_API_KEY"])
    history = db.session.scalars(
        db.select(Message).where(Message.user_id == current_user.id).order_by(Message.ts.desc()).limit(12)
    ).all()
    with ThreadPoolExecutor(max_workers=2) as executor:
        evaluation_future = executor.submit(
            _run_evaluator, app, client, current_app.config["LLM_MODEL"], content, current_user.id
        ) if valid else None
        tutor_future = executor.submit(
            _run_tutor, app, client, current_app.config["LLM_MODEL"], current_user.id, content, list(reversed(history))
        )
        evaluation = evaluation_future.result() if evaluation_future else None
        try:
            reply = tutor_future.result()
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
            return jsonify(error="The tutor is temporarily unavailable. Please try again."), 503

    changed = []
    if evaluation and evaluation.is_english and valid:
        for skill, observation in evaluation.skills.items():
            rating = db.session.get(SkillRating, (current_user.id, skill))
            if rating is None:
                continue
            before_level = rating_to_level(rating.rating)
            before = rating.rating
            rating.rating, weight = update_rating(rating.rating, observation.level, observation.confidence, valid_index)
            rating.n_updates += observation.confidence >= 0.3
            after_level = rating_to_level(rating.rating)
            db.session.add(RatingEvent(user_id=current_user.id, message_id=message.id, skill=skill,
                                       rating_before=before, rating_after=rating.rating,
                                       observed_level=observation.level, confidence=observation.confidence,
                                       weight=weight))
            if before_level != after_level:
                changed.append({"skill": skill, "level": after_level})
        for error in evaluation.errors:
            db.session.add(ErrorLog(user_id=current_user.id, message_id=message.id, topic=error.topic,
                                    error_type=error.type, original=error.original, corrected=error.corrected))
    db.session.add(Message(user_id=current_user.id, role="assistant", content=reply))
    db.session.commit()
    levels = {row.skill: rating_to_level(row.rating) for row in db.session.scalars(
        db.select(SkillRating).filter_by(user_id=current_user.id)
    )}
    return jsonify(reply=reply, levels=levels, level_changed=changed)


def _run_evaluator(app, client, model, content, user_id):
    with app.app_context():
        return evaluate_message(client, model, content, user_id, db)


def _run_tutor(app, client, model, user_id, content, history):
    from .tutor import tutor_reply
    with app.app_context():
        return tutor_reply(client, model, user_id, content, history, db)
