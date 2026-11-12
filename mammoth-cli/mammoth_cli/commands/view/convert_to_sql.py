"""Convert rules to one SQL rule: ``view task convert-plan``, ``convert-generate`` and ``convert``.

The server decides where a run of rules is cut. The caller names rules by their number (the
number the user sees; the task ``sequence``) and the CLI turns them into task ids.
"""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _forward_optional,
    _meta,
    _require_exact_parent,
    _require_int_positional_at,
    _resolve_dataset_id,
)
from mammoth_cli.errors.envelope import (
    CODE_API_ERROR,
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_RESOURCE_NOT_FOUND,
    CODE_UNSUPPORTED_BY_SERVER,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

_PLAN_SYMBOL = "mammoth.api.pipeline.PipelineAPI.plan_sql_conversion"
_CONVERT_SYMBOL = "mammoth.api.pipeline.PipelineAPI.convert_to_sql"
_TASK_LIST_SYMBOL = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_PREVIEW_SYMBOL = "mammoth.api.pipeline.PipelineAPI.preview_task"
_GENERATE_SQL_SYMBOL = "mammoth.api.ai.AIAPI.generate_sql"

_NOT_SUPPORTED = "This server does not support convert-to-sql yet."
_NOT_SUPPORTED_HINT = (
    "Update the server. Do not delete the rules one by one to replace them with a SQL rule: "
    "that makes one version per step and loses the text."
)

#: What each reason of a cut means, in plain words.
CUT_REASONS: dict[str, str] = {
    "rule_type_not_supported": (
        "This rule cannot be written as SQL (join, lookup, GenAI, metric or pivot). "
        "It stays as it is."
    ),
    "rule_not_active": "This rule is suspended. It stays as it is.",
    "single_rule": (
        "Only one rule can be converted here, so there is nothing to gain. It stays as it is."
    ),
    "not_selected": (
        "You did not select this rule, and it sits inside the selected span. " "It stays as it is."
    ),
    "gate_between_rules": (
        "A checkpoint, data check or export sits after this rule, so the rules are cut here."
    ),
}

#: The refusals of the convert route (HTTP 400), each in plain words.
REFUSALS: dict[str, str] = {
    "4DTVW039": "A group has fewer than two rules. Pick at least two consecutive rules.",
    "4DTVW040": "A rule in a group is not active (suspended). Leave it out of the group.",
    "4DTVW041": (
        "The rules in a group are not consecutive. "
        "Use the groups that 'view task convert-plan' returns."
    ),
    "4DTVW042": (
        "A rule in a group cannot be written as SQL (join, lookup, GenAI, metric or pivot)."
    ),
    "4DTVW043": (
        "A checkpoint, data check or export sits between the rules of a group. "
        "Convert each side on its own."
    ),
    "4DTVW044": (
        "The output of the pipeline is not available. Run the pipeline first, then try again."
    ),
    "4DTVW045": "The pipeline refused the change.",
}

_RANGE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def _invalid(message: str, hint: str | None = None) -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENT, message=message, exit_status=EXIT_USAGE, hint=hint)


def parse_rules(value: Any) -> list[int]:
    """Rule numbers from ``8``, ``"1-8"``, ``"1,3,5-6"`` or a list of those."""
    items = value if isinstance(value, list) else [value]
    numbers: list[int] = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, (int, str)):
            raise _invalid(f"Rule {item!r} is not a rule number.")
        if isinstance(item, int):
            numbers.append(item)
            continue
        for part in item.split(","):
            found = _RANGE.match(part)
            if found:
                first, last = int(found.group(1)), int(found.group(2))
                if first > last:
                    raise _invalid(f"The rule range {part.strip()!r} runs backwards.")
                numbers.extend(range(first, last + 1))
            elif part.strip().isdigit():
                numbers.append(int(part))
            else:
                raise _invalid(
                    f"Rule {part.strip()!r} is not a rule number.",
                    "Use a number, a range such as 1-8, or a list such as 1,3,5-6.",
                )
    if not numbers or any(n < 1 for n in numbers):
        raise _invalid("Rule numbers start at 1.")
    return sorted(set(numbers))


def _sequence_to_id(service: Any, view_id: int, dataset_id: int) -> dict[int, int]:
    """Rule number -> task id of the view's rules."""
    listing = service.call(_TASK_LIST_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
    tasks = listing.get("tasks") if isinstance(listing, dict) else None
    if not isinstance(tasks, list):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"Could not read the rules of view {view_id}.",
            exit_status=EXIT_API,
            details={"response": listing},
        )
    return {int(t["sequence"]): int(t["id"]) for t in tasks if isinstance(t, dict) and "id" in t}


def _ids_for_rules(rules: list[int], by_sequence: dict[int, int], view_id: int) -> list[int]:
    missing = [n for n in rules if n not in by_sequence]
    if missing:
        raise _invalid(
            f"View {view_id} has no rule {', '.join(map(str, missing))}; "
            f"it has {len(by_sequence)} rules.",
            f"Read the rules first: mammoth view task list {view_id}",
        )
    return [by_sequence[n] for n in rules]


