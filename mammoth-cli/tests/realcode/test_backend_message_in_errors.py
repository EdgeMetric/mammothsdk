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


def test_a_generic_backend_message_shows_the_reason_beneath_it() -> None:
    mapped = map_sdk_exception(
        _api_error(
            409,
            {
                "message": "Invalid arguments passed",
                "name": "INVALID_ARGUMENTS",
                "error_code": "4GENR001",
                "details": {"message": "There is no version of your data waiting here."},
            },
        )
    )
    assert mapped.message == (
        "Invalid arguments passed: There is no version of your data waiting here. [4GENR001]"
    )


def test_a_bare_not_found_on_agent_definitions_says_the_server_lacks_them() -> None:
    error = MammothAPIError(
        "x",
        status_code=404,
        method="GET",
        endpoint="/workspaces/7/agent-definitions",
        response_body={"detail": "Not Found", "status_code": 404},
    )
    mapped = map_sdk_exception(error)
    assert mapped.message == "This server does not have agent definitions."
    assert mapped.exit_status == 5


def test_a_missing_object_keeps_the_resource_id_hint() -> None:
    mapped = map_sdk_exception(
        _api_error(
            404, {"message": "No such dataset", "name": "NOT_FOUND", "error_code": "4DSET001"}
        )
    )
    assert mapped.hint == "Check the resource id and scope."
