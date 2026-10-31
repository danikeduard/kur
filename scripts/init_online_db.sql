-- LinguaPath PostgreSQL bootstrap schema.
-- Safe to run repeatedly: all DDL and seed inserts are idempotent.
-- Run with:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/init_online_db.sql

BEGIN;

CREATE TABLE IF NOT EXISTS cefr_level (
    code        TEXT PRIMARY KEY,
    ord         SMALLINT NOT NULL UNIQUE CHECK (ord BETWEEN 0 AND 5),
    center      INT NOT NULL UNIQUE,
    lower_bound INT,
    upper_bound INT,
    CHECK (lower_bound IS NULL OR upper_bound IS NULL OR lower_bound < upper_bound)
);

INSERT INTO cefr_level (code, ord, center, lower_bound, upper_bound)
VALUES
    ('A1', 0, 600,  NULL, 700),
    ('A2', 1, 800,  700,  900),
    ('B1', 2, 1000, 900, 1100),
    ('B2', 3, 1200, 1100, 1300),
    ('C1', 4, 1400, 1300, 1500),
    ('C2', 5, 1600, 1500, NULL)
ON CONFLICT (code) DO UPDATE SET
    ord = EXCLUDED.ord,
    center = EXCLUDED.center,
    lower_bound = EXCLUDED.lower_bound,
    upper_bound = EXCLUDED.upper_bound;

CREATE TABLE IF NOT EXISTS error_topic (
    id    SERIAL PRIMARY KEY,
    code  TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    area  TEXT NOT NULL CHECK (area IN ('grammar', 'vocab', 'writing'))
);

INSERT INTO error_topic (code, title, area)
VALUES
    ('articles', 'Articles', 'grammar'),
    ('present_simple', 'Present Simple', 'grammar'),
    ('present_continuous', 'Present Continuous', 'grammar'),
    ('past_simple', 'Past Simple', 'grammar'),
    ('past_continuous', 'Past Continuous', 'grammar'),
    ('present_perfect', 'Present Perfect', 'grammar'),
    ('past_perfect', 'Past Perfect', 'grammar'),
    ('future_forms', 'Future Forms', 'grammar'),
    ('modal_verbs', 'Modal Verbs', 'grammar'),
    ('conditionals', 'Conditionals', 'grammar'),
    ('reported_speech', 'Reported Speech', 'grammar'),
    ('passive_voice', 'Passive Voice', 'grammar'),
    ('relative_clauses', 'Relative Clauses', 'grammar'),
    ('gerunds_infinitives', 'Gerunds and Infinitives', 'grammar'),
    ('prepositions', 'Prepositions', 'grammar'),
    ('word_order', 'Word Order', 'grammar'),
    ('subject_verb_agreement', 'Subject-Verb Agreement', 'grammar'),
    ('countable_uncountable', 'Countable and Uncountable Nouns', 'grammar'),
    ('comparatives_superlatives', 'Comparatives and Superlatives', 'grammar'),
    ('phrasal_verbs', 'Phrasal Verbs', 'vocab'),
    ('collocations', 'Collocations', 'vocab'),
    ('word_choice', 'Word Choice', 'vocab'),
    ('false_friends', 'False Friends', 'vocab'),
    ('word_formation', 'Word Formation', 'vocab'),
    ('spelling', 'Spelling', 'writing'),
    ('punctuation', 'Punctuation', 'writing'),
    ('capitalization', 'Capitalization', 'writing'),
    ('coherence', 'Coherence', 'writing'),
    ('register', 'Register', 'writing'),
    ('sentence_structure', 'Sentence Structure', 'writing')
ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    area = EXCLUDED.area;

CREATE TABLE IF NOT EXISTS users (
    id                 BIGSERIAL PRIMARY KEY,
    email              TEXT NOT NULL UNIQUE,
    password_hash      TEXT NOT NULL,
    self_level         TEXT NOT NULL REFERENCES cefr_level(code),
    valid_msg_count    INT NOT NULL DEFAULT 0 CHECK (valid_msg_count >= 0),
    daily_cap_override INT,
    is_admin           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skill_rating (
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill           TEXT NOT NULL CHECK (skill IN ('grammar', 'vocab', 'writing')),
    rating          DOUBLE PRECISION NOT NULL,
    displayed_level TEXT NOT NULL REFERENCES cefr_level(code),
    n_updates       INT NOT NULL DEFAULT 0 CHECK (n_updates >= 0),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, skill)
);

CREATE TABLE IF NOT EXISTS message (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role                TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content             TEXT NOT NULL,
    is_valid_for_rating BOOLEAN NOT NULL DEFAULT FALSE,
    msg_index           INT,
    ts                  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_message_user_ts ON message(user_id, ts DESC);

CREATE TABLE IF NOT EXISTS rating_event (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id      BIGINT NOT NULL REFERENCES message(id) ON DELETE CASCADE,
    skill           TEXT NOT NULL CHECK (skill IN ('grammar', 'vocab', 'writing')),
    observed_level  TEXT NOT NULL REFERENCES cefr_level(code),
    confidence      REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    weight          REAL NOT NULL CHECK (weight IN (1.0, 2.0)),
    rating_before   DOUBLE PRECISION NOT NULL,
    rating_after    DOUBLE PRECISION NOT NULL,
    skipped         BOOLEAN NOT NULL DEFAULT FALSE,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_rating_event_user_skill_ts
    ON rating_event(user_id, skill, ts);

CREATE TABLE IF NOT EXISTS error_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id  BIGINT NOT NULL REFERENCES message(id) ON DELETE CASCADE,
    topic_id    INT NOT NULL REFERENCES error_topic(id),
    error_type  TEXT NOT NULL CHECK (error_type IN (
        'grammar', 'vocab', 'spelling', 'word_order', 'preposition', 'article'
    )),
    original    TEXT NOT NULL,
    corrected   TEXT NOT NULL,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_error_user_ts ON error_log(user_id, ts DESC);

CREATE TABLE IF NOT EXISTS api_metric (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT REFERENCES users(id) ON DELETE SET NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('tutor', 'evaluator')),
    latency_ms   INT NOT NULL,
    tokens_in    INT NOT NULL,
    tokens_out   INT NOT NULL,
    est_cost_usd NUMERIC(10, 6) NOT NULL,
    ok           BOOLEAN NOT NULL DEFAULT TRUE,
    ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedback (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    sus_answers JSONB NOT NULL CHECK (jsonb_array_length(sus_answers) = 10),
    free_text   TEXT,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
