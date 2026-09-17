#!/usr/bin/env python3
"""Capture one non-secret Mammoth CLI case for live-readiness review.

The command must use a saved profile; this runner rejects obvious credential
flags/tokens and never records environment variables. Output is a sanitized
JSON envelope containing argv, exit code, stdout/stderr, and SHA-256 hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import re
import selectors
import time
from datetime import datetime, timezone
from pathlib import Path


FORBIDDEN = ("api_key", "api-secret", "api_secret", "password", "token")
ALLOWED_ROOTS = {"project", "dataset", "batch", "view", "file", "folder"}
MAX_OUTPUT = 1_000_000
REDACT = re.compile(r"(?i)(api[_-]?(?:key|secret)|authorization|bearer)\s*[:=]\s*[^,\s}]+")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run_bounded(command: list[str]) -> tuple[int, bytes, bytes]:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selector = selectors.DefaultSelector()
    assert process.stdout is not None and process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + 60
    try:
        while selector.get_map():
            if time.monotonic() >= deadline:
                process.kill()
                break
            for key, _ in selector.select(timeout=1):
                chunk = key.fileobj.read(8192)
                if chunk:
                    streams[key.data].extend(chunk[: max(0, MAX_OUTPUT - len(streams[key.data]))])
                else:
                    selector.unregister(key.fileobj)
            if process.poll() is not None and not selector.get_map():
                break
    finally:
        selector.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    return process.returncode or 0, bytes(streams["stdout"]), bytes(streams["stderr"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    lowered = " ".join(command).lower()
    if any(flag in lowered for flag in FORBIDDEN):
        parser.error("credential-bearing flags/tokens are forbidden")
    if not command or command[0] != "mammoth":
        parser.error("command must begin with mammoth")
    if len(command) < 2 or command[1] not in ALLOWED_ROOTS:
        parser.error("only Core resource commands are allowed")
    try:
        output_index = command.index("--output")
        has_json_output = command[output_index + 1] == "json"
    except (ValueError, IndexError):
        has_json_output = False
    if "--no-input" not in command or not has_json_output or "--profile" not in command:
        parser.error("command must explicitly request --output json --no-input")

    exit_code, stdout, stderr = run_bounded(command)
    version_result = subprocess.run(
        ["mammoth", "--version"], capture_output=True, check=False
    )
    record = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cli_version": version_result.stdout.decode("utf-8", errors="replace").strip(),
        "argv": command,
        "exit_code": exit_code,
        "stdout": REDACT.sub("[REDACTED]", stdout[:MAX_OUTPUT].decode("utf-8", errors="replace")),
        "stderr": REDACT.sub("[REDACTED]", stderr[:MAX_OUTPUT].decode("utf-8", errors="replace")),
        "stdout_sha256": sha256(stdout),
        "stderr_sha256": sha256(stderr),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    args.out.chmod(0o600)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
