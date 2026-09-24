"""Connection helpers and project paths. Everything else imports from here."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt_project"
MODELS_DIR = DBT_DIR / "models"
STATE_DIR = PROJECT_ROOT / ".state"

load_dotenv(PROJECT_ROOT / ".env")


def dsn() -> dict:
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5433")),
        "user": os.getenv("PGUSER", "lineage"),
        "password": os.getenv("PGPASSWORD", "lineage"),
        "dbname": os.getenv("PGDATABASE", "warehouse"),
    }


def freshness_tolerance_hours() -> int:
    return int(os.getenv("FRESHNESS_TOLERANCE_HOURS", "24"))


@contextmanager
def connect(autocommit: bool = True):
    conn = psycopg2.connect(**dsn())
    conn.autocommit = autocommit
    try:
        yield conn
    finally:
        conn.close()


def execute(sql: str, params: tuple | None = None) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)


def query(sql: str, params: tuple | None = None) -> list[tuple]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def dbt_env() -> dict:
    env = os.environ.copy()
    env.setdefault("DBT_PROFILES_DIR", str(DBT_DIR))
    for key, value in dsn().items():
        env["PG" + {"dbname": "DATABASE"}.get(key, key.upper())] = str(value)
    return env