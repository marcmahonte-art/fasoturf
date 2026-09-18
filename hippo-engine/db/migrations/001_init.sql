-- ============================================================
-- Hippo Engine — migration 001 : schéma initial
-- Cible : PostgreSQL 14+ / Supabase
-- Toutes les tables portent une origine explicite (real | demo)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------
-- Référentiels
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS hippodromes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  TEXT UNIQUE,
    name         TEXT NOT NULL,
    country      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS horses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  TEXT UNIQUE,
    name         TEXT NOT NULL,
    sex          TEXT,
    age          INTEGER,
    country      TEXT,
    source       TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('real','demo')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_horses_name ON horses (name);

CREATE TABLE IF NOT EXISTS jockeys (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  TEXT UNIQUE,
    name         TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('real','demo')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trainers (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  TEXT UNIQUE,
    name         TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('real','demo')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- Courses
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS races (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id        TEXT UNIQUE,
    date               DATE NOT NULL,
    start_time         TIME,
    hippodrome         TEXT NOT NULL,
    country            TEXT,
    discipline         TEXT,
    race_type          TEXT,
    distance           INTEGER,
    terrain            TEXT,
    prize              NUMERIC(14,2),
    number_of_runners  INTEGER,
    status             TEXT NOT NULL DEFAULT 'scheduled'
                       CHECK (status IN ('scheduled','open','live','finished','cancelled')),
    source             TEXT NOT NULL DEFAULT 'real' CHECK (source IN ('real','demo')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_races_date ON races (date DESC);
CREATE INDEX IF NOT EXISTS idx_races_hippodrome ON races (hippodrome);

-- ------------------------------------------------------------
-- Partants
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS race_runners (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id           UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    horse_id          UUID NOT NULL REFERENCES horses(id) ON DELETE RESTRICT,
    number            INTEGER NOT NULL,
    draw              INTEGER,
    weight            NUMERIC(6,2),
    official_rating   NUMERIC(6,2),
    jockey_id         UUID REFERENCES jockeys(id) ON DELETE SET NULL,
    trainer_id        UUID REFERENCES trainers(id) ON DELETE SET NULL,
    morning_odds      NUMERIC(10,3),
    current_odds      NUMERIC(10,3),
    final_odds        NUMERIC(10,3),
    status            TEXT NOT NULL DEFAULT 'declared'
                      CHECK (status IN ('declared','non_runner','withdrawn')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (race_id, number)
);
CREATE INDEX IF NOT EXISTS idx_runners_race ON race_runners (race_id);
CREATE INDEX IF NOT EXISTS idx_runners_horse ON race_runners (horse_id);

-- ------------------------------------------------------------
-- Historique cheval
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS horse_results (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    horse_id         UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    race_id          UUID REFERENCES races(id) ON DELETE SET NULL,
    finish_position  INTEGER,
    distance         INTEGER,
    terrain          TEXT,
    weight           NUMERIC(6,2),
    draw             INTEGER,
    official_rating  NUMERIC(6,2),
    jockey_id        UUID REFERENCES jockeys(id) ON DELETE SET NULL,
    trainer_id       UUID REFERENCES trainers(id) ON DELETE SET NULL,
    odds             NUMERIC(10,3),
    date             DATE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_horse_results_horse_date ON horse_results (horse_id, date DESC);

-- ------------------------------------------------------------
-- Cotes (historique complet pour détecter le mouvement)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS odds_history (
    id          BIGSERIAL PRIMARY KEY,
    race_id     UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    runner_id   UUID NOT NULL REFERENCES race_runners(id) ON DELETE CASCADE,
    odds        NUMERIC(10,3) NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    source      TEXT NOT NULL DEFAULT 'pmu'
);
CREATE INDEX IF NOT EXISTS idx_odds_history_runner_ts ON odds_history (runner_id, timestamp);

-- ------------------------------------------------------------
-- Prédictions
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS predictions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id            UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    model_version      TEXT NOT NULL,
    prediction_version TEXT NOT NULL,
    data_timestamp     TIMESTAMPTZ NOT NULL,
    rank_score         NUMERIC(6,2),
    top3_probability   NUMERIC(6,4),
    top5_probability   NUMERIC(6,4),
    win_probability    NUMERIC(6,4),
    catboost_probability NUMERIC(6,4),
    value_score        NUMERIC(8,4),
    final_score        NUMERIC(6,2),
    confidence         TEXT CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    data_quality       TEXT CHECK (data_quality IN ('DATA_COMPLETE','DATA_PARTIAL','DATA_INSUFFICIENT')),
    status             TEXT NOT NULL DEFAULT 'published'
                       CHECK (status IN ('draft','published','settled')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (race_id, prediction_version)
);
CREATE INDEX IF NOT EXISTS idx_predictions_race ON predictions (race_id);

CREATE TABLE IF NOT EXISTS prediction_selections (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    runner_id     UUID NOT NULL REFERENCES race_runners(id) ON DELETE CASCADE,
    selection_type TEXT NOT NULL
                   CHECK (selection_type IN ('BASE','CHANCE','OUTSIDER','QUINTE','TIERCE','QUARTE','VALUE')),
    rank          INTEGER,
    score         NUMERIC(6,2),
    probability   NUMERIC(6,4),
    confidence    TEXT CHECK (confidence IN ('HIGH','MEDIUM','LOW')),
    UNIQUE (prediction_id, runner_id, selection_type)
);

-- ------------------------------------------------------------
-- Résultats
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS race_results (
    race_id          UUID PRIMARY KEY REFERENCES races(id) ON DELETE CASCADE,
    first            INTEGER,
    second           INTEGER,
    third            INTEGER,
    fourth           INTEGER,
    fifth            INTEGER,
    sixth            INTEGER,
    seventh          INTEGER,
    official_result  JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- Performance des prédictions
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS prediction_performance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id   UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    race_id         UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    tierce_hit      BOOLEAN NOT NULL DEFAULT false,
    quarte_hit      BOOLEAN NOT NULL DEFAULT false,
    quinte_hit      BOOLEAN NOT NULL DEFAULT false,
    base_hit        BOOLEAN NOT NULL DEFAULT false,
    top3_hit        BOOLEAN NOT NULL DEFAULT false,
    top5_hit        BOOLEAN NOT NULL DEFAULT false,
    brier_score     NUMERIC(8,6),
    log_loss        NUMERIC(8,6),
    roi             NUMERIC(8,4),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (prediction_id)
);

-- ------------------------------------------------------------
-- Model registry (#29)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS model_registry (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    version           TEXT NOT NULL,
    algorithm         TEXT NOT NULL,
    training_date     TIMESTAMPTZ,
    training_dataset  TEXT,
    features          JSONB,
    metrics           JSONB,
    status            TEXT NOT NULL DEFAULT 'TRAINED'
                      CHECK (status IN ('TRAINED','ACTIVE','ARCHIVED')),
    artifact_path     TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

-- ------------------------------------------------------------
-- Journal de synchronisation (data-status admin)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sync_runs (
    id            BIGSERIAL PRIMARY KEY,
    job           TEXT NOT NULL,
    provider      TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('ok','partial','failed')),
    rows_affected INTEGER DEFAULT 0,
    message       TEXT,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ
);
