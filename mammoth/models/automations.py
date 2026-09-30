"""Automation and schedule data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Read/response models (existing, kept as-is) ──────────────────────────────


class AutomationInfo(BaseModel):
    """Information about an automation."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleInfo(BaseModel):
    """Information about a schedule."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    cron: str | None = None
    status: str | None = None
    next_run: str | None = None
    last_run: str | None = None
    config: dict[str, Any] | None = None


# ── Shared schedule enums ─────────────────────────────────────────────────────


class RruleFrequency(str, Enum):
    """Recurrence-rule frequency values accepted by the schedule endpoint."""

    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Weekday(str, Enum):
    """Lowercase day-of-week code accepted by ``by_week_day``.

    The backend rejects anything else, including the uppercase ``"MO"``
    style RFC 5545 normally uses, with a 400 on
    ``conditions.0.details.by_week_day.0``.
    """

    MONDAY = "mo"
    TUESDAY = "tu"
    WEDNESDAY = "we"
    THURSDAY = "th"
    FRIDAY = "fr"
    SATURDAY = "sa"
    SUNDAY = "su"


class ScheduleStatus(str, Enum):
    """Schedule status values for a patch-status operation."""

    PAUSE = "pause"
    RESUME = "resume"


class SchedulePatchPath(str, Enum):
    """Allowed JSON-patch path values for schedule update."""

    RRULE = "rrule"
    STATUS = "status"


class WorkItemName(str, Enum):
    """Allowed ``name`` values for a schedule work item."""

    PULL_CLOUD_DATA = "pull_cloud_data"


class ScheduleType(str, Enum):
    """Execution schedule type for ``PullDataExecutionParams``."""

    MOMENT = "moment"
    PERIOD = "period"


class FirstPullAt(str, Enum):
    """When to perform the first data pull."""

    NOW = "now"
    LATER = "later"


class OnRefreshAction(str, Enum):
    """What to do with existing data on refresh."""

    REPLACE = "replace"
    APPEND = "append"


# ── Shared schedule param models ─────────────────────────────────────────────


class RruleSpec(BaseModel):
    """Recurrence-rule specification sent inside a schedule create/update body.

    Attributes:
        frequency: How often the schedule fires.
        start: When the schedule starts (UTC).
        interval: Optional repeat interval (must be > 0 if supplied).
        by_week_day: Days of the week, e.g. ``["mo", "we"]``.
        by_month_day: Days of the month (1–31).
    """

    frequency: RruleFrequency
    start: datetime
    interval: int | None = None
    by_week_day: list[Weekday] | None = None
    by_month_day: list[int] | None = None


class PullDataExecutionParams(BaseModel):
    """Execution parameters for a ``pull_cloud_data`` work item.

    Attributes:
        schedule_type: Whether this is a moment-based or period-based pull.
        first_pull_at: Whether to pull immediately or delay the first run.
        on_refresh_action: What to do with existing data when refreshing.
    """

    schedule_type: ScheduleType
    first_pull_at: FirstPullAt
    on_refresh_action: OnRefreshAction


class WorkItemSpec(BaseModel):
    """A single work item in a schedule create/update body.

    All three fields are required when ``work_items`` is provided (backend
    validates this at runtime; the SDK also validates proactively).

    Attributes:
        name: Task name.  Only ``pull_cloud_data`` is currently supported.
        execution_params: Execution parameters; must be a
            :class:`PullDataExecutionParams` instance for ``pull_cloud_data``.
        args: Dataset IDs (or other integer resource IDs) for the task.
    """

    name: WorkItemName
    execution_params: PullDataExecutionParams
    args: list[int]


class ScheduleCreateSpec(BaseModel):
    """Parameters for creating a schedule (shared by AutomationsAPI and SchedulesAPI).

    Attributes:
        rrule: Recurrence-rule specification.
        work_items: Optional list of work items.  If provided each item must
            have ``name``, ``execution_params``, and ``args``.
    """

    rrule: RruleSpec
    work_items: list[WorkItemSpec] | None = None


class SchedulePatchValue(BaseModel):
    """Value payload for a ``replace + rrule`` schedule patch operation.

    Both fields are required when patching the rrule path.
    """

    rrule: RruleSpec
    work_items: list[WorkItemSpec]


# ── Automation enums ──────────────────────────────────────────────────────────


class AutomationTaskType(str, Enum):
    """Allowed task types for an automation task."""

    RUN_DATA_RETRIEVAL = "run_data_retrieval"
    APPEND_DATA = "append_data"
    SEND_AN_ALERT = "send_an_alert"
    PULL_CLOUD_FILES = "pull_cloud_files"
    APPLY_RETENTION_POLICY = "apply_retention_policy"


class AutomationConditionType(str, Enum):
    """Allowed condition types for an automation condition."""

    AT_SPECIFIC_TIME = "at_specific_time"
    NEW_DATA_ADDITION_IN_FOLDER = "new_data_addition_in_folder"
    RUN_CONFIG = "run_config"
    CLOUD_SOURCE_NAME_PATTERN = "cloud_source_name_pattern"


class AutomationConditionMode(str, Enum):
    """How multiple conditions are combined."""

    AND = "and"
    OR = "or"


class AutomationPatchOp(str, Enum):
    """Allowed JSON-patch op values for automation update."""

    REPLACE = "replace"
    COMMAND = "command"


class AutomationPatchPath(str, Enum):
    """Allowed JSON-patch path values for automation update."""

    DETAILS = "details"
    RUN = "run"
    STATUS = "status"
    APPROVE_RETENTION = "approve_retention"
    REJECT_RETENTION = "reject_retention"


class AutomationStatus(str, Enum):
    """Allowed automation status values for a ``replace + status`` patch.

    Each names the ACTION, not the status it leaves behind: ``suspend`` sets
    the status "suspended". The route takes these two and no others.
    """

    SUSPEND = "suspend"
    RESTORE = "restore"
    # The backend's own word is "restore"; "resume" is the SDK's friendlier
    # alias, kept for parity with ScheduleStatus and translated on the wire.
    RESUME = "resume"


class AlertType(str, Enum):
    """Alert delivery type."""

    EMAIL = "email"


# ── Automation param models ───────────────────────────────────────────────────


class DataRefreshConfig(BaseModel):
    """A single data-source entry for a ``run_data_retrieval`` task.

    Attributes:
        ds_id: ID of the data source to refresh.
    """

    ds_id: int


class TaskDetailsSpec(BaseModel):
    """Details payload for an automation task.

    Only the fields relevant to the chosen ``task_type`` need to be set; the
    SDK validates the required fields per task type before sending.
    """

    # run_data_retrieval
    ds_details: list[DataRefreshConfig] | None = None

    # append_data
    destination_dataset_ids: list[int] | None = None
    source_folder_resource_id: int | None = None
    source_dataset_id: int | None = None
    include_nested_folders: bool | None = None

    # pull_cloud_files
    connector_key: str | None = None
    connection_key: str | None = None
    connection_profile: str | list[str] | None = None
    # A connector may name a folder by more than a path — Drive sends an id too.
    cloud_source_folder_path: dict[str, str] | str | None = None
    destination_folder_resource_id: int | None = None

    # send_an_alert
    alert_type: AlertType | None = None
    subject: str | None = None
    recipients: list[str] | None = None
    message: str | None = None
    attachments: dict[str, Any] | None = Field(
        None,
        description=(
            "dataview_ids: view ids to email as attachments; each view is sent "
            "as a CSV file. The combined row count of all attached views must "
            "stay within 100,000 -- over that, the automation is refused (and "
            "a run that grows past it fails)."
        ),
    )
    test_email: bool = False

    # apply_retention_policy
    datasource_id: int | None = Field(
        default=None, description="Dataset the retention policy applies to"
    )
    rule_type: Literal["time_based", "count_based", "condition_based"] | None = None
    threshold_value: int | None = Field(
        default=None,
        description="Number of minutes/hours/days/weeks/months for time_based",
        ge=1,
    )
    threshold_unit: Literal["minutely", "hourly", "daily", "weekly", "monthly", "yearly"] | None = (
        None
    )
    keep_count: int | None = Field(
        default=None, description="Most-recent batches to keep for count_based", ge=1
    )
    condition_sql: str | None = Field(
        default=None, description="WHERE clause predicate for condition_based"
    )
    intent: str | None = None
    notify: bool = False
    notify_recipients: list[str] = Field(default_factory=list)
    notify_trigger: Literal["approval_and_policy_runs", "approval_only", "runs_only"] = (
        "approval_and_policy_runs"
    )
    require_approval: bool = False
    action: Literal["delete", "suspend"] = "delete"
    timezone: str | None = None

    # pdf_orchestration: one destination watches exactly one folder
    destination_dataset_id: int | None = Field(default=None, gt=0)

    # shared optional
    id: int | None = Field(default=None, gt=0)


class AutomationTaskSpec(BaseModel):
    """A single task in an automation.

    Attributes:
        task_type: The type of work this task performs.
        details: Task-type-specific parameters.
        conditions: Optional per-task conditions (backend passthrough).
    """

    task_type: AutomationTaskType
    details: TaskDetailsSpec | None = None
    conditions: list[dict[str, Any]] | None = None


class UniqueSequenceColumn(BaseModel):
    """The column a refresh reads to tell new rows from ones it already has."""

    c_name: str
    c_type: Literal["numeric", "date"]


class ConditionDetailsSpec(BaseModel):
    """Details for an automation condition.

    Fields are optional on the struct; required combinations are validated
    per ``condition_type`` in :class:`AutomationConditionSpec`.
    """

    interval: int | None = None
    frequency: RruleFrequency | None = None
    start_at: datetime | None = None
    until: datetime | None = None
    by_month_day: list[int] | None = None
    by_week_day: list[Weekday] | None = None
    start_now: bool = True
    file_contains: str | None = None
    execution_mode: Literal["parallel", "sequential"] = "parallel"
    trigger_type: Literal["manual", "schedule"] = "manual"
    on_refresh_action: Literal["replace", "combine", "append"] = "replace"
    unique_sequence_column: UniqueSequenceColumn | None = None
    contains: str | None = None
    starts_with: str | None = None
    ends_with: str | None = None
    exact_match_with: str | None = None
    include_subfolders: bool = False
    all_files: bool = False
    case_sensitive: bool = False


class AutomationConditionSpec(BaseModel):
    """A single condition for an automation.

    Attributes:
        condition_type: The type of condition.
        details: Condition-type-specific parameters.
    """

    condition_type: AutomationConditionType
    details: ConditionDetailsSpec


class PatchAutomationDetails(BaseModel):
    """Value payload for a ``replace + details`` automation patch operation.

    At least one field must be set (validated by the SDK).
    """

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: Literal["active", "suspended", "failed"] | None = None
    tasks: list[AutomationTaskSpec] | None = None
    conditions: list[AutomationConditionSpec] | None = None
    condition_mode: AutomationConditionMode | None = None


class AutomationPatchItem(BaseModel):
    """A single JSON-patch operation for :meth:`AutomationsAPI.update`.

    Attributes:
        op: The patch operation.
        path: The field to patch.
        value: Depends on op+path combo (see :meth:`AutomationsAPI.update`).
    """

    op: AutomationPatchOp
    path: AutomationPatchPath
    # ``union_mode="left_to_right"``, with ``PatchAutomationDetails`` ordered
    # before the catch-all ``dict[str, Any]``: pydantic's default "smart"
    # union mode picks the exact ``dict[str, Any]`` match over coercing a
    # dict into ``PatchAutomationDetails`` (which needs nested-model
    # construction), so a ``path="details"`` patch built from a plain dict --
    # every real caller, since ``AutomationsAPI.update`` is invoked from
    # parsed JSON -- left ``value`` a bare dict and failed
    # ``_validate_automation_patch_item``'s ``isinstance`` check even when a
    # field like ``name`` was set.
    value: Annotated[
        str | PatchAutomationDetails | dict[str, Any], Field(union_mode="left_to_right")
    ]
