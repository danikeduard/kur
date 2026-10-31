# LinguaPath

LinguaPath is an adaptive AI English tutor prototype for coursework in
economic cybernetics. Learners choose a self-assessed CEFR level; the system
then estimates grammar, vocabulary, and writing levels from valid chat
messages. The first five valid messages receive double update weight.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
flask --app wsgi db init
flask --app wsgi db migrate -m "initial schema"
flask --app wsgi db upgrade
flask --app wsgi run
```

Set a real `SECRET_KEY`, PostgreSQL `DATABASE_URL`, and `GROQ_API_KEY` in
`.env`. The test suite uses in-memory SQLite only. For Neon deployments,
`neon deploy` pulls the PostgreSQL connection variables into `.env`; the
application uses `DATABASE_URL` through Flask-SQLAlchemy and psycopg2.

## Online PostgreSQL bootstrap

For the standalone PostgreSQL schema requested by the coursework, initialize
the online database once with:

```powershell
python scripts/init_online_db.py
```

The script reads `DATABASE_URL` and executes the idempotent
[init_online_db.sql](./scripts/init_online_db.sql). It is safe to run again
after a deployment or restart: tables, indexes, CEFR levels, and error-topic
seeds are protected with `IF NOT EXISTS`/`ON CONFLICT`. Alternatively, use
`psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/init_online_db.sql`.

This bootstrap schema is the canonical PostgreSQL design with `users`,
`displayed_level`, `topic_id`, and `skipped`. The current Flask prototype's
SQLAlchemy models are still used by the SQLite test harness; align the models
and create a migration before switching the running application to this
schema.

The Flask application tables are initialized separately with:

```powershell
python scripts/init_app_db.py
```

## Project map

- `app/rating.py`: pure level model and validity rules
- `app/evaluator.py`, `app/tutor.py`: validated LLM integrations
- `app/routes.py`: authentication-adjacent pages and chat/progress APIs
- `scripts/`: metrics, convergence, and SUS reports using logged data
- `docs/`: architecture, formal level model, and deployment guide

## Roadmap

Reading exercises, listening/TTS, spaced repetition, Open WebUI, and
LMS/Moodle integration are intentionally future work.
