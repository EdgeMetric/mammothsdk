"""A 4xx error carries the backend's own message, not a generic sentence."""

from __future__ import annotations

from mammoth.exceptions import MammothAPIError

from mammoth_cli.services.mapping import map_sdk_exception


def _api_error(status: int, body: dict[str, object]) -> MammothAPIError:
    return MammothAPIError("x", status_code=status, method="POST", response_body=body)


def test_conflict_shows_backend_message_and_error_code() -> None:
    mapped = map_sdk_exception(
        _api_error(
            409,
            {
                "message": "This workspace already has an agent with this key.",
                "name": "CONFLICT",
                "error_code": "4GENR007",
                "details": {
                    "detail": "Conflict for POST /workspaces/4/agent-definitions",
                    "status_code": 409,
                },
            },
        )
    )
    assert mapped.message.startswith("This workspace already has an agent with this key.")
    assert mapped.message.endswith("[4GENR007]")
    assert mapped.exit_status == 6


def test_validation_error_lists_one_field_per_line() -> None:
    mapped = map_sdk_exception(
        _api_error(
            400,
            {
                "details": {
                    "detail": "Validation failed for POST /workspaces/4/agent-definitions",
                    "extra": [
                        {
                            "key": "key",
                            "message": "String should match pattern '^[a-z][a-z0-9_-]{1,62}$'",
                        }
                    ],
                    "status_code": 400,
                },
                "error_code": "4GENR007",
                "message": "Validation error",
                "name": "VALIDATION_ERROR",
            },
        )
    )
    assert mapped.message.splitlines() == [
        "Validation error",
        "key: String should match pattern '^[a-z][a-z0-9_-]{1,62}$' [4GENR007]",
    ]
    assert mapped.exit_status == 1
