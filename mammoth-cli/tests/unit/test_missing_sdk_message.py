"""A CLI whose mammoth-io SDK cannot be imported says what is wrong and how to fix it."""

from __future__ import annotations

import subprocess
import sys

# ``sys.modules["mammoth"] = None`` is Python's own way to make ``import mammoth`` raise
# ModuleNotFoundError, the failure a venv gets when its editable mammoth-io points at a
# deleted checkout (issue #364).
_BROKEN_INSTALL = (
    "import sys; sys.modules['mammoth'] = None; sys.argv = ['mammoth', 'auth', 'status']; "
    "from mammoth_cli.__main__ import main; sys.exit(main())"
)

# The same break for a module that is not the SDK: that is a different fault, so it must
# surface as the real traceback and not be blamed on mammoth-io.
_BROKEN_OTHER_MODULE = _BROKEN_INSTALL.replace("sys.modules['mammoth']", "sys.modules['typer']")


def test_a_cli_that_cannot_import_the_sdk_names_the_fix_instead_of_a_traceback() -> None:
    done = subprocess.run(  # noqa: S603 -- fixed argv, the current interpreter
        [sys.executable, "-c", _BROKEN_INSTALL], capture_output=True, text=True, timeout=120
    )

    assert done.returncode == 1
    assert "mammoth-io SDK cannot be imported" in done.stderr
    assert "pipx install --force mammoth-cli" in done.stderr
    assert "Traceback" not in done.stderr


def test_a_missing_module_that_is_not_the_sdk_keeps_its_traceback() -> None:
    done = subprocess.run(  # noqa: S603 -- fixed argv, the current interpreter
        [sys.executable, "-c", _BROKEN_OTHER_MODULE], capture_output=True, text=True, timeout=120
    )

    assert done.returncode != 0
    assert "ModuleNotFoundError" in done.stderr
    assert "typer" in done.stderr
    assert "mammoth-io SDK cannot be imported" not in done.stderr
    assert "pipx install --force" not in done.stderr
