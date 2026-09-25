"""Invoke dbt and record what actually happened into meta.*.

Everything written here comes from dbt's own run_results.json artifact.
No run status is fabricated.

Usage:
    python tools/run_dbt.py
    python tools/run_dbt.py --select stg_orders+
    python tools/run_dbt.py --command run --select fct_daily_revenue
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from db import DBT_DIR, connect, dbt_env

RUN_RESULTS = DBT_DIR / "target" / "run_results.json"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _model_name(unique_id: str) -> str | None:
    parts = unique_id.split(".")
    if parts[0] != "model":
        return None
    return parts[-1]


def snapshot_schema(conn, at: datetime | None = None) -> None:
    """Record current column layout of every raw and analytics table."""
    at = at or datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into meta.column_snapshot
                (snapshot_at, table_schema, table_name, column_name, data_type)
            select %s, table_schema, table_name, column_name, data_type
            from information_schema.columns
            where table_schema in
                ('raw','analytics','analytics_staging','analytics_intermediate')
            on conflict do nothing
            """,
            (at,),
        )


def record_results(results_path: Path = RUN_RESULTS) -> int:
    if not results_path.exists():
        print(f"no artifact at {results_path}", file=sys.stderr)
        return 0

    payload = json.loads(results_path.read_text())
    invocation_id = payload["metadata"]["invocation_id"]
    recorded = 0

    with connect(autocommit=False) as conn:
        with conn.cursor() as cur:
            for result in payload["results"]:
                model = _model_name(result["unique_id"])
                if model is None:
                    continue

                status = result["status"]
                if status not in ("success", "error", "skipped"):
                    status = "error"

                timings = {t["name"]: t for t in result.get("timing", [])}
                execute = timings.get("execute") or timings.get("compile") or {}
                started = _parse_ts(execute.get("started_at")) or _parse_ts(
                    payload["metadata"]["generated_at"]
                )
                completed = _parse_ts(execute.get("completed_at"))
                rows = (result.get("adapter_response") or {}).get("rows_affected")
                message = result.get("message") if status == "error" else None

                cur.execute(
                    """
                    insert into meta.run_history
                        (invocation_id, model_name, status, started_at,
                         completed_at, rows_affected, error_message)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (invocation_id, model, status, started, completed, rows, message),
                )
                recorded += 1

                if status == "success" and completed is not None:
                    cur.execute(
                        """
                        insert into meta.materialization_log
                            (model_name, materialized_at, row_count, invocation_id)
                        values (%s, %s, %s, %s)
                        on conflict do nothing
                        """,
                        (model, completed, rows, invocation_id),
                    )

        snapshot_schema(conn)
        conn.commit()

    return recorded


def run(command: str = "build", select: str | None = None) -> int:
    argv = ["dbt", command, "--project-dir", str(DBT_DIR)]
    if select:
        argv += ["--select", select]

    proc = subprocess.run(argv, cwd=DBT_DIR, env=dbt_env())
    recorded = record_results()
    print(f"recorded {recorded} model result(s) into meta.run_history")
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", default="build", choices=["build", "run", "test"])
    parser.add_argument("--select", default=None)
    args = parser.parse_args()
    code = run(args.command, args.select)
    if code != 0:
        print(f"dbt exited {code} (recorded as run history, not a harness failure)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())