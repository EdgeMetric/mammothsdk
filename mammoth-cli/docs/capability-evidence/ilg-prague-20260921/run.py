"""ILG rebuild on prague, end to end, with the production procedure.

Fresh mock fixtures (seed 2109), three projects the run creates, `--dry-run`
before every write, `expected_task_count` on every pipeline write, every
number checked against a key computed here from the fixtures.
"""
from __future__ import annotations

import csv
import json
import random
import subprocess
import sys
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
FIX.mkdir(exist_ok=True)
CLI = "mammoth"  # the installed CLI on PATH
PROFILE = "prague"
RUN = (HERE / "run.jsonl").open("a")
RESULTS = (HERE / "results.jsonl").open("a")
STATE = HERE / "state.json"

CANON = ["Head Office", "Shrewsbury High School", "Eaton End School", "Northwood Prep", "Riverside Academy"]
RAW = {
    "Head Office": ["Head Office", "HEAD OFFICE"],
    "Shrewsbury High School": ["Shrewsbury High School", "SHREWSBURY HIGH SCHOOL"],
    "Eaton End School": ["Eaton End School", "Eaton End"],
    "Northwood Prep": ["Northwood Prep"],
    "Riverside Academy": ["Riverside Academy"],
}
MONTHS = [date(2025, m, 1) for m in range(1, 13)]
CASE_SQL = (
    "CASE WHEN UPPER(TRIM(\"Location\")) = 'HEAD OFFICE' THEN 'Head Office' "
    "WHEN UPPER(TRIM(\"Location\")) = 'SHREWSBURY HIGH SCHOOL' THEN 'Shrewsbury High School' "
    "WHEN UPPER(TRIM(\"Location\")) IN ('EATON END', 'EATON END SCHOOL') THEN 'Eaton End School' "
    "ELSE \"Location\" END"
)
NOT_ROLLUP = "\"Location\" IS NOT NULL AND TRIM(\"Location\") NOT IN ('', 'Total')"


