"""Write-state readback coverage for family group C (D-077, PLAN part A).

Unlike ``tests/unit/runtime/test_state.py`` (the mechanism's own tests,
which fake both the manifest record and the read-command handler),
these exercise the *real* manifest ``readback`` declarations this
group added -- ``user.update`` (``kind: object``) and
``workspace.llm-task`` (``kind: delivery``) -- through the real
``command_by_id`` lookup and the real registered read-command handler,
with only the network seam faked via ``fake_service``. One test per
readback kind used by this family group.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import with_state
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_USER_GET = "mammoth.api.user_profile.UserProfileAPI.get"
_JOB_GET = "mammoth.api.jobs.JobsAPI.get_job"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: Any) -> Invocation:
    return Invocation(command_id=command_id, **overrides)


def test_user_update_state_is_kind_object(fake_service: FakeMammothService) -> None:
    """``user.update`` declares ``readback: user.get``, ``kind: object``.

    The write's own response carries no useful "new state" (``UpdateUser``
    returns no content); the real value is what the read shows afterward.
    """
    fake_service.responses[_USER_GET] = {
        "id": 42,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
    }

    result = with_state(_inv("user.update"), {"status": "done"})

    assert result["state"] == {
        "kind": "object",
        "read_by": "user.get",
        "object": {
            "id": 42,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
        },
    }
    assert fake_service.call_log == [(_USER_GET, {})]


def test_workspace_llm_task_state_is_kind_delivery(fake_service: FakeMammothService) -> None:
    """``workspace.llm-task`` declares ``readback: job.get``, ``kind: delivery``.

    ``RunLlmTask`` returns an async job envelope (``{"job": {"id": ...}}``);
    the readback resolves ``result.job.id`` and reads the job's real status.
    """
    fake_service.responses[_JOB_GET] = {"status": "success", "response": {"sample_key": "Status"}}

    result = with_state(_inv("workspace.llm-task"), {"job": {"id": 91}})

    assert result["state"] == {
        "kind": "delivery",
        "read_by": "job.get 91",
        "status": "success",
        "detail": None,
    }
    assert fake_service.call_log == [(_JOB_GET, {"job_id": 91})]
