# Architecture

LinguaPath is a Flask application factory with blueprints for authentication
and pages/API routes. SQLAlchemy persists accounts, conversation messages,
ratings, error observations, feedback, and API metrics. The chat endpoint
submits evaluator and tutor calls concurrently; the tutor sees ratings from
before the current turn, while the evaluator updates ratings afterward.
Jinja renders the shell and vanilla JavaScript calls JSON endpoints without
injecting user or model content as HTML.
