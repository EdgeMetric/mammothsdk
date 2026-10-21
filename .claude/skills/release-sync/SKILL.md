---
name: release-sync
description: Check that every release surface of mammoth-io (SDK), mammoth-cli and mammoth-mcp-server matches main, then fix what lags — PyPI, tags, GitHub releases, CHANGELOG, uv.lock, MCP registry, the mm-ai-docs skill/contract and docs.mammoth.io, the mm-website changelog — and verify it all again. Use for "is everything released?", "are sdk/cli/mcp published?", "release sync", "do the releases", "update the registry", or after merging a version bump.
---

# release-sync

One loop: **check → fix the failing rows → check again**, until the table is green or only
rows the user chose to leave remain.

## 1. Check

```bash
git switch main && git pull --ff-only
python3 scripts/release_status.py          # --json for rows as data; exit 1 if a row fails
```

Read-only (git, gh, PyPI, the MCP registry, the live sites). Each failing row prints its fix.
Report the table to the user in short form: what is behind, and what you will do about it.

## 2. Fix

Work in this order: later rows depend on earlier ones. **Ask before every step marked ⚠**
(irreversible or public), unless the user already said to do the releases in this conversation.

| Row | Fix |
|---|---|
| version files agree | Fix on a branch, PR. Not a release step: stop and tell the user. |
| ⚠ on PyPI (mammoth-io) | Tag `sdk-vX` on the release commit and push (CI publishes), or the local path in `RELEASING.md`. The SDK goes before the CLI. |
| ⚠ on PyPI (mammoth-cli) | Same with `cli-vX`, after mammoth-io resolves on PyPI. |
| ⚠ on PyPI (mammoth-mcp-server) | No CI workflow. Run its tests (`cd mammoth-mcp-server && uv run --with-editable . --with pytest --with pytest-asyncio --with ../ python -m pytest tests -q`), then `SOURCE_DATE_EPOCH=1700000000 uv build --out-dir <scratch>`, `uvx twine check`, `uvx twine upload -r pypi --non-interactive <scratch>/*`. |
| tag missing | `git tag -a <prefix>X -m "<package> X" <release commit> && git push origin <prefix>X`. Prefixes: `sdk-v`, `cli-v`, `mcp-server-v`. |
| GitHub release missing | Use the **PyPI files**, not a rebuild: download the wheel and sdist from `https://pypi.org/pypi/<pkg>/<ver>/json`. CLI: add `mammoth-install.sh`/`.ps1` from the tag (`git show cli-vX:mammoth-cli/installers/…`) and `SHA256SUMS`, `gh release create cli-vX --verify-tag --latest`. SDK and MCP server: `--latest=false`, wheel + sdist (+ `SHA256SUMS`). |
| GitHub Latest release | `gh release edit cli-vX --latest` |
| installer URL | Add the installers and `SHA256SUMS` to the CLI release. |
| uv.lock pins | `cd mammoth-cli && poetry lock && uv lock`, commit both on a branch, PR. |
| CHANGELOG release heading | On a branch: move every entry under `## [Unreleased]` to a new `## mammoth-io X, mammoth-cli Y, mammoth-mcp-server Z (YYYY-MM-DD)` heading right below it (each `###` names its version), leave `## [Unreleased]` empty, PR. |
| ⚠ MCP registry | Check the "live server card" row first: publish only a version that is deployed. `cd mammoth-mcp-server`, log in with the DNS key (`~/.config/mammoth/mcp-registry-key.pem`, recipe in mm-ai-docs `deploy/README.md`, step 5), `mcp-publisher validate`, `mcp-publisher publish`. A version publishes once. |
| MCP server deployed | Deploy is outside this skill (`mammoth-mcp-server/deploy`). Tell the user. |
| mm-ai-docs main skill version | The row names the `auto/cli-contract-<ver>` PR when it exists. Verify it before merging: in a worktree of the PR, install the published CLI in a fresh venv and run `MAMMOTH_CLI=<venv>/bin/mammoth npm run -s docs:capabilities:check` and `<venv>/bin/python ai_backend/scripts/sync_skill.py --from-package --check`. A digest-only drift of `mammoth-cli.tar.gz` with identical extracted contents is gzip bytes, not content. No PR: run the "Regenerate CLI contract" workflow in mm-ai-docs. ⚠ Merge. |
| docs.mammoth.io skill version | Deploy is the user's (mm-ai-docs `deploy/README.md`). Ask them, then re-check. |
| mm-website changelog (warn) | Entries go in `content/changelog/data.json` on a branch off `release`, PR to `release`, then `release` → `main`. Write user-facing lines like the existing `SDK & CLI` entries; no version numbers. Draft them and show the user before opening the PR. |

### PRs and merging
- Branch first, never commit on `main`. End PR bodies with the attribution line from the session.
- These repos require a review and run no CI on docs. ⚠ Merge with `gh pr merge --merge --admin`
  only when the user said to merge; otherwise leave the PR open and list it.

## 3. Verify

Run `python3 scripts/release_status.py` again. It must pass every row you fixed. Also confirm what the table cannot:
- a fresh `pip install --no-cache-dir <pkg>==<ver>` works (the index can lag the upload by minutes);
- for a docs deploy: `/build/cli/<family>` and `/build/contract` say "generated from mammoth-cli <ver>".

## Report

One table: each package's version, and PyPI, tag, GitHub release, changelog, registry and docs
as ✅/❌. Then one line per action taken (with links), then what is left and who owns it
(deploys, the website changelog, anything the user declined). Don't claim a row passes
unless the re-check printed PASS for it.
