# Dashboard re-verification — release, CLI 2.0.14

Ran all 33 command ids from `COMMANDS.txt` against a disposable dashboard (id 56, `dashboard create-blank` on view 45, project 3) using `/home/euler/mammoth/mammothsdk/mammoth-cli/.venv/bin/mammoth --profile release --output json --no-input --project 3`. Full per-command evidence is in `results.jsonl`.

## Verdict counts

| verdict | count |
|---|---|
| ok | 13 |
| ok_empty | 1 |
| blocked_missing_fixture | 12 |
| backend_error | 5 |
| cli_error | 1 |
| skipped_out_of_scope | 1 |

(3 of the blocked_missing_fixture entries — assess-pbix, assess-twb, import-workbook — were not run at all, per hard rules: no workbook fixture.)

## The 11 previously-broken (CLI defect fixed in 2.0.14 / SDK 0.7.6) — status

| Command | Fixed? | Evidence |
|---|---|---|
| `dashboard.archive` | **Fixed** | Non-object 200 body parsed cleanly: `{"archived":true,"dashboard_id":56,"response":null}` |
| `dashboard.canvas.save` | **Fixed** (round-trip mechanics) | get→save round-trip succeeded, sequence 1→2, no `***REDACTED***` in canvas. Caveat: this fixture's `style_tokens` was `null`, not a populated dict, so the specific style_tokens-redaction path is UNVERIFIED on this fixture. |
| `dashboard.data.draft` | **Fixed** (envelope) | CLI sent the WidgetDataSpec `widget_id` envelope correctly; backend replied with a clean structured 409 `DASHBOARD_WRONG_ENGINE`, not a client-side error. |
| `dashboard.data.published` | **Fixed** (envelope) | Same as above, on `getPublishData`. |
| `dashboard.figure-intent` | **Fixed** | Returned a full matched structured body instead of raising ValidationError. |
| `dashboard.query` | **Fixed** | `descriptor.kind=scalar` ran cleanly: `{"descriptor_id":"fe38c0b407dc107c","job_id":300}`. |
| `dashboard.style.default.get` | **Fixed** | Returned `{"styleId":"stone"}` instead of raising ValidationError. |
| `dashboard.style.derive` | **Fixed** | Returned a full real `styleTokens` object, no redaction. |
| `dashboard.template.get` | **Fixed** | Returned a full matched body instead of raising ValidationError (tested read-only against the curated `sales-performance` template since our own template.create failed — see below). |

(`dashboard.og-card` is on the 11-item list in capabilities.md but is not in this run's COMMANDS.txt, so it is out of scope here.)

## Non-ok commands (22 of 33)

- `dashboard.assess-pbix`, `dashboard.assess-twb`, `dashboard.import-workbook` — **blocked_missing_fixture**, not run (no workbook files, per hard rules).
- `dashboard.data.draft`, `dashboard.data.published`, `dashboard.widget-data`, `dashboard.widget-data-by-url`, `dashboard.published-data-by-url` — **blocked_missing_fixture**: all hit `4DASH004 DASHBOARD_WRONG_ENGINE` (409). Our fixture is a v3/create-blank dashboard with no widgets; these are legacy-engine-only endpoints, and legacy `dashboard.create` is retired on release, so no fixture can reach them. CLI-side envelope sending for the two `data.*` routes is confirmed correct (see fixed-list above).
- `dashboard.pdf-artifact`, `dashboard.published.pdf-artifact` — **blocked_missing_fixture**: no real PDF-export job obtainable; tried against our only real job id (313, a descriptor-data job) and got a clean `4DASH001 DASHBOARD_NOT_FOUND` (404).
- `dashboard.template.create` — **backend_error**: HTTP 500 `outcome_unknown` on `POST /dashboards/v3/templates`, both attempts (2/2), reconciled via `template list` both times — neither attempt committed.
- `dashboard.template.delete`, `dashboard.template.rename` — **blocked_missing_fixture**: no owned template exists (upstream `template.create` failure); mutating a curated/system template was not attempted.
- `dashboard.templates.use` — **skipped_out_of_scope**: BRIEF asked to run this on our own template, which was unobtainable; the route is high_impact/confirm_target/unverified-on-release and resembles the AI-generation family explicitly excluded from this pass.
- `dashboard.source.list` — **backend_error**: HTTP 500 on `GET /dashboards/sources`, matches previously documented B04 SERVER_VARIANCE; still broken.
- `dashboard.published.pdf.export`, `dashboard.published.video.export` — **backend_error**: both now fail with `4PERM002 PERMISSION_ERROR` (403) *before* the previously-documented 4GENR001 stage. Flag for a human: this is a different failure point than capabilities.md records — worth checking whether the `type_of_auth: public` share this test used grants enough scope, or whether a permission gate changed.
- `dashboard.video.export` — **backend_error**: the previously-documented "publish before export" block is cleared once the dashboard is actually published; new blocker is `4GENR001 INVALID_ARGUMENTS`, "video export needs a motion-story dashboard" (400) — a dashboard-format constraint, not a CLI defect.
- `dashboard.published.data` — **cli_error**: real defect found. The route dispatches a job and the CLI polls `GET /jobs/{id}` (authenticated), which returns `4PERM002 PERMISSION_ERROR` (400) and is reported as a command failure — but `dashboard.job-by-url` on the *same* job id shows it actually completed successfully (`status:"success"`, value 58824). The CLI appears to poll the wrong (authenticated) job-status endpoint for a published/public-auth dashboard's job instead of the URL-scoped route, misreporting success as failure. Reproduced twice (2/2 attempts, same result both times, different job ids 311/313).
- `dashboard.share` — **ok_empty**: `dashboard share` itself returns `{"data":null}`, no url/slug in the body; the slug had to be read back via `dashboard get`. Also noted: `dashboard.share` alone did not flip `was_published` to true — that required `dashboard action {"action":"publish-presentation"}` as well.

## IDs created and deleted

- Dashboard **56** — fixture, created via `dashboard create-blank` (view 45). Shared public, published via `dashboard action publish-presentation`, url slug `IuZl5tk5KcEHJWTy4tnhrA`. Share reverted to `type_of_auth: mammoth`, then `dashboard trash 56` + `dashboard delete 56` (both exit 0).
- Dashboard **57** — created unexpectedly as a side effect of `dashboard.template.apply` (source_dashboard_id=56, target_dataview_id=45). Trashed and permanently deleted immediately after inspection (`dashboard trash 57` + `dashboard delete 57`, both exit 0).
- No template was ever created (`dashboard.template.create` failed both attempts, reconciled as not-committed) and no other objects were left behind.

Dashboard 48 and datasets 28–33 were never touched; view 45 was only read (`dataview_id` reference for create-blank/template.apply).

## Final state checks (verified, not assumed)

- `dashboard list --project 3` → **`[{"id":48,...}]`** only. Confirmed clean.
- `dashboard tags list` → `{"tags":[]}`.
- `dashboard template list` → no template titled "Reverify template 2.0.14" present (consistent with `template.create` never having committed — checked twice, once after each failed attempt).

All claims above come from command output captured during this run (saved under `raw/` in this same directory). Anything not directly observed is called out explicitly as UNVERIFIED or flagged for human follow-up (the `style_tokens=null` caveat on canvas.save, and the two `4PERM002` permission-gate points on the published pdf/video export routes).
