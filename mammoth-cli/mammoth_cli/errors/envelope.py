"""Stable machine error envelope and exit-status mapping.

Every failure an agent can encounter returns a versioned error envelope with a
stable code, a hint, structured details, whether the next step needs new
authority, and exact executable recovery commands. No Python repr, Rich markup,
terminal control code, or secret ever appears in the envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mammoth_cli import SCHEMA_VERSION

# Exit statuses (plan 02).
EXIT_OK = 0
EXIT_API = 1
EXIT_USAGE = 2
EXIT_AUTH = 4
EXIT_NOT_FOUND = 5
EXIT_CONFLICT = 6
EXIT_RETRYABLE = 7
EXIT_INTERRUPT = 130

# Stable machine-readable error codes shared across more than one call site.
# These are a compatibility contract: the *values* never change; centralizing
# them here keeps the repeated codes spelled identically everywhere they are
# raised. Codes raised from a single site stay inline literals.
CODE_MISSING_ARGUMENT = "missing_argument"
CODE_MISSING_FIELD = "missing_field"
CODE_SDK_SYMBOL_UNRESOLVED = "sdk_symbol_unresolved"
CODE_INVALID_ARGUMENT = "invalid_argument"
CODE_INVALID_ARGUMENTS = "invalid_arguments"
CODE_INVALID_CONFIG_VALUE = "invalid_config_value"
CODE_INVALID_INPUT_DOCUMENT = "invalid_input_document"
CODE_INVALID_INPUT_FORMAT = "invalid_input_format"
CODE_INVALID_WORKSPACE_ID = "invalid_workspace_id"
CODE_INPUT_FORMAT_REQUIRED = "input_format_required"
CODE_API_ERROR = "api_error"
CODE_RESOURCE_NOT_FOUND = "resource_not_found"
CODE_PROFILE_NOT_FOUND = "profile_not_found"
CODE_CONFIRMATION_REQUIRED = "confirmation_required"
CODE_CONFIRMATION_DECLINED = "confirmation_declined"
CODE_AUTHENTICATION_FAILED = "authentication_failed"


@dataclass
class CliError(Exception):
    """A classified CLI error that renders to the stable error envelope."""

    code: str
    message: str
    exit_status: int = EXIT_API
    hint: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    retryable: bool = False
    authorization_required: bool = False
    recovery_commands: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_envelope(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "error": {
                "code": self.code,
                "message": self.message,
                "hint": self.hint,
                "details": self.details,
                "request_id": self.request_id,
                "retryable": self.retryable,
                "authorization_required": self.authorization_required,
                "recovery_commands": list(self.recovery_commands),
            },
        }


# --- Common typed errors ---------------------------------------------------


def missing_project_error() -> CliError:
    return CliError(
        code="project_required",
        message="No project is set for this command.",
        exit_status=EXIT_USAGE,
        hint="Set an active project or pass --project.",
        recovery_commands=[
            "mammoth project list --output json",
            "mammoth context project use PROJECT_ID",
        ],
    )


def authorization_required_error(action: str) -> CliError:
    return CliError(
        code="authorization_required",
        message=f"You are not authorized to {action}.",
        exit_status=EXIT_AUTH,
        hint="Ask a workspace administrator for the required permission.",
        authorization_required=True,
    )


def timeout_error(*, job_id: str | None = None, command: str = "job") -> CliError:
    details: dict[str, Any] = {}
    recovery: list[str] = []
    if job_id is not None:
        details["job_id"] = job_id
        recovery.append(f"mammoth {command} wait {job_id} --output json")
        recovery.append(f"mammoth {command} get {job_id} --output json")
    return CliError(
        code="timeout",
        message="The operation did not finish before the timeout.",
        exit_status=EXIT_RETRYABLE,
        hint="Wait for the job to finish, then inspect its result.",
        details=details,
        retryable=True,
        recovery_commands=recovery,
    )


def not_implemented_error(command_id: str, sdk_symbol: str) -> CliError:
    return CliError(
        code="not_implemented",
        message=f"The command '{command_id}' is not implemented yet.",
        exit_status=EXIT_USAGE,
        hint="This command is planned. Its typed SDK method is not built yet.",
        details={"command_id": command_id, "planned_sdk_symbol": sdk_symbol},
    )


# --- Samples used by contract tests ----------------------------------------


def sample_missing_project_error() -> dict[str, Any]:
    return missing_project_error().to_envelope()


def sample_timeout_error(job_id: str) -> dict[str, Any]:
    return timeout_error(job_id=job_id).to_envelope()
