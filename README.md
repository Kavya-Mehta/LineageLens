# LineageLens

A data engineer spends twenty to ninety minutes answering "why is this number
wrong" by hand, several times a week. Did the model run? Did its upstream run?
Is the row count normal? Has this happened before? Six or seven lookups across
three systems, and all the information needed is already available — just
scattered.

LineageLens is an agent that does the stitching. dbt tells you a model failed.
LineageLens tells you whether anyone needs to care, and why.

---

## Status

**Component 1 of 4 complete.** This repository currently contains the scenario
environment — the warehouse, the dbt project, and the failure injector.
The MCP server, agent loop, and eval harness are in progress.

---

## Quickstart

```bash
cp .env.example .env
make setup
python break.py --list
python break.py --scenario silent-nulls
```

---

## The pipeline

raw.customers ──► stg_customers ──────────────────────────► dim_customers
raw.products ──► stg_products ▲
raw.orders ──► stg_orders ──┐ │
raw.order_items ► stg_order_items ─┴► int_order_totals ──► int_customer_orders
│
raw.payments ──► stg_payments ──► int_payments_by_order │
│ │
└──► fct_orders ◄────┘
│
┌────────────────┴──────────────────┐
▼ ▼
fct_daily_revenue fct_payment_reconciliation

`fct_daily_revenue` is the dashboard number. Every scenario is a different
reason it might be wrong — or a reason it might be fine.

---

## Scenarios

| Scenario          | What is injected                                                         | Correct answer                                 |
| ----------------- | ------------------------------------------------------------------------ | ---------------------------------------------- |
| `upstream-failed` | New orders land, then `unit_price` is renamed so `stg_order_items` fails | Diagnose: mart predates stranded rows          |
| `schema-changed`  | `raw.payments` gains `refund_amount`, staging ignores it                 | Diagnose: green pipeline, overstated revenue   |
| `silent-nulls`    | Today's order items land with NULL `unit_price`                          | Diagnose: row counts normal, SUM() skips NULLs |
| `nothing-wrong`   | Same failure as upstream-failed, no new data landed                      | Do not page. Freshness holds                   |
| `unanswerable`    | Run history and snapshots deleted for 3 days                             | Escalate. No evidence exists                   |

`upstream-failed` and `nothing-wrong` inject the identical failure through
the identical mechanism. The only difference is whether new rows landed after
the last successful mart build. An agent that pattern-matches on "a run
failed = incident" gets one of them wrong.

---

## What is real and what is not

**Synthetic:** the warehouse, orders, customers, runbooks, and the 14-day
backfilled run history in `tools/seed_history.py`.

**Real:** every run status the agent reads. `tools/run_dbt.py` invokes dbt,
parses `target/run_results.json`, and writes what actually happened.
Column snapshots come from `information_schema`, not from a list someone typed.

---

## Limitations

- One warehouse, one dbt project. Not a general integration.
- Postgres only.
- The backfilled run history is fabricated. Only today's runs are observed.
- Nothing here diagnoses anything yet. That is component 3.

---

## Stack

Python · dbt · PostgreSQL · Docker · Claude · MCP · pytest · Railway
