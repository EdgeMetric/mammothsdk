"""``schema find``: rank commands and recipes for a plain-language task."""

from __future__ import annotations

import re
from functools import cache
from typing import Any

from mammoth_cli.commands import how as how_cmd
from mammoth_cli.commands.schema import (
    _IN_PLACE_KEYWORDS,
    _INLINE_NOTES_MAX_CHARS,
    _compact_accepted_fields,
    _hidden_from_call,
    _operation_hints_by_command,
    edits_view_in_place,
)
from mammoth_cli.commands.schema.examples import _positionals
from mammoth_cli.discovery.purposes import COMMAND_DISCOVERY_PURPOSES, GROUP_DISCOVERY_PURPOSES
from mammoth_cli.errors.envelope import is_feature_unavailable
from mammoth_cli.manifest.loader import command_by_id, load_commands

_MAX_FIND_RESULTS = 20


# Outranks any word-overlap score: a command named by its full path comes first.
_NAMED_COMMAND_BOOST = 10_000


# Bag-of-words scoring cannot tell "create a NEW VIEW from an existing
# DATASET" (view.create) apart from "create a DATASET from an existing
# VIEW" (view.export.dataset): the two goals share the exact same word set,
# and only word order says which resource is being made and which already
# exists. No purpose text or synonym can encode that; this pair of small
# adjacency checks is the intentionally scoped exception. Extend the two
# dicts, never the regex, if another goal collides the same way.
_NEW_OBJECT_HINTS: dict[str, str] = {
    "view.create": "view",
    "view.export.dataset": "dataset",
}


_EXISTING_OBJECT_HINTS: dict[str, str] = {
    "view.create": "dataset",
    "view.export.dataset": "view",
}


_OBJECT_ADJACENCY_BOOST = 150


_MAX_FIND_LIMIT = 100


# How many of a find's top matches carry inline accepted_fields/agent_example.
# 35% of all eval tool calls were command discovery (schema find -> schema
# get) because find's compact entry gave a command_id but not what to pass
# it; inlining the top few lets an agent act without a second round trip in
# the common case where one of them is right. Bounded to a few commands so a
# broad query never balloons the result (the tool result goes into the
# model's context).
_INLINE_DETAIL_COUNT = 3


# Search is intentionally a small, deterministic intent matcher rather than a
# fuzzy/remote search service.  The aliases describe language users commonly
# use for a command; they do not add capabilities to the catalog.  Keeping the
# map here also makes a cold process produce the same ordering as a warm one.
_DISCOVERY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "show": ("list", "get", "browse", "display", "view"),
    "display": ("show", "list", "get", "view"),
    "visualize": ("dashboard", "chart", "analytics"),
    "spreadsheet": ("csv", "xlsx", "excel", "file", "upload"),
    "excel": ("spreadsheet", "xlsx", "file"),
    "csv": ("spreadsheet", "file", "upload"),
    "local": ("file", "download", "csv", "artifact"),
    "download": ("export", "file", "csv", "artifact", "local"),
    # "combine" alone is ambiguous between joining on a key and appending
    # rows; kept a weak alias match (not a literal word) here so a bare
    # "combine datasets" still favors join's own literal "combine" purpose
    # text, while "combine ... by appending rows" still resolves to the
    # export -- its own literal "append"/"union"/"stack" carry that case.
    "combine": ("append", "union", "stack", "merge"),
    # "publish" a dataset almost always means one of the typed exports
    # (Power BI, a live DB connection, a webhook, ...); every export
    # command's path literally contains "export", so this one alias covers
    # any "publish data to X" phrasing without a per-destination entry.
    "publish": ("export",),
    "column": ("columns", "field", "fields", "schema"),
    "columns": ("column", "field", "fields", "schema"),
    "display-name": ("name", "column", "columns", "field", "fields", "schema"),
    "language": ("name", "column", "columns", "field", "fields", "schema", "text"),
    "field": ("column", "columns", "fields"),
    "fields": ("column", "columns", "field"),
    "clean": ("transform", "replace", "remove", "edit"),
    "edit": ("transform", "update", "replace", "change"),
    "remove": ("delete", "trash", "bulk-delete"),
    "import": ("upload", "create", "file"),
    "ingest": ("upload", "import", "file"),
    "asynchronous": ("async", "job", "wait"),
    "async": ("job", "wait", "poll"),
    "poll": ("job", "wait", "status"),
    # "API keys" in the app (Settings > API keys) are client apps; `external-key`
    # holds other services' keys and wrongly won "list active API keys".
    "api": ("client-app",),
    "key": ("client-app",),
    "keys": ("client-app",),
    # "What did I ask you earlier?" is a past-conversation lookup: an agent
    # session. Nothing in `agent.session.list`/`agent.session.messages` text
    # says "conversation", "chat", or "history", so a query phrased that way
    # (rather than with the literal word "session") never found them.
    "conversation": ("session",),
    "conversations": ("session",),
    "chat": ("session",),
    "chats": ("session",),
    "history": ("session",),
    "previous": ("session",),
    "earlier": ("session",),
    "asked": ("session",),
    # British spellings search the same as the American ones.
    "summarise": ("summarize",),
    "standardise": ("standardize",),
    "normalise": ("normalize",),
    "categorise": ("categorize",),
    # Purpose words the agent writes where the command text says something else: a ranking
    # within a group is a window task, disabling an automation is an update, and so on.
    "ranking": ("rank", "window"),
    "rank": ("window", "partition"),
    "partition": ("window", "group"),
    "dedupe": ("duplicate", "duplicates", "distinct"),
    "unique": ("distinct", "duplicates"),
    "ranked": ("rank", "window"),
    "bq": ("bigquery",),
    "calculate": ("math", "formula", "expression"),
    "formula": ("math", "expression"),
    "disable": ("pause", "update"),
    "regex": ("pattern", "contains", "replace"),
}