def _rule_numbers(task_ids: list[int], by_sequence: dict[int, int], view_id: int) -> list[int]:
    by_id = {task_id: sequence for sequence, task_id in by_sequence.items()}
    unknown = [t for t in task_ids if t not in by_id]
    if unknown:
        raise _invalid(f"View {view_id} has no task {', '.join(map(str, unknown))}.")
    return sorted(by_id[t] for t in task_ids)


def _text_of(group: dict[str, Any], index: int) -> str:
    text = group.get("text")
    if not isinstance(text, str) or not text.strip():
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"Group {index + 1} needs a 'text' that says what its rules do. It is blank.",
            exit_status=EXIT_USAGE,
            hint=(
                "Write the text from the rules you read: what they filter, add, change "
                "and in what order."
            ),
        )
    return text.strip()


def _groups_of(document: dict[str, Any]) -> list[dict[str, Any]]:
    groups = document.get("groups")
    if not isinstance(groups, list) or not groups:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=(
                "This command requires the 'groups' input field: "
                "a list with one entry per group."
            ),
            exit_status=EXIT_USAGE,
            hint='Example: --input \'{"groups": [{"rules": "1-3", "text": "what the rules do"}]}\'',
        )
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise _invalid(f"Group {index + 1} must be an object.")
        if "rules" not in group and "task_ids" not in group:
            raise CliError(
                code=CODE_MISSING_FIELD,
                message=f"Group {index + 1} needs 'rules' (rule numbers) or 'task_ids'.",
                exit_status=EXIT_USAGE,
            )
    return groups


def _group_ids(group: dict[str, Any], by_sequence: dict[int, int], view_id: int) -> list[int]:
    if "task_ids" in group:
        ids = [int(t) for t in group["task_ids"]]
        _rule_numbers(ids, by_sequence, view_id)
        return ids
    return _ids_for_rules(parse_rules(group["rules"]), by_sequence, view_id)


def _unsupported(error: CliError) -> CliError:
    return CliError(
        code=CODE_UNSUPPORTED_BY_SERVER,
        message=_NOT_SUPPORTED,
        exit_status=EXIT_API,
        hint=_NOT_SUPPORTED_HINT,
        details={"status_code": 404},
        request_id=error.request_id,
    )


def _is_not_found(error: CliError) -> bool:
    return error.code == CODE_RESOURCE_NOT_FOUND or (error.details or {}).get("status_code") == 404


def _explain(error: CliError) -> CliError:
    """The route's refusals in plain words; a 404 means the server lacks the route."""
    if _is_not_found(error):
        return _unsupported(error)
    refusal = (error.details or {}).get("backend_code")
    if refusal in REFUSALS:
        return CliError(
            code=error.code,
            message=f"{REFUSALS[refusal]} ({refusal}; nothing was changed)",
            exit_status=error.exit_status,
            hint="Run 'view task convert-plan' again and use the groups it returns.",
            details={**error.details, "server_message": error.message},
            request_id=error.request_id,
        )
    return error


def view_task_convert_plan(invocation: Invocation) -> HandlerResult:
    """Show how rules would be grouped into SQL rules, and where and why they are cut.

    ``rules`` (an ``--input`` field: ``"1-8"``, ``"1,3,5"`` or a list) picks the rules; with
    none, the whole pipeline is planned. Changes nothing.
    """
    view_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    rules = parse_rules(document["rules"]) if "rules" in document else None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        by_sequence = _sequence_to_id(service, view_id, dataset_id)
        kwargs: dict[str, Any] = {"dataview_id": view_id, "dataset_id": dataset_id}
        if rules is not None:
            kwargs["task_ids"] = _ids_for_rules(rules, by_sequence, view_id)
        try:
            plan = service.call(_PLAN_SYMBOL, **kwargs)
        except CliError as error:
            raise _explain(error) from error
    return _show_plan(plan, view_id, dataset_id), _meta(invocation, auth.workspace_id, None)


def _show_plan(plan: dict[str, Any], view_id: int, dataset_id: int) -> dict[str, Any]:
    groups = [
        {
            "rules": list(range(g["first_sequence"], g["last_sequence"] + 1)),
            "first_rule": g["first_sequence"],
            "last_rule": g["last_sequence"],
            "task_ids": g["task_ids"],
        }
        for g in plan.get("groups", [])
    ]
    cuts = [
        {
            "rule": c["sequence"],
            "task_id": c.get("task_id"),
            "reason": c["reason"],
            "why": CUT_REASONS.get(c["reason"], c["reason"]),
        }
        for c in plan.get("cuts", [])
    ]
    shown: dict[str, Any] = {
        "view_id": view_id,
        "dataset_id": dataset_id,
        "groups": groups,
        "cuts": cuts,
        "changed": False,
        "note": (
            "Nothing changed. The server chose these groups and cuts. Tell the user what each "
            "cut means before you go on."
        ),
    }
    if groups:
        shown["next"] = (
            f"For each group write a text that says what its rules do, then run: mammoth view "
            f"task convert-generate {view_id} --input "
            + shlex.quote(
                json.dumps(
                    {
                        "dataset_id": dataset_id,
                        "groups": [
                            {
                                "rules": f"{g['first_rule']}-{g['last_rule']}",
                                "text": "<what the rules do>",
                            }
                            for g in groups
                        ],
                    }
                )
            )
        )
    return shown


