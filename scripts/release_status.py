#!/usr/bin/env python3
"""Report whether every release surface matches the versions on ``main``.

Read-only: it never publishes, tags, merges or deploys. Each row says what was checked, the
result, and the fix when it fails. The ``release-sync`` skill (``.claude/skills/release-sync``)
runs this, applies the fixes, and runs it again.

Surfaces checked, per package (mammoth-io, mammoth-cli, mammoth-mcp-server):
  - version files agree (pyproject.toml, __init__.py, server.json)
  - PyPI has the repo version
  - the release tag exists on origin and has a GitHub release (cli-v is Latest)
  - CHANGELOG.md no longer holds a published version under [Unreleased]
And once each:
  - mammoth-cli/uv.lock pins the repo's mammoth-cli and mammoth-io
  - the CLI installer URLs answer without a login
  - the MCP registry's latest io.mammoth/mcp and the live server card equal server.json
  - mm-ai-docs main and docs.mammoth.io serve the published CLI version
  - the mm-website changelog was generated on or after the CLI's PyPI upload

Needs ``git`` and an authenticated ``gh``. Exit status 1 when any row fails.

Usage:
    python scripts/release_status.py            # table
    python scripts/release_status.py --json     # rows as JSON
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPO = "EdgeMetric/mammothsdk"
DOCS_REPO = "EdgeMetric/mm-ai-docs"
WEBSITE_REPO = "EdgeMetric/mm-website"
DOCS_URL = "https://docs.mammoth.io"
MCP_CARD_URL = "https://mcp.mammoth.io/.well-known/mcp/server-card.json"
REGISTRY_URL = (
    "https://registry.modelcontextprotocol.io/v0/servers/io.mammoth%2Fmcp/versions/latest"
)
SKILL_INDEX = "vitepress-site/src/public/.well-known/agent-skills/index.json"
WEBSITE_CHANGELOG = "content/changelog/data.json"


@dataclass(frozen=True)
class Package:
    name: str
    pyproject: str
    init: str
    tag_prefix: str
    changelog_label: str


PACKAGES = (
    Package("mammoth-io", "pyproject.toml", "mammoth/__init__.py", "sdk-v", "mammoth-io"),
    Package(
        "mammoth-cli",
        "mammoth-cli/pyproject.toml",
        "mammoth-cli/mammoth_cli/__init__.py",
        "cli-v",
        "mammoth-cli",
    ),
    Package(
        "mammoth-mcp-server",
        "mammoth-mcp-server/pyproject.toml",
        "mammoth-mcp-server/mammoth_mcp_server/__init__.py",
        "mcp-server-v",
        "mammoth-mcp-server",
    ),
)


@dataclass
class Row:
    check: str
    status: str  # ok | fail | warn
    detail: str
    fix: str = ""


ROWS: list[Row] = []


def add(check: str, ok: bool, detail: str, fix: str = "", warn: bool = False) -> None:
    status = "ok" if ok else ("warn" if warn else "fail")
    ROWS.append(Row(check, status, detail, "" if ok else fix))


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def run(*cmd: str) -> str:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "mammoth-release-status"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except urllib.error.URLError:
        return 0, b""


def fetch_json(url: str) -> dict[str, Any] | None:
    status, body = fetch(url)
    if status != 200:
        return None
    try:
        data: dict[str, Any] = json.loads(body)
        return data
    except json.JSONDecodeError:
        return None


def gh_file(repo: str, path: str, ref: str = "main") -> str | None:
    try:
        out = run("gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-q", ".content")
    except subprocess.CalledProcessError:
        return None
    return base64.b64decode(out).decode()


def gh_blob(repo: str, path: str, ref: str = "main") -> str | None:
    """Like gh_file, for files over the contents API's 1 MB inline limit."""
    try:
        sha = run("gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-q", ".sha").strip()
        out = run("gh", "api", f"repos/{repo}/git/blobs/{sha}", "-q", ".content")
    except subprocess.CalledProcessError:
        return None
    return base64.b64decode(out).decode()


