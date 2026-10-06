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
from mammoth_cli.runtime import embedded

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
CODE_UPLOAD_REFUSED = "upload_refused"
CODE_INVALID_ARGUMENTS = "invalid_arguments"
CODE_INVALID_CONFIG_VALUE = "invalid_config_value"
CODE_INVALID_INPUT_DOCUMENT = "invalid_input_document"
CODE_INVALID_INPUT_FORMAT = "invalid_input_format"
CODE_INVALID_WORKSPACE_ID = "invalid_workspace_id"
CODE_INCOMPLETE_ENVIRONMENT_AUTH = "incomplete_environment_auth"
CODE_INPUT_FORMAT_REQUIRED = "input_format_required"
CODE_API_ERROR = "api_error"
CODE_RESOURCE_NOT_FOUND = "resource_not_found"
CODE_PROFILE_NOT_FOUND = "profile_not_found"
CODE_NO_SAVED_PROJECT = "no_saved_project"
CODE_NOT_AVAILABLE_EMBEDDED = "not_available_embedded"
CODE_NOT_AVAILABLE = "not_available"
CODE_CONFIRMATION_REQUIRED = "confirmation_required"
CODE_CONFIRMATION_DECLINED = "confirmation_declined"
CODE_AUTHENTICATION_FAILED = "authentication_failed"
CODE_AUTHORIZATION_REQUIRED = "authorization_required"
CODE_CONFLICT = "conflict"
CODE_RETRYABLE = "retryable_error"
CODE_OUTCOME_UNKNOWN = "outcome_unknown"
CODE_JOB_FAILED = "job_failed"
CODE_INTERRUPTED = "interrupted"
CODE_UNSUPPORTED_CONTRACT = "unsupported_contract"
CODE_NO_OP = "no_op"
CODE_WOULD_FAIL = "would_fail"
CODE_EMPTIES_VIEW = "empties_view"

# User-safe, one-line summaries shown to the customer instead of the model-facing
# ``message``/``hint``. Plain language only: no command names, ids, field names
# or jargon. Exactly one entry per error code the CLI can raise;
# ``tests/unit/test_error_summaries.py`` fails if a raised code has none.
_S_BAD_REQUEST = "The assistant's request wasn't valid, so it is trying a different way."
_S_BAD_INPUT = "Some of the information provided couldn't be used."
_S_SIGN_IN = "The assistant isn't signed in to Mammoth."
_S_INTERNAL = "The assistant hit an internal problem with this step."
_S_NOT_FOUND = "Something the assistant looked for couldn't be found."
_S_MISSING_INFO = "The assistant's request was missing some information."
_S_SETUP = "A setting needed for this step isn't set up correctly."
_S_UNAVAILABLE = "This step isn't available right now."

