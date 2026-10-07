"""A warm process that forks one child per fuzz case and runs the real ``main()``.

Starting ``python -m mammoth_cli`` costs over a second of imports, which makes a
case matrix of several thousand runs take hours. This process imports the CLI
once, then forks per request. The child runs exactly what the ``mammoth`` console
script runs (``mammoth_cli.__main__.main``) with stdin on /dev/null and stdout and
stderr captured to files, so the exit status and both streams are what a piped
run produces. Nothing in the CLI is replaced.

Protocol on stdin/stdout: one JSON object per line, ``{"argv": [...]}`` in,
``{"code": int, "stdout": str, "stderr": str}`` out.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback

from mammoth_cli.__main__ import main


def _run_child(argv: list[str], out_path: str, err_path: str) -> None:
    code = 0
    out = os.open(out_path, os.O_WRONLY | os.O_TRUNC)
    err = os.open(err_path, os.O_WRONLY | os.O_TRUNC)
    null = os.open(os.devnull, os.O_RDONLY)
    os.dup2(null, 0)
    os.dup2(out, 1)
    os.dup2(err, 2)
    sys.stdin = open(os.devnull)  # noqa: SIM115
    sys.argv = ["mammoth", *argv]
    try:
        result = main()
        code = result if isinstance(result, int) else 0
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BaseException:  # noqa: BLE001 - an escaped exception is a finding, shown as a traceback
        traceback.print_exc()
        code = 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)


def _serve() -> None:
    with tempfile.TemporaryDirectory(prefix="fuzz-zygote-") as scratch:
        out_path, err_path = os.path.join(scratch, "out"), os.path.join(scratch, "err")
        for line in sys.stdin:
            request = json.loads(line)
            for path in (out_path, err_path):
                open(path, "w").close()  # noqa: SIM115
            pid = os.fork()
            if pid == 0:
                _run_child(request["argv"], out_path, err_path)
            _, status = os.waitpid(pid, 0)
            code = os.waitstatus_to_exitcode(status)
            reply = {
                "code": code,
                "stdout": open(out_path, errors="replace").read(),  # noqa: SIM115
                "stderr": open(err_path, errors="replace").read(),  # noqa: SIM115
            }
            sys.__stdout__.write(json.dumps(reply) + "\n")  # type: ignore[union-attr]
            sys.__stdout__.flush()  # type: ignore[union-attr]


if __name__ == "__main__":
    _serve()