def read_init_version(path: str) -> str | None:
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', (ROOT / path).read_text(), re.M)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_package(pkg: Package, remote_tags: set[str], changelog_unreleased: str) -> dict[str, Any]:
    version = tomllib.loads((ROOT / pkg.pyproject).read_text())["project"]["version"]
    files = {pkg.pyproject: version, pkg.init: read_init_version(pkg.init)}
    if pkg.name == "mammoth-mcp-server":
        files["mammoth-mcp-server/server.json"] = json.loads(
            (ROOT / "mammoth-mcp-server/server.json").read_text()
        )["version"]
    add(
        f"{pkg.name}: version files agree",
        len(set(files.values())) == 1,
        ", ".join(f"{k}={v}" for k, v in files.items()),
        "set the same version in each file",
    )

    info = fetch_json(f"https://pypi.org/pypi/{pkg.name}/json")
    pypi = info["info"]["version"] if info else None
    uploaded = None
    if info and info["releases"].get(version):
        uploaded = info["releases"][version][0]["upload_time"]
    add(
        f"{pkg.name}: on PyPI",
        uploaded is not None,
        f"repo {version}, PyPI latest {pypi}"
        + (f" (uploaded {uploaded[:10]})" if uploaded else ""),
        "build and upload (RELEASING.md); PyPI allows each version once",
    )

    tag = f"{pkg.tag_prefix}{version}"
    add(
        f"{pkg.name}: tag {tag}",
        tag in remote_tags,
        "on origin" if tag in remote_tags else "missing on origin",
        f"git tag -a {tag} -m '{pkg.name} {version}' <release commit> && git push origin {tag}",
    )

    try:
        run("gh", "release", "view", tag, "-R", REPO, "--json", "tagName")
        has_release = True
    except subprocess.CalledProcessError:
        has_release = False
    add(
        f"{pkg.name}: GitHub release {tag}",
        has_release,
        "exists" if has_release else "missing",
        "gh release create with the PyPI wheel and sdist (RELEASING.md)"
        + (", --latest, installers and SHA256SUMS" if pkg.name == "mammoth-cli" else ""),
    )

    in_unreleased = bool(
        uploaded
        and re.search(
            rf"\({re.escape(pkg.changelog_label)} {re.escape(version)}\b", changelog_unreleased
        )
    )
    add(
        f"{pkg.name}: CHANGELOG release heading",
        not in_unreleased,
        (
            f"{version} still under [Unreleased]"
            if in_unreleased
            else "no published version under [Unreleased]"
        ),
        "add a dated release heading below [Unreleased]",
    )
    return {"version": version, "uploaded": uploaded, "tag": tag}


def check_cli_extras(cli: dict[str, Any], sdk: dict[str, Any]) -> None:
    lock = (ROOT / "mammoth-cli/uv.lock").read_text()

    def locked(name: str) -> str | None:
        match = re.search(rf'^name = "{name}"\nversion = "([^"]+)"', lock, re.M)
        return match.group(1) if match else None

    pins = {"mammoth-cli": locked("mammoth-cli"), "mammoth-io": locked("mammoth-io")}
    add(
        "mammoth-cli: uv.lock pins",
        pins == {"mammoth-cli": cli["version"], "mammoth-io": sdk["version"]},
        ", ".join(f"{k}={v}" for k, v in pins.items()),
        "cd mammoth-cli && poetry lock && uv lock, then commit both",
    )

    try:
        latest = run("gh", "api", f"repos/{REPO}/releases/latest", "-q", ".tag_name").strip()
    except subprocess.CalledProcessError:
        latest = None
    add(
        "mammoth-cli: GitHub Latest release",
        latest == cli["tag"],
        f"Latest is {latest}",
        f"gh release edit {cli['tag']} --latest",
    )

    base = f"https://github.com/{REPO}/releases"
    for url in (
        f"{base}/download/{cli['tag']}/mammoth-install.sh",
        f"{base}/latest/download/mammoth-install.sh",
    ):
        status, _ = fetch(url)
        add(
            f"installer URL {url.removeprefix(base + '/')}",
            status == 200,
            f"HTTP {status}",
            "add mammoth-install.sh/.ps1 and SHA256SUMS to the release",
        )