_DISCOVERY_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "me",
        "please",
        "for",
        "to",
        "of",
        "by",
        "with",
        "can",
        "i",
        # Filler in goal phrasing ("merge my two datasets"); a command never
        # turns on these words, so they must not sink an otherwise good match.
        "my",
        "our",
        "one",
        "two",
        "another",
        "other",
        "into",
        "from",
        "and",
        # Same as "and" -- an incidental conjunction ("Power BI or Tableau")
        # must not become a required match term.
        "or",
        "all",
        "each",
        "this",
        "that",
        "how",
        "what",
        "is",
        # The tail of "what's"/"it's" once the apostrophe splits the word.
        "s",
        "do",
        "want",
        "need",
        "using",
        "than",
        "via",
        # Filler prepositions in goal phrasing ("datasets as rows", "datasets
        # in a project", "join two datasets on a key"); no command turns on
        # any of these.
        "as",
        "in",
        "on",
    }
)


# How many near misses a search with no full match returns.
_MAX_SUGGESTIONS = 5


# Cap on the curated purpose text a match's ``matched_on`` field quotes back,
# so one long entry can't bloat every result in a page.
_MATCHED_ON_MAX_CHARS = 120


# T1-R-06: an agent reading "No command matched every word" stopped there and
# never tried what 'suggestions' actually held (automation.create among
# them) -- the framing read as a dead end even when it wasn't one. Word the
# two cases (some candidates vs. none at all) differently so the presence of
# 'suggestions' reads as "try these" rather than "nothing found".
_NO_MATCH_HINT_WITH_SUGGESTIONS = (
    "No single command matched every word, but 'suggestions' lists the closest candidates "
    "-- each with its own matched_terms. Try one of those before rephrasing."
)
_NO_MATCH_HINT_PARTIAL = (
    "No single command matched every word; 'matches' lists the closest candidates "
    "(partial: true) -- each with its own matched_terms. Try one of those before rephrasing."
)


