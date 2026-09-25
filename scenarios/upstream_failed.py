"""Upstream model failed and new data is stranded. The number IS wrong."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from .base import ScenarioResult, land_new_orders, now, rename_unit_price
from run_dbt import run as run_dbt

NAME = "upstream-failed"
QUESTION = "Revenue on the dashboard looks low for today. Is the number wrong?"
EXPECTED = (
    "Diagnose. stg_order_items failed because raw.order_items.unit_price "
    "no longer exists. int_order_totals, fct_orders and fct_daily_revenue "
    "were skipped, so the mart predates the orders that landed afterwards. "
    "Cite the failing run_id and the _loaded_at of the stranded rows."
)


def apply() -> ScenarioResult:
    landed = land_new_orders(n=14)
    rename_unit_price(to_broken=True)
    run_dbt(command="build")
    return ScenarioResult(
        name=NAME,
        applied_at=now(),
        notes=[
            f"landed {landed} new orders after the last good mart build",
            "renamed raw.order_items.unit_price -> unit_price_usd",
            "ran dbt build; stg_order_items errors, downstream skipped",
        ],
    )