# ----------------------------------------------------------------- fixtures
def make_fixtures(seed: int = 2109) -> dict:
    rng = random.Random(seed)
    key: dict = {}
    # P&L: 5 financial rows × 5 locations × 12 months + one Total and one blank rollup row
    rows = []
    sales = defaultdict(float)
    budget = defaultdict(float)
    for loc in CANON:
        base = rng.uniform(14000, 52000)
        for m in MONTHS:
            for frow in ["Total - Sales", "Operating Profit", "Total - 5005 - Direct Staff  Cost", "5025 - Agency Staff", "Total - Overheads"]:
                amt = round(base * rng.uniform(0.6, 1.5), 2)
                bud = round(amt * rng.uniform(0.85, 1.15), 2)
                rows.append([rng.choice(RAW[loc]), m.isoformat(), frow, amt, bud, round(amt - bud, 2)])
                if frow == "Total - Sales":
                    sales[(loc, m)] += amt
                    budget[(loc, m)] += bud
    rows.append(["Total", "2025-01-01", "Total - Sales", 999999.99, 888888.88, 111111.11])
    rows.append(["", "2025-01-01", "Total - Sales", 12345.67, 12345.67, 0.0])
    rng.shuffle(rows)
    with (FIX / "f_schoolpnl.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Location", "Period", "Financial Row", "Amount", "Budget Amount", "Amount Over Budget"])
        w.writerows(rows)
    key["pnl_rows"] = len(rows)
    key["sales_total"] = round(sum(sales.values()), 2)
    key["budget_total"] = round(sum(budget.values()), 2)
    key["sales_q1"] = round(sum(v for (l, m), v in sales.items() if m.month <= 3), 2)
    key["sales_by_loc"] = {loc: round(sum(v for (l, m), v in sales.items() if l == loc), 2) for loc in CANON}

    # HR absences: ~330 rows, 105 staff, each staff belongs to one location
    staff = [f"E{n:04d}" for n in range(1, 106)]
    home = {s: CANON[i % 5] for i, s in enumerate(staff)}
    hr = []
    for _ in range(330):
        s = rng.choice(staff)
        loc = home[s]
        d = date(2025, 1, 1) + timedelta(days=rng.randrange(365))
        hr.append([rng.choice(RAW[loc]), d.isoformat(), s, rng.choice(["Sickness", "Unplanned", "Unplanned"]), rng.randint(1, 5)])
    with (FIX / "hr_absences.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Location", "Absence Start", "Employee Ref", "Reason", "Days"])
        w.writerows(hr)
    key["absence_rows"] = len(hr)
    key["absence_days"] = sum(r[4] for r in hr)
    key["distinct_staff"] = len({r[2] for r in hr})
    key["distinct_staff_q1"] = len({r[2] for r in hr if r[1] <= "2025-03-31"})
    key["absence_rows_q1"] = sum(1 for r in hr if r[1] <= "2025-03-31")
    cells = {(home[r[2]], date.fromisoformat(r[1]).replace(day=1), r[2]) for r in hr}
    key["employee_rows"] = len(cells)
    key["consolidated_rows"] = len({(home[r[2]], date.fromisoformat(r[1]).replace(day=1)) for r in hr}) + len(cells)
    key["victim"] = hr[0][2]  # employee removed upstream in the last phase
    victim_rows = [r for r in hr if r[2] == key["victim"]]
    key["victim_rows"] = len(victim_rows)
    rest = [r for r in hr if r[2] != key["victim"]]
    key["consolidated_rows_after"] = len({(home[r[2]], date.fromisoformat(r[1]).replace(day=1)) for r in rest}) + len({(home[r[2]], date.fromisoformat(r[1]).replace(day=1), r[2]) for r in rest})
    key["distinct_staff_after"] = len({r[2] for r in rest})

    # Occupancy: monthly per location
    occ = []
    places_t = occupied_t = 0
    occ_q1 = defaultdict(lambda: [0, 0])
    for loc in CANON:
        places = rng.randint(110, 320)
        for m in MONTHS:
            o = int(places * rng.uniform(0.72, 0.98))
            occ.append([rng.choice(RAW[loc]), m.strftime("%Y-%m"), places, o])
            places_t += places
            occupied_t += o
            if m.month <= 3:
                occ_q1[m.month][0] += places
                occ_q1[m.month][1] += o
    rng.shuffle(occ)
    with (FIX / "o_occupancy.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Location", "Month", "Places", "Occupied"])
        w.writerows(occ)
    key["places_total"] = places_t
    key["occupied_total"] = occupied_t
    key["occupied_q1"] = sum(v[1] for v in occ_q1.values())
    key["occupancy_rate_q1"] = {m: round(100 * v[1] / v[0], 4) for m, v in sorted(occ_q1.items())}

    # Targets
    tg = [[rng.choice(RAW[loc]), rng.randint(14000, 23000)] for loc in CANON]
    with (FIX / "targets.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Location", "Monthly Target"])
        w.writerows(tg)
    key["target_total_x12"] = sum(t[1] for t in tg) * 12
    return key


# ----------------------------------------------------------------- harness
def sanitize(s: str) -> str:
    return s.replace(str(HERE), "<state-dir>")


def run(label: str, *args: str, project: int | None = None, expect: int | tuple[int, ...] = 0, timeout: int = 1500) -> dict:
    argv = [CLI, *args, "--profile", PROFILE, "-o", "json", "--no-progress"]
    if project is not None:
        argv += ["--project", str(project)]
    t0 = time.time()
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        resp = json.loads(out)
    except json.JSONDecodeError:
        resp = {"raw": out[:2000]}
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": label, "argv": sanitize(" ".join(["mammoth", *args])), "exit": proc.returncode, "secs": round(time.time() - t0, 1), "response": resp}
    RUN.write(json.dumps(rec) + "\n"); RUN.flush()
    ok_exits = (expect,) if isinstance(expect, int) else expect
    tag = "ok" if proc.returncode in ok_exits else "UNEXPECTED"
    print(f"[{rec['ts']}] {label}: exit {proc.returncode} ({rec['secs']}s) {tag}", flush=True)
    if proc.returncode not in ok_exits:
        print(json.dumps(resp)[:1500], flush=True)
        raise SystemExit(f"stop at {label}")
    return resp


def check(name: str, expected, actual, tol: float = 0.011) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        ok = abs(float(expected) - float(actual)) <= tol
    else:
        ok = expected == actual
    RESULTS.write(json.dumps({"check": name, "expected": expected, "actual": actual, "ok": ok}) + "\n"); RESULTS.flush()
    print(f"   check {name}: expected {expected!r} actual {actual!r} -> {'PASS' if ok else 'FAIL'}", flush=True)
    return ok


def data(resp: dict):
    return resp.get("data", resp)


