"""A column appeared upstream. Pipeline is green and the number is wrong."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from .base import ScenarioResult, now
from db import connect
from run_dbt import run as run_dbt

NAME = "schema-changed"
QUESTION = "Paid revenue for today looks higher than it should be. Everything ran green."
EXPECTED = (
    "Diagnose. raw.payments gained a refund_amount column between the last "
    "two schema snapshots. stg_payments uses an explicit column list so "
    "refunds are not subtracted and paid_revenue overstates. Every run "
    "succeeded so run status is not the evidence here — the column snapshot "
    "diff is. The payments-schema runbook describes this exact failure mode."
)


def apply() -> ScenarioResult:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "alter table raw.payments add column if not exists "
            "refund_amount numeric(10,2) not null default 0"
        )
        cur.execute(
            """
            update raw.payments
            set refund_amount = round(amount * 0.35, 2),
                _loaded_at = now()
            where paid_at::date = current_date
              and payment_id % 5 = 0
            """
        )
        affected = cur.rowcount
    run_dbt(command="build")
    return ScenarioResult(
        name=NAME,
        applied_at=now(),
        notes=[
            "added raw.payments.refund_amount",
            f"set a partial refund on {affected} of today's payments",
            "ran dbt build; all models succeed, paid_revenue overstates",
        ],
    )