ERROR_SUMMARIES: dict[str, str] = {
    "aborted": "This step was stopped before it finished.",
    "ambiguous_resource_identity": (
        "More than one item matched, so the assistant needs to be more specific."
    ),
    "api_error": "Mammoth couldn't complete this step.",
    "append_leaves_columns_blank": (
        "This append would leave columns of the destination empty, and needs them named."
    ),
    "append_mapping_incomplete": "The column mapping would leave columns out or add new ones.",
    "append_schema_mismatch": "The new data doesn't line up with the existing columns.",
    "append_type_mismatch": "A column has a different type than in the existing data.",
    "append_schema_unreadable": "The columns of the existing data couldn't be read.",
    "authentication_failed": "Mammoth didn't accept the sign-in for this step.",
    "authorization_required": "You don't have permission to do this.",
    "capability_not_found": "The assistant tried something Mammoth doesn't support.",
    "confirmation_declined": "This step was not confirmed, so nothing was changed.",
    "confirmation_required": "This step needs your confirmation before it can go ahead.",
    "confirmation_target_mismatch": (
        "The confirmation was for a different item, so nothing was changed."
    ),
    "conflict": "This conflicts with the current state of your data, so nothing was changed.",
    "dry_run_targets_unresolvable": (
        "The assistant couldn't tell exactly which items this would change, so nothing was changed."
    ),
    "download_failed": "A download didn't complete.",
    "dry_run_unsupported": "That command can't be previewed, so it was not run.",
    "duplicate_input_key": _S_BAD_INPUT,
    "empties_view": "No row matches, so this step would leave the view empty.",
    "empty_search_query": "The search was empty.",
    "export_already_exists": "An export with that name already exists.",
    "incomplete_environment_auth": _S_SIGN_IN,
    "input_file_not_found": _S_NOT_FOUND,
    "input_format_required": _S_BAD_INPUT,
    "input_not_found": _S_NOT_FOUND,
    "input_too_deep": _S_BAD_INPUT,
    "input_too_large": "The information provided was too large.",
    "input_unreadable": _S_BAD_INPUT,
    "insecure_credential_file": _S_SETUP,
    "insecure_input_file": _S_BAD_INPUT,
    "intent_only_dashboards": "The assistant builds dashboards from your request only.",
    "internal_column_name": "That column is internal to Mammoth and can't be used.",
    "internal_error": _S_INTERNAL,
    "interrupted": "This step was interrupted before it finished.",
    "invalid_argument": _S_BAD_REQUEST,
    "invalid_argument_combination": _S_BAD_REQUEST,
    "invalid_arguments": _S_BAD_REQUEST,
    "invalid_rule": "A conditional-format rule wasn't valid.",
    "invalid_condition": "A filter condition wasn't valid.",
    "invalid_condition_value": "A filter condition used a value that isn't valid.",
    "invalid_config_value": _S_SETUP,
    "invalid_credentials": "The sign-in details weren't accepted.",
    "invalid_input_document": _S_BAD_INPUT,
    "invalid_input_encoding": _S_BAD_INPUT,
    "invalid_input_field_type": _S_BAD_INPUT,
    "invalid_input_format": _S_BAD_INPUT,
    "invalid_login_document": "The sign-in details weren't valid.",
    "invalid_option_value": _S_BAD_REQUEST,
    "invalid_output_mode": _S_BAD_REQUEST,
    "invalid_profile_name": _S_SETUP,
    "invalid_project_id": "The project couldn't be identified.",
    "invalid_resource_context": _S_BAD_REQUEST,
    "invalid_server_prefix": _S_SETUP,
    "invalid_storage_mode": _S_SETUP,
    "invalid_workspace_id": "The workspace couldn't be identified.",
    "job_failed": "A background task didn't finish successfully.",
    "keyring_unavailable": _S_SETUP,
    "keyring_unresponsive": _S_SETUP,
    "login_input_required": _S_SIGN_IN,
    "missing_argument": _S_MISSING_INFO,
    "missing_field": _S_MISSING_INFO,
    "no_op": "There is nothing to change, so this step isn't needed.",
    "no_output": "This step didn't return anything.",
    "nonfinite_input_number": _S_BAD_INPUT,
    "not_authenticated": _S_SIGN_IN,
    "not_implemented": _S_UNAVAILABLE,
    "outcome_unknown": "It isn't clear whether this step went through. Check before trying again.",
    "pipeline_changed": "The pipeline was changed by someone else while this step ran.",
    "pipeline_reference_error": "A step in the pipeline refers to something that no longer exists.",
    "profile_not_found": _S_SETUP,
    "no_saved_project": "This step can't save a project here; each step names its own.",
    "not_available_embedded": "This step isn't available inside the Mammoth app.",
    "not_available": _S_UNAVAILABLE,
    "profile_write_failed": _S_SETUP,
    "project_required": "No project has been chosen for this step.",
    "pypi_response_invalid": "An update check didn't return a usable answer.",
    "pypi_unreachable": "An update check couldn't connect.",
    "replace_table_not_acknowledged": (
        "This export would drop and recreate a database table, and needs an explicit yes."
    ),
    "resource_identity_required": "The assistant needs to say which item it means.",
    "resource_not_found": _S_NOT_FOUND,
    "retryable_error": "Mammoth was temporarily unavailable. Trying again may work.",
    "schema_not_found": _S_NOT_FOUND,
    "sdk_symbol_unresolved": _S_INTERNAL,
    "skill_conflict": _S_SETUP,
    "table_name_too_long": "The database would cut this table name and write a different table.",
    "task_runtime_error": "A background task hit an error while running.",
    "timeout": "This step took too long. It may still be running.",
    "too_many_goals": _S_BAD_REQUEST,
    "unexpected_argument": _S_BAD_REQUEST,
    "unknown_agent": _S_SETUP,
    "unknown_column": "A column the assistant referred to doesn't exist.",
    "unknown_config_key": _S_SETUP,
    "unknown_input_field": _S_BAD_REQUEST,
    "unknown_option": _S_BAD_REQUEST,
    "unknown_scope": _S_SETUP,
    "unsupported_contract": _S_UNAVAILABLE,
    "unsupported_profile_base_url": _S_SETUP,
    "unsupported_shell": _S_UNAVAILABLE,
    "upload_refused": "Mammoth doesn't accept this kind of file, so nothing was uploaded.",
    "upgrade_failed": "The update didn't complete.",
    "usage_error": _S_BAD_REQUEST,
    "view_in_draft": "This view is still a draft and can't be used yet.",
    "would_fail": "This step would fail when it runs, so it was not added.",
}

#: Shown for a code with no entry (a runtime backstop only; the exhaustiveness
#: test keeps every raised code out of this path).
DEFAULT_ERROR_SUMMARY = "Something went wrong with this step."


