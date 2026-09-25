"""A batch landed with NULL prices. Row counts are normal, revenue is not."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from .base import ScenarioResult, now
from db import connect
from run_dbt import run as run_dbt

NAME = "silent-nulls"
QUESTION = "Gross revenue for today is down about a third. Did something break?"
EXPECTED = (
    "Diagnose. A batch of raw.order_items rows for today has NULL unit_price, "
    "so line_amount is NULL and SUM() skips those lines. Row counts on "
    "stg_order_items are normal, which is why the row-count check does not "
    "catch it. Cite the null rate and the _loaded_at of the affected batch. "
    "The price-feed runbook covers this."
)


def apply() -> ScenarioResult:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            update raw.order_items oi
            set unit_price = null,
                _loaded_at = now()
            from raw.orders o
            where o.order_id = oi.order_id
              and o.ordered_at::date = current_date
              and oi.order_item_id % 5 < 2
            """
        )
        affected = cur.rowcount
    run_dbt(command="build")
    return ScenarioResult(
        name=NAME,
        applied_at=now(),
        notes=[
            f"nulled unit_price on {affected} of today's order_items",
            "ran dbt build; all models succeed, row counts unchanged",
        ],
    )