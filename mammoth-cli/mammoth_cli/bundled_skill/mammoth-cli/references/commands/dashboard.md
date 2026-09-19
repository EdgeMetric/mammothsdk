# `dashboard` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.action`

Run: `mammoth dashboard action`. Exact input fields: `mammoth schema get dashboard.action`.

Example: `mammoth dashboard action 123 --input '{"action": "sync"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardActionResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned {"message":"Draft sync triggered for all sources."}. Contract says async:returns_job but no job_id was returned in the body -- only a human-readable message; not one of the 11 p…

### `dashboard.analytics`

Run: `mammoth dashboard analytics`. Exact input fields: `mammoth schema get dashboard.analytics`.

Example: `mammoth dashboard analytics 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardAnalyticsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: average_time_spent_seconds, current_concurrent_viewers, total_views, viewed_by. Single read only; no fixture variants, error envelopes, or write paths assessed. Also: Dashboard sweep…

### `dashboard.archive`

Run: `mammoth dashboard archive`. Exact input fields: `mammoth schema get dashboard.archive`.

Example: `mammoth dashboard archive 123 --input '{"archived": true}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardArchiveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: 2.0.14 cleanly parsed the backend's non-object 200 body and reported {"archived":true,"dashboard_id":56,"response":null} instead of crashing or misrepresenti…

### `dashboard.assess-pbix`

Run: `mammoth dashboard assess-pbix`. Exact input fields: `mammoth schema get dashboard.assess-pbix`.

Example: `mammoth dashboard assess-pbix sample.pbix`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `PbixAssessResponse`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.assess-twb`

Run: `mammoth dashboard assess-twb`. Exact input fields: `mammoth schema get dashboard.assess-twb`.

Example: `mammoth dashboard assess-twb sample.twb`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TwbAssessResponse`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.cancel-generation`

Run: `mammoth dashboard cancel-generation`. Exact input fields: `mammoth schema get dashboard.cancel-generation`.

Example: `mammoth dashboard cancel-generation 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardCancelGenerationResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: message. returned 'Cancel requested' even though no generation was in flight Single invocation only; no error-path or variant coverage.

### `dashboard.canvas.get`

Run: `mammoth dashboard canvas get`. Exact input fields: `mammoth schema get dashboard.canvas.get`.

Example: `mammoth dashboard canvas get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardCanvasGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Read back the authored canvas, plan.hints.kpis and meta.figures (figure key -> descriptor id) after each bake; used as the binding check the ILG brief requires. Single invocation only.

### `dashboard.canvas.restore`

Run: `mammoth dashboard canvas restore`. Exact input fields: `mammoth schema get dashboard.canvas.restore`.

Example: `mammoth dashboard canvas restore 123 --input '{"body": {"params": {"target_sequence": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardCanvasRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: bake_ok, canvas, history_index, sequence. restored to sequence 1, bake_ok=false, canvas returned Single invocation only; no error-path or variant coverage.

### `dashboard.canvas.save`

Run: `mammoth dashboard canvas save`. Exact input fields: `mammoth schema get dashboard.canvas.save`.

Example: `mammoth dashboard canvas save 123 --input '{"body": {"params": {"canvas": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardCanvasSaveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Authored a canvas from a blank one: page-level focus.kpis (sum with unit.prefix GBP, and a countDistinct card), added bar (measure+measure2), hbar, line on a derived ratio measure (canvas.derived),…

### `dashboard.chat.edit`

Run: `mammoth dashboard chat edit`. Exact input fields: `mammoth schema get dashboard.chat.edit`.

Example: `mammoth dashboard chat edit 123 --input '{"body": {"params": {"prompt": "Summarize revenue by region"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardChatEditResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: bake_ok, canvas, changed, layout_intent, message, options, sequence, version_before. AI chat edit applied display_title=Sweep Test; not AI-quota-gated Single invocation only; no error…

### `dashboard.chat.history`

Run: `mammoth dashboard chat history`. Exact input fields: `mammoth schema get dashboard.chat.history`.

Example: `mammoth dashboard chat history 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardChatHistoryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 chat-history read for retained dashboard48 returned empty history with sequence1; bounded and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: history_index, messages, sequence. no chat mess…

### `dashboard.context.create`

Run: `mammoth dashboard context create`. Exact input fields: `mammoth schema get dashboard.context.create`.

Example: `mammoth dashboard context create --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: context. created context id=1 Single invocation only; no error-path or variant coverage.

### `dashboard.context.delete`

Run: `mammoth dashboard context delete`. Exact input fields: `mammoth schema get dashboard.context.delete`.

Example: `mammoth dashboard context delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardContextDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted context 1 Single invocation only; no error-path or variant coverage.

