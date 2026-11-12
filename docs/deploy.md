# Deployment

1. Create a Supabase or Neon PostgreSQL database and copy its pooled
   `DATABASE_URL` connection string, including `sslmode=require`.
2. Set `SECRET_KEY`, `DATABASE_URL`, `GROQ_API_KEY`, `LLM_MODEL`,
   `DAILY_MESSAGE_CAP`, `RATE_LIMIT_CHAT`, and `ADMIN_EMAILS` in Render/Fly.io.
3. Use the release command `python scripts/init_app_db.py` and a start command
   `gunicorn --bind 0.0.0.0:$PORT wsgi:app`.
   This initializes the same SQLAlchemy `app_*` schema used by local tests;
   do not run the legacy standalone schema script against the same database.
4. Configure the custom domain and enable the platform's managed HTTPS.
5. Verify `/healthz`, registration, and a mocked/staging chat before opening
   the application to users.
