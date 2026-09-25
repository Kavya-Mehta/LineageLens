"""Populate the raw schema with 60 days of synthetic commerce data.

The data is synthetic and this is stated openly in the README.
Seeded RNG so every clean environment is byte-identical.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

from psycopg2.extras import execute_values

from db import connect

SEED = 20260920
DAYS = 60
N_CUSTOMERS = 120
N_PRODUCTS = 24

CATEGORIES = ["Audio", "Cables", "Displays", "Keyboards", "Storage", "Webcams"]
COUNTRIES = ["US", "US", "US", "CA", "GB", "DE", "IE"]
METHODS = ["card", "card", "card", "paypal", "bank_transfer"]
STATUSES = ["completed"] * 17 + ["cancelled", "pending", "refunded"]


def _truncate(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "truncate raw.payments, raw.order_items, raw.orders, "
            "raw.products, raw.customers restart identity cascade"
        )


def seed() -> dict:
    rng = random.Random(SEED)
    today = date.today()
    start = today - timedelta(days=DAYS - 1)

    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        signup = start - timedelta(days=rng.randint(0, 400))
        customers.append(
            (cid, f"user{cid:03d}@{rng.choice(['example.com','mail.test','corp.example'])}",
             signup, rng.choice(COUNTRIES))
        )

    products = []
    for pid in range(1, N_PRODUCTS + 1):
        products.append(
            (pid, f"SKU-{pid:04d}", f"Product {pid:02d}",
             rng.choice(CATEGORIES), round(rng.uniform(9.99, 349.00), 2))
        )

    orders, items, payments = [], [], []
    order_id = item_id = payment_id = 0

    for day_offset in range(DAYS):
        day = start + timedelta(days=day_offset)
        base = 18 if day.weekday() < 5 else 9
        n_orders = max(1, int(rng.gauss(base, 3)))

        for _ in range(n_orders):
            order_id += 1
            hour = rng.randint(0, 23)
            ordered_at = datetime(
                day.year, day.month, day.day, hour, rng.randint(0, 59),
                tzinfo=timezone.utc,
            )
            status = rng.choice(STATUSES)
            customer_id = rng.randint(1, N_CUSTOMERS)
            orders.append((order_id, customer_id, status, ordered_at, "USD"))

            gross = 0.0
            for _ in range(rng.randint(1, 4)):
                item_id += 1
                product = products[rng.randrange(N_PRODUCTS)]
                qty = rng.randint(1, 3)
                unit_price = round(product[4] * rng.uniform(0.85, 1.0), 2)
                items.append((item_id, order_id, product[0], qty, unit_price))
                gross += qty * unit_price

            if status in ("completed", "refunded"):
                payment_id += 1
                paid_at = ordered_at + timedelta(minutes=rng.randint(1, 240))
                payments.append(
                    (payment_id, order_id, round(gross, 2),
                     rng.choice(METHODS), paid_at)
                )

    with connect(autocommit=False) as conn:
        _truncate(conn)
        with conn.cursor() as cur:
            execute_values(cur,
                "insert into raw.customers "
                "(customer_id, email, signup_date, country) values %s",
                customers)
            execute_values(cur,
                "insert into raw.products "
                "(product_id, sku, product_name, category, list_price) values %s",
                products)
            execute_values(cur,
                "insert into raw.orders "
                "(order_id, customer_id, order_status, ordered_at, currency) values %s",
                orders)
            execute_values(cur,
                "insert into raw.order_items "
                "(order_item_id, order_id, product_id, quantity, unit_price) values %s",
                items)
            execute_values(cur,
                "insert into raw.payments "
                "(payment_id, order_id, amount, method, paid_at) values %s",
                payments)
        conn.commit()

    return {
        "customers": len(customers),
        "products": len(products),
        "orders": len(orders),
        "order_items": len(items),
        "payments": len(payments),
    }


if __name__ == "__main__":
    counts = seed()
    print("seeded raw schema:")
    for table, n in counts.items():
        print(f"  raw.{table:<12} {n:>6}")