### `dashboard.context.extract`

Run: `mammoth dashboard context extract`. Exact input fields: `mammoth schema get dashboard.context.extract`.

Example: `mammoth dashboard context extract --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ContextExtractResponse`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: condensed, figureHeavy, file, rejected, shape, skipped, suggestions. extracted suggestions from raw text Single invocation only; no error-path or variant coverage.

### `dashboard.context.list`

Run: `mammoth dashboard context list`. Exact input fields: `mammoth schema get dashboard.context.list`.

Example: `mammoth dashboard context list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty context list observed. No Full claim: no non-empty fixture. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: contexts. empty contexts list Single invoc…

### `dashboard.context.update`

Run: `mammoth dashboard context update`. Exact input fields: `mammoth schema get dashboard.context.update`.

Example: `mammoth dashboard context update resource-123 --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: context. renamed context 1 Single invocation only; no error-path or variant coverage.

### `dashboard.create`

Run: `mammoth dashboard create`. Exact input fields: `mammoth schema get dashboard.create`.

Example: `mammoth dashboard create 'Summarize revenue by region' --input '{"source": [1]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Do not run: not supported — backend returns HTTP 409 4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED (legacy dashboard creation retired). Use dashboard.create-blank or dashboard.v3.generate. Dashboard sweep 2026-09-18, CLI 2.0.12.

### `dashboard.create-blank`

Run: `mammoth dashboard create-blank`. Exact input fields: `mammoth schema get dashboard.create-blank`.

Example: `mammoth dashboard create-blank --input '{"params": {"dataview_id": 1}}' --yes`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardCreateBlankResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Two blank v3 dashboards bound to owned views (ids 63, 64). Single invocation only.

### `dashboard.data.draft`

Run: `mammoth dashboard data draft`. Exact input fields: `mammoth schema get dashboard.data.draft`.

Example: `mammoth dashboard data draft 123 --input '{"widget_id": "550e8400-e29b-41d4-a716-446655440000"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardDataDraftResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: Dashboard 56 (create-blank/v3 engine) has no widgets in its canvas and getDraftData rejects with backend_code 4DASH004 DASHBOARD_WRONG_ENGINE: "This dashbo. Re-check before relying on it.

### `dashboard.data.published`

Run: `mammoth dashboard data published`. Exact input fields: `mammoth schema get dashboard.data.published`.

Example: `mammoth dashboard data published 123 --input '{"widget_id": "550e8400-e29b-41d4-a716-446655440000"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardDataPublishedResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: Same as dashboard.data.draft: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/56/getPublishData. Re-check before relying on it.

### `dashboard.delete`

Run: `mammoth dashboard delete`. Exact input fields: `mammoth schema get dashboard.delete`.

Example: `mammoth dashboard delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Deleted dashboard 62. Single invocation only.

### `dashboard.descriptor-data`

Run: `mammoth dashboard descriptor-data`. Exact input fields: `mammoth schema get dashboard.descriptor-data`.

Example: `mammoth dashboard descriptor-data 123 --input '{"body": {"params": {"descriptor_ids": ["ef28f9bcc263c0f7"], "filter_state": {"Month": ["2025-01-01", "2025-03-31"]}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardDescriptorDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Evaluated baked descriptors by id with filter_state {Month: [start, end]}: countDistinct card = 111 unfiltered and 64 under a Q1 range (the fixture key; a summed per-cell count would read 83), sums…

### `dashboard.duplicate`

Run: `mammoth dashboard duplicate`. Exact input fields: `mammoth schema get dashboard.duplicate`.

Example: `mammoth dashboard duplicate 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardDuplicateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: id. duplicated D=52 -> D2=54 Single invocation only; no error-path or variant coverage.

### `dashboard.exemplar.extract`

Run: `mammoth dashboard exemplar extract`. Exact input fields: `mammoth schema get dashboard.exemplar.extract`.

