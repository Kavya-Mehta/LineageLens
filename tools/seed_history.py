"""Backfill 14 days of nightly run history before today.

These rows are synthesized, not observed. Only today's runs come
from real dbt artifacts. The backfill exists so the agent has a
baseline to compare against.

Includes two transient failures followed by successful retries,
so a failure in the log is not by itself evidence of a problem.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from db import connect

SEED = 4242
DAYS = 14
NIGHTLY_HOUR = 2

MODELS = [
    "stg_customers", "stg_products", "stg_orders", "stg_order_items", "stg_payments",
    "int_order_totals", "int_payments_by_order", "int_customer_orders",
    "fct_orders", "fct_daily_revenue", "dim_customers", "fct_payment_reconciliation",
]

BASELINE_ROWS = {
    "stg_customers": 120, "stg_products": 24, "stg_orders": 850,
    "stg_order_items": 2100, "stg_payments": 720,
    "int_order_totals": 850, "int_payments_by_order": 700, "int_customer_orders": 120,
    "fct_orders": 850, "fct_daily_revenue": 60, "dim_customers": 120,
    "fct_payment_reconciliation": 850,
}

TRANSIENT_FAILURES = [(9, "stg_products"), (4, "dim_customers")]


def backfill() -> int:
    rng = random.Random(SEED)
    now = datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    inserted = 0
    transient = {(d, m) for d, m in TRANSIENT_FAILURES}

    with connect(autocommit=False) as conn, conn.cursor() as cur:
        for days_ago in range(DAYS, 0, -1):
            run_start = midnight - timedelta(days=days_ago)
            run_start = run_start.replace(hour=NIGHTLY_HOUR, minute=rng.randint(0, 4))
            invocation = f"backfill-{run_start:%Y%m%d}"
            offset = 0

            for model in MODELS:
                started = run_start + timedelta(seconds=offset)
                duration = rng.randint(2, 25)
                offset += duration + rng.randint(1, 4)
                completed = started + timedelta(seconds=duration)
                rows = int(BASELINE_ROWS[model] * rng.uniform(0.97, 1.03))

                if (days_ago, model) in transient:
                    cur.execute(
                        """insert into meta.run_history
                            (invocation_id, model_name, status, started_at,
                             completed_at, rows_affected, error_message)
                           values (%s, %s, 'error', %s, %s, null, %s)""",
                        (invocation, model, started, completed,
                         "could not obtain connection from pool"),
                    )
                    inserted += 1
                    started = started + timedelta(minutes=20)
                    completed = started + timedelta(seconds=duration)
                    invocation_used = f"{invocation}-retry"
                else:
                    invocation_used = invocation

                cur.execute(
                    """insert into meta.run_history
                        (invocation_id, model_name, status, started_at,
                         completed_at, rows_affected, error_message)
                       values (%s, %s, 'success', %s, %s, %s, null)""",
                    (invocation_used, model, started, completed, rows),
                )
                cur.execute(
                    """insert into meta.materialization_log
                        (model_name, materialized_at, row_count, invocation_id)
                       values (%s, %s, %s, %s)
                       on conflict do nothing""",
                    (model, completed, rows, invocation_used),
                )
                inserted += 1

        conn.commit()
    return inserted


if __name__ == "__main__":
    print(f"backfilled {backfill()} run_history rows across {DAYS} days")