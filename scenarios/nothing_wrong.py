"""A run failed, but the number is fine. Nobody needs paging."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from .base import ScenarioResult, now, rename_unit_price
from run_dbt import run as run_dbt

NAME = "nothing-wrong"
QUESTION = "I see a failed dbt run this morning. Is today's revenue number affected?"
EXPECTED = (
    "Do not raise an incident. stg_order_items failed, but fct_daily_revenue "
    "was materialized successfully before that failure and no rows have landed "
    "in raw.orders or raw.order_items since. Freshness is within tolerance. "
    "The dashboard is correct. Note the failure still needs fixing."
)


def apply() -> ScenarioResult:
    rename_unit_price(to_broken=True)
    run_dbt(command="build")
    return ScenarioResult(
        name=NAME,
        applied_at=now(),
        notes=[
            "no new upstream data landed",
            "renamed raw.order_items.unit_price -> unit_price_usd",
            "ran dbt build; failure occurs after the last good materialization",
        ],
    )