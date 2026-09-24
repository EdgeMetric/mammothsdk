# mammoth dashboard * capability sweep — release, workspace 4 / project 3

CLI: `/home/euler/mammoth/mammothsdk/mammoth-cli/.venv/bin/mammoth` 2.0.12, profile `release`.
Fixture dashboards created and fully cleaned up: D=52 (`create-blank` on dataview 45), D3=53 (`v3 generate`), D2=54 (`duplicate` of D). All three were trashed then deleted by the end of the run. Self-created tags (13, then 11/12 auto-attached by AI generation), one QA session (+1 fork), one signature, one context, one custom style were all deleted along the way.

104/104 `dashboard.*` command ids from `schema list` are covered, one line each in `results.jsonl`.

## Verdict counts

| Verdict | Count |
|---|---|
| ok | 57 |
| blocked_missing_fixture | 14 |
| cli_error | 11 |
| skipped_out_of_scope | 11 |
| ok_empty | 8 |
| server_error | 1 |
| not_supported | 1 |
| validation_error | 1 |
| **Total** | **104** |

## ok (57)
dashboard.analytics, cancel-generation, canvas.get, canvas.restore, chat.edit, context.create/update/delete/extract, create-blank, delete, descriptor-data, duplicate, exemplar.extract, get, get-by-url, list, page.plan, pages.add, qa.ask/comment.create/comment.delete/feedback/session.create/session.delete/session.fork/session.get/session.list/session.rename/session.set-visibility/settings.get/settings.set, rls.assignment.set/column.list/value.list, signature.create/delete/update, style.custom.create/delete/update, style.extract-brand, style.preset.list, suggestion.list, swap-data, tags.delete/merge/rename/set, template.fit/list/preview/resolve-mapping, trash, update, v3.generate, video-state.

One-line details worth keeping: `dashboard create-blank` and `dashboard v3.generate` both worked cleanly and are the two live ways to create a dashboard now. `dashboard get-by-url` returns full dashboard data via the share-url slug even when `was_published=false` — a dashboard apparently gets a url at creation regardless of publish state. `dashboard swap-data` and `dashboard template.resolve-mapping`/`preview` correctly re-mapped columns between two same-shaped Terra OWID reference dataviews. `dashboard qa ask` produced a real AI-computed KPI answer, not gated. `dashboard chat.edit` and `dashboard page.plan` both did real AI dashboard editing/composition, not gated.

## ok_empty (8)
chat.history, context.list, restore, rls.assignment.list, signature.list, style.custom.list, tags.list, templates.pending.

`dashboard restore` deserves a flag here even though it "succeeded": called on D2=54 while it was **archived** (not trashed), it returned `{}` (success) but silently did nothing — verified via `dashboard list` that the archived flag was unchanged afterward. It doesn't error when used outside its documented scope ("restore a trashed dashboard"); it silently no-ops.

## blocked_missing_fixture (14)
- `dashboard.widget-data` — HTTP 409 `4DASH004 DASHBOARD_WRONG_ENGINE`: this endpoint only serves the legacy dashboard engine, and no legacy dashboard is obtainable because `dashboard.create` (the only thing that makes legacy dashboards) is retired.
- `dashboard.pdf.export` — HTTP 400 `4GENR001`: needs `params.data` to be a full **client-hydrated** `DashboardData` map (`data.pages`) with pre-rendered widget results; server explicitly says it only stores query descriptors and "cannot rebuild it." Not producible from the CLI without a browser render pass.
- `dashboard.pdf-artifact` — needs a real pdf-export `job_id`, which is unreachable because `pdf.export` above never got a job started.
- `dashboard.published.*` (canvas, data, og-card, pdf-artifact, pdf.export, share-page, video-artifact, video.export), `published-data-by-url`, `widget-data-by-url`, `job-by-url` — all need a **publicly published** dashboard URL. The only publish mechanism found (`dashboard share --input '{"type_of_auth": "public"}'`) is explicitly out of scope per the hard rules, so no publishable url could be produced. Confirmed the failure mode directly on two of them (`published.canvas`, `published.share-page`): HTTP 404 `4DASH001 DASHBOARD_NOT_FOUND` when hit with D's real (but unpublished) share slug; the rest are extrapolated from that identical mechanism and not separately re-run.

