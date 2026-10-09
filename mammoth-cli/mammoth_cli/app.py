"""Root Typer application and manifest-driven command registration.

The command tree is built from the reviewed command manifests so the registered
surface can never drift from the parity records: every non-alias command record
becomes exactly one Typer command at its manifest ``command_path``, and nothing
else is registered.

Every command exposes the global machine-output and agent-mode options
(``--output``, ``--no-input``, ``--no-progress``, ``--color``, ``--profile``,
``--project`` and the timeout family) so an autonomous agent gets deterministic,
promptless behavior on any command without reading source. Command-specific
positionals and options are added per family as each handler is implemented.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import replace
from difflib import get_close_matches
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

import typer
from typer._click import exceptions as _typer_click_exceptions
from typer._click.core import Command as _ClickCommand
from typer._click.core import Parameter as _ClickParameter
from typer.core import TyperCommand, TyperGroup

from mammoth_cli import __version__
from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError, not_implemented_error
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.output.policy import (
    COLOR_MODES,
    MACHINE_OUTPUTS,
    OUTPUT_AUTO,
    SELECTABLE_OUTPUTS,
    VALID_OUTPUTS,
    resolve_output,
)
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals

if TYPE_CHECKING:
    from mammoth_cli.commands.registry import Handler
    from mammoth_cli.runtime.invocation import Invocation

OUTPUT_MODES = VALID_OUTPUTS

# Root help is the first piece of discovery most people (and agents) see.  The
# command tree itself remains manifest-driven; these labels only organize the
# existing top-level families into a small set of tasks rather than a flat list
# of several dozen nouns.
_GROUP_DESCRIPTIONS = {
    "activity": "Inspect workspace activity and audit history.",
    "addon": "Manage workspace add-ons.",
    "agent": "Work with Mammoth agent sessions, the changes a chat made, and its runs.",
    "ai": "Generate AI-assisted expressions and conditions.",
    "annotation": "Manage annotations on Mammoth resources.",
    "auth": "Sign in, sign out, and inspect credentials.",
    "automation": "Create and manage automations.",
    "batch": "Run and inspect batch operations.",
    "billing": "Manage billing and hosted checkout flows.",
    "browse": "Browse projects and workspace resources.",
    "capability": "Discover API operation support and policies.",
    "client-app": (
        "Manage the workspace's API keys (client apps): key + secret credentials "
        "for scripts and integrations."
    ),
    "token": "Create, list, and revoke long-lived API keys (aliases of client-app).",
    "collection": "Group dashboards into a collection and share the set as one.",
    "completion": "Install or print shell completion.",
    "config": "Read and update local CLI configuration.",
    "connector": "Manage data connectors and connector profiles.",
    "log": "Locate and read the local run log.",
    "context": "Inspect and select the active project context.",
    "dashboard": "Build, query, and publish dashboards.",
    "data-app": "Create and manage data applications.",
    "dataset": "Create, inspect, and manage datasets.",
    "external-key": "Manage LLM provider keys (OpenAI, Anthropic, etc.) used by AI features.",
    "file": "Upload and manage source files.",
    "folder": "Organize folders and their contents.",
    "job": "Inspect and wait for asynchronous jobs.",
    "notification": "Manage workspace notifications.",
    "parameter": "Manage parameters and parameter groups.",
    "project": "Create and manage projects.",
    "report": "Create and manage reports.",
    "schedule": "Manage scheduled work.",
    "schema": "Find concise command input guidance or fetch full schemas.",
    "skill": "Install and manage the Mammoth agent skill.",
    "snippet": "Manage reusable snippets.",
    "support": "Manage support and administration resources.",
    "template": "Manage templates.",
    "trash": "Inspect, restore, and remove trashed resources.",
    "user": "Manage users and account settings.",
    "view": "Transform, query, and publish data views.",
    "webhook": "Manage webhooks.",
    "workflow": "Create and manage workflows.",
    "workspace": "Manage workspace settings and members.",
}

# One line per ``agent`` subgroup, so ``mammoth agent --help`` tells them apart.
_AGENT_SUBGROUP_DESCRIPTIONS = {
    "access": "Set who may use an agent definition.",
    "action": "List and delete the changes an agent chat made.",
    "charter": "Read, change and restore an agent definition's charter.",
    "feedback": "Read the feedback an agent definition has received.",
    "goldens": "Manage and run the golden cases an agent definition is proven against.",
    "memory": "Manage the facts an agent definition has learned, per project.",
    "message": "Correct the request kind of a reply in an agent chat.",
    "plan": "Edit the waiting workflow proposal of an agent chat plan.",
    "projects": "Set or clear the projects an agent definition works in.",
    "run": "Inspect and control an agent's runs.",
    "scratch": "Read, write and clear an agent definition's scratchpad notes per project.",
    "session": "List, read, delete and share agent chat sessions.",
    "team": "Set the agents this agent may consult while answering.",
    "turn": "Control one turn of an agent chat session.",
}


# One line per nested group below the top level, so ``mammoth view --help`` tells its
# subgroups apart instead of repeating the top-level description. ``agent`` groups are above.
_SUBGROUP_DESCRIPTIONS = {
    "addon connector": "Add or remove the connector add-on.",
    "addon storage": "Add or remove the storage add-on.",
    "addon user": "Add or remove the user add-on.",
    "agent run units": "List and read the units of work inside an agent run.",
    "ai condition": "Generate a filter condition from a description.",
    "ai expression": "Generate a column expression from a description.",
    "ai retention": "Generate a data-retention condition from a description.",
    "ai sql": "Generate SQL from a description.",
    "ai suggestion": "List AI suggestions for a view.",
    "annotation comment": "Add comments to annotations.",
    "billing invoice": "List and charge invoices.",
    "billing stripe": "Manage the Stripe subscription: checkout, trial, payment methods, invoices.",
    "billing stripe payment-method": "List, delete and default Stripe payment methods.",
    "billing stripe storage": "Set the Stripe storage tier.",
    "billing subscription": "Read and update the subscription.",
    "browse resources": "Browse workspace resources in bulk.",
    "collection dashboards": "Add dashboards to a collection or remove them.",
    "collection files": "Upload files to a collection.",
    "collection members": "Remove members from a collection.",
    "connector ai": "Chat with the connector assistant to set up a connection.",
    "connector ai session": "List connector assistant sessions and their messages.",
    "connector connection": "Create, read, update and delete connector connections.",
    "connector ds-config": "Create, read, update and delete data-source configs.",
    "connector query": "Generate connector queries and check their status.",
    "context project": "Show, select or clear the active project.",
    "dashboard audience": "Read who views a dashboard and its digest.",
    "dashboard audience digest": "Read and set the audience digest of a dashboard.",
    "dashboard canvas": "Read, save and restore a dashboard canvas.",
    "dashboard chat": "Edit a dashboard by chat and read the chat history.",
    "dashboard context": "Create, review, apply and manage dashboard contexts.",
    "dashboard data": "Read the data behind a dashboard, draft or published.",
    "dashboard embed": "Manage dashboard embedding: keys, origins, tokens and usage.",
    "dashboard embed config": "Read and set the embed configuration.",
    "dashboard embed key": "Rotate the embed key.",
    "dashboard embed lifetime": "Set the embed token lifetime.",
    "dashboard embed origin": "Revoke an allowed embed origin.",
    "dashboard embed preview-token": "Create an embed preview token.",
    "dashboard embed secret": "Rotate the embed secret.",
    "dashboard embed usage": "Read embed usage and its summary.",
    "dashboard engagement": "Read a dashboard's engagement and remind its viewers.",
    "dashboard exemplar": "Extract an exemplar from a dashboard.",
    "dashboard figure": "Add figures to a dashboard.",
    "dashboard filter": "Add, list and remove dashboard filters.",
    "dashboard gallery": "List and read gallery dashboards.",
    "dashboard own-data": "Start, check and finish a dashboard's own-data setup.",
    "dashboard page": "Plan dashboard pages.",
    "dashboard pages": "Add pages to a dashboard.",
    "dashboard pdf": "Export a dashboard as a PDF.",
    "dashboard published": "Read and export a published dashboard.",
    "dashboard published pdf": "Export a published dashboard as a PDF.",
    "dashboard published video": "Export a published dashboard as a video.",
    "dashboard qa": "Ask questions of a dashboard and manage the Q&A sessions.",
    "dashboard qa comment": "Create and delete Q&A comments.",
    "dashboard qa session": "Create, read, fork, rename and share Q&A sessions.",
    "dashboard qa settings": "Read and set Q&A settings.",
    "dashboard rls": "Row-level security for a dashboard.",
    "dashboard rls assignment": "List and set row-level security assignments.",
    "dashboard rls column": "List the columns row-level security can use.",
    "dashboard rls value": "List the values row-level security can use.",
    "dashboard signature": "Create, list, update and delete dashboard signatures.",
    "dashboard source": "List the data sources of dashboards.",
    "dashboard style": "Manage dashboard styles: presets, tokens, custom and default.",
    "dashboard style custom": "Create, list, update and delete custom styles.",
    "dashboard style default": "Read and set the default style.",
    "dashboard style preset": "List style presets.",
    "dashboard style token": "List style tokens.",
    "dashboard suggestion": "List dashboard suggestions.",
    "dashboard tags": "List, set, rename, merge and delete dashboard tags.",
    "dashboard template": "Create, apply and manage dashboard templates.",
    "dashboard template thumbnail": "Read, set and clear a template thumbnail.",
    "dashboard templates": "Use or list pending dashboard templates.",
    "dashboard v3": "Generate v3 dashboards.",
    "dashboard video": "Export a dashboard as a video.",
    "data-app user": "List and remove the users of a data app.",
    "dataset broken-rows": "List and resolve rows that failed to load.",
    "dataset file-settings": "Read, update and undo a dataset's file settings.",
    "dataset interpretation": "Preview and confirm how a file is interpreted.",
    "parameter group": "Create, list, update, reorder and delete parameter groups.",
    "project checkpoint": "List project checkpoints.",
    "project data-check": "List project data checks.",
    "project memory": "Add, list and remove project memory notes.",
    "project resource-dependencies": "Update project resource dependencies.",
    "project user": "Add, update and remove project users.",
    "skill agents-md": "Install the agent instructions file.",
    "support connector": "Create, list, update and delete connectors.",
    "support connector-profile": "Manage connector profiles and their connectors.",
    "support feature": "Create, list, update and delete features.",
    "support feature-profile": "Manage feature profiles and their features.",
    "support ownership": "Transfer ownership.",
    "support plan": "Manage billing plans.",
    "support plan storage-option": "Manage a plan's storage options.",
    "support subscription": "Create, read and update subscriptions.",
    "support template": "Audit, edit, import, export and publish templates.",
    "support template thumbnail": "Set and clear a template thumbnail.",
    "support user": "List, register and update users.",
    "support workspace": "Manage workspaces: create, suspend, restore and delete.",
    "support workspace user": "Add, list, remove and transfer workspace users.",
    "user avatar": "Upload or delete the avatar.",
    "user preference": "Read and update user preferences.",
    "view active-user": "List the users active on a view and mark activity.",
    "view ai": "AI profile and generated data for a view.",
    "view checkpoint": "Create, list, update and delete view checkpoints.",
    "view conditional-format": "Create, list, update and delete conditional formats.",
    "view data": "Read, query, aggregate, compare and profile a view's data.",
    "view data-check": "Create, list, update and delete data checks on a view.",
    "view derivative": "Create, list, update and delete derivative views.",
    "view draft": "Enter, run, submit or discard a view draft.",
    "view explore-panel": "Read and change the Explore cards of a view.",
    "view export": "Export a view to a file, database or service.",
    "view exportable-config": "Read and apply a view's exportable config.",
    "view pipeline": "Read, edit, rerun and wait on a view's pipeline.",
    "view task": "Add, list, update and delete pipeline tasks.",
    "view transform": "Add transformations to a view.",
    "view variants": "Create view variants.",
    "view version": "List, read, apply and delete view versions.",
    "workflow block": "Add and configure workflow blocks.",
    "workspace invite": "List, resend, revoke and delete workspace invites.",
    "workspace segment": "List and update workspace segments.",
    "workspace user": "Add, list, update and remove workspace users.",
}


def _group_description(tokens: tuple[str, ...]) -> str:
    """Return the help line for the group at ``tokens``."""
    path = " ".join(tokens)
    if path in _SUBGROUP_DESCRIPTIONS:
        return _SUBGROUP_DESCRIPTIONS[path]
    if tokens[0] == "agent" and len(tokens) > 1 and tokens[1] in _AGENT_SUBGROUP_DESCRIPTIONS:
        return _AGENT_SUBGROUP_DESCRIPTIONS[tokens[1]]
    if len(tokens) > 1:
        return f"Commands for {path}."
    return _GROUP_DESCRIPTIONS.get(tokens[0], f"Commands for {path}.")


_ROOT_HELP_PANELS = {
    "auth": "Start here",
    "context": "Start here",
    "doctor": "Start here",
    "project": "Start here",
    "schema": "Discover commands",
    "capability": "Discover commands",
    "browse": "Discover commands",
    "dataset": "Work with data",
    "file": "Work with data",
    "folder": "Work with data",
    "view": "Work with data",
    "job": "Work with data",
    "batch": "Work with data",
    "dashboard": "Build and share",
    "collection": "Build and share",
    "data-app": "Build and share",
    "report": "Build and share",
    "template": "Build and share",
    "snippet": "Build and share",
    "automation": "Automate and integrate",
    "schedule": "Automate and integrate",
    "webhook": "Automate and integrate",
    "workflow": "Automate and integrate",
    "connector": "Automate and integrate",
    "addon": "Manage resources",
    "agent": "Manage resources",
    "ai": "Manage resources",
    "annotation": "Manage resources",
    "billing": "Manage resources",
    "client-app": "Manage resources",
    "token": "Manage resources",
    "external-key": "Manage resources",
    "notification": "Manage resources",
    "parameter": "Manage resources",
    "trash": "Manage resources",
    "user": "Manage resources",
    "workspace": "Manage resources",
    "activity": "Manage resources",
    "support": "Manage resources",
    "config": "CLI and agent tools",
    "completion": "CLI and agent tools",
    "skill": "CLI and agent tools",
    "log": "CLI and agent tools",
    "upgrade": "CLI and agent tools",
    "version": "CLI and agent tools",
}

# Typer (pinned >=0.27,<0.28) ships a *vendored* click fork (``typer._click``)
# and does NOT depend on the external ``click`` package. Command resolution
# raises that fork's ``UsageError``/``Abort``, so the interceptor keys on the
# vendored classes only -- importing the external ``click`` here would add a
# phantom dependency that is absent from a clean wheel install.
_USAGE_ERRORS: tuple[type[BaseException], ...] = (_typer_click_exceptions.UsageError,)
_abort_type = getattr(_typer_click_exceptions, "Abort", None)
_ABORT_ERRORS: tuple[type[BaseException], ...] = (
    (_abort_type,) if isinstance(_abort_type, type) else ()
)

# Raised by a group invoked with no subcommand (``no_args_is_help``). Click has
# already printed the help text by then, so it carries a deliberately *empty*
# message -- which would reach an agent as a ``usage_error`` saying nothing.
_NO_ARGS_ERROR: type[BaseException] | None = getattr(
    _typer_click_exceptions, "NoArgsIsHelpError", None
)
_NO_SUCH_COMMAND = re.compile(r"No such command '(?P<name>[^']*)'")


def _output_mode_from_argv(argv: Sequence[str] | None) -> str:
    """Recover the requested ``--output`` mode from raw argv tokens.

    Used when a Click ``UsageError`` is raised *before* the per-command option
    is parsed (an unknown command, an unexpected argument, a bad option value),
    so the top-level error renderer can still honor the machine-output contract.
    Defaults to the same ``auto`` default the ``--output`` option declares, then
    resolves it against whether stdout is a terminal — so a piped invocation
    gets the machine envelope even for an error raised before option parsing.
    """
    tokens = list(argv) if argv is not None else sys.argv[1:]
    mode = OUTPUT_AUTO
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--output", "-o"):
            if index + 1 < len(tokens):
                mode = tokens[index + 1]
            index += 2
            continue
        if token.startswith("--output="):
            mode = token.split("=", 1)[1]
        elif token.startswith("-o") and len(token) > 2:
            mode = token[2:]
        index += 1
    return resolve_output(mode, is_tty=sys.stdout.isatty())


def _unknown_flag_in(error: Any, tokens: Sequence[str]) -> str | None:
    """The first ``--flag`` in ``tokens`` that neither a global option nor the command declares."""
    known, _valued = _global_option_flags()
    command = getattr(getattr(error, "ctx", None), "command", None)
    known = known | {
        flag
        for param in getattr(command, "params", [])
        for flag in (*param.opts, *param.secondary_opts)
    }
    return next(
        (
            token.split("=", 1)[0]
            for token in tokens
            if token.startswith("--") and token.split("=", 1)[0] not in known
        ),
        None,
    )


@cache
def _global_option_flags() -> tuple[frozenset[str], frozenset[str]]:
    """Return every global option spelling, and the subset that takes a value.

    Derived from :func:`_shared_option_params` so the two stay in lockstep: a
    global option added there is recognized here without a second edit. Typer
    stores the first declaration string in ``default`` and any alias in
    ``param_decls``, so both are collected.
    """
    every: set[str] = set()
    valued: set[str] = set()
    for param in _shared_option_params():
        decls: list[str] = []
        for meta in getattr(param.annotation, "__metadata__", ()):
            first = getattr(meta, "default", None)
            if isinstance(first, str) and first.startswith("-"):
                decls.append(first)
            decls.extend(d for d in getattr(meta, "param_decls", None) or () if d.startswith("-"))
        if not decls:
            continue
        every.update(decls)
        # A boolean flag takes no value, so it must not swallow the next token
        # when the corrected command line is rebuilt.
        if getattr(param.annotation, "__origin__", None) is not bool:
            valued.update(decls)
    return frozenset(every), frozenset(valued)


def _corrected_command(tokens: Sequence[str]) -> str | None:
    """Rebuild an invocation with leading global options moved after the command.

    ``mammoth --profile prod doctor`` becomes ``mammoth doctor --profile prod``.
    Returns None when there is nothing to move or nothing to move it behind.
    """
    every, valued = _global_option_flags()
    leading: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name = token.split("=", 1)[0]
        if name not in every:
            break
        leading.append(token)
        index += 1
        if "=" not in token and name in valued and index < len(tokens):
            leading.append(tokens[index])
            index += 1
    rest = list(tokens[index:])
    if not leading or not rest:
        return None
    return " ".join(["mammoth", *rest, *leading])


def _usage_error_report(error: Any, tokens: Sequence[str]) -> CliError | None:
    """Classify a usage error whose own Click message is empty or misleading.

    Returns None when Click's message already reads well, so the generic
    ``usage_error`` envelope and Click's own human rendering are kept.
    """
    if _NO_ARGS_ERROR is not None and isinstance(error, _NO_ARGS_ERROR):
        context = getattr(error, "ctx", None)
        path = getattr(context, "command_path", None) or "mammoth"
        # The root group is the one with no parent context; the program name
        # itself can contain spaces (``python -m mammoth_cli``), so it is not a
        # reliable signal.
        is_root = context is not None and getattr(context, "parent", None) is None
        subject = "command" if is_root else "subcommand"
        # No recovery command: the caller has to choose a command, and there is
        # no single runnable one to replay. The message and hint carry it.
        return CliError(
            code="usage_error",
            message=f"No {subject} given for '{path}'.",
            exit_status=EXIT_USAGE,
            hint=f"Run '{path} --help' to list the available {subject}s.",
            details={"command_path": path},
        )

    match = _NO_SUCH_COMMAND.search(error.format_message() or "")
    if match is None:
        return None
    name = match.group("name").split("=", 1)[0]
    if not name.startswith("-") or name not in _global_option_flags()[0]:
        return None
    # Only leaf commands declare the global options, so a group reads one as a
    # subcommand name and reports a misleading "No such command '--profile'".
    context = getattr(error, "ctx", None)
    path = getattr(context, "command_path", None) or "mammoth"
    if context is not None and getattr(context, "parent", None) is not None:
        # The option sits after a group that still needs a subcommand.
        return CliError(
            code="usage_error",
            message=f"'{path}' is a command group; it needs a subcommand before '{name}'.",
            exit_status=EXIT_USAGE,
            hint=f"Run '{path} --help' to list its subcommands.",
            details={"option": name, "command_path": path},
        )
    corrected = _corrected_command(tokens)
    return CliError(
        code="usage_error",
        message=f"Global option '{name}' must come after the command, not before it.",
        exit_status=EXIT_USAGE,
        hint=(
            f"Try: {corrected}"
            if corrected
            else "Every command declares the global options itself, so they follow the command."
        ),
        details={"option": name},
        recovery_commands=[corrected] if corrected else [],
    )


class _LeafGroup(TyperGroup):
    """Group for a node that is also an invocable command with positionals.

    Click resolves the first bare token after a group as a subcommand name, so
    ``mammoth project resource-dependencies 3`` failed with ``No such command
    '3'`` even though the manifest (and every printed example) takes the
    project id positionally. When the leading token is not a registered
    subcommand, keep every token as an argument for the group callback instead;
    genuine subcommands (``... resource-dependencies update 3``) are unaffected.
    """

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        # Click's parser consumes ``args`` in place; keep the tokens for the second parse.
        tokens = list(args)
        super().parse_args(ctx, args)
        protected = list(getattr(ctx, "_protected_args", ()) or ())
        if protected and protected[0] not in self.commands:
            # Leaf invocation. A group parser stops at the first bare token, so
            # options after the positional were left unparsed; parse again as a
            # plain command with interspersed options, keeping the bare tokens
            # as the callback's positional arguments.
            ctx.allow_interspersed_args = True
            ctx.args = _ClickCommand.parse_args(self, ctx, tokens)
            # Click's own attribute for the pending subcommand token (Click
            # >= 8.2 made it private); not an SDK member.
            setattr(ctx, "_protected_args", [])  # noqa: B010
        return list(ctx.args)


class _EnvelopeGroup(TyperGroup):
    """Root group that renders Click usage errors as the machine error envelope.

    It also materialises top-level command groups lazily (see
    :func:`_load_top_level_group`): ``list_commands`` and ``get_command`` know
    every group by name from the manifest, but a group's Click tree is only
    built when it is invoked, completed or listed in ``--help``. Reading
    ``commands`` directly materialises them all, so tools that walk the tree
    still see the full surface.

    Click's standalone error handling prints a human ``Usage: ... Error: ...``
    message and exits, even under ``--output json``: an agent driving the CLI
    then receives un-parseable prose (or, for a leaf that also parents
    subcommands, a raw ``No such command`` error) instead of the stable JSON
    envelope every handler-level failure emits. This override intercepts every
    usage error (Typer's vendored ``UsageError``) raised anywhere in the command
    tree and, when a machine output was requested, emits the same envelope
    contract. Human output is unchanged (Click's own rendering is reused).

    The interception runs Click's machinery with ``standalone_mode=False`` so
    usage errors propagate here rather than being printed by Click, then restores
    the ``SystemExit`` contract the console entry point and the test runner rely
    on.
    """

    @property  # type: ignore[override]
    def commands(self) -> dict[str, Any]:
        loaded: dict[str, Any] = self.__dict__.setdefault("_eager_commands", {})
        for name in _LAZY_GROUP_NAMES:
            if name not in loaded:
                loaded[name] = _load_lazy_root(name)
        return loaded

    @commands.setter
    def commands(self, value: Any) -> None:
        self.__dict__["_eager_commands"] = dict(value or {})

    def list_commands(self, ctx: Any) -> list[str]:
        eager = self.__dict__.get("_eager_commands", {})
        # Top-level leaves list ahead of groups, the order they were registered in.
        lazy = sorted(_LAZY_GROUP_NAMES, key=lambda name: name not in _LAZY_LEAF_IDS)
        return [*eager, *(name for name in lazy if name not in eager)]

    def get_command(self, ctx: Any, cmd_name: str) -> Any:
        eager: dict[str, Any] = self.__dict__.setdefault("_eager_commands", {})
        if cmd_name not in eager and cmd_name in _LAZY_GROUP_NAMES:
            if self.__dict__.get("_listing_help"):
                if cmd_name in _LAZY_LEAF_IDS:
                    return _root_leaf_stub(cmd_name)
                return _group_stub(cmd_name)
            eager[cmd_name] = _load_lazy_root(cmd_name)
        return eager.get(cmd_name)

    def resolve_command(self, ctx: Any, args: list[str]) -> Any:
        # Typer's override suggests close names from ``self.commands``, which
        # builds every group; the names alone are all a suggestion needs.
        try:
            return self._click_resolve_command(ctx, args)
        except _typer_click_exceptions.UsageError as error:
            if self.suggest_commands and args:
                matches = get_close_matches(args[0], self.list_commands(ctx))
                if matches:
                    suggestions = ", ".join(f"{m!r}" for m in matches)
                    error.message = f"{error.message.rstrip('.')}. Did you mean {suggestions}?"
            raise

    def format_help(self, ctx: Any, formatter: Any) -> None:
        # Root ``--help`` only needs each group's name, panel and one-line
        # description; building all ~550 commands to print them cost seconds.
        self.__dict__["_listing_help"] = True
        try:
            super().format_help(ctx, formatter)
        finally:
            self.__dict__["_listing_help"] = False

    def main(self, *args: Any, **kwargs: Any) -> Any:
        if not kwargs.get("standalone_mode", True):
            return super().main(*args, **kwargs)
        kwargs["standalone_mode"] = False
        try:
            result = super().main(*args, **kwargs)
        except _USAGE_ERRORS as error:
            argv = kwargs.get("args")
            if argv is None:
                argv = args[0] if args else None
            self.render_usage_error(error, argv)
            raise SystemExit(getattr(error, "exit_code", EXIT_USAGE)) from None
        except _ABORT_ERRORS:
            typer.echo("Aborted!", err=True)
            raise SystemExit(1) from None
        # Under standalone_mode=False a normal return is either None (success) or
        # an int exit code (a click Exit, e.g. --help/--version or our own
        # CliError path). Re-raise SystemExit so both the console script and the
        # in-process test runner observe the exit status as before.
        raise SystemExit(result if isinstance(result, int) else 0)

    def render_usage_error(self, error: Any, argv: Sequence[str] | None) -> None:
        """Emit a usage error as the JSON envelope (machine) or Click prose (human).

        A *missing required argument* is reported with the stable
        ``missing_argument`` code that the handler-level ``_require_*`` helpers
        also raise, so the machine error contract is identical whether a required
        positional is now enforced natively by Typer (a Click-layer
        ``MissingParameter``, the common case since positionals are declared with
        their real requiredness) or by a handler that reads it from
        ``extra_args``. Every other usage error (unknown command, bad option or
        argument value, an id read as a subcommand) stays ``usage_error``.

        Two Click messages are unusable as-is and are replaced by
        :func:`_usage_error_report`: the empty one a group raises when invoked
        with no subcommand, and the "No such command '--profile'" a global
        option written before the command produces.
        """
        tokens = list(argv) if argv is not None else sys.argv[1:]
        # Missing required parameters must not be rewritten by the generic
        # group-level classifier (schema get and nested commands rely on the
        # stable missing_argument envelope).
        error_message = error.format_message()
        is_missing_parameter = (
            isinstance(error, _typer_click_exceptions.MissingParameter)
            or error.__class__.__name__ == "MissingParameter"
            or bool(re.match(r"^Missing argument '[^']+'\.", error_message))
        )
        report = None if is_missing_parameter else _usage_error_report(error, tokens)
        if is_missing_parameter and (option := _unknown_flag_in(error, tokens)):
            # A misspelt flag is the first thing to fix, ahead of a missing argument.
            report = CliError(
                code="unknown_option",
                message=f"Unknown option '{option}'.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"option": option},
            )
        if _output_mode_from_argv(argv) in MACHINE_OUTPUTS:
            if report is None:
                missing = is_missing_parameter
                if missing:
                    report = CliError(
                        code="missing_argument",
                        message=error_message,
                        exit_status=EXIT_USAGE,
                        hint="Check the command schema with 'mammoth schema get'.",
                    )
                elif isinstance(error, _typer_click_exceptions.NoSuchOption):
                    option = getattr(error, "option_name", None) or "unknown"
                    close = getattr(error, "possibilities", None) or []
                    report = CliError(
                        code="unknown_option",
                        message=f"Unknown option '{option}'.",
                        exit_status=EXIT_USAGE,
                        hint=(
                            f"Did you mean {' or '.join(sorted(close))}?"
                            if close
                            else "Check the command schema with 'mammoth schema get'."
                        ),
                        details={"option": option},
                    )
                elif isinstance(error, _typer_click_exceptions.BadParameter):
                    # With optional typed positionals Click may consume an
                    # unknown option token as the positional value. Only
                    # classify an argv flag that is not a known global option;
                    # a known option's malformed value remains usage_error.
                    option = _unknown_flag_in(error, tokens)
                    if option:
                        report = CliError(
                            code="unknown_option",
                            message=f"Unknown option '{option}'.",
                            exit_status=EXIT_USAGE,
                            hint="Check the command schema with 'mammoth schema get'.",
                            details={"option": option},
                        )
                    else:
                        report = CliError(
                            code="usage_error",
                            message=error.format_message(),
                            exit_status=EXIT_USAGE,
                            hint="Check the command schema with 'mammoth schema get'.",
                        )
                else:
                    report = CliError(
                        code="missing_argument" if missing else "usage_error",
                        message=error.format_message(),
                        exit_status=EXIT_USAGE,
                        hint="Check the command schema with 'mammoth schema get'.",
                    )
            from mammoth_cli.runtime import executor

            executor.emit_error(report, machine=True)
        elif report is None:
            error.show()
        else:
            typer.echo(f"Error: {report.message}", err=True)
            # A no-subcommand error arrives with the help text already on
            # screen, so repeating "run --help" below it would be noise.
            no_args = _NO_ARGS_ERROR is not None and isinstance(error, _NO_ARGS_ERROR)
            if report.hint and not no_args:
                typer.echo(report.hint, err=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(0)


def _shared_option_params() -> list[inspect.Parameter]:
    """Build the global-option parameters shared by every command.

    These are the machine-output and agent-mode options every command exposes.
    They are declared once, as :class:`inspect.Parameter`s, so a dynamically
    synthesized command signature can splice them in after any positionals while
    keeping the option contract in exactly one place.
    """
    p = inspect.Parameter

    def opt(name: str, default: Any, annotation: Any) -> inspect.Parameter:
        return p(name, p.POSITIONAL_OR_KEYWORD, default=default, annotation=annotation)

    return [
        opt(
            "output",
            OUTPUT_AUTO,
            Annotated[
                str,
                typer.Option(
                    "--output",
                    "-o",
                    help="Output format. 'auto' picks a table on a terminal, JSON when piped.",
                    metavar="|".join(SELECTABLE_OUTPUTS),
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "profile",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--profile",
                    help="Credential profile name.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "project",
            None,
            Annotated[
                int | None,
                typer.Option(
                    "--project",
                    help="Active project id override.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "session",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--session",
                    help="Agent chat session id for 'agent action' and 'agent run' commands.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--timeout",
                    help="Per-request timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "job_timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--job-timeout",
                    help="Job wait timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "return_running",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--return-running",
                    help=(
                        "When a job or pipeline wait runs out, exit 0 with "
                        "{status: running, job_id or dataview_id, resume} instead of a "
                        "timeout error; resume with 'mammoth job wait JOB_ID' "
                        "(reports success, failure or still running; waits at most "
                        "15 minutes by default)."
                    ),
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "pipeline_timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--pipeline-timeout",
                    help="Pipeline wait timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "color",
            "auto",
            Annotated[
                str,
                typer.Option(
                    "--color",
                    help="Color policy.",
                    metavar="|".join(COLOR_MODES),
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "no_input",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--no-input",
                    help="Never prompt; fail instead.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "no_progress",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--no-progress",
                    help="Never render progress.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "debug",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--debug",
                    help="Emit diagnostic detail to stderr.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "yes",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--yes",
                    "-y",
                    help="Confirm a mutation without prompting.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "confirm",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--confirm",
                    help="Exact target name required for high-impact actions.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "dry_run",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--dry-run",
                    help="Resolve and validate, then report the request instead of sending it.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "allow_empty",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--allow-empty",
                    help="Add a keep filter that matches no row; without it the dry run fails.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "standing",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--standing",
                    help="Stage a step that changes no row today, as a rule for future data.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "input_file",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--input",
                    help="Strict JSON/YAML request document, or '-' for stdin.",
                    rich_help_panel="Request input",
                ),
            ],
        ),
        opt(
            "input_format",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--input-format",
                    help="Required for stdin: json or yaml.",
                    rich_help_panel="Request input",
                ),
            ],
        ),
    ]


_SHARED_OPTION_PARAMS = _shared_option_params()


def _positional_param(spec: PositionalSpec) -> inspect.Parameter:
    """Build a Typer ``Argument`` parameter for one positional spec.

    The argument is declared with the spec's native scalar type (``int`` or
    ``str``) and its native requiredness, so ``--help`` shows the truth: a
    required id renders as ``DATASET_ID`` / ``<int>`` (not an optional
    ``[DATASET_ID]`` / ``<str>``) and Typer enforces both presence and type at
    parse time. A missing or ill-typed *required* positional raises a Click-layer
    usage error that :class:`_EnvelopeGroup` renders as the stable JSON envelope
    under a machine ``--output`` (``missing_argument`` for an absent one,
    ``usage_error`` for a bad value), preserving the machine error contract. An
    *optional* positional keeps a ``None`` default and an ``Optional`` annotation;
    the handler fills it from ``--input`` or resolved context when omitted.
    """
    if spec.required:
        return inspect.Parameter(
            spec.name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[spec.type, typer.Argument(help=spec.help, metavar=spec.metavar)],
        )
    return inspect.Parameter(
        spec.name,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Annotated[
            spec.type | None, typer.Argument(help=spec.help, metavar=spec.metavar)
        ],
    )


def _build_leaf(command_id: str, *, is_group_callback: bool = False) -> Callable[..., None]:
    """Return a Typer callback bound to one manifest command id.

    Every callback shares the same global-option signature so ``--help`` for any
    command advertises the machine-output and agent-mode contract, and declares
    one native Typer ``Argument`` per positional derived for the command (see
    :func:`mammoth_cli.services.positionals.resolve_positionals`), so its
    ``--help`` shows an Arguments panel and the parsed values route into
    :attr:`Invocation.positionals` — a single, code-derived source of truth for
    the command's positional shape.

    The parsed positionals are also mirrored, in declared order, into
    :attr:`Invocation.extra_args` ahead of any genuine surplus tokens. Handlers
    may read them positionally (``extra_args``) or by name
    (:meth:`Invocation.positional`); both views come from the same declaration,
    so they cannot drift, and the surplus/id checks in
    :mod:`mammoth_cli.runtime.strict` and :mod:`mammoth_cli.runtime.validate`
    (which align a command's derived positionals against ``extra_args``) keep
    working unchanged.

    When ``is_group_callback`` is set the command sits at a node that also has
    subcommands; the callback then only runs when no subcommand is invoked and
    declares no positionals.
    """
    positionals: tuple[PositionalSpec, ...] = (
        () if is_group_callback else resolve_positionals(command_id)
    )
    positional_names = tuple(spec.name for spec in positionals)

    def leaf(**params: Any) -> None:
        from mammoth_cli.runtime.invocation import Invocation

        ctx: typer.Context = params.pop("ctx")
        if is_group_callback and ctx.invoked_subcommand is not None:
            return
        resolved = {name: params.pop(name) for name in positional_names}
        present = {name: value for name, value in resolved.items() if value is not None}
        # Mirror the bound positionals (in declared order) into extra_args ahead
        # of any genuine surplus tokens, so handlers reading extra_args by index
        # and the derived-positional surplus/id checks both keep working.
        mirrored = [str(resolved[name]) for name in positional_names if resolved[name] is not None]
        invocation = Invocation(
            command_id=command_id,
            positionals=present,
            extra_args=[*mirrored, *ctx.args],
            **params,
        )
        _execute(invocation)

    signature_params = [
        inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context),
        *(_positional_param(spec) for spec in positionals),
        *_SHARED_OPTION_PARAMS,
    ]
    leaf.__signature__ = inspect.Signature(signature_params)  # type: ignore[attr-defined]
    leaf.__annotations__ = {param.name: param.annotation for param in signature_params}
    leaf.__name__ = "cmd_" + command_id.replace(".", "_").replace("-", "_")
    return leaf


def _execute(invocation: Invocation) -> None:
    """Run one command: dispatch to its handler and render the envelope."""
    # Freeze the fallback profile before opening a service.  A recovery command
    # must inspect the same account that submitted/observed a job, rather than
    # resolving the mutable selected-profile pointer after an interrupt.
    from mammoth_cli.context import profiles
    from mammoth_cli.runtime import executor, validate
    from mammoth_cli.runtime.dataset_health import with_dataset_health
    from mammoth_cli.runtime.intent_only import refuse_hand_crafted_write
    from mammoth_cli.runtime.locked_files import with_locked_files
    from mammoth_cli.runtime.new_data import with_new_data_path
    from mammoth_cli.runtime.opens import with_opens
    from mammoth_cli.runtime.strict import validate_extra_args

    if invocation.profile is None:
        invocation = replace(invocation, profile=profiles.get_selected())

    def producer() -> tuple[Any, dict[str, Any]]:
        refuse_hand_crafted_write(invocation.command_id)
        validate.validate_invocation(invocation)
        validate_extra_args(invocation.command_id, invocation.extra_args)
        validate.validate_positional_ids(invocation.command_id, invocation.extra_args)
        # Admit structured input before resolving a handler or opening a
        # service.  Handlers retain ``load_input`` for compatibility, but it
        # now returns this invocation-local prepared value.
        invocation.prepare_input()
        # S2 API-backed families use the same resolved contract for the final
        # input-to-SDK binding.  Run that boundary before dispatch even for a
        # zero-input/positional-only handler so every migrated route has one
        # admission and binding path and a binding defect cannot become a
        # late network-side error.
        from mammoth_cli.services.command_contract import S2_COMMANDS

        if invocation.command_id in S2_COMMANDS:
            invocation.bound_input()
        handler = HANDLERS.get(invocation.command_id)
        if handler is None:
            record = command_by_id(invocation.command_id)
            sdk_symbol = record.get("sdk_symbol", "") if record else ""
            raise not_implemented_error(invocation.command_id, sdk_symbol)
        if invocation.dry_run:
            return _dry_run(handler, invocation)
        data, meta = handler(invocation)
        checked = with_locked_files(with_dataset_health(_apply_verify(invocation, data)))
        return with_new_data_path(checked), with_opens(invocation, checked, meta)

    executor.run(
        invocation.command_id,
        invocation.output,
        producer,
        agent_mode=invocation.no_input,
        invocation=invocation,
        profile=invocation.profile,
    )


def _apply_verify(invocation: Invocation, data: Any) -> Any:
    """Add the automatic write read-back to a real, mutating, API-backed result.

    A read command and a command with no reviewed ``sdk_symbol`` (a local or
    not-yet-backed command) are returned unchanged; ``--dry-run`` never
    reaches this at all, since it returns before the handler's real call.

    Two independent read-backs are layered on top of the raw result: ``verify``
    (status/row-count signals derived from the write's own response) and
    ``state`` (a fresh read of what the write actually produced, per the
    command's manifest ``readback``/``no_readback`` declaration -- see
    :mod:`mammoth_cli.runtime.state`).
    """
    from mammoth_cli.runtime.state import with_state
    from mammoth_cli.runtime.verify import with_verify

    record = command_by_id(invocation.command_id) or {}
    if record.get("mutation_class") == "read" or not record.get("sdk_symbol"):
        return data
    return with_state(invocation, with_verify(data, invocation))


def _dry_run(handler: Handler, invocation: Invocation) -> tuple[Any, dict[str, Any]]:
    """Run ``handler`` until its request would leave; report that request.

    Local commands never open a service, so a dry run of one is the real run.
    An API-backed handler that returns normally under ``--dry-run`` made no
    gated SDK call at all (a pure read path); its result is returned as is.
    """
    from mammoth_cli.runtime.dryrun import DryRunStop
    from mammoth_cli.runtime.dryrun_targets import resolve_dependents, resolve_targets
    from mammoth_cli.runtime.session import open_service, resolved_project

    try:
        return handler(invocation)
    except DryRunStop as stop:
        with open_service(invocation) as (service, _auth):
            would_call = stop.record["would_call"]
            targets = resolve_targets(service, invocation.command_id, would_call)
            dependents = resolve_dependents(
                service, invocation.command_id, would_call, resolved_project(invocation)
            )
        impact = invocation.predicted_impact
        report = {**stop.record, "targets": targets}
        if dependents is not None:
            report["dependents"] = dependents
        if impact is not None:
            report["predicted_impact"] = impact
        return report, {"profile": invocation.profile, "project_id": resolved_project(invocation)}


def live_command_summary(command_id: str) -> str | None:
    """The backing handler's docstring first line, the lead of a command's help.

    Reading it imports the handler's module, so a group listing takes it from
    the generated index (:func:`_indexed_summary`) instead.
    """
    handler = HANDLERS.get(command_id) or BESPOKE.get(command_id)
    doc = inspect.getdoc(handler) if handler is not None else None
    if not doc:
        return None
    # First non-empty line, with RST inline-code backticks flattened to plain
    # quotes so the help reads as prose rather than reStructuredText.
    return doc.strip().splitlines()[0].strip().replace("``", "'") or None


@cache
def _summary_index() -> dict[str, str]:
    """Every command's help summary, generated by ``scripts/gen_help_summaries.py``."""
    path = Path(__file__).parent / "commands" / "help_summaries.json"
    return cast(dict[str, str], json.loads(path.read_text(encoding="utf-8")))


def _indexed_summary(command_id: str) -> str | None:
    return _summary_index().get(command_id)


#: A line of ``--help`` a command needs that its handler's shared docstring cannot carry.
_RAW_NOTE = "Input field raw: true returns DATE values with their time, not the date alone."
_HELP_NOTES = {
    "view.data.get": _RAW_NOTE,
    "view.data.query": _RAW_NOTE,
    "view.export.dataset": (
        "Omit dataset_name unless the user gave one; the product default 'Result Dataset' is used."
    ),
}


def _command_help(command_id: str, record: dict[str, Any] | None) -> str | None:
    """Build a command's user-facing ``--help`` summary.

    Kept deliberately distinct from ``known_restrictions`` (internal review and
    planning notes), which used to be shown here verbatim and leaked plan-document
    prose -- e.g. "specified in plan 02's ... contract" -- into the user-facing
    ``--help``. Instead the summary is the backing handler's docstring first line
    (actionable field guidance such as "``columns``/``mapping`` required"),
    followed by the manifest's runnable ``agent_example``, which already encodes
    every required positional and ``--input`` field. ``known_restrictions``
    remains available to machines through ``schema get``.
    """
    from mammoth_cli.commands.schema import IN_PLACE_RECIPE, edits_view_in_place

    parts: list[str] = []
    summary = live_command_summary(command_id)
    if summary:
        parts.append(summary)
    if record is not None and edits_view_in_place(record):
        parts.append(IN_PLACE_RECIPE)
    if command_id in _HELP_NOTES:
        parts.append(_HELP_NOTES[command_id])
    example = (record or {}).get("agent_example")
    if example:
        parts.append(f"Example: {example}")
    fields = _help_input_fields(command_id)
    if fields:
        parts.append(f"Input fields: {fields}")
    return "\n\n".join(parts) or None


def _help_input_fields(command_id: str) -> str | None:
    """One line naming the ``--input`` fields, so ``--help`` can replace ``schema get``.

    Required fields come first and are marked with ``*``; each carries its
    short type, or its enum values. Bounded to keep ``--help`` readable; the
    full contract stays behind ``schema get``.
    """
    from mammoth_cli.services.command_contract import resolve_command_contract

    try:
        contract = resolve_command_contract(command_id)
    except Exception:  # noqa: BLE001 -- help must never fail on a contract quirk
        return None
    if contract is None or not contract.accepted_fields:
        return None
    rendered: list[str] = []
    fields = sorted(contract.accepted_fields, key=lambda item: (not item.required, item.name))
    for field in fields:
        label = f"{field.name}*" if field.required else field.name
        enum = field.enum_values
        kind = "|".join(str(item) for item in enum[:6]) if enum else _short_type(field.type_name)
        rendered.append(f"{label} ({kind})" if kind else label)
        if len(rendered) == 12 and len(fields) > 12:
            rendered.append(f"... {len(fields) - 12} more (schema get {command_id})")
            break
    return ", ".join(rendered)


def _short_type(type_name: str) -> str:
    """``mammoth.condition.Condition | ...`` -> ``condition``; dotted names lose their module."""
    text = str(type_name or "")
    if "condition." in text:
        return "condition"
    return " | ".join(part.strip().rsplit(".", 1)[-1] for part in text.split("|"))[:40]


def _command_records() -> list[dict[str, Any]]:
    return [r for r in load_commands() if r.get("disposition") != "alias"]


@cache
def _command_tree() -> tuple[dict[tuple[str, ...], str], frozenset[tuple[str, ...]]]:
    """Map every command path to its id, and name the container nodes.

    A "container command" sits at a node that also has deeper subcommands
    (e.g. ``dataset file-settings``, which also has ``... undo`` / ``... update``).
    """
    path_to_command = {
        tuple(r["command_path"].split()): r["command_id"] for r in _command_records()
    }
    prefixes: set[tuple[str, ...]] = set()
    for tokens in path_to_command:
        for depth in range(1, len(tokens)):
            prefixes.add(tokens[:depth])
    return path_to_command, frozenset(prefixes & path_to_command.keys())


def _leaf_context_settings(command_id: str) -> dict[str, bool]:
    """Click settings for one command: a bespoke command declares every option it
    accepts, so Click itself rejects an unknown one; a generic leaf collects its
    trailing tokens and validates them in :func:`validate_extra_args`."""
    if command_id in BESPOKE:
        return {}
    return {"allow_extra_args": True, "ignore_unknown_options": True}


def _group_typer(tokens: tuple[str, ...], command_id: str | None) -> typer.Typer:
    if command_id is not None:
        # This node is both a group and an invocable command.
        sub = typer.Typer(
            cls=_LeafGroup,
            no_args_is_help=False,
            invoke_without_command=True,
            context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
        )
        sub.callback()(_build_leaf(command_id, is_group_callback=True))
        return sub
    return typer.Typer(
        help=_group_description(tokens),
        no_args_is_help=True,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )


def _lazy_help_command(command_id: str) -> type[TyperCommand]:
    """A command class whose help is read from the handler only when printed.

    Building a group registers every command in it; reading each help text up
    front imports every handler module of the group, though a run uses one.
    """

    class LazyHelpCommand(TyperCommand):
        @property
        def help(self) -> str | None:
            return _command_help(command_id, command_by_id(command_id))

        @help.setter
        def help(self, value: str | None) -> None:
            """Ignore the registration-time placeholder; the handler is the source."""

        @property
        def short_help(self) -> str | None:
            """The group listing prints only the first paragraph, which is the summary."""
            return _indexed_summary(command_id)

        @short_help.setter
        def short_help(self, value: str | None) -> None:
            """Ignore the registration-time value; the handler is the source."""

    return LazyHelpCommand


def _unbuilt_leaf() -> None:
    """Registration placeholder: a lazy leaf takes its real callback from the built command."""


def _lazy_leaf_command(command_id: str) -> type[TyperCommand]:
    """A generic leaf whose parameters and callback are built when first read.

    Building a leaf derives its positionals from the SDK signature, which
    imports the SDK model modules. A group's ``--help`` lists names and help
    only, so it never reads them; a run reads them for the one command used.
    """

    class LazyLeafCommand(_lazy_help_command(command_id)):  # type: ignore[misc]
        _built: _ClickCommand | None = None

        def _real(self) -> _ClickCommand:
            if self._built is None:
                from typer.models import CommandInfo

                info = CommandInfo(
                    name=self.name,
                    callback=_build_leaf(command_id),
                    help=_command_help(command_id, command_by_id(command_id)),
                    rich_help_panel=self.rich_help_panel,
                    context_settings=_leaf_context_settings(command_id),
                )
                self._built = typer.main.get_command_from_info(
                    info,
                    pretty_exceptions_short=_LAZY_SETTINGS["pretty_exceptions_short"],
                    rich_markup_mode=self.rich_markup_mode,
                )
            return self._built

        @property
        def params(self) -> list[_ClickParameter]:
            return self._real().params

        @params.setter
        def params(self, value: list[_ClickParameter]) -> None:
            """Ignore the registration-time parameters; the built command owns them."""

        @property
        def callback(self) -> Any:
            return self._real().callback

        @callback.setter
        def callback(self, value: Any) -> None:
            """Ignore the registration-time placeholder callback."""

    return LazyLeafCommand


def _populate(base: tuple[str, ...], group: typer.Typer) -> None:
    """Register every command below ``base`` (exclusive) on ``group``."""
    path_to_command, containers = _command_tree()
    groups: dict[tuple[str, ...], typer.Typer] = {base: group}

    def _group_for(tokens: tuple[str, ...]) -> typer.Typer:
        if tokens in groups:
            return groups[tokens]
        parent = _group_for(tokens[:-1])
        sub = _group_typer(tokens, path_to_command.get(tokens))
        top_level = tokens[0]
        parent.add_typer(
            sub,
            name=tokens[-1],
            help=_group_description(tokens),
            rich_help_panel=_ROOT_HELP_PANELS.get(top_level) if len(tokens) == 1 else None,
        )
        groups[tokens] = sub
        return sub

    below = {t: c for t, c in path_to_command.items() if t[: len(base)] == base and t != base}
    # Ensure every container group exists (parents before children).
    for tokens in sorted((t for t in below if t in containers), key=len):
        _group_for(tokens)

    # Register every non-container command as a leaf under its parent group.
    # A command_id with a bespoke, fully-typed callback overrides the generic
    # leaf at the same registered name and path; the manifest-driven surface
    # is otherwise unchanged.
    for tokens, command_id in sorted(below.items()):
        if tokens in containers:
            continue
        bespoke = BESPOKE.get(command_id)
        _group_for(tokens[:-1]).command(
            name=tokens[-1],
            cls=_lazy_help_command(command_id) if bespoke else _lazy_leaf_command(command_id),
            help="",
            rich_help_panel=_ROOT_HELP_PANELS.get(tokens[0]) if len(tokens) == 1 else None,
            context_settings=_leaf_context_settings(command_id),
        )(bespoke or _unbuilt_leaf)


@cache
def _top_level_typer(name: str) -> typer.Typer:
    """Build (once) the Typer sub-app for one top-level command group."""
    path_to_command, _ = _command_tree()
    sub = _group_typer((name,), path_to_command.get((name,)))
    _populate((name,), sub)
    return sub


# Top-level groups are converted to Click on first use. Building the leaf
# callbacks and ``--help`` text for all ~550 commands, then letting Typer
# convert every one of them, used to cost most of the CLI's start-up time on
# every invocation; a run touches one group.
_LAZY_GROUP_NAMES: list[str] = []
_LAZY_SETTINGS: dict[str, Any] = {}


def _load_top_level_group(name: str) -> Any:
    from typer.models import TyperInfo

    info = TyperInfo(
        _top_level_typer(name),
        name=name,
        help=_GROUP_DESCRIPTIONS.get(name, f"Commands for {name}."),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
    )
    return typer.main.get_group_from_info(info, **_LAZY_SETTINGS)


# Root ``--help`` prints each top-level leaf's help; reading it from the handler
# would import the handler's module (and its SDK dependencies). A test pins this
# table to :func:`_command_help` so it cannot drift.
_ROOT_LEAF_HELP: dict[str, str] = {
    "calc": (
        "Evaluate one arithmetic expression exactly."
        "\n\nExample: mammoth calc '2063664 - 1917815'"
    ),
    "doctor": (
        "Run environment and connectivity diagnostics."
        "\n\nExample: mammoth doctor\n\nInput fields: wait (int)"
    ),
    "link": (
        "Read the workspace, project, folder, dataset and view ids out of a pasted app URL."
        "\n\nExample: mammoth link https://app.mammoth.io/workspaces/1/projects/2/data/datasets"
    ),
    "resolve": (
        "Say what NAME refers to: a dataset, a view or a project, with ids and projects."
        "\n\nExample: mammoth resolve uqa-w29-ren\n\nInput fields: all_projects (bool)"
    ),
    "upgrade": (
        "Upgrade the mammoth CLI to the latest (or a specified) version from PyPI."
        "\n\nExample: mammoth upgrade"
    ),
    "version": "Example: mammoth version",
}
_LAZY_LEAF_IDS: dict[str, str] = {}


def _load_root_leaf(name: str) -> Any:
    from typer.models import CommandInfo

    command_id = _LAZY_LEAF_IDS[name]
    info = CommandInfo(
        name=name,
        callback=BESPOKE.get(command_id) or _build_leaf(command_id),
        help=_command_help(command_id, command_by_id(command_id)),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        context_settings=_leaf_context_settings(command_id),
    )
    return typer.main.get_command_from_info(
        info,
        pretty_exceptions_short=_LAZY_SETTINGS["pretty_exceptions_short"],
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
    )


def _root_leaf_stub(name: str) -> Any:
    """A placeholder leaf carrying only what the root ``--help`` listing prints."""
    return TyperCommand(
        name=name,
        help=_ROOT_LEAF_HELP[name],
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
    )


def _load_lazy_root(name: str) -> Any:
    return _load_root_leaf(name) if name in _LAZY_LEAF_IDS else _load_top_level_group(name)


def _group_stub(name: str) -> Any:
    """A placeholder group carrying only what the root ``--help`` listing prints."""
    return TyperGroup(
        name=name,
        help=_GROUP_DESCRIPTIONS.get(name, f"Commands for {name}."),
        rich_help_panel=_ROOT_HELP_PANELS.get(name),
        rich_markup_mode=_LAZY_SETTINGS["rich_markup_mode"],
    )


def build_app() -> typer.Typer:
    """Construct the Typer command tree from the command manifests.

    Top-level leaves (``doctor``, ``version``, ...) are registered here; every
    top-level group is materialised by :class:`_EnvelopeGroup` on demand.
    """
    root = typer.Typer(
        name="mammoth",
        help=(
            "Command-line interface for the Mammoth Analytics platform.\n\n"
            "Start with 'mammoth doctor' to check access, 'mammoth schema find QUERY' "
            "to locate a command, and 'mammoth schema get COMMAND_ID' for its full input schema."
        ),
        no_args_is_help=True,
        add_completion=True,
        cls=_EnvelopeGroup,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )

    @root.callback()
    def _root(
        version: bool = typer.Option(
            False, "--version", callback=_version_callback, is_eager=True, help="Show version."
        ),
    ) -> None:
        """Root callback holding eager global options."""

    path_to_command, containers = _command_tree()
    top_names = sorted({tokens[0] for tokens in path_to_command})
    lazy: list[str] = []
    for name in top_names:
        if (name,) in containers or (name,) not in path_to_command:
            lazy.append(name)
            continue
        _LAZY_LEAF_IDS[name] = path_to_command[(name,)]
        lazy.append(name)
    _LAZY_GROUP_NAMES[:] = lazy
    _LAZY_SETTINGS.update(
        pretty_exceptions_short=root.pretty_exceptions_short,
        rich_markup_mode=root.rich_markup_mode,
        suggest_commands=root.suggest_commands,
    )
    return root


def registered_command_paths() -> set[str]:
    """Return every registered command path by walking the built Typer trees.

    Container commands (a node that is both a group and invocable) are counted
    by their own path as well as their subcommands.
    """
    paths: set[str] = set()

    def walk(instance: typer.Typer, prefix: tuple[str, ...]) -> None:
        for command in instance.registered_commands:
            name = command.name or (command.callback.__name__ if command.callback else None)
            if name:
                paths.add(" ".join((*prefix, name)))
        for group in instance.registered_groups:
            sub = group.typer_instance
            name = group.name
            if sub is None or not name:
                continue
            node = (*prefix, name)
            if sub.registered_callback is not None:
                paths.add(" ".join(node))
            walk(sub, node)

    walk(app, ())
    for name in _LAZY_GROUP_NAMES:
        if name in _LAZY_LEAF_IDS:
            paths.add(name)
            continue
        sub = _top_level_typer(name)
        if sub.registered_callback is not None:
            paths.add(name)
        walk(sub, (name,))
    return paths


@cache
def _root_click_command() -> Any:
    """Build (once) and cache the fully resolved Click command tree.

    ``typer.main.get_command`` walks and converts every registered Typer
    sub-app into its Click representation; over the full manifest-driven tree
    that is expensive enough that recomputing it per lookup made a full sweep
    over every command (see the contract test) take minutes. Cached because
    the tree is fixed for the process lifetime (:data:`app` is built once at
    import time).
    """
    root: Any = typer.main.get_command(app)
    root.commands  # noqa: B018 -- materialise every lazy top-level group
    return root


def command_option_names(command_path: str) -> set[str]:
    """Return every declared option flag for one registered command path.

    Walks the built Click command tree by ``command_path`` tokens (for example
    ``"view transform bulk-replace"``) and collects each parameter's option
    strings (``"--output"``, ``"-o"``, ...). This is a structural check: it
    reads the already-parsed command declaration, so it is fast and immune to
    the rendered-width and terminal-detection nondeterminism of asserting on
    rendered ``--help`` text. Command nodes are walked duck-typed (via their
    ``commands`` mapping) rather than by an ``isinstance`` check against
    ``click``'s public types, since Typer's pinned version resolves its command
    tree through its own vendored click fork (``typer._click``), whose classes
    are not the public ``click`` package's.

    Args:
        command_path: The space-separated manifest command path.

    Returns:
        The union of every parameter's primary and secondary option strings
        declared on that command (or group callback).

    Raises:
        ValueError: When ``command_path`` does not resolve to a registered
            command.
    """
    command: Any = _root_click_command()
    for token in command_path.split():
        subcommands: dict[str, Any] | None = getattr(command, "commands", None)
        if subcommands is None or token not in subcommands:
            raise ValueError(f"'{command_path}' is not a registered command path.")
        command = subcommands[token]
    names: set[str] = set()
    for param in command.params:
        names.update(getattr(param, "opts", ()))
        names.update(getattr(param, "secondary_opts", ()))
    return names


app = build_app()


def main() -> Any:
    """Console-script entry point."""
    return app()


if __name__ == "__main__":  # pragma: no cover
    main()