def _query_of(generated: Any) -> str:
    """The SQL of a ``sql_generation`` answer (a job whose response holds ``result``)."""
    query: Any
    if isinstance(generated, str):
        query = generated
    else:
        response = generated.get("response", generated) if isinstance(generated, dict) else {}
        inner = response.get("response", response) if isinstance(response, dict) else {}
        query = inner.get("result") if isinstance(inner, dict) else None
    if not isinstance(query, str) or not query.strip():
        raise CliError(
            code=CODE_API_ERROR,
            message="The server returned no SQL for this group.",
            exit_status=EXIT_API,
            details={"response": generated},
        )
    return query


def view_task_convert_generate(invocation: Invocation) -> HandlerResult:
    """Write the SQL for each group and preview its result. Changes nothing.

    ``groups`` is a list of ``{"rules": "1-3" | "task_ids": [...], "text": "..."}``. The answer
    holds the SQL and the preview of each group, and the ready ``view task convert`` command
    with those exact queries, so the saved SQL equals the previewed SQL.
    """
    view_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    groups = _groups_of(document)
    texts = [_text_of(group, index) for index, group in enumerate(groups)]
    # Imported here: view_ops imports the view package.
    from mammoth_cli.commands.view_ops.transforms import _bind_view_table

    results: list[dict[str, Any]] = []
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        by_sequence = _sequence_to_id(service, view_id, dataset_id)
        for group, text in zip(groups, texts, strict=True):
            ids = _group_ids(group, by_sequence, view_id)
            rules = _rule_numbers(ids, by_sequence, view_id)
            generated = service.call(
                _GENERATE_SQL_SYMBOL,
                intent=text,
                sequence_number=rules[0],
                dataset_id=dataset_id,
                dataview_id=view_id,
                task_ids=ids,
            )
            query = _bind_view_table(service, dataset_id, view_id, _query_of(generated), invocation)
            spec = {
                "DATAVIEW_ID": view_id,
                "SEQUENCE_NUMBER": rules[0],
                "SQL": {"USER_QUERY": query, "INTENT": text},
            }
            preview = service.call(
                _PREVIEW_SYMBOL, dataview_id=view_id, task_spec=spec, dataset_id=dataset_id
            )
            results.append(
                {"rules": rules, "task_ids": ids, "text": text, "sql": query, "preview": preview}
            )
    project_id = resolved_project(invocation)
    body = {
        "dataset_id": dataset_id,
        "groups": [
            {"task_ids": r["task_ids"], "text": r["text"], "query": r["sql"]} for r in results
        ],
    }
    scope = f" --project {project_id}" if project_id is not None else ""
    data = {
        "view_id": view_id,
        "groups": results,
        "changed": False,
        "note": (
            "The view is unchanged. Show the user each text, SQL and preview. After they approve, "
            "run 'convert' (add --yes)."
        ),
        "convert": (
            f"mammoth view task convert {view_id} "
            f"--input {shlex.quote(json.dumps(body))}{scope}"
        ),
    }
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_task_convert(invocation: Invocation) -> HandlerResult:
    """Replace each group of rules by one SQL rule, in one save. Prompt or ``--yes`` required.

    ``groups`` is a list of ``{"rules" | "task_ids", "text", "query"}``. A blank ``text`` or
    ``query`` is refused before any request. The rules are replaced for good: one pipeline
    version holds the change.
    """
    view_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    groups = _groups_of(document)
    texts = [_text_of(group, index) for index, group in enumerate(groups)]
    queries = [_query_field(group, index) for index, group in enumerate(groups)]
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"replace rules of view {view_id} by SQL rules",
    )
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, view_id, kwargs)
        by_sequence = _sequence_to_id(service, view_id, kwargs["dataset_id"])
        body = [
            {
                "task_ids": _group_ids(group, by_sequence, view_id),
                "SQL": {"USER_QUERY": query, "INTENT": text},
            }
            for group, text, query in zip(groups, texts, queries, strict=True)
        ]
        try:
            data = service.call(_CONVERT_SYMBOL, groups=body, **kwargs)
        except CliError as error:
            raise _explain(error) from error
    return data, _meta(invocation, auth.workspace_id, None)


def _query_field(group: dict[str, Any], index: int) -> str:
    query = group.get("query")
    if not isinstance(query, str) or not query.strip():
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=(
                f"Group {index + 1} needs a 'query': "
                "the SQL that 'view task convert-generate' returned."
            ),
            exit_status=EXIT_USAGE,
        )
    return query
