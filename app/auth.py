"""Registration, login, and account lifecycle routes."""

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from .extensions import db, login_manager
from .models import SkillRating, User
from .rating import LEVELS, initial_ratings

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.chat"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        level = request.form.get("level", "").upper()
        if not EMAIL_RE.match(email) or len(password) < 8 or level not in LEVELS:
            flash("Use a valid email, an 8-character password, and choose a CEFR level.", "error")
            return render_template("register.html", levels=LEVELS)
        if db.session.scalar(db.select(User).filter_by(email=email)):
            flash("An account with that email already exists.", "error")
            return render_template("register.html", levels=LEVELS)
        user = User(email=email, self_level=level, is_admin=email in __import__("flask").current_app.config["ADMIN_EMAILS"])
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        for skill, rating in initial_ratings(level).items():
            db.session.add(SkillRating(user_id=user.id, skill=skill, rating=rating))
        db.session.commit()
        login_user(user)
        return redirect(url_for("main.chat"))
    return render_template("register.html", levels=LEVELS)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = db.session.scalar(db.select(User).filter_by(email=request.form.get("email", "").strip().lower()))
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            login_user(user, remember=True)
            return redirect(url_for("main.chat"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