def check_mcp(server_version: str) -> None:
    entry = fetch_json(REGISTRY_URL)
    registry = entry["server"]["version"] if entry else None
    add(
        "MCP registry io.mammoth/mcp latest",
        registry == server_version,
        f"registry {registry}, server.json {server_version}",
        "cd mammoth-mcp-server && mcp-publisher login dns --domain mammoth.io ... && "
        "mcp-publisher publish (mm-ai-docs deploy/README.md)",
    )
    card = fetch_json(MCP_CARD_URL)
    live = card.get("version") if card else None
    add(
        "MCP server deployed (live server card)",
        live == server_version,
        f"live {live}, server.json {server_version}",
        "deploy mammoth-mcp-server (mammoth-mcp-server/deploy)",
    )


def check_docs(cli: dict[str, Any]) -> None:
    published = cli["version"] if cli["uploaded"] else None
    if published is None:
        add(
            "docs: CLI version",
            False,
            "CLI repo version is not on PyPI yet",
            "publish the CLI first",
            warn=True,
        )
        return

    raw = gh_file(DOCS_REPO, SKILL_INDEX)
    found = re.search(r'"version":\s*"([^"]+)"', raw) if raw else None
    on_main = found.group(1) if found else None
    fix = f"merge the auto/cli-contract-{published} PR in {DOCS_REPO}"
    if on_main != published:
        try:
            prs = run(
                "gh",
                "pr",
                "list",
                "-R",
                DOCS_REPO,
                "--head",
                f"auto/cli-contract-{published}",
                "--json",
                "number,url",
                "-q",
                ".[].url",
            ).split()
        except subprocess.CalledProcessError:
            prs = []
        fix = (
            f"merge {prs[0]}"
            if prs
            else f"run the Regenerate CLI contract workflow in {DOCS_REPO} "
            "(or sync_skill.py --from-package + npm run docs:capabilities) and open a PR"
        )
    add(
        f"{DOCS_REPO} main skill version",
        on_main == published,
        f"main {on_main}, CLI {published}",
        fix,
    )

    live = fetch_json(f"{DOCS_URL}/.well-known/agent-skills/index.json")
    live_version = None
    if live:
        live_version = live["skills"][0].get("metadata", {}).get("version")
    add(
        "docs.mammoth.io skill version",
        live_version == published,
        f"live {live_version}, CLI {published}",
        f"deploy {DOCS_REPO} main (deploy/README.md)",
    )


def check_website(cli: dict[str, Any]) -> None:
    if not cli["uploaded"]:
        return
    raw = gh_blob(WEBSITE_REPO, WEBSITE_CHANGELOG)
    generated = json.loads(raw).get("generated") if raw else None
    released = cli["uploaded"][:10]
    add(
        f"{WEBSITE_REPO} changelog covers CLI {cli['version']}",
        bool(generated and generated >= released),
        f"changelog generated {generated}, CLI uploaded {released}",
        "add SDK & CLI entries for the release in content/changelog/data.json (PR to release, "
        "then release -> main)",
        warn=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true", help="print rows as JSON")
    args = parser.parse_args()

    remote_tags = {
        line.split("refs/tags/")[1].removesuffix("^{}")
        for line in run("git", "ls-remote", "--tags", "origin").splitlines()
        if "refs/tags/" in line
    }
    changelog = (ROOT / "CHANGELOG.md").read_text()
    match = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## )", changelog, re.M | re.S)
    unreleased = match.group(1) if match else ""

    results = {pkg.name: check_package(pkg, remote_tags, unreleased) for pkg in PACKAGES}
    check_cli_extras(results["mammoth-cli"], results["mammoth-io"])
    check_mcp(results["mammoth-mcp-server"]["version"])
    check_docs(results["mammoth-cli"])
    check_website(results["mammoth-cli"])

    if args.json:
        print(json.dumps([asdict(r) for r in ROWS], indent=2))
    else:
        mark = {"ok": "PASS", "fail": "FAIL", "warn": "WARN"}
        width = max(len(r.check) for r in ROWS)
        for r in ROWS:
            print(f"{mark[r.status]}  {r.check:<{width}}  {r.detail}")
            if r.fix:
                print(f"      {'':<{width}}  fix: {r.fix}")
        failed = sum(r.status == "fail" for r in ROWS)
        warned = sum(r.status == "warn" for r in ROWS)
        print(f"\n{len(ROWS)} checks: {failed} failed, {warned} warnings")
    return 1 if any(r.status == "fail" for r in ROWS) else 0


if __name__ == "__main__":
    sys.exit(main())
