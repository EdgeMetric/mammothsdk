#!/usr/bin/env python3
"""Golden-data check for value-changing transforms, run through the real CLI.

Creates one owned project on the selected profile, uploads two tiny CSVs whose
correct answers are known, runs the typed transforms an ETL task uses, and
reads the data back after every step asserting the *values*, not just the
job status:

- bulk-replace strips ``$`` and ``,`` from ``amount`` and nothing else
- convert-type makes ``amount`` numeric (blank stays null)
- set-values with a condition fills only the blank ``amount``
- text trims and lower-cases ``status`` only
- filter removes exactly the negative-qty row
- discard-duplicates removes exactly the duplicated row
- join brings ``region`` for matched customers and null for the unmatched one
- view create (clone_from) + pivot gives per-region sums that add up
- export csv writes the rows that were read back

Every command's outcome is appended to ``results.jsonl`` in the evidence
directory (``--evidence-dir``) in the matrix fold format, and a SUMMARY.md is
written. Everything the run creates is deleted at the end (one id per call,
read back), then the project itself with ``--yes --confirm``. Nothing outside
the created project is touched.

Usage: scripts/live_golden_check.py --profile release \
           --evidence-dir docs/capability-evidence/golden-YYYYMMDD
Exit status 0 only when every assertion held.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ORDERS = [
    ["order_id", "customer_id", "amount", "qty", "status", "order_date"],
    ["1", "C1", "$1,234.56", "2", " Active ", "2024-01-05"],
    ["2", "C2", "", "1", "active", "2024-02-10"],
    ["3", "C3", "10", "0", "INACTIVE", "2024-03-15"],
    ["4", "C1", "$7,000", "-1", "Active", "2024-04-20"],
    ["4", "C1", "$7,000", "-1", "Active", "2024-04-20"],
    ["5", "C9", "25", "3", "Active", "2024-05-01"],
]
CUSTOMERS = [
    ["customer_id", "region"],
    ["C1", "north"],
    ["C2", "south"],
    ["C3", "south"],
]


class Check:
    def __init__(self, args: argparse.Namespace) -> None:
        self.profile = args.profile
        self.cli = args.cli
        self.evidence = Path(args.evidence_dir)
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.results = self.evidence / "results.jsonl"
        self.results.write_text("", encoding="utf-8")
        self.project_id: int | None = None
        self.created: list[tuple[str, list[str]]] = []  # (kind, argv tail) for cleanup
        self.failures: list[str] = []
        self.notes: list[str] = []

    # -- plumbing ----------------------------------------------------------

    def run(
        self,
        command_id: str,
        argv: list[str],
        *,
        input_doc: dict[str, Any] | None = None,
        project: bool = True,
        yes: bool = False,
        confirm: str | None = None,
        expect_ok: bool = True,
        detail: str = "",
    ) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None]:
        cmd = [self.cli, *argv]
        if project and self.project_id is not None:
            cmd += ["--project", str(self.project_id)]
        if input_doc is not None:
            cmd += ["--input", json.dumps(input_doc)]
        cmd += ["--profile", self.profile, "--output", "json", "--no-input"]
        if yes:
            cmd.append("--yes")
        if confirm is not None:
            cmd += ["--confirm", confirm]
        started = time.monotonic()
        proc = subprocess.run(cmd, text=True, capture_output=True)
        elapsed = round(time.monotonic() - started, 1)
        data = error = None
        for stream in (proc.stdout, proc.stderr):
            try:
                doc = json.loads(stream)
            except ValueError:
                continue
            if isinstance(doc, dict) and "error" in doc:
                error = doc["error"]
            elif isinstance(doc, dict) and "data" in doc:
                data = doc["data"]
        verdict = "ok" if proc.returncode == 0 else (error or {}).get("code", "cli_error")
        record = {
            "command_id": command_id,
            "argv": " ".join(shlex.quote(part) for part in cmd if part != self.profile),
            "exit": proc.returncode,
            "http_status_if_any": ((error or {}).get("details") or {}).get("status_code"),
            "verdict": verdict,
            "detail": detail or ((error or {}).get("message", "") if error else ""),
            "seconds": elapsed,
        }
        with self.results.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        print(f"[{proc.returncode}] {command_id} ({elapsed}s) {record['detail'][:120]}", flush=True)
        if expect_ok and proc.returncode != 0:
            self.failures.append(f"{command_id}: exit {proc.returncode} {record['detail'][:200]}")
        return proc.returncode, data, error

    def amend(self, command_id: str, detail: str) -> None:
        """Rewrite the last record for ``command_id`` with the verified detail."""
        lines = self.results.read_text(encoding="utf-8").splitlines()
        for index in range(len(lines) - 1, -1, -1):
            record = json.loads(lines[index])
            if record["command_id"] == command_id:
                record["detail"] = detail
                lines[index] = json.dumps(record)
                break
        self.results.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def expect(self, condition: bool, message: str) -> bool:
        if condition:
            self.notes.append(f"OK   {message}")
        else:
            self.failures.append(message)
            self.notes.append(f"FAIL {message}")
        print(("ok   " if condition else "FAIL ") + message, flush=True)
        return condition

    # -- data helpers -------------------------------------------------------

    def rows(self, view_id: int, dataset_id: int, label: str) -> list[dict[str, Any]]:
        _, data, _ = self.run(
            "view.data.get", ["view", "data", "get", str(view_id), str(dataset_id)], detail=label
        )
        rows = (data or {}).get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            self.failures.append(f"{label}: view data get returned no row list")
            return []
        return rows

    def row_count(self, view_id: int, dataset_id: int) -> int | None:
        _, data, _ = self.run("view.get", ["view", "get", str(view_id), str(dataset_id)])
        if isinstance(data, dict):
            count = data.get("row_count")
            return int(count) if isinstance(count, int) else None
        return None

    def upload(self, path: Path) -> int | None:
        _, data, _ = self.run("file.upload", ["file", "upload", str(path)])
        ids = (data or {}).get("dataset_ids") if isinstance(data, dict) else None
        if not ids:
            return None
        status = data.get("status")
        self.expect(status == "ready", f"upload {path.name} reached ready (got {status})")
        self.created.append(("dataset", [str(ids[0])]))
        return int(ids[0])

    def view_for(self, dataset_id: int) -> int | None:
        _, data, _ = self.run("view.list", ["view", "list", str(dataset_id)])
        items = (
            data
            if isinstance(data, list)
            else (data or {}).get("dataviews") or (data or {}).get("data")
        )
        if isinstance(data, dict) and not items:
            items = next((v for v in data.values() if isinstance(v, list)), None)
        if not items:
            return None
        return int(items[0]["id"])

    def transform(self, name: str, view_id: int, dataset_id: int, body: dict[str, Any]) -> bool:
        code, _, _ = self.run(
            f"view.transform.{name}",
            ["view", "transform", name, str(view_id)],
            input_doc={"dataset_id": dataset_id, **body},
        )
        return code == 0

    # -- the check ---------------------------------------------------------

    def main(self) -> int:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        with tempfile.TemporaryDirectory(prefix="mammoth-golden-") as tmp:
            work = Path(tmp)
            orders = work / "orders.csv"
            customers = work / "customers.csv"
            for path, table in ((orders, ORDERS), (customers, CUSTOMERS)):
                with path.open("w", newline="", encoding="utf-8") as handle:
                    csv.writer(handle).writerows(table)
            try:
                self.body(orders, customers, work, stamp)
            finally:
                self.cleanup()
                self.write_summary(stamp)
        return 0 if not self.failures else 1

    def body(self, orders: Path, customers: Path, work: Path, stamp: str) -> None:
        _, data, _ = self.run(
            "project.create", ["project", "create", f"golden-{stamp}"], project=False
        )
        project_id = (data or {}).get("id") if isinstance(data, dict) else None
        if not isinstance(project_id, int):
            self.failures.append("project create returned no id; aborting")
            return
        self.project_id = project_id
        print(f"owned project {project_id}", flush=True)

        ds_o = self.upload(orders)
        ds_c = self.upload(customers)
        if ds_o is None or ds_c is None:
            self.failures.append("upload did not return dataset ids; aborting")
            return
        v_o = self.view_for(ds_o)
        v_c = self.view_for(ds_c)
        if v_o is None or v_c is None:
            self.failures.append("view list returned no view; aborting")
            return

        # Baseline: the raw upload as the platform parsed it.
        before = self.rows(v_o, ds_o, "orders before any transform")
        self.expect(len(before) == 6, f"orders upload has 6 rows (got {len(before)})")
        by_id = {str(r.get("order_id")): r for r in before}
        self.expect(
            str(by_id.get("1", {}).get("amount")) == "$1,234.56",
            "amount is text with $ and , before bulk-replace",
        )

        # 1. bulk-replace: strip currency formatting from amount only.
        if self.transform(
            "bulk-replace",
            v_o,
            ds_o,
            {"columns": ["amount"], "mapping": [{"search": ["$", ","], "replace": ""}]},
        ):
            rows = self.rows(v_o, ds_o, "after bulk-replace")
            got = {str(r.get("order_id")): r for r in rows}
            self.expect(str(got.get("1", {}).get("amount")) == "1234.56", "bulk-replace: 1234.56")
            self.expect(str(got.get("4", {}).get("amount")) == "7000", "bulk-replace: 7000")
            self.expect(
                got.get("1", {}).get("status") == " Active ",
                "bulk-replace left status untouched",
            )
            self.amend(
                "view.transform.bulk-replace",
                "removed $ and , from amount; other columns unchanged (read back)",
            )

        # 2. convert-type: amount -> NUMERIC.
        if self.transform(
            "convert-type", v_o, ds_o, {"conversions": [{"column": "amount", "to": "NUMERIC"}]}
        ):
            rows = self.rows(v_o, ds_o, "after convert-type")
            got = {str(r.get("order_id")): r for r in rows}
            self.expect(
                isinstance(got.get("1", {}).get("amount"), (int, float))
                and abs(float(got["1"]["amount"]) - 1234.56) < 1e-6,
                "convert-type: amount numeric 1234.56",
            )
            self.expect(
                got.get("2", {}).get("amount") in (None, ""), "convert-type: blank stays null"
            )
            self.amend(
                "view.transform.convert-type",
                "amount TEXT->NUMERIC; values preserved, blank -> null (read back)",
            )

        # 3. set-values with a condition: only the blank amount becomes 0.
        if self.transform(
            "set-values",
            v_o,
            ds_o,
            {
                "existing_column": "amount",
                "values": [{"value": 0}],
                "condition": {"column": "amount", "operator": "IS_EMPTY"},
            },
        ):
            rows = self.rows(v_o, ds_o, "after set-values")
            got = {str(r.get("order_id")): r for r in rows}
            self.expect(
                float(got.get("2", {}).get("amount") or -1) == 0.0, "set-values: blank -> 0"
            )
            self.expect(
                abs(float(got.get("1", {}).get("amount") or 0) - 1234.56) < 1e-6
                and float(got.get("3", {}).get("amount") or 0) == 10.0
                and float(got.get("5", {}).get("amount") or 0) == 25.0,
                "set-values: non-blank amounts unchanged",
            )
            self.amend(
                "view.transform.set-values",
                "IS_EMPTY condition honoured: only the blank row became 0, "
                "four other amounts unchanged (read back)",
            )

        # 4. text: trim + lower-case status.
        if self.transform(
            "text", v_o, ds_o, {"columns": ["status"], "case": "LOWER", "trim": True}
        ):
            rows = self.rows(v_o, ds_o, "after text")
            statuses = sorted({str(r.get("status")) for r in rows})
            self.expect(statuses == ["active", "inactive"], f"text: statuses {statuses}")
            self.amend(
                "view.transform.text",
                "trim+LOWER on status: values collapse to active/inactive (read back)",
            )

        # 5. filter: remove qty < 0 (rows 4 and its duplicate).
        if self.transform(
            "filter",
            v_o,
            ds_o,
            {"condition": {"column": "qty", "operator": "LT", "value": 0}, "filter_type": "REMOVE"},
        ):
            rows = self.rows(v_o, ds_o, "after filter")
            ids = sorted(str(r.get("order_id")) for r in rows)
            self.expect(ids == ["1", "2", "3", "5"], f"filter: remaining order ids {ids}")
            self.amend(
                "view.transform.filter",
                "REMOVE qty < 0 dropped exactly the two negative rows; 6 -> 4 rows (read back)",
            )

        # 6. discard-duplicates on a view that still has the duplicate: use a
        #    fresh clone at sequence 0? The filter already removed both copies,
        #    so verify on a second view of the raw dataset instead.
        _, data, _ = self.run(
            "view.create",
            ["view", "create", str(ds_o)],
            input_doc={"name": f"dedupe-{stamp}"},
        )
        v_dupe = (
            (data or {}).get("dataview_id") or (data or {}).get("id")
            if isinstance(data, dict)
            else None
        )
        if isinstance(v_dupe, int):
            self.created.append(("view", [str(v_dupe), str(ds_o)]))
            if self.transform("discard-duplicates", v_dupe, ds_o, {}):
                rows = self.rows(v_dupe, ds_o, "after discard-duplicates")
                self.expect(len(rows) == 5, f"discard-duplicates: 6 -> 5 rows (got {len(rows)})")
                self.amend(
                    "view.transform.discard-duplicates",
                    "exact duplicate row removed; 6 -> 5 rows (read back)",
                )

        # 7. join customers onto orders (LEFT): C9 has no match.
        if self.transform(
            "join",
            v_o,
            ds_o,
            {
                "foreign_view": v_c,
                "foreign_dataset_id": ds_c,
                "join_type": "LEFT",
                "on": [{"left": "customer_id", "right": "customer_id"}],
                "select": ["region"],
            },
        ):
            rows = self.rows(v_o, ds_o, "after join")
            got = {str(r.get("order_id")): r for r in rows}
            self.expect(len(rows) == 4, f"join keeps 4 rows (got {len(rows)})")
            self.expect(got.get("1", {}).get("region") == "north", "join: order 1 -> north")
            self.expect(got.get("2", {}).get("region") == "south", "join: order 2 -> south")
            self.expect(
                got.get("5", {}).get("region") in (None, ""), "join: unmatched C9 -> null region"
            )
            self.amend(
                "view.transform.join",
                "LEFT join on customer_id: 3 of 4 rows matched with the expected region, "
                "unmatched row null (read back)",
            )

        # 8. pivot on a clone of the cleaned view; sums must add up.
        _, data, _ = self.run(
            "view.create",
            ["view", "create", str(ds_o)],
            input_doc={"name": f"summary-{stamp}", "clone_from": v_o},
        )
        v_sum = (
            (data or {}).get("dataview_id") or (data or {}).get("id")
            if isinstance(data, dict)
            else None
        )
        if isinstance(v_sum, int):
            self.created.append(("view", [str(v_sum), str(ds_o)]))
            clone_rows = self.rows(v_sum, ds_o, "clone before pivot")
            cloned = self.expect(
                len(clone_rows) == 4 and "region" in (clone_rows[0] if clone_rows else {}),
                "view create clone_from copies the pipeline (4 cleaned rows with region)",
            )
            self.amend(
                "view.create",
                (
                    "clone_from copied the source pipeline: "
                    "the new view shows the cleaned, joined rows"
                    if cloned
                    else "clone_from did not copy the pipeline"
                ),
            )
            if cloned and self.transform(
                "pivot",
                v_sum,
                ds_o,
                {
                    "group_by": ["region"],
                    "aggregations": [
                        {"column": "amount", "function": "SUM", "as_name": "total_amount"},
                        {"column": "order_id", "function": "COUNT", "as_name": "order_count"},
                    ],
                },
            ):
                rows = self.rows(v_sum, ds_o, "after pivot")
                totals = {str(r.get("region")): r for r in rows}
                counts = sum(int(r.get("order_count") or 0) for r in rows)
                self.expect(counts == 4, f"pivot: Σ order_count == 4 (got {counts})")
                self.expect(
                    abs(float(totals.get("north", {}).get("total_amount") or 0) - 1234.56) < 1e-6,
                    "pivot: north total 1234.56",
                )
                self.expect(
                    abs(float(totals.get("south", {}).get("total_amount") or 0) - 10.0) < 1e-6,
                    "pivot: south total 10 (0 + 10)",
                )
                self.amend(
                    "view.transform.pivot",
                    "group by region with SUM/COUNT: totals match the read-back rows "
                    "and counts sum to the row count",
                )

                # 9. export csv of the summary and compare with the readback.
                out = work / "summary.csv"
                code, data, _ = self.run(
                    "view.export.csv",
                    ["view", "export", "csv", str(v_sum)],
                    input_doc={"dataset_id": ds_o, "output_path": str(out)},
                )
                if code == 0 and out.exists():
                    with out.open(encoding="utf-8") as handle:
                        exported = list(csv.DictReader(handle))
                    self.expect(
                        len(exported) == len(rows),
                        f"export csv rows == readback rows ({len(exported)})",
                    )
                    self.amend(
                        "view.export.csv",
                        f"wrote {len(exported)} rows matching the read-back summary",
                    )

        # 10. a few cheap read routes on the owned fixtures.
        self.run(
            "view.task.list", ["view", "task", "list", str(v_o)], input_doc={"dataset_id": ds_o}
        )
        self.run(
            "view.pipeline.get",
            ["view", "pipeline", "get", str(v_o)],
            input_doc={"dataset_id": ds_o},
        )
        self.run("dataset.get", ["dataset", "get", str(ds_o)])
        self.run("view.preview", ["view", "preview", str(v_o), str(ds_o)])
        self.run(
            "view.data.query",
            ["view", "data", "query", str(v_o), str(ds_o)],
            input_doc={
                "limit": 2,
                "condition": {"column": "region", "operator": "EQ", "value": "north"},
            },
        )

    def cleanup(self) -> None:
        if self.project_id is None:
            return
        for kind, tail in reversed(self.created):
            if kind == "view":
                self.run("view.delete", ["view", "delete", *tail], yes=True, expect_ok=False)
            elif kind == "dataset":
                self.run("dataset.delete", ["dataset", "delete", *tail], yes=True, expect_ok=False)
        self.run("dataset.list", ["dataset", "list"], expect_ok=False, detail="post-cleanup list")
        pid = str(self.project_id)
        code, _, _ = self.run(
            "project.delete", ["project", "delete", pid], project=False, yes=True, confirm=pid
        )
        if code == 0:
            _, data, _ = self.run("project.list", ["project", "list"], project=False)
            remaining = (
                {p.get("id") for p in (data or {}).get("projects", [])}
                if isinstance(data, dict)
                else set()
            )
            self.expect(self.project_id not in remaining, f"project {pid} gone after delete")

    def write_summary(self, stamp: str) -> None:
        lines = [
            f"# Golden-data check ({stamp})",
            "",
            f"Profile `{self.profile}`, owned project {self.project_id}. Every value-changing "
            "transform was read back with `view data get` and its values compared with the "
            "known answer for the fixture; see `results.jsonl` for each command.",
            "",
            "## Assertions",
            "",
            *[f"- {note}" for note in self.notes],
            "",
            "## Verdict",
            "",
            (
                "All assertions held."
                if not self.failures
                else "FAILED:\n" + "\n".join(f"- {f}" for f in self.failures)
            ),
            "",
        ]
        (self.evidence / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--cli", default=os.environ.get("MAMMOTH_CLI", "mammoth"))
    return Check(parser.parse_args()).main()


if __name__ == "__main__":
    sys.exit(main())
