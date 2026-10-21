"""Every command's ``agent_example`` must be safe to copy and run.

A generated example once carried the literal ``"sample"`` for string fields, so
``view transform pivot`` grouped by a column named ``sample`` and
``dataset file-settings update`` set the delimiter to ``sample``; and
``view transform lookup`` omitted the field the command requires, so it was
refused with ``invalid_arguments``. This walks every command schema and runs
each example's ``--input`` through the command's own local validation (unknown
fields, scalar types, required fields); no network.
"""

from __future__ import annotations

import copy
import json
import re
import shlex
from typing import Any

import pytest

from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.positionals import resolve_positionals

#: ``schema get`` documents itself; no other command's example may be a pointer to it.
_SCHEMA_GET = "schema.get"
_HANDOFF = "mammoth schema get "
#: A placeholder, not data: the word ``sample`` as a whole word or segment (``sample_key``,
#: ``sample.csv``), or an angle-bracket template such as ``<role>``. A real host such as
#: ``sampledata.mammoth.io`` does not match.
_PLACEHOLDER = re.compile(r"(?<![A-Za-z])sample(?![A-Za-z])|<[A-Za-z_]+>", re.IGNORECASE)
#: ``--input FILE`` is allowed only where the request carries a secret (a password, a key):
#: a credential must never be put in argv, so the example points at a protected file.
_PROTECTED_FILE = re.compile(r"^/private/path/")
_NUMBER = re.compile(r"^\d+$")
#: Never synthesized: a credential document.
_NOT_SYNTHESIZED = {"auth.login"}
#: Resolved from the active dataset/project, not typed by the caller.
_RESOLVED_FIELDS = {"dataset_id"}


#: ``confirm_target`` commands whose target is not a positional the example can show: it is the
#: workspace (or the project ids in the request) the CLI resolves at run time. Their example
#: carries ``--yes``; the refusal names the exact target (``Pass --confirm N``).
_TARGET_RESOLVED_AT_RUN_TIME = frozenset(
    {
        "addon.connector.add",
        "addon.connector.remove",
        "addon.storage.add",
        "addon.storage.remove",
        "addon.user.add",
        "addon.user.remove",
        "agent.access.settings.update",
        "billing.hosted-page",
        "billing.invoice.charge",
        "billing.stripe.cancel",
        "billing.stripe.checkout-url",
        "billing.stripe.create",
        "billing.stripe.end-trial",
        "billing.stripe.held-change.cancel",
        "billing.stripe.portal-url",
        "billing.stripe.resume",
        "billing.stripe.retry-payment",
        "billing.stripe.storage.set",
        "billing.stripe.sync",
        "billing.subscription.update",
        "dataset.bulk-update",
        "dataset.update",
        "external-key.create",
        "project.bulk-delete",
        "project.bulk-update",
        "user.change-password",
        "user.delete-account",
        "workspace.user.update-batch",
    }
)


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    return []


def example_problems(record: dict[str, Any]) -> list[str]:
    """What is wrong with one record's ``agent_example`` (empty when it is runnable)."""
    command_id = record["command_id"]
    example = record["agent_example"]
    if command_id in _NOT_SYNTHESIZED or command_id == _SCHEMA_GET:
        return []
    problems: list[str] = []
    if example.startswith(_HANDOFF):
        return ["the example is a pointer to 'schema get', not a runnable command"]
    tokens = shlex.split(example)
    policy = record.get("confirmation", "none")
    if policy != "none":
        if "--yes" not in tokens:
            problems.append(f"policy {policy} needs --yes in the example")
        if policy == "confirm_target" and command_id not in _TARGET_RESOLVED_AT_RUN_TIME:
            if "--confirm" not in tokens:
                problems.append("confirm_target needs --confirm TARGET in the example")
            else:
                given_target = tokens[tokens.index("--confirm") + 1]
                positional_tokens = tokens[1 + len(record["command_path"].split()) :]
                if given_target not in positional_tokens[: positional_tokens.index("--yes")]:
                    problems.append("--confirm does not equal a positional of the example")
    # The command's own words are not data (``project sample-flow`` is a real command).
    if any(
        _PLACEHOLDER.search(token) for token in tokens[1 + len(record["command_path"].split()) :]
    ):
        problems.append("a placeholder string ('sample' or <name>) is in the command line")
    # Distinct ids in the documented positional order: ``123 123`` hides which is which.
    command_tokens = 1 + len(record["command_path"].split())
    end = command_tokens
    while end < len(tokens) and not tokens[end].startswith("-"):
        end += 1
    numbers = [t for t in tokens[command_tokens:end] if _NUMBER.match(t)]
    if len(numbers) != len(set(numbers)):
        problems.append(f"positional ids repeat: {' '.join(numbers)}")
    document: dict[str, Any] | None = None
    if "--input" in tokens:
        raw = tokens[tokens.index("--input") + 1]
        if _PROTECTED_FILE.match(raw):
            if not record.get("secret_fields"):
                problems.append("--input points at a file but the request carries no secret")
            return problems
        if not raw.startswith("{"):
            return [*problems, "--input is neither inline JSON nor a protected secret file"]
        try:
            document = json.loads(raw)
        except ValueError:
            return [*problems, "--input is not valid JSON"]
    contract = resolve_command_contract(command_id)
    if contract is None:
        return problems
    given = set(document or {})
    positional_names = [p.name for p in resolve_positionals(command_id)]
    covered = set(positional_names)
    if (
        "dataset_id" in positional_names
        and len(numbers) >= positional_names.index("dataset_id") + 1
    ):
        covered.add("dataset_id")
    for field in contract.accepted_fields:
        if field.required and field.name not in given and field.name not in covered:
            problems.append(f"required field '{field.name}' is missing")
    if document is None:
        return problems
    try:
        validate_input_fields(command_id, copy.deepcopy(document))
    except Exception as error:  # noqa: BLE001 -- any rejection is a broken example
        problems.append(f"local validation: {getattr(error, 'code', error)}")
    return problems