_NO_MATCH_HINT_NO_SUGGESTIONS = (
    "No command matched any word; try fewer or other words. 'mammoth view transform --help' "
    "lists every data transformation (join, pivot, filter, dedupe, math, ...), and 'mammoth "
    "schema list' is the complete inventory."
)


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _ordered_tokens(value: str) -> tuple[str, ...]:
    """The words of ``value`` in the order written, each once.

    A hyphenated word is kept whole and also split into its parts, so that
    ``date`` finds ``extract-date`` and ``date-diff`` as well as ``convert-type``'s
    example text. The order is the text's, not a hash's: adjacent words make compounds.
    """
    tokens: dict[str, None] = {}
    for token in _TOKEN_RE.findall(value.casefold()):
        tokens[token] = None
        if "-" in token:
            tokens.update(dict.fromkeys(token.split("-")))
    return tuple(tokens)


def _tokens(value: str) -> frozenset[str]:
    """Tokenize search text consistently across platforms and Python runs."""
    return frozenset(_ordered_tokens(value))


def _query_tokens(query: str) -> tuple[str, ...]:
    # Bare numbers ("top 10") are values, not intent words.
    return tuple(
        token
        for token in _ordered_tokens(query)
        if token not in _DISCOVERY_STOPWORDS and not token.isdigit()
    )


def _token_aliases(token: str) -> frozenset[str]:
    """Return the finite synonym neighborhood for one intent token."""
    return frozenset((token, *_DISCOVERY_SYNONYMS.get(token, ())))


def _adjacent_compound_forms(terms: tuple[str, ...]) -> dict[str, frozenset[str]]:
    """Map each query term to the compound spellings an adjacent pair makes.

    A route's un-hyphenated compound name (``powerbi``, ``bigquery``,
    ``onedrive``, ``sharepoint``, ...) never shares a token with the natural
    two-word phrasing a user types ("power bi", "big query"), since neither
    half is a substring match in the token-set membership test. Generalizes
    over any adjacent pair rather than hardcoding destination names: "azure
    blob" -> "azureblob"/"azure-blob", "share point" -> "sharepoint", and so
    on for whatever the query happens to contain.
    """
    forms: dict[str, set[str]] = {}
    for left, right in zip(terms, terms[1:], strict=False):
        for compound in (left + right, f"{left}-{right}"):
            forms.setdefault(left, set()).add(compound)
            forms.setdefault(right, set()).add(compound)
    return {term: frozenset(compounds) for term, compounds in forms.items()}


@cache
def _command_vocabulary_tokens() -> frozenset[str]:
    """Every token that names a command or appears in its curated purpose text.

    Distinguishes genuine CLI vocabulary from a data word -- a column,
    table, or other business noun from the caller's own data (``orders``,
    ``revenue``, ``store``) -- riding along in a goal. Counts a command's own
    id/path (``user``, ``workspace``, ``invoice`` are real resource nouns a
    command is named after) plus ``COMMAND_DISCOVERY_PURPOSES``/
    ``GROUP_DISCOVERY_PURPOSES`` -- text hand-curated specifically to
    describe what a command is for. Deliberately excludes ``human_example``/
    ``agent_example`` and OpenAPI-derived operation hints: those are
    illustrative sample values (a placeholder project name like "Revenue
    report", a sample filename like "sales.csv") reused verbatim across
    dozens of unrelated commands, so counting them would make almost any
    plausible business noun look like real vocabulary and defeat this
    check. A term absent from this set is not something any command is
    named after or actually about, so :func:`find_schemas` drops it from a
    goal's required terms rather than letting it sink an otherwise complete
    match.
    """
    vocabulary: set[str] = set()
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        command_id = str(record["command_id"])
        command_path = str(record["command_path"])
        text = (
            f"{command_id} {command_path} "
            f"{COMMAND_DISCOVERY_PURPOSES.get(command_id, '')} "
            f"{GROUP_DISCOVERY_PURPOSES.get(command_path.split()[0], '')}"
        )
        vocabulary.update(_tokens(text))
    return frozenset(vocabulary)


def _inline_call_detail(entries: list[dict[str, Any]]) -> None:
    """Add each entry's compact accepted fields and agent example in place."""
    for entry in entries:
        record = command_by_id(entry["command_id"])
        if record is None:
            continue
        entry["positionals"] = [
            {key: item[key] for key in ("name", "metavar", "type", "required")}
            for item in _positionals(entry["command_id"])
        ]
        fields = _compact_accepted_fields(record)
        if fields is not None:
            entry["accepted_fields"] = fields
        if record.get("agent_example"):
            entry["agent_example"] = record["agent_example"]
        notes = record.get("known_restrictions")
        if isinstance(notes, str) and notes:
            cut = notes[:_INLINE_NOTES_MAX_CHARS]
            entry["known_restrictions"] = cut + ("..." if len(notes) > len(cut) else "")


