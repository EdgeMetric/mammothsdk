# `annotation` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `annotation.comment.add`

Run: `mammoth annotation comment add`. Exact input fields: `mammoth schema get annotation.comment.add --output json --no-input`.

Example: `mammoth annotation comment add 123 --input '{"body": "sample"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AnnotationCommentAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `annotation.create`

Run: `mammoth annotation create`. Exact input fields: `mammoth schema get annotation.create --output json --no-input`.

Example: `mammoth annotation create --input '{"target_type": "sample", "target_id": 1, "body": "sample"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AnnotationCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `annotation.delete`

Run: `mammoth annotation delete`. Exact input fields: `mammoth schema get annotation.delete --output json --no-input`.

Example: `mammoth annotation delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `AnnotationDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `annotation.list`

Run: `mammoth annotation list`. Exact input fields: `mammoth schema get annotation.list --output json --no-input`.

Example: `mammoth annotation list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AnnotationListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.10 — Bounded release read with published CLI 1.1.10 returned an empty annotation collection; target_type=project produced structured API error and target_id=0 produced deterministic invalid_input_field_type. No Full claim: no non-empty annotation fixture.

### `annotation.update`

Run: `mammoth annotation update`. Exact input fields: `mammoth schema get annotation.update --output json --no-input`.

Example: `mammoth annotation update 123 --input '{"status": "sample"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AnnotationUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