def task_count(view: int, project: int) -> int:
    return len(data(run(f"tasks.{view}", "view", "task", "list", str(view), project=project))["tasks"])


def write_with_procedure(label: str, view: int, dataset: int, project: int, *cmd: str, body: dict) -> dict:
    """Dry-run, then the real write, both carrying the current task count."""
    n = task_count(view, project)
    doc = {"dataset_id": dataset, "expected_task_count": n, **body}
    dry = run(f"{label}.dry", *cmd, str(view), "--dry-run", "--input", json.dumps(doc), project=project)
    check(f"{label}.dry.reports", True, data(dry).get("dry_run") is True and "would_call" in data(dry))
    check(f"{label}.dry.no-task-added", n, task_count(view, project))
    return run(label, *cmd, str(view), "--input", json.dumps(doc), project=project)


def rows(view: int, dataset: int, project: int, label: str) -> list[dict]:
    r = data(run(label, "view", "data", "get", str(view), str(dataset), "--input", '{"limit": 400}', project=project))
    return r["data"]


def upload(label: str, path: Path, project: int) -> int:
    """Upload; when the platform asks for file settings, confirm them (need-action recipe)."""
    up = data(run(label, "file", "upload", str(path), project=project))
    ds = int(up["dataset_id"])
    if up.get("status") == "need_action":
        fs = data(run(f"{label}.settings.get", "dataset", "file-settings", "get", str(ds), project=project))["info"]
        doc = {k: fs[k] for k in ("delimiter", "has_header", "initial_skip_count", "quotechar")}
        if fs.get("has_ambiguous_dates"):
            doc["date_format"] = "UK"  # fixtures are ISO yyyy-mm-dd; either reading is identical
        run(f"{label}.settings.update.dry", "dataset", "file-settings", "update", str(ds), "--dry-run", "--input", json.dumps(doc), project=project)
        run(f"{label}.settings.update", "dataset", "file-settings", "update", str(ds), "--input", json.dumps(doc), project=project)
        for _ in range(20):
            st = data(run(f"{label}.poll", "dataset", "get", str(ds), project=project)).get("dataset", {})
            if st.get("status") not in ("need_action", "processing", None):
                break
            time.sleep(3)
        check(f"{label}.resolved", "ready", st.get("status"))
    return ds


def views_of(dataset: int, project: int, label: str) -> list[dict]:
    return data(run(label, "view", "list", str(dataset), project=project))["dataviews"]


def num(v) -> float:
    return float(str(v).replace(",", "")) if v not in (None, "") else 0.0


