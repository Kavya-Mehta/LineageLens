"""The metadata needed to answer does not exist. Escalate."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from .base import ScenarioResult, now
from db import connect

NAME = "unanswerable"
WINDOW_DAYS = 3
QUESTION = "Revenue for the last couple of days looks off to me. What happened?"
EXPECTED = (
    "Escalate. There is no run history, no materialization record and no "
    "schema snapshot for the last three days, and no runbook describes an "
    "orchestrator gap. File an incident stating the observation, the exact "
    "window with no metadata, and the fact that root cause is not "
    "determinable from available sources. Do not propose a likely cause."
)


def apply() -> ScenarioResult:
    with connect(autocommit=False) as conn, conn.cursor() as cur:
        cutoff = f"date_trunc('day', now()) - interval '{WINDOW_DAYS - 1} days'"
        cur.execute(f"delete from meta.run_history where started_at >= {cutoff}")
        runs = cur.rowcount
        cur.execute(f"delete from meta.materialization_log where materialized_at >= {cutoff}")
        mats = cur.rowcount
        cur.execute(f"delete from meta.column_snapshot where snapshot_at >= {cutoff}")
        snaps = cur.rowcount
        conn.commit()
    return ScenarioResult(
        name=NAME,
        applied_at=now(),
        notes=[
            f"deleted {runs} run_history rows in the last {WINDOW_DAYS} days",
            f"deleted {mats} materialization_log rows",
            f"deleted {snaps} column_snapshot rows",
            "no dbt run performed",
        ],
    )