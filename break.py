#!/usr/bin/env python3
"""Break the warehouse on demand.

    python break.py --list
    python break.py --scenario upstream-failed
    python break.py --scenario unanswerable --reveal
    python break.py --status
    python break.py --reset

Every scenario starts from a reset: raw and meta are rebuilt, sixty days of
orders are re-seeded, fourteen days of run history are backfilled, and one
clean dbt build runs. Only then is the failure injected. That makes runs
reproducible, which the eval harness depends on.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from db import PROJECT_ROOT, connect
from run_dbt import run as run_dbt
from scenarios import REGISTRY
from scenarios.base import clear_state, read_state

INIT_DIR = PROJECT_ROOT / "warehouse" / "init"


def reset(quiet: bool = False) -> None:
    say = (lambda *a: None) if quiet else print

    say("dropping and recreating schemas...")
    with connect() as conn, conn.cursor() as cur:
        for schema in ("analytics", "analytics_staging", "analytics_intermediate",
                       "meta", "raw"):
            cur.execute(f"drop schema if exists {schema} cascade")
        for path in sorted(INIT_DIR.glob("*.sql")):
            say(f"  running {path.name}")
            cur.execute(path.read_text())

    say("seeding raw data...")
    import seed_raw
    counts = seed_raw.seed()
    say("  " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    say("backfilling run history...")
    import seed_history
    say(f"  {seed_history.backfill()} rows")

    say("running clean baseline dbt build...")
    run_dbt(command="build")
    clear_state()
    say("reset complete — warehouse is clean, nothing is broken")


def status() -> None:
    state = read_state()
    if state is None:
        print("no scenario loaded (warehouse is clean)")
        return
    print(f"scenario:   {state['scenario']}")
    print(f"applied at: {state['applied_at']}")
    for note in state["notes"]:
        print(f"  - {note}")


def list_scenarios() -> None:
    width = max(len(name) for name in REGISTRY)
    print("scenarios:\n")
    for name, module in REGISTRY.items():
        summary = (module.__doc__ or "").strip().splitlines()[0]
        print(f"  {name:<{width}}  {summary}")
    print(f"\n  {'reset':<{width}}  Rebuild the warehouse clean")


def apply_scenario(name: str, reveal: bool) -> int:
    if name not in REGISTRY:
        print(f"unknown scenario: {name}", file=sys.stderr)
        list_scenarios()
        return 2

    module = REGISTRY[name]
    print(f"--- resetting before applying {name} ---")
    reset(quiet=True)
    print(f"--- applying {name} ---")
    result = module.apply()
    result.write_state()

    print(f"\nloaded: {name}")
    for note in result.notes:
        print(f"  - {note}")
    print("\nask the agent:\n")
    print(textwrap.indent(textwrap.fill(module.QUESTION, 72), "  "))

    if reveal:
        print("\nexpected behaviour (grading only):\n")
        print(textwrap.indent(textwrap.fill(module.EXPECTED, 72), "  "))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="name of the failure to inject")
    group.add_argument("--reset", action="store_true", help="rebuild clean")
    group.add_argument("--status", action="store_true", help="what is loaded")
    group.add_argument("--list", action="store_true", help="list scenarios")
    parser.add_argument("--reveal", action="store_true",
                        help="print expected behaviour for grading")
    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return 0
    if args.status:
        status()
        return 0
    if args.reset:
        reset()
        return 0
    return apply_scenario(args.scenario, args.reveal)


if __name__ == "__main__":
    raise SystemExit(main())