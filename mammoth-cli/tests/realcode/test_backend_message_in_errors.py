"""A 4xx error carries the backend's own message, not a generic sentence."""

from __future__ import annotations

from mammoth.exceptions import MammothAPIError

from mammoth_cli.services.mapping import map_sdk_exception


def _api_error(status: int, body: dict[str, object]) -> MammothAPIError:
    return MammothAPIError("x", status_code=status, method="POST", response_body=body)


def test_conflict_shows_backend_detail_and_code() -> None:
    mapped = map_sdk_exception(
        _api_error(409, {"detail": "Agent key 'sample' is taken.", "code": "agent_key_taken"})
    )
    assert "Agent key 'sample' is taken." in mapped.message
    assert "agent_key_taken" in mapped.message
    assert mapped.exit_status == 6


def test_validation_errors_list_one_field_per_line() -> None:
    mapped = map_sdk_exception(
        _api_error(
            422,
            {
                "detail": [
                    {"loc": ["body", "key"], "msg": "must match ^[a-z][a-z0-9_-]{1,62}$"},
                    {"loc": ["body", "name"], "msg": "field required"},
                ]
            },
        )
    )
    assert mapped.message.splitlines() == [
        "key: must match ^[a-z][a-z0-9_-]{1,62}$",
        "name: field required",
    ]
    assert mapped.exit_status == 1
