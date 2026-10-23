# `recipe` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `recipe.list`

Run: `mammoth recipe list`. Exact input fields: `mammoth schema get recipe.list`.

Example: `mammoth recipe list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `RecipeListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `recipe.run`

Run: `mammoth recipe run`. Exact input fields: `mammoth schema get recipe.run`.

Example: `mammoth recipe run export-csv --input '{"inputs": {"view_id": 1}}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `RecipeRunResult`; mutation `high_impact`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.