def _inline_picks(page: list[dict[str, Any]], offset: int) -> list[dict[str, Any]]:
    """The entries to inline: the top ones, plus read commands ranked below a write.

    A read that answers the question is worth its fields even when a write such as
    ``view.transform.pivot`` outranks it; otherwise the caller needs a ``schema get``.
    """
    head = page[: max(0, _INLINE_DETAIL_COUNT - offset)]
    reads = [
        entry
        for entry in page[len(head) :]
        if (command_by_id(entry["command_id"]) or {}).get("mutation_class") == "read"
    ]
    return head + reads[:_INLINE_DETAIL_COUNT]


#: How to drill down from a find: a family's full command list, or every family.
_BROWSE_NEXT = (
    "mammoth schema list FAMILY lists every command in a family; mammoth schema list "
    "lists the families"
)


def find_schemas(
    query: str,
    *,
    limit: int = _MAX_FIND_RESULTS,
    cursor: int = 0,
) -> dict[str, Any]:
    """Return compact command matches for interactive and agent discovery.

    ``schema list`` deliberately remains the complete, machine-readable
    inventory.  This search avoids returning a large nested schema for every
    command when callers only need to locate the right command id first; use
    the included ``full_schema_command`` to fetch the authoritative detail.
    Every whitespace-separated term must occur in a command name, its examples,
    or its stable operation-purpose text, making the result deterministic and
    easy to compose in scripts.  When no command carries every term, the result
    adds ``suggestions`` (the commands that carry the most terms) and a ``hint``,
    so a cold caller who phrased the goal in other words is not left with an
    empty list.
    """
    # A query made only of filler words keeps them, rather than matching
    # every command.
    raw_terms = _query_tokens(query) or tuple(_tokens(query))
    compound_forms = _adjacent_compound_forms(raw_terms)
    # A term no command's discovery-purpose text would ever say is a data
    # word (a column/table/business noun from the caller's own data, not CLI
    # vocabulary) riding along in the goal; drop it before the all-terms
    # rule and scoring so it can't sink an otherwise complete match. If
    # every term would be dropped, keep them all -- a query that is nothing
    # but data words still deserves its ordinary near-miss treatment rather
    # than becoming a match-everything wildcard. A literal full-path lookup
    # (the ``named`` check below) always uses the un-dropped ``raw_terms``,
    # so naming a command by its exact path never depends on this filter.
    vocabulary = _command_vocabulary_tokens()
    cli_terms = tuple(
        term
        for term in raw_terms
        if (_token_aliases(term) & vocabulary)
        or (compound_forms.get(term, frozenset()) & vocabulary)
    )
    terms = cli_terms or raw_terms
    query_cf = query.casefold()
    # Clamp caller-provided bounds instead of allowing an accidental unbounded
    # discovery response.  A negative cursor is a usage mistake, not a request
    # to wrap around the catalog.
    bounded_limit = max(1, min(int(limit), _MAX_FIND_LIMIT))
    offset = max(0, int(cursor))
    ranked_matches: list[tuple[int, dict[str, Any]]] = []
    near_misses: list[tuple[int, int, dict[str, Any], list[str]]] = []
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        if is_feature_unavailable(str(record["command_id"])) or _hidden_from_call(record):
            continue
        command_id = str(record["command_id"])
        command_path = str(record["command_path"])
        positional_help = " ".join(
            str(positional.get("help", "")) for positional in record.get("positionals", [])
        )
        primary_text = f"{command_id} {command_path}".casefold()
        sources = (
            (30, f"{record.get('human_example', '')} {record.get('agent_example', '')}"),
            (20, positional_help),
            (15, _operation_hints_by_command().get(command_id, "")),
            (15, _IN_PLACE_KEYWORDS if edits_view_in_place(record) else ""),
            (60, COMMAND_DISCOVERY_PURPOSES.get(command_id, "")),
            (3, GROUP_DISCOVERY_PURPOSES.get(command_path.split()[0], "")),
        )
        searchable = " ".join(source for _, source in sources).casefold()
        searchable_tokens = _tokens(f"{primary_text} {searchable}")
        matched_terms = [
            term
            for term in terms
            if (_token_aliases(term) & searchable_tokens)
            or (compound_forms.get(term, frozenset()) & searchable_tokens)
        ]
        if not matched_terms:
            continue
        score = 0
        for term in matched_terms:
            if term in _tokens(primary_text):
                score += 100
            elif term in _tokens(searchable):
                score += 40
            else:
                score += 20
            # Exact phrase/path matches outrank a synonym match, then stable
            # command-id ordering breaks all remaining ties.
            if term in searchable_tokens:
                score += 10
        # Purpose and command-specific hints are stronger than generic
        # family words such as ``data`` or ``show``.
        score += 5 * sum(
            1
            for term in matched_terms
            if any(term in source.casefold() for _, source in sources[:2])
        )
        command_purpose = COMMAND_DISCOVERY_PURPOSES.get(command_id, "").casefold()
        score += 100 * sum(1 for term in matched_terms if term in _tokens(command_purpose))
        action = command_path.split()[1] if len(command_path.split()) > 1 else ""
        if "show" in matched_terms and action in {"list", "get", "browse"}:
            score += 80
        new_object = _NEW_OBJECT_HINTS.get(command_id)
        if new_object and re.search(rf"\bnew\s+{new_object}s?\b", query_cf):
            score += _OBJECT_ADJACENCY_BOOST
        existing_object = _EXISTING_OBJECT_HINTS.get(command_id)
        if existing_object and re.search(rf"\bexisting\s+{existing_object}s?\b", query_cf):
            score += _OBJECT_ADJACENCY_BOOST
        is_support = command_id.startswith("support.")
        entry = {
            "command_id": command_id,
            "command_path": command_path,
            "mutation_class": record["mutation_class"],
            "confirmation": record["confirmation"],
            "server_status": record.get("server_status", "served"),
            "full_schema_command": f"mammoth schema get {command_id}",
        }
        # A match on hidden curated purpose text (T1-I-07) is otherwise
        # invisible to the caller: only command_id/command_path/matched_terms
        # come back, and a terse docstring-derived example can read as
        # something else entirely (connector.ai.chat's own example reads as
        # "ask the AI a question", not "build a connector for an unsupported
        # API"). Echo the purpose text that matched, capped so a long entry
        # doesn't bloat every result.
        if command_purpose and any(term in _tokens(command_purpose) for term in matched_terms):
            purpose_text = COMMAND_DISCOVERY_PURPOSES[command_id]
            entry["matched_on"] = (
                purpose_text
                if len(purpose_text) <= _MATCHED_ON_MAX_CHARS
                else purpose_text[:_MATCHED_ON_MAX_CHARS].rstrip() + "..."
            )
        if is_support:
            # These operate on another workspace/customer on the caller's
            # behalf (Mammoth-operator tooling), not the caller's own
            # workspace. A query that also has an ordinary match should
            # never surface the operator command first.
            entry["operator_only"] = (
                "support.* commands act on another workspace as an operator, not the "
                "caller's own; ordinary workspace work uses the non-support command."
            )
        # A query that spells out this command's whole path (``aggregate view
        # data ...``) asks for it by name, whatever goal words ride along.
        path_tokens = set(_tokens(command_path))
        named = len(path_tokens) >= 3 and path_tokens <= set(raw_terms)
        if named:
            score += _NAMED_COMMAND_BOOST
        if named or len(matched_terms) == len(terms):
            ranked_matches.append((score, entry))
        else:
            near_misses.append((len(matched_terms), score, entry, matched_terms))
    ranked_matches.sort(
        key=lambda item: (
            item[1]["command_id"].startswith("support."),
            -item[0],
            item[1]["command_id"],
        )
    )
    total_matches = len(ranked_matches)
    page = [match for _, match in ranked_matches[offset : offset + bounded_limit]]
    _inline_call_detail(_inline_picks(page, offset))
    has_more = offset + len(page) < total_matches
    continuation = (
        {
            "next_cursor": str(offset + len(page)),
            "has_more": True,
            "limit": bounded_limit,
            "query": query,
        }
        if has_more
        else None
    )
    result: dict[str, Any] = {"query": query}
    recipes = how_cmd.runnable_for(query) if offset == 0 else []
    if recipes:
        # A whole task in one command outranks the single commands it is made of.
        result["recipes"] = recipes
    result |= {
        "matches": page,
        "total_matches": total_matches,
        "truncated": has_more,
        "continuation": continuation,
    }
    if total_matches == 0:
        # Most terms first, then the ordinary score: a command that carries
        # two of three words beats one that carries a single common word.
        near_misses.sort(key=lambda item: (-item[0], -item[1], item[2]["command_id"]))
        result["suggestions"] = [
            {**entry, "matched_terms": matched}
            for _, _, entry, matched in near_misses[:_MAX_SUGGESTIONS]
        ]
        # A goal phrased in the user's words rarely carries every term; the
        # best near misses still say how to call them, so one find suffices.
        _inline_call_detail(result["suggestions"][:_INLINE_DETAIL_COUNT])
        # A script that reads only ``matches`` must not be left with nothing: the best
        # partial matches go there too, marked so they are not mistaken for full ones
        # (``total_matches`` stays 0 and each carries the ``matched_terms`` it has).
        result["matches"] = [{**entry, "partial": True} for entry in result["suggestions"]]
        result["partial_matches"] = bool(result["matches"])
        result["hint"] = (
            _NO_MATCH_HINT_WITH_SUGGESTIONS
            if result["suggestions"]
            else _NO_MATCH_HINT_NO_SUGGESTIONS
        )
    result["browse"] = _browse(page or result.get("suggestions", []))
    return result


