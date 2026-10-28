"""The SDK's pure helpers for adding a file to an existing dataset, under public names.

The mode words and what each does, the matching of an upload's batches among the ones
that appeared meanwhile, and the report of an append, with no request sent. The SDK's own
``client.appends`` builds its report with these, so a server that sends the file itself
reports exactly what the SDK does.
"""

from __future__ import annotations

from mammoth._pure.appends import (
    ADDING_MODES,
    EFFECTS,
    FAILED_STATUSES,
    NO_RECORD,
    NOT_ADDED,
    SETTLED_STATUSES,
    UNKNOWN_EFFECT,
    WOULD_EMPTY,
    UnknownUpdateMethodError,
    batch_labels,
    describe_append,
    describe_update_method,
    match_batches,
    mode_word,
    refuse_batch_removal,
    rows_of,
    sent_names,
    status_of,
    stored_mode,
    unknown_update_method,
)

__all__ = [
    "ADDING_MODES",
    "EFFECTS",
    "FAILED_STATUSES",
    "NO_RECORD",
    "NOT_ADDED",
    "SETTLED_STATUSES",
    "UNKNOWN_EFFECT",
    "WOULD_EMPTY",
    "UnknownUpdateMethodError",
    "batch_labels",
    "describe_append",
    "describe_update_method",
    "match_batches",
    "mode_word",
    "refuse_batch_removal",
    "rows_of",
    "sent_names",
    "status_of",
    "stored_mode",
    "unknown_update_method",
]
