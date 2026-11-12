# LinguaPath

LinguaPath is an adaptive AI English tutor prototype for coursework in
economic cybernetics. Learners choose a self-assessed CEFR level; the system
then estimates grammar, vocabulary, and writing levels from valid chat
messages. The first five valid messages receive double update weight.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
flask --app wsgi db upgrade
flask --app wsgi run
```

Set a real `SECRET_KEY` and `GROQ_API_KEY` in `.env`. Leave `DATABASE_URL`
commented out for local development: the app stores SQLite data at
`instance/linguapath.db`. The local database enables foreign keys and WAL
mode, so conversation deletion preserves rating and error history correctly.

For a presentation without an external API key, set `DEMO_MODE=true`.

Reset the local database when a clean development database is needed:

```powershell
python scripts/reset_local_db.py --yes
```

Back up the local database with SQLite's online backup API:

```powershell
python scripts/backup_local_db.py
```

To use PostgreSQL later, install the optional driver and set `DATABASE_URL` in
`.env`; no application code changes are required:

```powershell
pip install psycopg2-binary
DATABASE_URL=postgresql://user:password@host:5432/database
```

Schema workflow:

```powershell
flask --app wsgi db migrate -m "describe the model change"
# review the generated migration
flask --app wsgi db upgrade
```

The application does not call `db.create_all()` for schema changes.

## Project map

- `app/rating.py`: pure level model and validity rules
- `app/evaluator.py`, `app/tutor.py`: validated LLM integrations
- `app/routes.py`: authentication-adjacent pages and chat/progress APIs
- `scripts/`: metrics, convergence, and SUS reports using logged data
- `docs/`: architecture, formal level model, and deployment guide
- `docs/user_study.md`: reproducible replay and usability-study protocol

To compare the baseline and adaptive rating models on logged observations:

```powershell
python scripts/replay_models.py
```

The replay reports label changes, mean absolute rating movement, and messages
needed to approach the final estimate. It is intentionally non-causal because
live tutor responses influenced the original messages; use it for model
comparison, not as an evaluation certificate.

## Chat workspace features

The tutor workspace now supports the core interaction patterns expected from
modern AI chat applications:

- searchable, pinnable, archivable, and paginated conversations
- duplicate a conversation to safely branch a practice session
- export a conversation as JSON or Markdown
- rate assistant messages with optional feedback
- organize conversations into folders and tags
- persist reply length, emoji, and theme settings per account
- configure the LLM provider and model on the server; users cannot choose them
- capture provider, model, token, latency, cost, retry, and status telemetry
- keep an auditable chat-turn record for each tutor request
- adaptive tutor replies and CEFR skill tracking remain unchanged

API metrics are server-configured. Rows with `model='allam-2-7b'` are historical
and should be excluded from coursework statistics, for example:

```powershell
python scripts/metrics_report.py --model openai/gpt-oss-120b
```

## Changing the model or provider

Set `LLM_MODEL` and `LLM_PROVIDER` in `.env` for local development. Optional
per-role model variables (`LLM_MODEL_EVALUATOR`, `LLM_MODEL_TITLE`, and
`LLM_MODEL_EXPLAIN`) override the default model for those calls. Restart the
server after changing these values. In production, set the same variables in
the hosting provider's environment settings. Users cannot select a model or
provider in the application.

After deploying the new chat workspace features to an existing PostgreSQL
database, run `python scripts/init_app_db.py` before starting the application
to apply the checked-in Alembic migrations. The current migration removes the
obsolete per-account model, provider, and language preferences while keeping
conversation, rating, and progress data.

## Roadmap

Reading exercises, listening/TTS, spaced repetition, file uploads/RAG, web
search, and LMS/Moodle integration remain future work.
These are intentionally separate from the current tutoring flow so they can be
added with explicit privacy, storage, and cost controls.