#: Keys of an inlined accepted field that a caller needs to fill it in. ``schema`` is the nested
#: shape of an object-typed field (``GenerateDashboardV3Spec``), set only when it is small enough
#: to inline; without it the caller sees a bare type name and needs a ``schema get``.
_FIND_FIELD_KEYS = ("name", "type", "required", "enum", "schema")
#: Entry keys a find leaves out unless ``--full``: ``schema get`` has them.
_FIND_DROPPED_KEYS = ("full_schema_command", "known_restrictions", "matched_on")


def _trim_find_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """One match cut to what picks and calls it: id, summary, safety class, example.

    The command id is the key ``schema get`` takes for the rest.
    """
    from mammoth_cli.app.help_text import _indexed_summary

    trimmed = {key: value for key, value in entry.items() if key not in _FIND_DROPPED_KEYS}
    summary = _indexed_summary(entry["command_id"])
    if summary:
        trimmed["summary"] = summary
    if trimmed.get("server_status") == "served":
        del trimmed["server_status"]
    if "accepted_fields" in trimmed:
        trimmed["accepted_fields"] = [
            {key: field[key] for key in _FIND_FIELD_KEYS if field.get(key) is not None}
            for field in trimmed["accepted_fields"]
        ]
    return trimmed


def trim_find_result(result: dict[str, Any]) -> dict[str, Any]:
    """The default ``schema find`` shape: trimmed entries, near misses listed once.

    ``suggestions`` repeated the partial ``matches`` entry for entry, so only
    ``matches`` stays. ``--full`` returns the whole shape.
    """
    trimmed = dict(result)
    trimmed["matches"] = [_trim_find_entry(entry) for entry in result["matches"]]
    if "suggestions" in trimmed:
        del trimmed["suggestions"]
        trimmed["hint"] = (
            _NO_MATCH_HINT_PARTIAL if trimmed["matches"] else _NO_MATCH_HINT_NO_SUGGESTIONS
        )
    return trimmed


def _browse(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """The families behind *entries* and how to list each one in full: a keyword
    find surfaces one way to do a thing, its family holds the siblings."""
    families = list(dict.fromkeys(entry["command_path"].split()[0] for entry in entries))
    return {"families": families, "next": _BROWSE_NEXT}