def test_every_agent_example_is_runnable() -> None:
    broken = {
        record["command_id"]: problems
        for record in load_commands()
        if record.get("disposition") != "alias" and (problems := example_problems(record))
    }
    assert broken == {}


@pytest.mark.parametrize(
    ("command_id", "expected"),
    [
        ("view.transform.lookup", ("new_column", "existing_column")),
    ],
)
def test_examples_name_the_field_the_command_requires_one_of(
    command_id: str, expected: tuple[str, ...]
) -> None:
    record = next(r for r in load_commands() if r["command_id"] == command_id)
    document = json.loads(
        shlex.split(record["agent_example"])[
            shlex.split(record["agent_example"]).index("--input") + 1
        ]
    )
    assert any(name in document for name in expected)


def test_file_settings_example_uses_single_character_delimiters() -> None:
    record = next(r for r in load_commands() if r["command_id"] == "dataset.file-settings.update")
    tokens = shlex.split(record["agent_example"])
    document = json.loads(tokens[tokens.index("--input") + 1])
    assert len(document["delimiter"]) == 1 and len(document["quotechar"]) == 1


def test_the_checker_flags_the_old_broken_examples() -> None:
    base = {"disposition": "command", "agent_example": "", "command_path": "view transform pivot"}
    lookup = {
        **base,
        "command_id": "view.transform.lookup",
        "command_path": "view transform lookup",
        "agent_example": (
            "mammoth view transform lookup 123 --input "
            + shlex.quote(
                json.dumps({"source": "A", "lookup_view_id": 1, "key": "A", "value": "sample"})
            )
        ),
    }
    assert example_problems(lookup)
    pivot = {
        **base,
        "command_id": "view.transform.pivot",
        "agent_example": (
            "mammoth view transform pivot 123 --input "
            + shlex.quote(json.dumps({"group_by": ["sample"], "aggregations": []}))
        ),
    }
    assert any("placeholder" in problem for problem in example_problems(pivot))
    twice = {
        **base,
        "command_id": "batch.get",
        "command_path": "batch get",
        "agent_example": "mammoth batch get 123 123",
    }
    assert any("repeat" in problem for problem in example_problems(twice))
    pointer = {**base, "command_id": "data-app.create", "agent_example": "mammoth schema get x"}
    assert any("pointer" in problem for problem in example_problems(pointer))


def test_the_walk_covers_every_command_in_the_registry() -> None:
    records = [r for r in load_commands() if r.get("disposition") != "alias"]
    assert len(records) > 700
    assert all(r.get("agent_example") for r in records)


def test_the_same_checks_flag_the_published_sweep_findings() -> None:
    """The counts the offline sweep found, as properties that must now be zero."""
    records = [r for r in load_commands() if r.get("disposition") != "alias"]
    examples = [(r["command_id"], r["agent_example"]) for r in records]
    assert [c for c, e in examples if _PLACEHOLDER.search(e) and "sample-flow" not in e] == []
    assert [c for c, e in examples if "/private/path" in e and c not in _secret_commands()] == []
    assert [c for c, e in examples if e.startswith(_HANDOFF) and c != _SCHEMA_GET] == []


def _secret_commands() -> set[str]:
    return {r["command_id"] for r in load_commands() if r.get("secret_fields")}
