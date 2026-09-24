-- Schemas. dbt writes into analytics_staging / analytics_intermediate / analytics.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS analytics_staging;
CREATE SCHEMA IF NOT EXISTS analytics_intermediate;

-- Two roles. Read-only tools bind to lineagelens_ro.
-- The single write tool (create_incident) binds to lineagelens_rw.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lineagelens_ro') THEN
    CREATE ROLE lineagelens_ro LOGIN PASSWORD 'lineagelens_ro';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lineagelens_rw') THEN
    CREATE ROLE lineagelens_rw LOGIN PASSWORD 'lineagelens_rw';
  END IF;
END
$$;

GRANT USAGE ON SCHEMA raw, meta, analytics, analytics_staging, analytics_intermediate
  TO lineagelens_ro, lineagelens_rw;

ALTER DEFAULT PRIVILEGES IN SCHEMA raw
  GRANT SELECT ON TABLES TO lineagelens_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta
  GRANT SELECT ON TABLES TO lineagelens_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics
  GRANT SELECT ON TABLES TO lineagelens_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_staging
  GRANT SELECT ON TABLES TO lineagelens_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_intermediate
  GRANT SELECT ON TABLES TO lineagelens_ro;

ALTER DEFAULT PRIVILEGES IN SCHEMA raw
  GRANT SELECT ON TABLES TO lineagelens_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta
  GRANT SELECT ON TABLES TO lineagelens_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics
  GRANT SELECT ON TABLES TO lineagelens_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_staging
  GRANT SELECT ON TABLES TO lineagelens_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_intermediate
  GRANT SELECT ON TABLES TO lineagelens_rw;