# Deployment

1. Create a Supabase or Neon PostgreSQL database and copy its pooled
   `DATABASE_URL` connection string, including `sslmode=require`.
2. Set `SECRET_KEY`, `DATABASE_URL`, `GROQ_API_KEY`, `LLM_MODEL`,
   `DAILY_MESSAGE_CAP`, `RATE_LIMIT_CHAT`, and `ADMIN_EMAILS` in Render/Fly.io.
3. Use a release command `flask --app wsgi db upgrade` and a start command
   `gunicorn --bind 0.0.0.0:$PORT wsgi:app`.
4. Configure the custom domain and enable the platform's managed HTTPS.
5. Verify `/healthz`, registration, and a mocked/staging chat before opening
   the application to users.
