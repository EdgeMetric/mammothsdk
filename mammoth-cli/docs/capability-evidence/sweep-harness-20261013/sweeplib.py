"""Harness for the 2026-10-13 capability-evidence sweeps (drives the real CLI)."""

import json
import subprocess
import sys

M = "/tmp/claude-1000/ev-venv/bin/mammoth"
SKIP_FAMILIES = {
    "auth",
    "config",
    "context",
    "completion",
    "upgrade",
    "skill",
    "log",
    "doctor",
}


def run(argv, profile, project=None, timeout=90):
    cmd = [
        M,
        *argv,
        "--profile",
        profile,
        "--output",
        "json",
        "--no-input",
        "--timeout",
        "60",
    ]
    if project is not None and "--project" not in argv:
        cmd += ["--project", str(project)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, {"error": {"code": "timeout", "message": "harness timeout"}}
    txt = p.stdout.strip() or p.stderr.strip()
    try:
        return p.returncode, json.loads(txt)
    except Exception:
        return p.returncode, {"error": {"code": "non_json", "message": txt[:200]}}


def shape(d):
    if isinstance(d, dict):
        return sorted(d.keys())
    if isinstance(d, list):
        return f"list[{len(d)}]"
    return type(d).__name__


def is_empty(d):
    if d in (None, [], {}):
        return True
    if isinstance(d, dict):
        vals = [v for k, v in d.items() if isinstance(v, list)]
        return (
            bool(vals)
            and all(not v for v in vals)
            and len(vals) == len([1 for v in d.values() if isinstance(v, (list, dict))])
        )
    return False


def classify(code, env):
    if code == 0 and "error" not in env:
        return "ok_empty" if is_empty(env.get("data")) else "ok", {}
    e = env.get("error", {})
    det = e.get("details") or {}
    sc = det.get("status_code") or e.get("status_code")
    ec = e.get("code")
    info = {
        "error_code": ec,
        "status_code": sc,
        "backend_message": (e.get("message") or "")[:200],
    }
    if det.get("backend_code"):
        info["backend_code"] = det["backend_code"]
    if ec in ("authorization_required",) or sc in (401, 403):
        v = "authorization_error"
    elif ec in ("resource_not_found",) or sc in (404, 405, 501):
        v = "not_supported" if sc in (405, 501) else "not_found"
    elif isinstance(sc, int) and sc >= 500:
        v = "server_error"
    elif ec in (
        "validation_error",
        "invalid_input",
        "missing_required_field",
        "unknown_input_field",
        "usage_error",
    ) or sc in (400, 422):
        v = "validation_error"
    else:
        v = "cli_error"
    return v, info


def first_id(data, keys=("id", "name_key", "key")):
    if isinstance(data, list):
        for it in data:
            if isinstance(it, dict):
                for k in keys:
                    if it.get(k) not in (None, ""):
                        return it[k]
        return None
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, (list, dict)):
                r = first_id(v, keys)
                if r is not None:
                    return r
    return None


def fixture_from_list(profile, project, list_argv, keys=("id", "name_key", "key")):
    code, env = run(list_argv, profile, project)
    if code != 0:
        return None
    return first_id(env.get("data"), keys)


def results_path(folder):
    return f"{folder}/results.jsonl"