def user_summary(code: str) -> str:
    """The user-safe one-line summary for an error code."""
    return ERROR_SUMMARIES.get(code, DEFAULT_ERROR_SUMMARY)


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
    #: Where this invocation's run log is (``{"file", "run_id"}``); set by the
    #: executor when a run log is active so a failure can be traced to its
    #: request trail. Omitted from the envelope when no log was written.
    log_ref: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_envelope(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "summary": user_summary(self.code),
            "message": self.message,
            "hint": self.hint,
            "details": self.details,
            "request_id": self.request_id,
            "retryable": self.retryable,
            "authorization_required": self.authorization_required,
            "recovery_commands": list(self.recovery_commands),
        }
        if self.log_ref is not None:
            error["log_ref"] = dict(self.log_ref)
        return {"schema_version": SCHEMA_VERSION, "error": error}


# --- Common typed errors ---------------------------------------------------


def missing_project_error() -> CliError:
    if embedded.active():
        # An embedded call has no profile to save a project in.
        return CliError(
            code="project_required",
            message="No project is set for this command.",
            exit_status=EXIT_USAGE,
            hint="Pass --project PROJECT_ID.",
            recovery_commands=["mammoth project list", "mammoth dataset find SUBSTRING"],
        )
    return CliError(
        code="project_required",
        message="No project is set for this command.",
        exit_status=EXIT_USAGE,
        hint="Set an active project or pass --project.",
        recovery_commands=[
            "mammoth project list",
            "mammoth context project use PROJECT_ID",
            "mammoth dataset find SUBSTRING",
        ],
    )


def no_saved_project_error() -> CliError:
    """``context project use``/``clear`` in an embedded call, which has no profile."""
    return CliError(
        code=CODE_NO_SAVED_PROJECT,
        message="This environment keeps no active project.",
        exit_status=EXIT_USAGE,
        hint="Pass --project PROJECT_ID on each command.",
        recovery_commands=["mammoth project list"],
    )


EMBEDDED_AUTH_HINT = "Your session expired or is not authorised; ask the user to reload the page."
EMBEDDED_NO_PROFILE_HINT = "This environment keeps no profiles; the login comes from the host."


def not_available_embedded_error(command: str) -> CliError:
    """A host-machine-only command (login, install, upgrade...) run in an embedded call."""
    return CliError(
        code=CODE_NOT_AVAILABLE_EMBEDDED,
        message=f"'{command}' is not available inside the Mammoth app.",
        exit_status=EXIT_USAGE,
        hint="The app supplies the login, project and tools; use the other commands.",
    )


def not_available_error(command: str, *, web_path: str, instead: str | None = None) -> CliError:
    """A command whose server route no longer exists: say where the web app does it."""
    hint = f"Do it in the web app: {web_path}."
    if instead:
        hint += f" {instead}"
    return CliError(
        code=CODE_NOT_AVAILABLE,
        message=f"'{command}' is not available: the server no longer offers it.",
        exit_status=EXIT_USAGE,
        hint=hint,
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
        recovery.append(f"mammoth {command} wait {job_id}")
        recovery.append(f"mammoth {command} get {job_id}")
    return CliError(
        code="timeout",
        message="The operation did not finish before the timeout.",
        exit_status=EXIT_RETRYABLE,
        hint="Wait for the job to finish, then inspect its result.",
        details=details,
        retryable=True,
        recovery_commands=recovery,
    )


def interrupted_error(
    *,
    job_id: object | None = None,
    operation_state: str | None = None,
    phase: str | None = None,
    details: dict[str, Any] | None = None,
) -> CliError:
    """Return the resumable, secret-safe error for a user interrupt.

    A SIGINT is not a successful cancellation: an asynchronous operation may
    still be running remotely.  Keep the last observed handle and a concrete
    inspection action when one is available, while using the conventional
    shell status 130.
    """
    merged = dict(details or {})
    if job_id is not None:
        merged.setdefault("job_id", job_id)
        merged.setdefault("job_handle", job_id)
    merged.setdefault("operation_state", operation_state or "outcome_unknown")
    if phase is not None:
        merged.setdefault("phase", phase)
    recovery: list[str] = []
    if job_id is not None:
        if isinstance(job_id, (list, tuple)):
            ids = ",".join(str(item) for item in job_id)
            recovery.extend(
                [
                    f"mammoth job get-many --input '{{\"job_ids\": [{ids}]}}'",
                    f"mammoth job wait-many --input '{{\"job_ids\": [{ids}]}}'",
                ]
            )
        else:
            recovery.extend(
                [
                    f"mammoth job get {job_id}",
                    f"mammoth job wait {job_id}",
                ]
            )
    return CliError(
        code=CODE_INTERRUPTED,
        message="The operation was interrupted before a terminal result was observed.",
        exit_status=EXIT_INTERRUPT,
        hint=(
            "Inspect the observed job or resource before continuing; do not replay "
            "an unknown mutation."
        ),
        details=merged,
        retryable=False,
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
