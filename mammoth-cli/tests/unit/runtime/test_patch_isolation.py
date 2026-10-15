"""A test that patches ``open_service`` must not leave the patch in a command module.

Command modules are imported on first use and bind ``open_service`` by name at
import time. ``test_confirm`` patched ``mammoth_cli.runtime.session.open_service``
and then ran ``dataset delete``; when that was the first use of the dataset module,
the module imported while the patch was active and kept the raising stub for the
rest of the session, so ``test_confirmation_dispatch[dataset.delete]`` failed with
``internal_error`` depending only on which test ran first.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_TESTS = Path(__file__).resolve().parents[1]
_PATCHER = "runtime/test_confirm.py::test_dataset_delete_with_wrong_confirm_makes_no_api_call"
_VICTIM = (
    "commands/test_confirmation_dispatch.py::test_a_confirmed_command_sends_nothing_without_yes"
)


def test_dataset_delete_dispatch_passes_after_the_open_service_patcher() -> None:
    """Run the patching test first, then the dispatch case, in a fresh interpreter."""
    done = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(_TESTS / _PATCHER.split("::")[0]) + "::" + _PATCHER.split("::")[1],
            str(_TESTS / _VICTIM.split("::")[0])
            + "::"
            + _VICTIM.split("::")[1]
            + "[dataset.delete]",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-1000:]
