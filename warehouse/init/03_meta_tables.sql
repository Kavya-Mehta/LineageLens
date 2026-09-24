CREATE TABLE meta.run_history (
  run_id         BIGSERIAL PRIMARY KEY,
  invocation_id  TEXT        NOT NULL,
  model_name     TEXT        NOT NULL,
  status         TEXT        NOT NULL CHECK (status IN ('success','error','skipped')),
  started_at     TIMESTAMPTZ NOT NULL,
  completed_at   TIMESTAMPTZ,
  rows_affected  BIGINT,
  error_message  TEXT
);
CREATE INDEX ON meta.run_history (model_name, started_at DESC);

CREATE TABLE meta.materialization_log (
  model_name       TEXT        NOT NULL,
  materialized_at  TIMESTAMPTZ NOT NULL,
  row_count        BIGINT,
  invocation_id    TEXT,
  PRIMARY KEY (model_name, materialized_at)
);

CREATE TABLE meta.column_snapshot (
  snapshot_at   TIMESTAMPTZ NOT NULL,
  table_schema  TEXT NOT NULL,
  table_name    TEXT NOT NULL,
  column_name   TEXT NOT NULL,
  data_type     TEXT NOT NULL,
  PRIMARY KEY (snapshot_at, table_schema, table_name, column_name)
);

CREATE TABLE meta.runbooks (
  runbook_id  SERIAL PRIMARY KEY,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  tags        TEXT[] NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON meta.runbooks USING GIN (to_tsvector('english', title || ' ' || body));

CREATE TABLE meta.incidents (
  incident_id      SERIAL PRIMARY KEY,
  title            TEXT NOT NULL,
  evidence         JSONB NOT NULL,
  idempotency_key  TEXT UNIQUE NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT INSERT, SELECT ON meta.incidents TO lineagelens_rw;
GRANT USAGE, SELECT ON SEQUENCE meta.incidents_incident_id_seq TO lineagelens_rw;