"""LinguaPath Flask application factory."""

import logging
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from flask import Flask
from groq import APIError

from .extensions import csrf, db, limiter, login_manager, migrate
from .i18n import install_i18n


def create_app(config_class=None) -> Flask:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not getattr(config_class, "TESTING", False):
        dotenv = dotenv_values(env_path)
        for name in ("LLM_MODEL", "LLM_MODEL_EVALUATOR", "LLM_MODEL_TITLE", "LLM_MODEL_EXPLAIN"):
            if name in os.environ and dotenv.get(name) and os.environ[name] != dotenv[name]:
                logging.getLogger(__name__).warning("OS environment %s differs from %s", name, env_path.resolve())
        load_dotenv(env_path, override=True)
    from .config import Config

    config_class = config_class or Config
    app = Flask(__name__)
    app.config.from_object(config_class)
    if not getattr(config_class, "TESTING", False):
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
        app.config["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY")
        app.config["LLM_PROVIDER"] = os.environ.get("LLM_PROVIDER", app.config["LLM_PROVIDER"])
    model = (app.config.get("LLM_MODEL") if getattr(config_class, "TESTING", False)
             else os.environ.get("LLM_MODEL", "")).strip()
    if not model:
        raise RuntimeError("LLM_MODEL must be configured with a non-empty model name.")
    app.config["LLM_MODEL"] = model
    for role in ("EVALUATOR", "TITLE", "EXPLAIN"):
        app.config[f"LLM_MODEL_{role}"] = os.environ.get(f"LLM_MODEL_{role}", model).strip() or model
    app.config["ENV_FILE_PATH"] = str(env_path.resolve())
    logging.getLogger(__name__).info("dotenv file=%s", env_path.resolve())
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be configured")

    db.init_app(app)
    install_i18n(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    from config.llm import get_model, log_effective_models
    with app.app_context():
        log_effective_models()
    if not app.config.get("TESTING") and not app.config.get("DEMO_MODE") and app.config.get("GROQ_API_KEY"):
        try:
            from groq import Groq
            available = {item.id for item in Groq(api_key=app.config["GROQ_API_KEY"]).models.list().data}
            for role in ("tutor", "evaluator", "title", "explain"):
                with app.app_context():
                    configured = get_model(role)
                if configured not in available:
                    logging.getLogger(__name__).warning("configured LLM model is unavailable role=%s model=%s", role, configured)
        except (APIError, OSError, RuntimeError, ValueError) as error:
            logging.getLogger(__name__).warning("could not check Groq model availability: %s", type(error).__name__)

    from .auth import auth_bp
    from .routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return app


from . import models  # noqa: F401
