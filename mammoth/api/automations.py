"""Automations API client for managing automations and schedules in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import (
    AutomationConditionMode,
    AutomationConditionSpec,
    AutomationConditionType,
    AutomationPatchItem,
    AutomationPatchOp,
    AutomationPatchPath,
    AutomationStatus,
    AutomationTaskSpec,
    AutomationTaskType,
    PatchAutomationDetails,
    ScheduleCreateSpec,
    SchedulePatchPath,
    SchedulePatchValue,
    ScheduleStatus,
)

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_AUTOMATION_NAME_EMPTY = "`name` must be a non-empty string."
ERR_AUTOMATION_TASKS_EMPTY = "`tasks` must contain at least one task."
ERR_TASK_DS_DETAILS_REQUIRED = (
    "task_type='run_data_retrieval' requires `details.ds_details` with at least one entry."
)
ERR_TASK_DEST_DATASETS_REQUIRED = (
    "task_type='append_data' requires `details.destination_dataset_ids`."
)
ERR_TASK_APPEND_SOURCE_REQUIRED = (
    "task_type='append_data' requires either `details.source_folder_resource_id` "
    "or `details.source_dataset_id`."
)
ERR_TASK_CLOUD_FILES_FIELDS = (
    "task_type='pull_cloud_files' requires `details.connector_key`, "
    "`details.connection_key`, `details.cloud_source_folder_path`, "
    "and `details.destination_folder_resource_id`."
)
ERR_TASK_ALERT_FIELDS = (
    "task_type='send_an_alert' requires `details.alert_type`, "
    "`details.recipients`, and `details.subject`."
)
ERR_CONDITION_AT_SPECIFIC_TIME = (
    "condition_type='at_specific_time' requires `details.interval` (> 0) " "and `details.start_at`."
)
ERR_CONDITION_BY_MONTH_DAY = "All `details.by_month_day` values must be between 1 and 31; got {0}."
ERR_AUTOMATION_ID_POSITIVE = "`automation_id` must be a positive integer, got {0}."
ERR_AUTOMATION_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."
ERR_PATCH_COMMAND_PATH = "op='command' requires path='run'."
ERR_PATCH_STATUS_VALUE = (
    "op='replace', path='status' value must be 'suspend' or 'resume', got {0!r}."
)
ERR_PATCH_DETAILS_EMPTY = (
    "op='replace', path='details' value must include at least one of: "
    "name, description, tasks, conditions."
)
ERR_SCHEDULE_ID_POSITIVE = "`schedule_id` must be a positive integer, got {0}."
ERR_SCHEDULE_PATCH_EMPTY = "`patch` must be a non-empty list of schedule patch operations."
ERR_SCHEDULE_PATCH_OP = "Only op='replace' is implemented for schedule patches, got {0!r}."
ERR_SCHEDULE_PATCH_PATH = "path must be 'rrule' or 'status', got {0!r}."
ERR_SCHEDULE_RRULE_VALUE = (
    "op='replace', path='rrule' requires value with both `rrule` and `work_items`."
)
ERR_SCHEDULE_STATUS_VALUE = (
    "op='replace', path='status' value must be 'pause' or 'resume', got {0!r}."
)
ERR_RRULE_INTERVAL_POSITIVE = "`rrule.interval` must be > 0, got {0}."
ERR_WORK_ITEM_FIELDS = "Each work item must have `name`, `execution_params`, and `args`."


# ── Schedule patch item model (shared with SchedulesAPI) ─────────────────────


class SchedulePatchItem(BaseModel):
    """A single JSON-patch operation for schedule update.

    Attributes:
        op: Must be ``"replace"`` (only implemented op).
        path: ``"rrule"`` or ``"status"``.
        value: For ``path='rrule'``: a
            :class:`~mammoth.models.automations.SchedulePatchValue` with both
            ``rrule`` and ``work_items``.  For ``path='status'``: a
            :class:`~mammoth.models.automations.ScheduleStatus` or the string
            ``"pause"`` / ``"resume"``.
    """

    op: str
    path: SchedulePatchPath
    value: SchedulePatchValue | ScheduleStatus | str


# ── Internal helpers ──────────────────────────────────────────────────────────


def _validate_task(task: AutomationTaskSpec) -> None:
    d = task.details
    tt = task.task_type
    if tt is AutomationTaskType.RUN_DATA_RETRIEVAL:
        if not d or not d.ds_details:
            raise MammothValidationError(ERR_TASK_DS_DETAILS_REQUIRED)
    elif tt is AutomationTaskType.APPEND_DATA:
        if not d or not d.destination_dataset_ids:
            raise MammothValidationError(ERR_TASK_DEST_DATASETS_REQUIRED)
        if not d.source_folder_resource_id and not d.source_dataset_id:
            raise MammothValidationError(ERR_TASK_APPEND_SOURCE_REQUIRED)
    elif tt is AutomationTaskType.PULL_CLOUD_FILES:
        if (
            not d
            or not d.connector_key
            or not d.connection_key
            or not d.cloud_source_folder_path
            or not d.destination_folder_resource_id
        ):
            raise MammothValidationError(ERR_TASK_CLOUD_FILES_FIELDS)
    elif tt is AutomationTaskType.SEND_AN_ALERT and (
        not d or not d.alert_type or not d.recipients or not d.subject
    ):
        raise MammothValidationError(ERR_TASK_ALERT_FIELDS)


def _validate_condition(cond: AutomationConditionSpec) -> None:
    d = cond.details
    if cond.condition_type is AutomationConditionType.AT_SPECIFIC_TIME and (
        not d.interval or d.interval <= 0 or d.start_at is None
    ):
        raise MammothValidationError(ERR_CONDITION_AT_SPECIFIC_TIME)
    if d.by_month_day:
        for v in d.by_month_day:
            if not (1 <= v <= 31):
                raise MammothValidationError(ERR_CONDITION_BY_MONTH_DAY.format(v))


def _task_to_dict(task: AutomationTaskSpec) -> dict[str, Any]:
    result: dict[str, Any] = {"task_type": task.task_type.value}
    if task.details is not None:
        result["details"] = task.details.model_dump(mode="json", exclude_unset=True)
    if task.conditions is not None:
        result["conditions"] = task.conditions
    return result


def _condition_to_dict(cond: AutomationConditionSpec) -> dict[str, Any]:
    return {
        "condition_type": cond.condition_type.value,
        "details": cond.details.model_dump(mode="json", exclude_unset=True),
    }


def _rrule_spec_to_dict(spec: ScheduleCreateSpec) -> dict[str, Any]:
    """Serialize a ScheduleCreateSpec to the wire body."""
    rrule: dict[str, Any] = {
        "frequency": spec.rrule.frequency.value,
        "start": spec.rrule.start.isoformat(),
    }
    if spec.rrule.interval is not None:
        rrule["interval"] = spec.rrule.interval
    if spec.rrule.by_week_day is not None:
        rrule["by_week_day"] = spec.rrule.by_week_day
    if spec.rrule.by_month_day is not None:
        rrule["by_month_day"] = spec.rrule.by_month_day
    body: dict[str, Any] = {"rrule": rrule}
    if spec.work_items is not None:
        body["work_items"] = [
            {
                "name": item.name.value,
                "execution_params": item.execution_params.model_dump(mode="json"),
                "args": item.args,
            }
            for item in spec.work_items
        ]
    return body


def _validate_schedule_create(spec: ScheduleCreateSpec) -> None:
    if spec.rrule.interval is not None and spec.rrule.interval <= 0:
        raise MammothValidationError(ERR_RRULE_INTERVAL_POSITIVE.format(spec.rrule.interval))


def _patch_value_to_dict(value: SchedulePatchValue) -> dict[str, Any]:
    """Serialize a SchedulePatchValue to the wire body."""
    rrule: dict[str, Any] = {
        "frequency": value.rrule.frequency.value,
        "start": value.rrule.start.isoformat(),
    }
    if value.rrule.interval is not None:
        rrule["interval"] = value.rrule.interval
    if value.rrule.by_week_day is not None:
        rrule["by_week_day"] = value.rrule.by_week_day
    if value.rrule.by_month_day is not None:
        rrule["by_month_day"] = value.rrule.by_month_day
    return {
        "rrule": rrule,
        "work_items": [
            {
                "name": item.name.value,
                "execution_params": item.execution_params.model_dump(mode="json"),
                "args": item.args,
            }
            for item in value.work_items
        ],
    }


def _validate_automation_patch_item(item: AutomationPatchItem) -> None:
    if item.op is AutomationPatchOp.COMMAND and item.path is not AutomationPatchPath.RUN:
        raise MammothValidationError(ERR_PATCH_COMMAND_PATH)
    if (
        item.op is AutomationPatchOp.REPLACE
        and item.path is AutomationPatchPath.STATUS
        and item.value not in {AutomationStatus.SUSPEND.value, AutomationStatus.RESUME.value}
    ):
        raise MammothValidationError(ERR_PATCH_STATUS_VALUE.format(item.value))
    if item.op is AutomationPatchOp.REPLACE and item.path is AutomationPatchPath.DETAILS:
        if not isinstance(item.value, PatchAutomationDetails):
            raise MammothValidationError(ERR_PATCH_DETAILS_EMPTY)
        v = item.value
        if not any([v.name, v.description, v.tasks, v.conditions]):
            raise MammothValidationError(ERR_PATCH_DETAILS_EMPTY)


def build_schedule_patch_ops(patch: _list[SchedulePatchItem]) -> _list[dict[str, Any]]:
    """Validate and serialize a list of SchedulePatchItems to wire ops.

    Shared by AutomationsAPI.update_schedule and SchedulesAPI.update.

    Args:
        patch: Non-empty list of :class:`SchedulePatchItem` to validate and
            serialize.

    Returns:
        List of wire-format op dicts ready for the schedule PATCH body.

    Raises:
        MammothValidationError: If any op is not ``"replace"``, any path is
            not ``"rrule"`` or ``"status"``, a ``rrule`` value is not a
            :class:`~mammoth.models.automations.SchedulePatchValue`, or a
            ``status`` value is not ``"pause"`` or ``"resume"``.
    """
    ops: _list[dict[str, Any]] = []
    for item in patch:
        if item.op != "replace":
            raise MammothValidationError(ERR_SCHEDULE_PATCH_OP.format(item.op))
        if item.path not in {SchedulePatchPath.RRULE, SchedulePatchPath.STATUS}:
            raise MammothValidationError(ERR_SCHEDULE_PATCH_PATH.format(item.path))

        op_dict: dict[str, Any] = {"op": item.op, "path": item.path.value}
        if item.path is SchedulePatchPath.RRULE:
            if not isinstance(item.value, SchedulePatchValue):
                raise MammothValidationError(ERR_SCHEDULE_RRULE_VALUE)
            op_dict["value"] = _patch_value_to_dict(item.value)
        else:
            val = item.value.value if isinstance(item.value, ScheduleStatus) else item.value
            if val not in {ScheduleStatus.PAUSE.value, ScheduleStatus.RESUME.value}:
                raise MammothValidationError(ERR_SCHEDULE_STATUS_VALUE.format(val))
            op_dict["value"] = val
        ops.append(op_dict)
    return ops


class AutomationsAPI:
    """Client for managing automations and schedules.

    Access via ``client.automations``::

        automations = client.automations.list()
        automation = client.automations.create(
            name="Nightly refresh",
            description="Pulls cloud data every night",
            tasks=[AutomationTaskSpec(
                task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
                details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
            )],
        )
        schedules = client.automations.list_schedules()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self) -> int:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return proj

    # ── Automations ──────────────────────────────────────────────

    def list(self) -> _list[dict[str, Any]]:
        """List all automations.

        Returns:
            List of automation dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations"
        )
        return response.get("automations", response if isinstance(response, _list) else [])

    def create(
        self,
        name: str,
        description: str,
        tasks: _list[AutomationTaskSpec],
        conditions: _list[AutomationConditionSpec] | None = None,
        condition_mode: AutomationConditionMode = AutomationConditionMode.AND,
    ) -> dict[str, Any]:
        """Create a new automation.

        Args:
            name: Automation name (non-empty).
            description: Human-readable description (may be empty string).
            tasks: Non-empty list of :class:`~mammoth.models.automations.AutomationTaskSpec`.
                Each task must supply the fields required by its ``task_type``.
            conditions: Optional list of
                :class:`~mammoth.models.automations.AutomationConditionSpec`.
            condition_mode: How multiple conditions are combined
                (``"and"`` or ``"or"``; default ``"and"``).

        Returns:
            Dict with created automation info.

        Raises:
            MammothValidationError: If *name* is empty, *tasks* is empty,
                a task is missing required fields for its type, or a condition
                is missing required fields for its type.
        """
        if not name:
            raise MammothValidationError(ERR_AUTOMATION_NAME_EMPTY)
        if not tasks:
            raise MammothValidationError(ERR_AUTOMATION_TASKS_EMPTY)
        for task in tasks:
            _validate_task(task)
        for cond in conditions or []:
            _validate_condition(cond)

        body: dict[str, Any] = {
            "name": name,
            "description": description,
            "tasks": [_task_to_dict(t) for t in tasks],
            "conditions": [_condition_to_dict(c) for c in conditions or []],
            "condition_mode": condition_mode.value,
        }
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations", json=body
        )

    def get(self, automation_id: int) -> dict[str, Any]:
        """Get automation details.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with automation details.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}"
        )

    def update(
        self,
        automation_id: int,
        patch: _list[AutomationPatchItem],
    ) -> dict[str, Any]:
        """Update an automation via JSON-patch operations.

        Args:
            automation_id: ID of the automation (must be > 0).
            patch: Non-empty list of :class:`~mammoth.models.automations.AutomationPatchItem`.

                Supported combos:

                * ``op=command, path=run`` — trigger the automation immediately.
                * ``op=replace, path=status`` — suspend or resume; ``value``
                  must be ``"suspend"`` or ``"resume"``.
                * ``op=replace, path=details`` — update fields; ``value`` must
                  be a :class:`~mammoth.models.automations.PatchAutomationDetails`
                  with at least one of name/description/tasks/conditions set.

        Returns:
            Dict with updated automation info.

        Raises:
            MammothValidationError: If *automation_id* ≤ 0, *patch* is empty,
                or an op+path+value combination is invalid.
        """
        if automation_id <= 0:
            raise MammothValidationError(ERR_AUTOMATION_ID_POSITIVE.format(automation_id))
        if not patch:
            raise MammothValidationError(ERR_AUTOMATION_PATCH_EMPTY)
        for item in patch:
            _validate_automation_patch_item(item)

        ops: _list[dict[str, Any]] = []
        for item in patch:
            op_dict: dict[str, Any] = {"op": item.op.value, "path": item.path.value}
            if item.op is AutomationPatchOp.COMMAND:
                op_dict["value"] = {}
            elif item.path is AutomationPatchPath.STATUS:
                op_dict["value"] = item.value
            else:
                assert isinstance(item.value, PatchAutomationDetails)
                op_dict["value"] = item.value.model_dump(mode="json", exclude_unset=True)
            ops.append(op_dict)

        body: dict[str, Any] = {"patch": ops}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}",
            json=body,
        )

    def delete(self, automation_id: int) -> dict[str, Any]:
        """Delete an automation.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}",
        )

    def restore(self, automation_id: int) -> dict[str, Any]:
        """Restore a trashed automation.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with the restored automation info.
        """
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}/restore",
        )

    def trash(self, automation_id: int) -> dict[str, Any]:
        """Move an automation to trash.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with the trashed automation info.
        """
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}/trash",
        )

    # ── Schedules ────────────────────────────────────────────────

    def list_schedules(self) -> _list[dict[str, Any]]:
        """List all schedules.

        Returns:
            List of schedule dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules"
        )
        return response.get("schedules", response if isinstance(response, _list) else [])

    def create_schedule(self, spec: ScheduleCreateSpec) -> dict[str, Any]:
        """Create a new schedule.

        Args:
            spec: :class:`~mammoth.models.automations.ScheduleCreateSpec` describing
                the recurrence rule and optional work items.

        Returns:
            Dict with created schedule info.

        Raises:
            MammothValidationError: If ``rrule.interval`` ≤ 0.
        """
        _validate_schedule_create(spec)
        body = _rrule_spec_to_dict(spec)
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules", json=body
        )

    def update_schedule(
        self,
        schedule_id: int,
        patch: _list[SchedulePatchItem],
    ) -> dict[str, Any]:
        """Update a schedule via JSON-patch operations.

        Args:
            schedule_id: ID of the schedule (must be > 0).
            patch: Non-empty list of :class:`SchedulePatchItem`.

                Supported combos:

                * ``op=replace, path=rrule`` — update recurrence rule + work items;
                  ``value`` must be a
                  :class:`~mammoth.models.automations.SchedulePatchValue`.
                * ``op=replace, path=status`` — pause or resume; ``value`` must
                  be ``"pause"`` or ``"resume"``.

        Returns:
            Dict with updated schedule info.

        Raises:
            MammothValidationError: If *schedule_id* ≤ 0, *patch* is empty,
                or an op+path+value combination is invalid.
        """
        if schedule_id <= 0:
            raise MammothValidationError(ERR_SCHEDULE_ID_POSITIVE.format(schedule_id))
        if not patch:
            raise MammothValidationError(ERR_SCHEDULE_PATCH_EMPTY)

        ops = build_schedule_patch_ops(patch)
        body: dict[str, Any] = {"patch": ops}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules/{schedule_id}",
            json=body,
        )

    def delete_schedule(self, schedule_id: int) -> dict[str, Any]:
        """Delete a schedule.

        Args:
            schedule_id: ID of the schedule.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules/{schedule_id}"
        )
