"""A status flag named after a credential is not a credential.

FB-14/FB-15: the CLI masked a file's ``password_protected`` flag as
``***REDACTED***``, so the agent could not see that its PDF was locked and
spent 20 calls finding out.
"""

from __future__ import annotations

from mammoth_cli.output.normalize import REDACTED, normalize


def test_a_files_locked_flag_stays_visible() -> None:
    info = {"additional_info": {"password_protected": True}}
    assert normalize(info) == info


def test_a_real_password_is_still_masked() -> None:
    assert normalize({"password": "tigers42"}) == {"password": REDACTED}