## cli_error (11) — see "CLI defects" below for the write-ups
archive, canvas.save, data.draft, data.published, figure-intent, og-card, query, style.default.get, style.derive, style.token.list, template.get.

## server_error (1)
`dashboard.source.list` — HTTP 500 on `GET /dashboards/sources`. Matches the schema's own documented precondition (`B04 SERVER_VARIANCE: documented as returning HTTP 500 on some servers`), so this is a known, already-flagged backend issue, not a new finding.

## not_supported (1)
`dashboard.create` — HTTP 409 `4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED`: "New dashboards are built on the current engine. Your existing dashboards are unchanged and still editable." The command still exists in the CLI and schema but the backend route is retired; `create-blank` / `v3 generate` are the replacements.

## validation_error (1)
`dashboard.video.export` — HTTP 400 `4GENR001`, clear actionable message: "publish the dashboard before exporting a video." Correctly gated behind the same publish step that's out of scope this run.

## skipped_out_of_scope (11)
action, assess-pbix, assess-twb, import-workbook, share, style.default.set, template.apply, template.create, template.delete, template.rename, templates.use — per hard rule 2 verbatim, or requiring a `.pbix`/`.twb` file.

---

## CLI defects (all UNVERIFIED beyond what's stated; each was observed directly against release)

1. **Systemic "***REDACTED***" placeholder corrupts round-trips and hides results (3 confirmed spots).**
   - `dashboard canvas get` returns `canvas.style_tokens` as the literal string `"***REDACTED***"` instead of the actual token dict. Feeding that straight back into `dashboard canvas save` (exactly the "round-trip the canvas you read" step the run plan calls for) fails with HTTP 400 `4GENR001` (pydantic: `style_tokens` must be a dict, got a string). Confirmed root cause by stripping the field and resubmitting: identical payload minus `style_tokens` succeeds (200, `bake_job_id` returned).
   - `dashboard style derive` returns `{"styleTokens": "***REDACTED***"}` as its **entire** result — a 200 response that gives back nothing usable, for a command whose whole purpose is to hand you derived style tokens.
   - `dashboard style token list <id>` (after discovering the `id` positional actually wants a style/preset id, not a dashboard id — the generic help text "Identifier of the resource" and the 404 error you get from passing a dashboard id both point you the wrong way) returns `{"tokens": "***REDACTED***"}` — again the entire payload masked.
   - This is one systemic bug (an output-sanitizer that nukes anything named `*token*`), not three separate ones, but it hits three different commands and actively breaks the one documented workflow (canvas get → save) that depends on it.

2. **`dashboard og-card` fails to parse its own 200 response.** `GET /dashboards/{id}/og-card` returns HTTP 200, but the CLI raises `JSONDecodeError` (`exception_type: JSONDecodeError`, `operation_state: not_started`) trying to treat the response as JSON. og-card almost certainly returns an image; the CLI has no non-JSON response path for it.

3. **`dashboard archive` reports failure on a mutation that actually committed.** `dashboard archive 54 --input '{"archived": true}' --yes --confirm 54` returned exit 7, `code: outcome_unknown`, HTTP 200, with the message "The request may have committed, but its outcome was not confirmed" and a hint to not replay it. Immediately checking `dashboard list` afterward showed `archived: true` on dashboard 54 — the mutation had in fact succeeded. The CLI told the operator to treat a successful, verifiable mutation as unconfirmed.