# ----------------------------------------------------------------- phases
def main() -> None:
    key = make_fixtures()
    (HERE / "key.json").write_text(json.dumps(key, indent=1, default=str))
    print("key:", json.dumps(key, default=str)[:600])
    st: dict = json.loads(STATE.read_text()) if STATE.exists() else {}

    # Phase 0 — projects (never project 3)
    for name, slot in (("ILG prague target", "T"), ("ILG prague source A", "A"), ("ILG prague source B", "B")):
        if slot not in st:
            r = data(run(f"project.ensure.{slot}", "project", "ensure", name))
            pid = int(r["project_id"])
            assert pid != 3 and r["project"]["name"] == name, r
            st[slot] = pid
            STATE.write_text(json.dumps(st))
    T, A, B = st["T"], st["A"], st["B"]
    print("projects:", st)

    # Phase 1 — sources and sends
    dsA_pnl = upload("A.upload.pnl", FIX / "f_schoolpnl.csv", A)
    vA_pnl = views_of(dsA_pnl, A, "A.views.pnl")[0]["id"]
    check("A.pnl.rows", key["pnl_rows"], views_of(dsA_pnl, A, "A.views.pnl.rows")[0]["row_count"])

    dsB: dict[str, int] = {}
    vB: dict[str, int] = {}
    for name, fname in (("hr", "hr_absences.csv"), ("occ", "o_occupancy.csv"), ("targets", "targets.csv")):
        dsB[name] = upload(f"B.upload.{name}", FIX / fname, B)
        vB[name] = views_of(dsB[name], B, f"B.views.{name}")[0]["id"]
    check("B.hr.rows", key["absence_rows"], views_of(dsB["hr"], B, "B.views.hr.rows")[0]["row_count"])

    # existing same-project send on HR (PowerBI stand-in), then add-only cross-project sends
    run("B.hr.exports.before", "view", "export", "list", str(vB["hr"]), project=B)
    run("B.hr.existing-send", "view", "export", "dataset", str(vB["hr"]), "--yes", "--input", json.dumps({"dataset_name": "HR absences - existing send (PowerBI stand-in)"}), project=B)
    before = data(run("B.hr.pipeline.before", "view", "pipeline", "items", str(vB["hr"]), "--input", '{"fields": "__full"}', project=B))["items"]
    check("B.hr.pipeline.before.count", 1, len(before))

    sent: dict[str, int] = {}
    for name, view in (("hr", vB["hr"]), ("occ", vB["occ"]), ("targets", vB["targets"])):
        body = json.dumps({"dataset_name": f"{name} (sent)", "target_project_id": T})
        dry = run(f"B.{name}.send.dry", "view", "export", "dataset", str(view), "--dry-run", "--input", body, project=B)
        check(f"B.{name}.send.dry.reports", True, data(dry).get("dry_run") is True)
        sent[name] = data(run(f"B.{name}.send", "view", "export", "dataset", str(view), "--yes", "--input", body, project=B))["dataset_id"]
    after = data(run("B.hr.pipeline.after", "view", "pipeline", "items", str(vB["hr"]), "--input", '{"fields": "__full"}', project=B))["items"]
    check("B.hr.pipeline.after.count", 2, len(after))
    first_before = {k: before[0].get(k) for k in ("id", "sequence", "execution_start_time", "execution_end_time", "reordered")}
    first_after = {k: next(i for i in after if i["id"] == before[0]["id"]).get(k) for k in first_before}
    check("B.hr.existing-send.untouched", first_before, first_after)
    run("B.hr.exports.after", "view", "export", "list", str(vB["hr"]), project=B)

    body = json.dumps({"dataset_name": "pnl (sent)", "target_project_id": T})
    run("A.pnl.send.dry", "view", "export", "dataset", str(vA_pnl), "--dry-run", "--input", body, project=A)
    sent["pnl"] = data(run("A.pnl.send", "view", "export", "dataset", str(vA_pnl), "--yes", "--input", body, project=A))["dataset_id"]

    # Phase 2 — conform and join in the target
    ds_list = data(run("T.datasets", "dataset", "list", project=T))["datasets"]
    check("T.datasets.sent", sorted(sent.values()), sorted(d["id"] for d in ds_list if d["id"] in sent.values()))
    v: dict[str, int] = {n: views_of(d, T, f"T.views.{n}")[0]["id"] for n, d in sent.items()}
    check("T.pnl.rows.landed", key["pnl_rows"], views_of(sent["pnl"], T, "T.views.pnl.rows")[0]["row_count"])

    # stale precondition must block (task count is 0; claim 1)
    stale = run("T.pnl.stale-precondition", "view", "transform", "add-sql", str(v["pnl"]), "--input", json.dumps({"dataset_id": sent["pnl"], "expected_task_count": 1, "query": f'SELECT * FROM "view:{v["pnl"]}"'}), project=T, expect=(1, 2, 3, 4))
    check("T.pnl.stale-precondition.code", "pipeline_changed", stale.get("error", {}).get("code"))
    check("T.pnl.stale-precondition.no-task", 0, task_count(v["pnl"], T))

    pnl_conform = (
        f'SELECT {CASE_SQL} AS "Location", DATE_TRUNC(\'month\', "Period") AS "Month", SUM("Amount") AS "Sales Actual", '
        f'SUM("Budget Amount") AS "Sales Budget", COUNT(*) AS "PnL Rows" FROM "view:{v["pnl"]}" '
        f'WHERE "Financial Row" = \'Total - Sales\' AND {NOT_ROLLUP} GROUP BY 1, 2'
    )
    write_with_procedure("T.pnl.conform", v["pnl"], sent["pnl"], T, "view", "transform", "add-sql", body={"query": pnl_conform})
    write_with_procedure("T.pnl.key", v["pnl"], sent["pnl"], T, "view", "transform", "add-sql", body={"query": f'SELECT "Location", "Month", "Sales Actual", "Sales Budget", "PnL Rows", "Location" || \'|\' || CAST("Month" AS VARCHAR) AS "Join Key" FROM "view:{v["pnl"]}"'})
    pnl_rows = rows(v["pnl"], sent["pnl"], T, "T.pnl.data")
    check("T.pnl.spine", 60, len(pnl_rows))
    check("T.pnl.sales_total", key["sales_total"], round(sum(num(r["Sales Actual"]) for r in pnl_rows), 2))
    check("T.pnl.budget_total", key["budget_total"], round(sum(num(r["Sales Budget"]) for r in pnl_rows), 2))
    check("T.pnl.locations", CANON, sorted({r["Location"] for r in pnl_rows}, key=CANON.index))

    occ_conform = (
        f'SELECT "Location", "Month", "Places", "Occupied", "Location" || \'|\' || CAST("Month" AS VARCHAR) AS "Join Key" FROM ('
        f'SELECT {CASE_SQL} AS "Location", CAST("Month" || \'-01\' AS TIMESTAMPTZ) AS "Month", SUM("Places") AS "Places", SUM("Occupied") AS "Occupied" '
        f'FROM "view:{v["occ"]}" WHERE {NOT_ROLLUP} GROUP BY 1, 2) c'
    )
    write_with_procedure("T.occ.conform", v["occ"], sent["occ"], T, "view", "transform", "add-sql", body={"query": occ_conform})
    occ_rows = rows(v["occ"], sent["occ"], T, "T.occ.data")
    check("T.occ.spine", 60, len(occ_rows))
    check("T.occ.places_total", key["places_total"], sum(num(r["Places"]) for r in occ_rows))
    check("T.occ.occupied_total", key["occupied_total"], sum(num(r["Occupied"]) for r in occ_rows))

    write_with_procedure("T.targets.conform", v["targets"], sent["targets"], T, "view", "transform", "add-sql", body={"query": f'SELECT {CASE_SQL} AS "Location", "Monthly Target" FROM "view:{v["targets"]}"'})

    inner_hr = (
        f'SELECT {CASE_SQL} AS "Location", DATE_TRUNC(\'month\', "Absence Start") AS "Month", "Employee Ref", "Days" '
        f'FROM "view:{v["hr"]}" WHERE {NOT_ROLLUP}'
    )
    hr_mixed = (
        f'SELECT "Location", "Month", CAST(NULL AS VARCHAR) AS "Employee Ref", COUNT(*) AS "Absence Rows", SUM("Days") AS "Absence Days", '
        f'COUNT(DISTINCT "Employee Ref") AS "Absent Staff (cell)", "Location" || \'|\' || CAST("Month" AS VARCHAR) AS "Join Key" FROM ({inner_hr}) b GROUP BY 1, 2 '
        f'UNION ALL SELECT DISTINCT "Location", "Month", "Employee Ref", CAST(NULL AS NUMERIC), CAST(NULL AS NUMERIC), CAST(NULL AS NUMERIC), '
        f'"Location" || \'|\' || CAST("Month" AS VARCHAR) || \'#\' || "Employee Ref" FROM ({inner_hr}) e'
    )
    write_with_procedure("T.hr.mixedgrain", v["hr"], sent["hr"], T, "view", "transform", "add-sql", body={"query": hr_mixed})
    hr_rows = rows(v["hr"], sent["hr"], T, "T.hr.data")
    spine = [r for r in hr_rows if r["Employee Ref"] in (None, "")]
    emp = [r for r in hr_rows if r["Employee Ref"] not in (None, "")]
    check("T.hr.employee_rows", key["employee_rows"], len(emp))
    check("T.hr.absence_rows", key["absence_rows"], sum(num(r["Absence Rows"]) for r in spine))
    check("T.hr.absence_days", key["absence_days"], sum(num(r["Absence Days"]) for r in spine))
    check("T.hr.distinct_staff", key["distinct_staff"], len({r["Employee Ref"] for r in emp}))

    write_with_procedure("T.pnl.join.targets", v["pnl"], sent["pnl"], T, "view", "transform", "join", body={"foreign_view": v["targets"], "foreign_dataset_id": sent["targets"], "join_type": "LEFT", "on": [{"left": "Location", "right": "Location"}], "select": ["Monthly Target"]})
    write_with_procedure("T.hr.join.pnl", v["hr"], sent["hr"], T, "view", "transform", "join", body={"foreign_view": v["pnl"], "foreign_dataset_id": sent["pnl"], "join_type": "LEFT", "on": [{"left": "Join Key", "right": "Join Key"}], "select": ["Sales Actual", "Sales Budget", "PnL Rows", "Monthly Target"]})
    write_with_procedure("T.hr.join.occ", v["hr"], sent["hr"], T, "view", "transform", "join", body={"foreign_view": v["occ"], "foreign_dataset_id": sent["occ"], "join_type": "LEFT", "on": [{"left": "Join Key", "right": "Join Key"}], "select": ["Places", "Occupied"]})
    cons = rows(v["hr"], sent["hr"], T, "T.consolidated.data")
    spine = [r for r in cons if r["Employee Ref"] in (None, "")]
    emp = [r for r in cons if r["Employee Ref"] not in (None, "")]
    check("T.cons.rows", key["consolidated_rows"], len(cons))
    check("T.cons.sales_total", key["sales_total"], round(sum(num(r["Sales Actual"]) for r in spine), 2))
    check("T.cons.occupied_total", key["occupied_total"], sum(num(r["Occupied"]) for r in spine))
    check("T.cons.target_x12", key["target_total_x12"], sum(num(r["Monthly Target"]) for r in spine))
    check("T.cons.measure_leak_on_employee_rows", 0, sum(1 for r in emp if any(r[c] not in (None, "") for c in ("Sales Actual", "Places", "Occupied", "Monthly Target"))))
    check("T.cons.task_count", 3, task_count(v["hr"], T))

    body = json.dumps({"dataset_id": sent["hr"], "dataset_name": "ILG Consolidated (prague)"})
    run("T.consolidated.send.dry", "view", "export", "dataset", str(v["hr"]), "--dry-run", "--input", body, project=T)
    ds_cons = data(run("T.consolidated.send", "view", "export", "dataset", str(v["hr"]), "--yes", "--input", body, project=T))["dataset_id"]
    v_cons_info = views_of(ds_cons, T, "T.views.cons")[0]
    v_cons = v_cons_info["id"]
    check("T.cons.materialised_rows", key["consolidated_rows"], v_cons_info["row_count"])

    # Phase 3 — dashboards
    dash = data(run("T.dash.create", "dashboard", "create-blank", "--yes", "--input", json.dumps({"params": {"dataview_id": v_cons, "title": "ILG prague - Overview"}}), project=T))["id"]
    canvas = data(run("T.dash.canvas.get", "dashboard", "canvas", "get", str(dash), project=T))["canvas"]
    canvas["derived"] = [{"id": "occupancy_rate", "label": "Occupancy rate", "numerator": "Occupied", "denominator": "Places"}]
    canvas["filters"] = [{"field": "Month", "control": "range", "label": "Month"}, {"field": "Location", "control": "multi", "label": "Location"}]
    canvas["currency"] = "£"
    page = canvas["pages"][0]
    page["title"] = "Overview"
    page["focus"] = {"measure": "Sales Actual", "dim": "Location", "kpis": [
        {"field": "Sales Actual", "agg": "sum", "label": "Sales Actual", "unit": {"prefix": "£"}, "decimals": 0},
        {"field": "Sales Budget", "agg": "sum", "label": "Sales Budget", "unit": {"prefix": "£"}, "decimals": 0},
        {"field": "Employee Ref", "agg": "countDistinct", "label": "Unplanned Absences (distinct staff)"},
        {"field": "Occupied", "agg": "sum", "label": "Occupied places"},
    ]}
    page["added"] = [
        {"kind": "bar", "title": "Sales Actual vs Budget by Month", "measure": "Sales Actual", "measure2": "Sales Budget", "agg": "sum", "date_bucket": {"field": "Month", "unit": "month"}},
        {"kind": "hbar", "title": "Sales Actual by Location", "dim": "Location", "measure": "Sales Actual", "agg": "sum", "sort": "desc"},
        {"kind": "line", "title": "Occupancy rate by Month", "measure": "occupancy_rate", "date_bucket": {"field": "Month", "unit": "month"}},
    ]
    save_doc = HERE / "canvas-overview.json"
    save_doc.write_text(json.dumps({"body": {"params": {"canvas": canvas}}}))
    run("T.dash.canvas.save.dry", "dashboard", "canvas", "save", str(dash), "--dry-run", "--input", str(save_doc), project=T)
    saved = data(run("T.dash.canvas.save", "dashboard", "canvas", "save", str(dash), "--input", str(save_doc), project=T))
    if saved.get("bake_job_id"):
        run("T.dash.bake", "job", "wait", str(saved["bake_job_id"]), project=T)
    got = data(run("T.dash.canvas.get.after", "dashboard", "canvas", "get", str(dash), project=T))
    figs = got.get("meta", {}).get("figures", {})
    pid = got["canvas"]["pages"][0]["id"]
    ids = {k: fig["descriptors"]["value"] for k, fig in figs.items() if k.startswith(f"{pid}:kpi:")}
    check("T.dash.kpi.descriptors", 4, len(ids))
    tiles = {k: fig["descriptors"] for k, fig in figs.items() if not k.startswith(f"{pid}:kpi:")}
    print("   figures:", json.dumps(ids), json.dumps(tiles)[:400])
    hints = got.get("plan", {}).get("hints", {}).get("kpis")
    check("T.dash.kpi.agg.countDistinct.persisted", True, any(k.get("agg") == "countDistinct" for k in (hints or [])) or any(k.get("agg") == "countDistinct" for k in got["canvas"]["pages"][0]["focus"]["kpis"]))

    k_sales, k_budget, k_staff, k_occ = (ids[f"{pid}:kpi:{i}"] for i in range(4))
    line_tile = next((t["id"] for t in got["canvas"]["pages"][0]["added"] if t.get("measure") == "occupancy_rate"), None)
    line_id = figs.get(f"{pid}:add:{line_tile}", {}).get("descriptors", {}).get("value") if line_tile else None
    check("T.dash.tile.descriptors", 3, sum(1 for k in figs if k.startswith(f"{pid}:add:")))
    ev = lambda label, extra: data(run(label, "dashboard", "descriptor-data", str(dash), "--input", json.dumps({"body": {"params": {"descriptor_ids": [k_sales, k_staff, k_occ] + ([line_id] if line_id else []), **extra}}}), project=T))["results"]
    all_ = ev("T.dash.eval.all", {})
    check("T.dash.eval.all.sales", key["sales_total"], num(all_[k_sales]["value"]))
    check("T.dash.eval.all.distinct_staff", key["distinct_staff"], num(all_[k_staff]["value"]))
    check("T.dash.eval.all.occupied", key["occupied_total"], num(all_[k_occ]["value"]))
    q1 = ev("T.dash.eval.q1", {"filter_state": {"Month": ["2025-01-01", "2025-03-31"]}})
    check("T.dash.eval.q1.sales", key["sales_q1"], num(q1[k_sales]["value"]))
    check("T.dash.eval.q1.distinct_staff", key["distinct_staff_q1"], num(q1[k_staff]["value"]))
    check("T.dash.eval.q1.occupied", key["occupied_q1"], num(q1[k_occ]["value"]))
    if line_id and line_id in q1 and q1[line_id].get("data"):
        got_rate = {int(p["key"][-2:]): round(p["value"], 4) for p in q1[line_id]["data"]}
        check("T.dash.eval.q1.occupancy_rate", key["occupancy_rate_q1"], got_rate, tol=0.001)

    # LLM-guarded page add (records what the guard does with £)
    pages_body = json.dumps({"body": {"params": {"pages": [{"title": "By Location", "focus": {"measure": "Sales Actual", "dim": "Location", "kpis": [{"field": "Sales Actual", "agg": "sum", "label": "Sales Actual", "unit": {"prefix": "£"}}, {"field": "Employee Ref", "agg": "countDistinct", "label": "Distinct absent staff"}]}, "charts": [{"kind": "hbar", "title": "Absence days by Location", "dim": "Location", "measure": "Absence Days", "agg": "sum"}]}]}}})
    run("T.dash.pages.add.dry", "dashboard", "pages", "add", str(dash), "--dry-run", "--input", pages_body, project=T)
    added = data(run("T.dash.pages.add", "dashboard", "pages", "add", str(dash), "--yes", "--confirm", str(dash), "--input", pages_body, project=T, expect=(0, 1)))
    print("   pages add:", json.dumps(added)[:400])
    got2 = data(run("T.dash.canvas.get.pages", "dashboard", "canvas", "get", str(dash), project=T))["canvas"]
    check("T.dash.pages.count", 2, len(got2["pages"]))

    # satellite board on the occupancy view (table + series line)
    dash2 = data(run("T.dash2.create", "dashboard", "create-blank", "--yes", "--input", json.dumps({"params": {"dataview_id": v["occ"], "title": "ILG prague - Occupancy (satellite)"}}), project=T))["id"]
    c2 = data(run("T.dash2.canvas.get", "dashboard", "canvas", "get", str(dash2), project=T))["canvas"]
    c2["derived"] = [{"id": "occupancy_rate", "label": "Occupancy rate", "numerator": "Occupied", "denominator": "Places"}]
    c2["filters"] = [{"field": "Month", "control": "range", "label": "Month"}]
    p2 = c2["pages"][0]
    p2["title"] = "Occupancy"
    p2["focus"] = {"measure": "Occupied", "dim": "Location", "kpis": [{"field": "Places", "agg": "sum", "label": "Places"}, {"field": "Occupied", "agg": "sum", "label": "Occupied"}, {"field": "occupancy_rate", "label": "Occupancy rate"}]}
    p2["added"] = [
        {"kind": "table", "title": "Occupancy by Location and Month", "columns": ["Location", "Month", "Places", "Occupied"], "sort_by": "Month", "limit": 100},
        {"kind": "line", "title": "Occupancy rate by Month", "measure": "occupancy_rate", "series": "Location", "date_bucket": {"field": "Month", "unit": "month"}},
    ]
    d2 = HERE / "canvas-occupancy.json"
    d2.write_text(json.dumps({"body": {"params": {"canvas": c2}}}))
    s2 = data(run("T.dash2.canvas.save", "dashboard", "canvas", "save", str(dash2), "--input", str(d2), project=T))
    if s2.get("bake_job_id"):
        run("T.dash2.bake", "job", "wait", str(s2["bake_job_id"]), project=T)
    g2 = data(run("T.dash2.canvas.get.after", "dashboard", "canvas", "get", str(dash2), project=T))
    f2 = g2.get("meta", {}).get("figures", {})
    pid2 = g2["canvas"]["pages"][0]["id"]
    ids2 = [f2[f"{pid2}:kpi:{i}"]["descriptors"]["value"] for i in range(3) if f"{pid2}:kpi:{i}" in f2]
    check("T.dash2.kpi.descriptors", 3, len(ids2))
    r2 = data(run("T.dash2.eval", "dashboard", "descriptor-data", str(dash2), "--input", json.dumps({"body": {"params": {"descriptor_ids": ids2}}}), project=T))["results"]
    check("T.dash2.eval.places", key["places_total"], num(r2[ids2[0]]["value"]))
    check("T.dash2.eval.occupied", key["occupied_total"], num(r2[ids2[1]]["value"]))
    check("T.dash2.eval.rate", round(100 * key["occupied_total"] / key["places_total"], 3), round(num(r2[ids2[2]]["value"]), 3), tol=0.01)

    # Phase 4 — upstream change in source B propagates through the sends
    write_with_procedure("B.hr.filter.upstream", vB["hr"], dsB["hr"], B, "view", "transform", "filter", body={"filter_type": "REMOVE", "condition": {"column": "Employee Ref", "operator": "EQ", "value": key["victim"]}})
    check("B.hr.rows.after", key["absence_rows"] - key["victim_rows"], views_of(dsB["hr"], B, "B.views.hr.after")[0]["row_count"])
    # the send re-runs asynchronously; poll the consolidated dataset's view until it changes
    expected_rows = key["consolidated_rows_after"]
    deadline = time.time() + 600
    landed = None
    while time.time() < deadline:
        landed = views_of(ds_cons, T, "T.views.cons.poll")[0]["row_count"]
        if landed == expected_rows:
            break
        time.sleep(15)
    check("T.cons.rows.after_upstream", expected_rows, landed)
    after_ev = data(run("T.dash.eval.after_upstream", "dashboard", "descriptor-data", str(dash), "--input", json.dumps({"body": {"params": {"descriptor_ids": [k_staff, k_sales]}}}), project=T))["results"]
    check("T.dash.eval.after_upstream.distinct_staff", key["distinct_staff_after"], num(after_ev[k_staff]["value"]))
    check("T.dash.eval.after_upstream.sales_unchanged", key["sales_total"], num(after_ev[k_sales]["value"]))

    # CSV download of the consolidated view (a download, not a pipeline step)
    out_csv = HERE / "consolidated.csv"
    run("T.cons.csv", "view", "export", "csv", str(v_cons), str(ds_cons), "--input", json.dumps({"output_path": str(out_csv)}), project=T)

    st.update({"datasets": {"A": {"pnl": dsA_pnl}, "B": dsB, "T": {**sent, "consolidated": ds_cons}}, "views": {"A": {"pnl": vA_pnl}, "B": vB, "T": {**v, "consolidated": v_cons}}, "dashboards": [dash, dash2]})
    STATE.write_text(json.dumps(st, indent=1))
    print("DONE", json.dumps(st))


if __name__ == "__main__":
    main()