Example: `mammoth dashboard exemplar extract --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ExemplarExtractResponse`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: brand, countable, measures, palette, rejected, scopes, source, spec. extracted measures/countable columns from dataview 45; rejected.reason=unreadable (no real doc content, expected f…

### `dashboard.figure-intent`

Run: `mammoth dashboard figure-intent`. Exact input fields: `mammoth schema get dashboard.figure-intent`.

Example: `mammoth dashboard figure-intent 123 --input '{"body": {"params": {"intent": "Summarize revenue by region"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardFigureIntentResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a full matched structured body ({"added":{...},"kind":"bar","spec":{...},"intentApplied":true,...}) instead of raising ValidationError on an unmatch…

### `dashboard.get`

Run: `mammoth dashboard get`. Exact input fields: `mammoth schema get dashboard.get`.

Example: `mammoth dashboard get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. auto_sync for the bound view showed last_synced_at after the upstream data change. Single invocation only.

### `dashboard.get-by-url`

Run: `mammoth dashboard get-by-url`. Exact input fields: `mammoth schema get dashboard.get-by-url`.

Example: `mammoth dashboard get-by-url https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardGetByUrlResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 exact observed URL slug resolved retained dashboard48; bounded single-dashboard read and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: auto_publish, auto_sync, id, is_publish_pending, is_…

### `dashboard.import-workbook`

Run: `mammoth dashboard import-workbook`. Exact input fields: `mammoth schema get dashboard.import-workbook`.

Example: `mammoth dashboard import-workbook sample.twbx --project 456 --yes --confirm 456`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ImportDatasetResponse`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.job-by-url`

Run: `mammoth dashboard job-by-url`. Exact input fields: `mammoth schema get dashboard.job-by-url`.

Example: `mammoth dashboard job-by-url https://example.com/data.csv 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardJobByUrlResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned real job state: {"job":{"id":313,"operation":"dispatch_descriptor_data","status":"success","response":{"completed":1,"expected":1,"results":{"fe38c0b407dc107c":{"status":"succes…

### `dashboard.list`

Run: `mammoth dashboard list`. Exact input fields: `mammoth schema get dashboard.list`.

Example: `mammoth dashboard list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded in project 3; empty dashboard list observed. No Full claim: no non-empty dashboard fixture or independent wire oracle. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: list[1]. 1 pre-existing das…

### `dashboard.og-card`

Run: `mammoth dashboard og-card`. Exact input fields: `mammoth schema get dashboard.og-card`.

Example: `mammoth dashboard og-card 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardOgCardResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: binary PNG body returned as described base64 content ({"data":{"content_base64":"iVBORw0KGgo..."}}) instead of crashing/misreporting. Dashboard 59 was our own dashboard.create-blank on v…

### `dashboard.page.plan`

Run: `mammoth dashboard page plan`. Exact input fields: `mammoth schema get dashboard.page.plan`.

Example: `mammoth dashboard page plan 123 --input '{"body": {"params": {"intent": "Summarize revenue by region"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPagePlanResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: composed, message, page, preview. returned a proposed executive_overview page plan Single invocation only; no error-path or variant coverage.

### `dashboard.pages.add`

Run: `mammoth dashboard pages add`. Exact input fields: `mammoth schema get dashboard.pages.add`.

Example: `mammoth dashboard pages add 123 --input '{"body": {"params": {"pages": [{"title": "By region", "focus": {"measure": "Revenue", "dim": "Region", "kpis": [{"field": "Revenue", "agg": "sum", "label": "Revenue"}]}, "charts": [{"kind": "hbar", "title": "Revenue by region", "dim": "Region", "measure": "Revenue", "agg": "sum"}]}]}}}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardPagesAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Needs --yes --confirm DASHBOARD_ID. body.params.pages[] takes PageAdd objects (title, focus{kpis}, charts[]); the route runs through the LLM guard and dropped unit.prefix on a money card ('nothing…

### `dashboard.pdf-artifact`

Run: `mammoth dashboard pdf-artifact`. Exact input fields: `mammoth schema get dashboard.pdf-artifact`.

Example: `mammoth dashboard pdf-artifact 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPdfArtifactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.pdf.export`

Run: `mammoth dashboard pdf export`. Exact input fields: `mammoth schema get dashboard.pdf.export`.

Example: `mammoth dashboard pdf export 123 --input '{"body": {"params": {"data": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Do not run: not supported — backend HTTP 400 4GENR001 requires params.data to be the browser-hydrated DashboardData map and states it cannot rebuild it from stored descriptors (dashboard sweep and Haiku e2e, 2026-09-18). The route works only with a client render pass.

### `dashboard.published-data-by-url`

Run: `mammoth dashboard published-data-by-url`. Exact input fields: `mammoth schema get dashboard.published-data-by-url`.

Example: `mammoth dashboard published-data-by-url https://example.com/data.csv --input '{"body": {"params": {"widget_id": "00000000-0000-4000-8000-000000000001"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedDataByUrlResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/getPublishData, same class of blocker as widget-data: this v3 dashbo. Re-check before relying on it.

### `dashboard.published.canvas`

Run: `mammoth dashboard published canvas`. Exact input fields: `mammoth schema get dashboard.published.canvas`.

Example: `mammoth dashboard published canvas https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedCanvasResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned the full published canvas object (dataset.dataview_id=45, pages, meta.figures={}, etc.) for our own published dashboard 56/url IuZl5tk5KcEHJWTy4tnhrA. Confirms publishing via da…

### `dashboard.published.data`

Run: `mammoth dashboard published data`. Exact input fields: `mammoth schema get dashboard.published.data`.

Example: `mammoth dashboard published data https://example.com/data.csv --input '{"body": {"params": {"descriptor_ids": ["resource-123"]}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: Could not publish dashboard 59 to reach a live published state: `dashboard action 59 {action:publish-presentation}` failed twice with HTTP 500 outcome_unkn. Re-check before relying on it.

### `dashboard.published.og-card`

Run: `mammoth dashboard published og-card`. Exact input fields: `mammoth schema get dashboard.published.og-card`.

Example: `mammoth dashboard published og-card https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedOgCardResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.published.pdf-artifact`

Run: `mammoth dashboard published pdf-artifact`. Exact input fields: `mammoth schema get dashboard.published.pdf-artifact`.

Example: `mammoth dashboard published pdf-artifact https://example.com/data.csv 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedPdfArtifactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: Same as dashboard.pdf-artifact: no real pdf job available; used job 313 (descriptor-data job) as the only real job id in hand and got backend_code 4DASH001. Re-check before relying on it.

### `dashboard.published.pdf.export`

Run: `mammoth dashboard published pdf export`. Exact input fields: `mammoth schema get dashboard.published.pdf.export`.

Example: `mammoth dashboard published pdf export https://example.com/data.csv --input '{"body": {"params": {"data": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedPdfExportResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: Got backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/pdf (403), envelope: {"err. Re-check before relying on it.

### `dashboard.published.share-page`

Run: `mammoth dashboard published share-page`. Exact input fields: `mammoth schema get dashboard.published.share-page`.

Example: `mammoth dashboard published share-page https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedSharePageResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned a real rendered HTML share page (text/html, 1319 bytes, sha256 given) with correct og:title/og:image/redirect script pointing at the dashboard's own url slug. Minor cosmetic bac…

### `dashboard.published.video-artifact`

Run: `mammoth dashboard published video-artifact`. Exact input fields: `mammoth schema get dashboard.published.video-artifact`.

Example: `mammoth dashboard published video-artifact https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedVideoArtifactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.published.video.export`

Run: `mammoth dashboard published video export`. Exact input fields: `mammoth schema get dashboard.published.video.export`.

Example: `mammoth dashboard published video export https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedVideoExportResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/video (403). Re-check before relying on it.

### `dashboard.qa.ask`

Run: `mammoth dashboard qa ask`. Exact input fields: `mammoth schema get dashboard.qa.ask`.

Example: `mammoth dashboard qa ask 123 123 --input '{"body": {"params": {"question": "Summarize revenue by region"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaAskResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: answer. AI answered with kpi block and narrative text; not quota-gated Single invocation only; no error-path or variant coverage.

### `dashboard.qa.comment.create`

Run: `mammoth dashboard qa comment create`. Exact input fields: `mammoth schema get dashboard.qa.comment.create`.

Example: `mammoth dashboard qa comment create 123 123 --input '{"body": {"params": {"body": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaCommentCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. created comment id=1 on session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.comment.delete`

Run: `mammoth dashboard qa comment delete`. Exact input fields: `mammoth schema get dashboard.qa.comment.delete`.

Example: `mammoth dashboard qa comment delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardQaCommentDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. deleted comment 1 from session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.feedback`

Run: `mammoth dashboard qa feedback`. Exact input fields: `mammoth schema get dashboard.qa.feedback`.

Example: `mammoth dashboard qa feedback 123 123 123 --input '{"body": {"params": {"rating": "up"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaFeedbackResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. recorded thumbs-up feedback on message id=2 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.create`

Run: `mammoth dashboard qa session create`. Exact input fields: `mammoth schema get dashboard.qa.session.create`.

Example: `mammoth dashboard qa session create 123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. created qa session id=1 on D=52 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.delete`

Run: `mammoth dashboard qa session delete`. Exact input fields: `mammoth schema get dashboard.qa.session.delete`.

Example: `mammoth dashboard qa session delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardQaSessionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted forked session 2 and original session 1, both ok:true Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.fork`

Run: `mammoth dashboard qa session fork`. Exact input fields: `mammoth schema get dashboard.qa.session.fork`.

Example: `mammoth dashboard qa session fork 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionForkResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. forked session 1 -> new session id=2 with copied messages Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.get`

Run: `mammoth dashboard qa session get`. Exact input fields: `mammoth schema get dashboard.qa.session.get`.

Example: `mammoth dashboard qa session get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. fetched session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.list`

Run: `mammoth dashboard qa session list`. Exact input fields: `mammoth schema get dashboard.qa.session.list`.

Example: `mammoth dashboard qa session list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 / SDK 0.7.1 Q&A session-list read succeeded for retained dashboard 48 with empty mine/shared lists. One dashboard only; not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: mine, shared. 1 own s…

### `dashboard.qa.session.rename`

Run: `mammoth dashboard qa session rename`. Exact input fields: `mammoth schema get dashboard.qa.session.rename`.

Example: `mammoth dashboard qa session rename 123 123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionRenameResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. renamed session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.set-visibility`

Run: `mammoth dashboard qa session set-visibility`. Exact input fields: `mammoth schema get dashboard.qa.session.set-visibility`.

Example: `mammoth dashboard qa session set-visibility 123 123 --input '{"body": {"params": {"visibility": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionSetVisibilityResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. set visibility=shared Single invocation only; no error-path or variant coverage.

### `dashboard.qa.settings.get`

Run: `mammoth dashboard qa settings get`. Exact input fields: `mammoth schema get dashboard.qa.settings.get`.

Example: `mammoth dashboard qa settings get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSettingsGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 / SDK 0.7.1 Q&A settings read succeeded for retained dashboard 48. One dashboard only; not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: allow_viewer_qa, can_manage, public_link. returned all…

### `dashboard.qa.settings.set`

Run: `mammoth dashboard qa settings set`. Exact input fields: `mammoth schema get dashboard.qa.settings.set`.

Example: `mammoth dashboard qa settings set 123 --input '{"body": {"params": {"allow_viewer_qa": true}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSettingsSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: allow_viewer_qa, can_manage, public_link. set allow_viewer_qa=true Single invocation only; no error-path or variant coverage.

### `dashboard.query`

Run: `mammoth dashboard query`. Exact input fields: `mammoth schema get dashboard.query`.

Example: `mammoth dashboard query 123 --input '{"body": {"params": {"descriptor": {"kind": "scalar", "agg": "count"}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQueryResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: descriptor with kind=scalar ran cleanly, returned {"descriptor_id":"fe38c0b407dc107c","job_id":300}. Single invocation only.

### `dashboard.restore`

Run: `mammoth dashboard restore`. Exact input fields: `mammoth schema get dashboard.restore`.

Example: `mammoth dashboard restore 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: n/a. returned {} (success) but D2=54 was archived, not trashed -- verified via dashboard list that archived state was unchanged afterward (still archived=True). 'restore' is a no-op o…

### `dashboard.rls.assignment.list`

Run: `mammoth dashboard rls assignment list`. Exact input fields: `mammoth schema get dashboard.rls.assignment.list`.

Example: `mammoth dashboard rls assignment list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardRlsAssignmentListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 RLS assignment read for retained dashboard48 returned disabled empty state; bounded and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: assignments, enabled, filter_column. RLS not enabled,…

### `dashboard.rls.assignment.set`

Run: `mammoth dashboard rls assignment set`. Exact input fields: `mammoth schema get dashboard.rls.assignment.set`.

Example: `mammoth dashboard rls assignment set 123 --input '{"body": {"params": {"assignments": [{"email": "analyst@example.com"}]}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardRlsAssignmentSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: message. set RLS assignment for own account restricted to Entity=India on D=52 Single invocation only; no error-path or variant coverage.

### `dashboard.rls.column.list`

Run: `mammoth dashboard rls column list`. Exact input fields: `mammoth schema get dashboard.rls.column.list`.

Example: `mammoth dashboard rls column list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardRlsColumnListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 RLS column read for retained dashboard48 returned 9 display columns; bounded and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: columns. returned 4 columns Single invocation only; no error…

### `dashboard.rls.value.list`

Run: `mammoth dashboard rls value list`. Exact input fields: `mammoth schema get dashboard.rls.value.list`.

Example: `mammoth dashboard rls value list 123 --input '{"column": "Status"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardRlsValueListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 RLS value read using observed display column Entity returned 205 values; bounded and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: column, total, values. returned 269 distinct Entity valu…

### `dashboard.share`

Run: `mammoth dashboard share`. Exact input fields: `mammoth schema get dashboard.share`.

Example: `mammoth dashboard share 123 --input '{"type_of_auth": "mammoth"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardShareResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned {"data":null}. The share call itself did not return a url/slug in its response body; had to fetch it separately via dashboard get (data.url="IuZl5tk5KcEHJWTy4tnhrA", data.share.…

### `dashboard.signature.create`

Run: `mammoth dashboard signature create`. Exact input fields: `mammoth schema get dashboard.signature.create`.

Example: `mammoth dashboard signature create --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardSignatureCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: signature. created signature id=1 Single invocation only; no error-path or variant coverage.

### `dashboard.signature.delete`

Run: `mammoth dashboard signature delete`. Exact input fields: `mammoth schema get dashboard.signature.delete`.

Example: `mammoth dashboard signature delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardSignatureDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted signature 1 Single invocation only; no error-path or variant coverage.

### `dashboard.signature.list`

Run: `mammoth dashboard signature list`. Exact input fields: `mammoth schema get dashboard.signature.list`.

Example: `mammoth dashboard signature list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardSignatureListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty signature list observed. No Full claim: no non-empty fixture. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: signatures. empty signatures list Single…

### `dashboard.signature.update`

Run: `mammoth dashboard signature update`. Exact input fields: `mammoth schema get dashboard.signature.update`.

Example: `mammoth dashboard signature update resource-123 --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardSignatureUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: signature. renamed signature 1 Single invocation only; no error-path or variant coverage.

### `dashboard.source.list`

Run: `mammoth dashboard source list`. Exact input fields: `mammoth schema get dashboard.source.list`.

Example: `mammoth dashboard source list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardSourceListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocker; still broken, not one of the 11 CLI-fixed commands. Re-check before relying on it.

### `dashboard.style.custom.create`

Run: `mammoth dashboard style custom create`. Exact input fields: `mammoth schema get dashboard.style.custom.create`.

Example: `mammoth dashboard style custom create --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: style. created custom style id=1 with full unredacted colors/font/viz (no tokens field passed) Single invocation only; no error-path or variant coverage.

### `dashboard.style.custom.delete`

Run: `mammoth dashboard style custom delete`. Exact input fields: `mammoth schema get dashboard.style.custom.delete`.

Example: `mammoth dashboard style custom delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardStyleCustomDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted custom style 1 Single invocation only; no error-path or variant coverage.

### `dashboard.style.custom.list`

Run: `mammoth dashboard style custom list`. Exact input fields: `mammoth schema get dashboard.style.custom.list`.

Example: `mammoth dashboard style custom list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty custom-style list observed. No Full claim: no non-empty fixture. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: styles. empty custom styles list Sing…

### `dashboard.style.custom.update`

Run: `mammoth dashboard style custom update`. Exact input fields: `mammoth schema get dashboard.style.custom.update`.

Example: `mammoth dashboard style custom update resource-123 --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: style. renamed custom style 1 Single invocation only; no error-path or variant coverage.

### `dashboard.style.default.get`

Run: `mammoth dashboard style default get`. Exact input fields: `mammoth schema get dashboard.style.default.get`.

Example: `mammoth dashboard style default get`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDefaultGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a real matched body {"styleId":"stone"} instead of raising ValidationError on an unmatched 2xx. Single invocation only.

### `dashboard.style.default.set`

Run: `mammoth dashboard style default set`. Exact input fields: `mammoth schema get dashboard.style.default.set`.

Example: `mammoth dashboard style default set --input '{"body": {"params": {"styleId": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDefaultSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Set styleId to the exact value read from style default get ("stone"), i.e. a verified no-op restore. Result {"styleId":"stone"}; re-ran style default get afterward and confirmed it still…

### `dashboard.style.derive`

Run: `mammoth dashboard style derive`. Exact input fields: `mammoth schema get dashboard.style.derive`.

Example: `mammoth dashboard style derive --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDeriveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a full real styleTokens object (colors, font, viz palette, radius, shadow, etc.) with no '***REDACTED***' placeholders anywhere in the body. Single…

### `dashboard.style.extract-brand`

Run: `mammoth dashboard style extract-brand`. Exact input fields: `mammoth schema get dashboard.style.extract-brand`.

Example: `mammoth dashboard style extract-brand --input '{"body": {"params": {"url": "https://example.com/data.csv"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleExtractBrandResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: screenshot, signals. captured screenshot + extracted brand signals (accents/font/ground/primary), no redaction here Single invocation only; no error-path or variant coverage.

### `dashboard.style.preset.list`

Run: `mammoth dashboard style preset list`. Exact input fields: `mammoth schema get dashboard.style.preset.list`.

Example: `mammoth dashboard style preset list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStylePresetListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; 10 stock presets returned. No Full claim: custom preset fixture not observed. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: presets. returns built-in styl…

### `dashboard.style.token.list`

Run: `mammoth dashboard style token list`. Exact input fields: `mammoth schema get dashboard.style.token.list`.

Example: `mammoth dashboard style token list resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleTokenListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 read of observed preset stone returned a redacted token payload. Bounded to one preset and redacted semantics; not Full. Dashboard sweep 2026-09-18 on release observed cli_error: HTTP 200 but result is tokens='***REDACTED…

### `dashboard.suggestion.list`

Run: `mammoth dashboard suggestion list`. Exact input fields: `mammoth schema get dashboard.suggestion.list`.

Example: `mammoth dashboard suggestion list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardSuggestionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 job-backed suggestion read for retained dataview46 reconciled job158 to terminal success with 9 structured suggestions; bounded to one job and not Full. A permitted reread spawned pending job159 with null payload. Also: Dashboard swe…

### `dashboard.swap-data`

Run: `mammoth dashboard swap-data`. Exact input fields: `mammoth schema get dashboard.swap-data`.

Example: `mammoth dashboard swap-data 123 --input '{"body": {"params": {"dataview_id": 1}}}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ObjectJobSchema`; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: bake_ok, fidelity, id, sequence. swapped D=52 from dataview 45 (population) to dataview 46 (GDP), both Terra OWID reference views with similar schema; fidelity: 1 mapped, 1 dropped, n…

### `dashboard.tags.delete`

Run: `mammoth dashboard tags delete`. Exact input fields: `mammoth schema get dashboard.tags.delete`.

Example: `mammoth dashboard tags delete 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardTagsDeleteResult`; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: n/a. deleted self-created tag 12 (entity) Single invocation only; no error-path or variant coverage. Current checkout binding is committed structural mapping; release behavior remains…

### `dashboard.tags.list`

Run: `mammoth dashboard tags list`. Exact input fields: `mammoth schema get dashboard.tags.list`.

Example: `mammoth dashboard tags list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTagsListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty tag list observed. No Full claim: no non-empty fixture. Current checkout binding is committed structural mapping; release behavior remains unverified. Current checkout binding is commi…

### `dashboard.tags.merge`

Run: `mammoth dashboard tags merge`. Exact input fields: `mammoth schema get dashboard.tags.merge`.

Example: `mammoth dashboard tags merge 123 --input '{"target_id": 456}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardTagsMergeResult`; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: id, merged_into, name. merged self-created tag 13 into self-created tag 11 (population); no pre-existing tag touched Single invocation only; no error-path or variant coverage. Current…

### `dashboard.tags.rename`

Run: `mammoth dashboard tags rename`. Exact input fields: `mammoth schema get dashboard.tags.rename`.

Example: `mammoth dashboard tags rename 123 --input '{"name": "Revenue"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardTagsRenameResult`; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: id, merged_into, name. renamed tag 13 (created by this run's dashboard.tags.set) successfully Single invocation only; no error-path or variant coverage. Current checkout binding is co…

### `dashboard.tags.set`

Run: `mammoth dashboard tags set`. Exact input fields: `mammoth schema get dashboard.tags.set`.

Example: `mammoth dashboard tags set 123 --input '{"tags": ["Revenue"]}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardTagsSetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: tags. set tag sweep-tag-alpha on D=52 Single invocation only; no error-path or variant coverage. Current checkout binding is committed structural mapping; release behavior remains unv…

### `dashboard.template.apply`

Run: `mammoth dashboard template apply`. Exact input fields: `mammoth schema get dashboard.template.apply`.

Example: `mammoth dashboard template apply --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateApplyResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Succeeded and created a NEW dashboard (id 57, derived_from 56, url U6WuS1Z2haJj8h96JkcFxw) mapped onto view 45 with fidelity {"blocked":false,"dropped":0,"unmatched_required":[]}. This i…

### `dashboard.template.create`

Run: `mammoth dashboard template create`. Exact input fields: `mammoth schema get dashboard.template.create`.

Example: `mammoth dashboard template create --input '{"body": {"params": {"dashboard_id": 1, "title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: POST /dashboards/v3/templates HTTP 500 empty body / outcome_unknown, as on 2026-09-18. Re-check before relying on it.

### `dashboard.template.delete`

Run: `mammoth dashboard template delete`. Exact input fields: `mammoth schema get dashboard.template.delete`.

Example: `mammoth dashboard template delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardTemplateDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: dashboard.template.create never produced an owned template (HTTP 500 both attempts, reconciled as not-committed via template list). Re-check before relying on it.

### `dashboard.template.fit`

Run: `mammoth dashboard template fit`. Exact input fields: `mammoth schema get dashboard.template.fit`.

Example: `mammoth dashboard template fit 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateFitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: dataview_id, fits. Single read only; no fixture variants, error envelopes, or write paths assessed. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: d…

### `dashboard.template.get`

Run: `mammoth dashboard template get`. Exact input fields: `mammoth schema get dashboard.template.get`.

Example: `mammoth dashboard template get resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a full matched structured body ({"explore":{...},"self_fit":{"grade":"great",...},"source_dashboard_id":1,"template":{...}}) instead of raising Vali…

### `dashboard.template.list`

Run: `mammoth dashboard template list`. Exact input fields: `mammoth schema get dashboard.template.list`.

Example: `mammoth dashboard template list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Returned the template catalogue (formats, functions, ...). Single invocation only.

### `dashboard.template.preview`

Run: `mammoth dashboard template preview`. Exact input fields: `mammoth schema get dashboard.template.preview`.

Example: `mammoth dashboard template preview --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplatePreviewResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: canvas, fidelity, mapping, meta, plan, specs, target_fields. previewed D=52's canvas retargeted to dataview 47 (life expectancy dataset) Single invocation only; no error-path or varia…

### `dashboard.template.rename`

Run: `mammoth dashboard template rename`. Exact input fields: `mammoth schema get dashboard.template.rename`.

Example: `mammoth dashboard template rename resource-123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateRenameResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.template.resolve-mapping`

Run: `mammoth dashboard template resolve-mapping`. Exact input fields: `mammoth schema get dashboard.template.resolve-mapping`.

Example: `mammoth dashboard template resolve-mapping --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateResolveMappingResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: fidelity, mapping, target_fields. resolved mapping from D=52's current dataview (46, GDP after swap-data) to target dataview 47 (life expectancy) Single invocation only; no error-path…

### `dashboard.templates.pending`

Run: `mammoth dashboard templates pending`. Exact input fields: `mammoth schema get dashboard.templates.pending`.

Example: `mammoth dashboard templates pending`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `PendingTemplateResponse`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: slug. slug null -- no pending template session for this project Single invocation only; no error-path or variant coverage.

### `dashboard.templates.use`

Run: `mammoth dashboard templates use`. Exact input fields: `mammoth schema get dashboard.templates.use`.

Example: `mammoth dashboard templates use sample --input '{"body": {"params": {"project_id": 1}}}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ObjectJobSchema | JobResponse`; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`.

Status on release: observed blocker — skipped_out_of_scope: BRIEF instructs running templates.use "on that template" (i.e. Re-check before relying on it.

### `dashboard.trash`

Run: `mammoth dashboard trash`. Exact input fields: `mammoth schema get dashboard.trash`.

Example: `mammoth dashboard trash 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: n/a. trashed D2=54; confirmed via dashboard list -- 54 no longer appears in the active list Single invocation only; no error-path or variant coverage. Also exercised successfully in t…

### `dashboard.update`

Run: `mammoth dashboard update`. Exact input fields: `mammoth schema get dashboard.update`.

Example: `mammoth dashboard update 123 --input '{"patch": [{"op": "replace", "path": "title", "value": "Renamed dashboard"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: message. renamed D=52 successfully. NOTE: first attempt using RFC6902-style path '/title' failed with invalid_input_field_type; correct path is bare enum word 'title' (enum: intent,ti…

### `dashboard.v3.generate`

Run: `mammoth dashboard v3 generate`. Exact input fields: `mammoth schema get dashboard.v3.generate`.

Example: `mammoth dashboard v3 generate --input '{"body": {"params": {"intent": "Summarize revenue by region", "dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardV3GenerateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: bake_ok, canvas, data_job_id, id, message, sequence, tags, title, url. created dashboard id=53 via AI generation; not quota-gated; bake_ok=true Single invocation only; no error-path o…

### `dashboard.video-state`

Run: `mammoth dashboard video-state`. Exact input fields: `mammoth schema get dashboard.video-state`.

Example: `mammoth dashboard video-state 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardVideoStateResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 video-state read for retained dashboard48 returned status none and stale false; bounded and not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: stale, status. status none, stale false Single in…

### `dashboard.video.export`

Run: `mammoth dashboard video export`. Exact input fields: `mammoth schema get dashboard.video.export`.

Example: `mammoth dashboard video export 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardVideoExportResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: After publishing dashboard 56 (dashboard.share public + dashboard.action publish-presentation), the previously-documented "publish the dashboard before exporting a v. Re-check before relying on it.

### `dashboard.widget-data`

Run: `mammoth dashboard widget-data`. Exact input fields: `mammoth schema get dashboard.widget-data`.

Example: `mammoth dashboard widget-data 123 --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardWidgetDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, "This dashboard uses a different rendering engine -- use the matching endpoints", on POST /dashboards/56/widg. Re-check before relying on it.

### `dashboard.widget-data-by-url`

Run: `mammoth dashboard widget-data-by-url`. Exact input fields: `mammoth schema get dashboard.widget-data-by-url`.

Example: `mammoth dashboard widget-data-by-url https://example.com/data.csv --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardWidgetDataByUrlResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: Same backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/widgets/data. Re-check before relying on it.
