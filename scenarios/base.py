"""Shared machinery for failure injection.

Design rule: inject a cause, never an answer.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from db import STATE_DIR, connect

STATE_FILE = STATE_DIR / "current.json"


@dataclass
class ScenarioResult:
    name: str
    applied_at: datetime
    notes: list[str] = field(default_factory=list)

    def write_state(self) -> None:
        STATE_DIR.mkdir(exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(
                {
                    "scenario": self.name,
                    "applied_at": self.applied_at.isoformat(),
                    "notes": self.notes,
                },
                indent=2,
            )
        )


def clear_state() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def read_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def now() -> datetime:
    return datetime.now(timezone.utc)


def land_new_orders(n: int = 12, seed: int = 77) -> int:
    """Land a fresh batch of orders into raw, as an ingestion job would."""
    rng = random.Random(seed)
    landed_at = now()
    today = landed_at.date()

    with connect(autocommit=False) as conn, conn.cursor() as cur:
        cur.execute("select coalesce(max(order_id), 0) from raw.orders")
        order_id = cur.fetchone()[0]
        cur.execute("select coalesce(max(order_item_id), 0) from raw.order_items")
        item_id = cur.fetchone()[0]
        cur.execute("select coalesce(max(payment_id), 0) from raw.payments")
        payment_id = cur.fetchone()[0]
        cur.execute("select product_id, list_price from raw.products")
        products = cur.fetchall()
        cur.execute("select customer_id from raw.customers")
        customers = [row[0] for row in cur.fetchall()]

        for _ in range(n):
            order_id += 1
            ordered_at = datetime(
                today.year, today.month, today.day,
                rng.randint(6, 20), rng.randint(0, 59), tzinfo=timezone.utc,
            )
            cur.execute(
                "insert into raw.orders (order_id, customer_id, order_status, "
                "ordered_at, currency, _loaded_at) values (%s,%s,'completed',%s,'USD',%s)",
                (order_id, rng.choice(customers), ordered_at, landed_at),
            )
            gross = 0.0
            for _ in range(rng.randint(1, 3)):
                item_id += 1
                product_id, list_price = products[rng.randrange(len(products))]
                qty = rng.randint(1, 3)
                unit_price = round(float(list_price) * rng.uniform(0.85, 1.0), 2)
                cur.execute(
                    "insert into raw.order_items (order_item_id, order_id, product_id, "
                    "quantity, unit_price, _loaded_at) values (%s,%s,%s,%s,%s,%s)",
                    (item_id, order_id, product_id, qty, unit_price, landed_at),
                )
                gross += qty * unit_price
            payment_id += 1
            cur.execute(
                "insert into raw.payments (payment_id, order_id, amount, method, "
                "paid_at, _loaded_at) values (%s,%s,%s,'card',%s,%s)",
                (payment_id, order_id, round(gross, 2),
                 ordered_at + timedelta(minutes=rng.randint(1, 90)), landed_at),
            )
        conn.commit()
    return n


def rename_unit_price(to_broken: bool = True) -> None:
    """Rename raw.order_items.unit_price, breaking stg_order_items."""
    old, new = ("unit_price", "unit_price_usd") if to_broken else ("unit_price_usd", "unit_price")
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "select 1 from information_schema.columns where table_schema='raw' "
            "and table_name='order_items' and column_name=%s",
            (old,),
        )
        if cur.fetchone():
            cur.execute(f"alter table raw.order_items rename column {old} to {new}")