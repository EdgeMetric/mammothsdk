"""Pure helpers for adding a file to an existing dataset: no HTTP, no client.

A dataset has an update method (``data_addition_mode``, "Update Method" in the web
app): ``combine`` (the caller's word: ``add``) puts a new file's rows under the rows
the dataset holds, ``replace`` throws the old rows away and keeps the new ones. Every
upload into the dataset follows it.

Adding a file makes a batch, which is what can be removed again. This module holds the
vocabulary (mode words and what each does), the matching of an upload's batches among
the ones that merely appeared meanwhile, and the report built from what was read before
and after. ``mammoth.api.appends.AppendsAPI`` does the reading and calls these.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

#: The caller's word for each stored mode, and the stored name for each word.
STORED_MODES: dict[str, str] = {"add": "combine", "replace": "replace"}
MODE_WORDS: dict[str, str] = {stored: word for word, stored in STORED_MODES.items()}
#: Other words accepted for a mode, with the word they stand for.
MODE_ALIASES: dict[str, str] = {"combine": "add", "append": "add"}
#: What each mode does to the next file, said plainly.
EFFECTS: dict[str, str] = {
    "add": "Each new file adds its rows to the rows the dataset holds.",
    "replace": "Each new file replaces the rows the dataset holds.",
}
#: The modes under which a batch is added and can be removed again.
ADDING_MODES = frozenset({"add"})
#: Said when a batch is asked to be removed and nothing records how it was added.
NO_RECORD = (
    "Batch {0} was not added through this client, so what it was added under is not known:"
    " it is not removed. Remove it in Mammoth."
)
#: Said when a batch was added under a mode that replaced the rows.
NOT_ADDED = (
    "Batch {0} was added under the update method {1}: the dataset's rows depend on it, so it"
    " is not removed. To get the old rows back, upload the old file again."
)
#: Said when removing the batches would leave the dataset with none.
WOULD_EMPTY = (
    "Removing {0} would remove every batch the dataset has and leave it empty: it is not"
    " removed. Delete the dataset instead, if that is what the user wants."
)
#: Said of an update method that could not be read.
UNKNOWN_EFFECT = "Unknown: the dataset's update method could not be read."
#: Dataset statuses in which the dataset is no longer taking rows in.
SETTLED_STATUSES = frozenset({"ready", "processed", "empty"})
#: Dataset statuses of an upload that failed.
FAILED_STATUSES = frozenset({"error", "failed", "failure"})
#: The flag the server sets on an uploaded file's ``additional_data`` when its columns do not
#: match the dataset it was to be appended to, and the key of the dataset it names.
SCHEMA_MISMATCH_FLAG = "schema_mismatch"
SCHEMA_MISMATCH_TARGET = "schema_mismatch_target_ds_id"
#: The ``failure`` an append reports when the server held the file back for its columns.
FAILURE_SCHEMA_MISMATCH = "schema_mismatch"
#: Said when the server held a file back instead of appending it.
SCHEMA_MISMATCH_REASON = (
    "The server did not append the file: its columns do not match dataset {0}'s (a column the"
    " dataset has is missing, or a column has another type). Nothing was added to dataset {0}."
    " The file's own dataset {1} is kept in the project as a separate dataset that still holds"
    " the rows."
)
#: What to do about it.
SCHEMA_MISMATCH_NEXT = (
    "Compare the file's columns with dataset {0}'s. Fix the file and upload it again, or delete"
    " the kept dataset {1} if it is not wanted."
)
#: Said when ``override_target_schema`` is asked for under a method the server ignores it for.
OVERRIDE_NEEDS_REPLACE = (
    "override_target_schema has no effect unless the dataset's update method is 'replace': the"
    " server applies it only when the upload also replaces the dataset's rows, so under '{0}'"
    " a column mismatch would hold the file back as before. Nothing was uploaded. To replace"
    " the dataset's columns and rows with the file's, pass mode 'replace' as well: that DELETES"
    " the rows the dataset holds now."
)


class UnknownUpdateMethodError(ValueError):
    """A stored or asked-for update method this SDK does not know.

    Guessing which way an unknown mode goes could delete rows, so it is never mapped
    to a known one.
    """


def mode_word(stored: Any) -> str:
    """The caller's word (``add`` or ``replace``) for a stored mode.

    Args:
        stored: The stored ``data_addition_mode``. None or an empty value means the
            dataset has none stored, and the platform then adds.

    Returns:
        ``add`` or ``replace``.

    Raises:
        UnknownUpdateMethodError: If the value is stored and is not a known mode.
    """
    if stored is None or stored == "":
        return "add"
    word = MODE_WORDS.get(stored) if isinstance(stored, str) else None
    if word is None:
        raise UnknownUpdateMethodError(f"The dataset's update method {stored!r} is not known.")
    return word


def stored_mode(word: Any) -> str:
    """The stored name (``combine`` or ``replace``) for a caller's word.

    Args:
        word: ``add``, ``replace`` or one of the aliases ``combine`` and ``append``.

    Returns:
        ``combine`` or ``replace``.

    Raises:
        UnknownUpdateMethodError: If the word is not one of those.
    """
    key = word.strip().lower() if isinstance(word, str) else None
    resolved = MODE_ALIASES.get(key, key) if key else None
    if resolved is None or resolved not in STORED_MODES:
        raise UnknownUpdateMethodError(f"'mode' must be 'replace' or 'add', got {word!r}.")
    return STORED_MODES[resolved]


def refuse_batch_removal(
    batch_ids: Sequence[int],
    recorded: Mapping[int, str | None],
    existing_ids: Sequence[int],
) -> str | None:
    """Say why batches may not be removed, or None when they may.

    A batch is removed only when it was recorded, at upload time, as added under a mode that
    adds (:data:`ADDING_MODES`). One with no record (added elsewhere, or the record expired)
    and one added under a replace are refused: the dataset's current mode says nothing of how
    they were made. Removing every batch a dataset has is refused too, as it would leave it
    empty.

    Args:
        batch_ids: The batches asked to be removed.
        recorded: The mode word recorded for each batch id; absent or None when none is.
        existing_ids: The ids of every batch the dataset has now.

    Returns:
        The reason, for the user and the model, or None.
    """
    for batch_id in batch_ids:
        mode = recorded.get(batch_id)
        if mode is None:
            return NO_RECORD.format(batch_id)
        if mode not in ADDING_MODES:
            return NOT_ADDED.format(batch_id, mode)
    if set(existing_ids) <= set(batch_ids):
        return WOULD_EMPTY.format(sorted(set(batch_ids)))
    return None


def refuse_override(override: Any, mode: str | None) -> str | None:
    """Say why ``override_target_schema`` may not be sent, or None when it may.

    The server adopts the file's columns as the dataset's only when the dataset's update
    method is ``replace`` (the public upload route turns that into "delete the existing rows
    after the append", and the override needs both). Under ``add``, or an unknown method, the
    flag is dropped silently and a schema mismatch holds the file back.

    Args:
        override: The ``override_target_schema`` the caller asked for.
        mode: The update method the upload will run under (``add``, ``replace``), or None
            when it could not be read.

    Returns:
        The reason, or None when the flag is off or the method is ``replace``.
    """
    if not override or mode == "replace":
        return None
    return OVERRIDE_NEEDS_REPLACE.format(mode if mode is not None else "unknown")


def held_back(pending: Iterable[Any], target: int) -> list[dict[str, Any]]:
    """The pending items the server flagged as held back for ``target``'s schema.

    Args:
        pending: The ``pending_batches`` the target's batch listing holds.
        target: The dataset the files were to be appended to.

    Returns:
        The items whose ``additional_data`` carries :data:`SCHEMA_MISMATCH_FLAG` and names
        ``target``, and whose ``dataset_id`` is an int.
    """
    items: list[dict[str, Any]] = []
    for item in pending:
        extra = item.get("additional_data") if isinstance(item, dict) else None
        if (
            isinstance(extra, dict)
            and extra.get(SCHEMA_MISMATCH_FLAG) is True
            and extra.get(SCHEMA_MISMATCH_TARGET) == target
            and isinstance(item.get("dataset_id"), int)
        ):
            items.append(item)
    return items


def schema_mismatches(
    pending: Iterable[Any],
    target: int,
    known: Iterable[int],
    staging_ids: Iterable[int],
    sent: Sequence[str],
) -> list[int]:
    """The files the server held back for ``target`` because their columns do not match.

    The server lists such a file as a pending batch of the target whose ``additional_data``
    carries :data:`SCHEMA_MISMATCH_FLAG` and the target's id. One counts as this upload's when
    it is not in ``known`` (those listed before the upload) and is the staging dataset the
    upload made or names a file that was sent.

    Args:
        pending: The ``pending_batches`` the target's batch listing holds.
        target: The dataset the file was to be appended to.
        known: Dataset ids of held-back files already listed before the upload.
        staging_ids: The staging dataset ids the upload job made.
        sent: The names of the files that were sent.

    Returns:
        The ids of the datasets the held-back files became (``dataset_id`` of each item).
    """
    skip = set(known)
    staging = set(staging_ids)
    wanted = {name.lower() for name in sent} | {PurePosixPath(n).stem.lower() for n in sent}
    found: list[int] = []
    for item in held_back(pending, target):
        dataset_id = item["dataset_id"]
        if dataset_id in skip:
            continue
        labels = batch_labels({"source": item.get("source"), "name": item.get("name")})
        stems = {PurePosixPath(label).stem for label in labels}
        if dataset_id in staging or labels & wanted or stems & wanted:
            found.append(dataset_id)
    return found


def describe_update_method(result: Any) -> dict[str, Any]:
    """Say what a dataset's update method means for the next file.

    Args:
        result: What ``DatasetsAPI.get_update_method`` returned (the stored settings),
            or ``set_update_method`` (``{"data_addition_mode",
            "previous_data_addition_mode", "schema_settings"}``). Empty for a dataset
            with nothing stored.

    Returns:
        ``mode`` (``add`` or ``replace``), its ``effect`` in words and the
        ``schema_mapping`` that matches a file's columns to the dataset's; after a
        change also ``previous_mode`` and ``changed``.

    Raises:
        UnknownUpdateMethodError: If a stored mode is not a known one.
    """
    body = result if isinstance(result, dict) else {}
    settings = body.get("schema_settings", body)
    mode = mode_word(body.get("data_addition_mode"))
    shaped: dict[str, Any] = {
        "mode": mode,
        "effect": EFFECTS[mode],
        "schema_mapping": settings.get("schema_mapping") if isinstance(settings, dict) else None,
    }
    if "previous_data_addition_mode" in body:
        previous = mode_word(body.get("previous_data_addition_mode"))
        shaped["previous_mode"] = previous
        shaped["changed"] = previous != mode
    return shaped


def unknown_update_method(error: str) -> dict[str, Any]:
    """The ``update_method`` entry for a mode that could not be read, with why."""
    return {"mode": None, "effect": UNKNOWN_EFFECT, "error": error}


def sent_names(files: Any) -> list[str]:
    """The base names of the files an upload sends (paths, or file objects with a name)."""
    names: list[str] = []
    for item in files if isinstance(files, list) else [files]:
        raw = item if isinstance(item, (str, Path)) else getattr(item, "name", None)
        if isinstance(raw, (str, Path)) and str(raw):
            names.append(PurePosixPath(str(raw).replace("\\", "/")).name)
    return names


def batch_labels(row: dict[str, Any]) -> set[str]:
    """The lower-case names a batch row carries for its source: file, name, dataset name."""
    source = row.get("source")
    source = source if isinstance(source, dict) else {}
    labels = (source.get("file_name"), source.get("name"), source.get("ds_name"), row.get("name"))
    return {
        PurePosixPath(label).name.lower() for label in labels if isinstance(label, str) and label
    }


def match_batches(
    before_ids: Iterable[int],
    after: Sequence[dict[str, Any]],
    sent: Sequence[str],
    staging_ids: Iterable[int] = (),
) -> tuple[list[int], list[int]]:
    """Tell the batches an upload added from the ones that merely appeared meanwhile.

    The backend appends a staging dataset into the target and records it as the batch's
    source, so a new batch is the upload's only when its source names a file that was
    sent (with or without its extension, in any case) or the staging dataset made from
    it. Any other new batch (a folder automation, another user) is reported apart and
    never offered for removal.

    Args:
        before_ids: The ids of the dataset's batches before the files were sent.
        after: The batch rows now.
        sent: The names of the files that were sent (:func:`sent_names`).
        staging_ids: The staging dataset ids the upload job made.

    Returns:
        ``(ids of this upload's batches, ids of new batches not tied to it)``.
    """
    known = set(before_ids)
    staging = set(staging_ids)
    wanted = {name.lower() for name in sent} | {PurePosixPath(n).stem.lower() for n in sent}
    ours: list[int] = []
    unmatched: list[int] = []
    for row in after:
        batch_id = row.get("id")
        if not isinstance(batch_id, int) or batch_id in known:
            continue
        source = row.get("source")
        linked = isinstance(source, dict) and source.get("datasource_id") in staging
        labels = batch_labels(row)
        stems = {PurePosixPath(label).stem for label in labels}
        (ours if linked or labels & wanted or stems & wanted else unmatched).append(batch_id)
    return ours, unmatched


def rows_have_landed(
    plan: dict[str, Any],
    rows_after: int | None,
    after: Sequence[dict[str, Any]],
    sent: Sequence[str],
    staging_ids: Iterable[int],
    listed_before: bool,
) -> bool:
    """Whether the dataset's row count shows the rows of a batch that is already listed.

    The batch can be listed before the dataset's count moves, so a count read earlier may be
    stale. When the new batches carry their own ``row_count`` that decides: under ``add`` the
    dataset holds at least the rows before plus theirs, under ``replace`` exactly theirs, and
    a batch of 0 rows is done at once. Without batch counts, ``add`` is done when the count
    differs from the one before, and ``replace`` (whose count may stay the same) when one
    more read has been made since the batch was listed.

    Args:
        plan: What ``AppendsAPI.prepare`` read before the files were sent.
        rows_after: The dataset's rows at the latest read, or None when unreadable.
        after: The batch rows now.
        sent: The names of the files that were sent.
        staging_ids: The staging dataset ids the upload job made.
        listed_before: Whether the batch was already listed at the previous poll, so that
            ``rows_after`` was read after it.

    Returns:
        True when the count can be trusted as the upload's.
    """
    before = plan.get("rows_before")
    if rows_after is None or not isinstance(before, int):
        return True
    ours, unmatched = match_batches(plan.get("batch_ids_before", []), after, sent, staging_ids)
    wanted = set(ours or unmatched)
    counts = [row.get("row_count") for row in after if row.get("id") in wanted]
    replacing = plan["update_method"].get("mode") == "replace"
    if counts and all(isinstance(n, int) and not isinstance(n, bool) for n in counts):
        total = sum(n for n in counts if isinstance(n, int))
        return rows_after == total if replacing else rows_after >= before + total
    return listed_before if replacing else rows_after != before


def rows_of(response: Any) -> int | None:
    """The row count a dataset read holds, or None when it holds none."""
    dataset = response.get("dataset", response) if isinstance(response, dict) else None
    stats = dataset.get("stats") if isinstance(dataset, dict) else None
    rows = stats.get("row_count") if isinstance(stats, dict) else None
    return rows if isinstance(rows, int) else None


def status_of(response: Any) -> str | None:
    """The status a dataset read holds, or None when it holds none."""
    dataset = response.get("dataset", response) if isinstance(response, dict) else None
    status = dataset.get("status") if isinstance(dataset, dict) else None
    return status if isinstance(status, str) else None


def describe_append(
    plan: dict[str, Any],
    rows_after: int | None,
    ours: list[int],
    unmatched: list[int],
    settled: bool,
    status: str | None = None,
    read_error: str | None = None,
    mismatched: Sequence[int] = (),
) -> dict[str, Any]:
    """Report what an upload into a dataset did.

    Args:
        plan: What ``AppendsAPI.prepare`` read before the files were sent.
        rows_after: The dataset's rows now, or None when they could not be read.
        ours: The batches this upload added.
        unmatched: New batches that could not be tied to this upload.
        settled: Whether the dataset had taken the rows in by the time it was read.
        status: The dataset's status at the last read, or None when it was never read.
        read_error: Why the dataset could not be read at the last try, if it could not.
        mismatched: The datasets the server kept for files it held back for a schema mismatch
            (:func:`schema_mismatches`).

    Returns:
        ``appended_to``, the ``update_method`` the upload ran under (``mode``,
        ``effect``, ``previous_mode`` when this upload changed it, ``error`` when it
        could not be read), the rows before and after with ``rows_added`` (negative
        when a replace shrank the dataset), ``batch_ids``, and when present
        ``unmatched_batch_ids``, ``append_pending`` (with ``read_error`` when the last read of
        the dataset failed) and, when the dataset ended in a failed status, ``append_failed``
        with that ``status``. A file the server held back because its columns do not match
        reports ``append_failed`` with ``failure`` ``schema_mismatch``, the ``reason``, the
        ``kept_dataset_ids`` (the file's own datasets, which stay in the project) and a
        ``next_step``.
    """
    entry = plan["update_method"]
    report: dict[str, Any] = {"appended_to": plan["target"], "update_method": dict(entry)}
    before = plan.get("rows_before")
    if isinstance(before, int) and rows_after is not None:
        report.update(rows_before=before, rows_after=rows_after, rows_added=rows_after - before)
    report["batch_ids"] = list(ours)
    if unmatched:
        report["unmatched_batch_ids"] = list(unmatched)
    if mismatched:
        target = plan["target"]
        kept = ", ".join(str(dataset_id) for dataset_id in mismatched)
        report["append_failed"] = True
        report["failure"] = FAILURE_SCHEMA_MISMATCH
        report["reason"] = SCHEMA_MISMATCH_REASON.format(target, kept)
        report["kept_dataset_ids"] = list(mismatched)
        report["next_step"] = SCHEMA_MISMATCH_NEXT.format(target, kept)
    elif status in FAILED_STATUSES:
        report["append_failed"] = True
        report["status"] = status
    elif not settled:
        report["append_pending"] = True
        if read_error:
            report["read_error"] = read_error
    return report
