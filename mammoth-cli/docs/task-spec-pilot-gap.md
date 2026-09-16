# Typed task-spec pilot and remaining gap

The installed CLI exposes 30 typed `view transform.*` commands. The SDK has
pure builders for their backend task payloads. Limited builder/transport smoke
tests cover `math`, `filter`, `join`, and `convert-type`. Their examples resolve
display names and emit the public `View` payload shape. One math control
compares the outgoing body to a literal payload. These tests do not provide
independent backend semantic oracles or close C2 typed task-spec coverage.

The generic `view task add`, `view task preview`, and `view task update`
routes remain low-level expert operations. The SDK types their `task_spec`
field as `dict[str, Any]`, and the installed command schema cannot publish a
complete discriminated union. The captured OpenAPI shape is permissive and
does not establish the backend's per-task payload contract. Therefore this
release does not invent a union or silently translate typed transform input
into preview/update requests.

Agents should use the typed transform commands for supported construction and
the generic routes only with an independently verified backend task payload.
Typed builders must reject unknown fields and unresolved or ambiguous display
names before any request. Preview/update for the four pilot families remain an
implementation gap until the backend supplies authoritative schemas and exact
method/path/body semantics. The readiness workbook tracks the remaining
surface in its 27 payload-enum / 30 CLI-transform inventory. This note does not
claim independent semantic proof for all 30 commands or enum values.
