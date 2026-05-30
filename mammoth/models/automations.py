"""Automation and schedule data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

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
        by_week_day: Days of the week, e.g. ``["MO", "WE"]``.
        by_month_day: Days of the month (1–31).
    """

    frequency: RruleFrequency
    start: datetime
    interval: int | None = None
    by_week_day: list[str] | None = None
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


class AutomationStatus(str, Enum):
    """Allowed automation status values for a ``replace + status`` patch."""

    SUSPEND = "suspend"
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
    cloud_source_folder_path: str | None = None
    destination_folder_resource_id: int | None = None

    # send_an_alert
    alert_type: AlertType | None = None
    subject: str | None = None
    recipients: list[str] | None = None
    message: str | None = None
    attachments: dict[str, Any] | None = None
    test_email: bool = False

    # shared optional
    id: int | None = None


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
    by_week_day: list[str] | None = None
    start_now: bool = True
    file_contains: str | None = None
    execution_mode: str | None = None
    trigger_type: str | None = None
    on_refresh_action: str | None = None
    unique_sequence_column: dict[str, str] | None = None
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

    name: str | None = None
    description: str | None = None
    status: str | None = None
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
    value: str | dict[str, Any] | PatchAutomationDetails