4. **Two documented `runnable_example`s do not run as printed.**
   - `dashboard query 52 --input '{"body": {"params": {"descriptor": {}}}}'` is the schema's own `agent_example`/`runnable_example`. It fails with HTTP 400 (`4GENR001`, pydantic `union_tag_not_found` on discriminator `kind`) — the empty `{}` descriptor the example uses can never satisfy the real discriminated union (`group`/`scalar`/`rate`/`detail`/`options`/`range`), and `schema get` exposes no hint of the discriminator or its allowed values.
   - `dashboard pdf export 52 --input '{"body": {"params": {"data": {}}}}'` is likewise the documented example; it fails with HTTP 400 telling you `data` must be a hydrated `DashboardData` map, which `{}` is not, and which the schema gives no way to construct.

5. **`dashboard data draft` / `dashboard data published` schemas omit the request envelope the backend actually requires.** The schema's `input_schema` and `runnable_example` both say the body is only `{"sql": "..."}` at the top level. The backend rejects this with HTTP 400 `4GENR007 VALIDATION_ERROR`, `"key": "params", "message": "Field required"` — i.e. it wants `{"params": {"sql": ...}}` like every other dashboard sub-command, but the schema for these two commands never says so.

6. **`dashboard update`'s own docstring ("Apply a JSON Patch") sets up the wrong mental model.** `patch[].path` must be one of a fixed bare-word enum (`intent`, `title`, `theme`, `pages`, `filters`), not an RFC 6902 JSON-pointer string. A natural first attempt (`"path": "/title"`, per real JSON Patch syntax) is rejected with `invalid_input_field_type`; the correct form is `"path": "title"`. Worth a docstring/example fix given the command is explicitly billed as JSON Patch.

7. **Generic, empty `ValidationError` envelopes with zero diagnostic content (3 occurrences).** `dashboard figure-intent 52 --input '{"body": {"params": {"intent": "..."}}}'` (an input that matches the documented schema exactly), `dashboard template get sales-performance` (a real template id taken from `dashboard template list`'s own catalog), and `dashboard style default get` (run exactly as its `runnable_example`) all fail identically: `exception_type: ValidationError`, no `status_code`, no `backend_code`, no `endpoint`, no `response_body`, no `hint` — only "The Mammoth operation failed unexpectedly." There is no way for an operator (human or agent) to tell what was wrong with any of these three calls from the error alone.

## Backend defects

1. **`dashboard.source.list` returns HTTP 500** on `GET /dashboards/sources` — already flagged in the command's own schema (`B04 SERVER_VARIANCE`), reproduced here on release, not a new finding but confirmed still live in 2.0.12/release.
2. **Misleading "Dashboard not found" for a bad job id, not a bad dashboard id.** `dashboard pdf-artifact 52 999999` (dashboard 52 exists and is accessible; job 999999 does not) returns HTTP 404 `4DASH001` with message "Dashboard not found or you don't have access to it." The actual missing resource is the pdf job, not the dashboard; the error message points at the wrong entity.
3. **`dashboard create` is fully retired (`4DASH012`) but still listed and schema'd as a live command** with a `returns_job` contract and a runnable example that will always 409. Not a bug in the sense of unexpected behavior — the message is clear — but the CLI surface (help text, schema catalog) gives no indication the command can never succeed on release.

## Baseline diff (hard rule 3)

- `dashboard list` (project 3): before = `{48}` only; after = `{48}` only. Identical.
- `dashboard tags list`, `dashboard signature list`, `dashboard context list`, `dashboard style custom list`: all empty before and after.
- `view list` for datasets 28, 29, 30, 31, 33: id/name sets identical before and after (auto_sync metadata churn on view 45 from the fixture dashboards is expected/cosmetic and not part of the id/name identity check; no views were added, removed, or renamed).
- All dashboards created during the run (52, 53, 54) were trashed then permanently deleted; all self-created tags (11, 12, 13), the one QA session (plus its fork), one signature, one context, and one custom style were explicitly deleted before the final snapshot.

**Net result: baseline fully restored. No pre-existing resource (dashboard 48, datasets 28/29/30/31/33, or their views) was mutated.**
