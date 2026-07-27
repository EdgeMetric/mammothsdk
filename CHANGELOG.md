# Changelog

All notable changes to `mammoth-io` are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.2]

### Fixed
- **`views.get()` no longer fails in restricted workspaces.** Some workspaces
  permit the dataset-scoped dataview listing the web app uses but deny the
  single-dataview metadata endpoint, so `client.views.get(view_id)` (and
  `get_view`) raised a 403 even though the caller could see the view. It now
  falls back to the listing, whose record carries the state pipeline operations
  need. Every other API failure still propagates, and the original 403 is
  preserved when the view is genuinely absent from the permitted listing.

## [0.5.1]

### Fixed
- **`mammoth.__version__` now reports the correct version.** It was pinned at
  `"0.4.0"` while `pyproject.toml` had moved to `0.5.0`, so the published 0.5.0
  wheel reported the wrong version at runtime. Both places are now `0.5.1` and
  kept in sync.

## [0.5.0]

### Added
- **DSL engine — pure builders.** COMBINE literal string-prefix support, a
  `limit` param on `build_window_params`, `DateComponent.YEAR_MONTH_NUMBER`
  (produces TEXT output in EXTRACT_DATE), and `FILTER_TYPE=SHOW` on SET value
  conditions. Export/dashboard builders now use `ExportTargetKey` /
  `DashboardSpecKey` constants instead of hardcoded wire keys.

## [0.4.0]

### Added
- **`mammoth._pure` — pure parameter builders.** A new side-effect-free layer
  (`mammoth/_pure/builders.py`, `mammoth/_pure/resolve.py`) that turns the typed
  transformation specs into backend task payloads with no HTTP/View dependency.
  Each `build_<op>_params` takes the typed specs (`ConversionSpec`, `CopySpec`,
  `SetValue`, …) plus a column map, so the payload-building logic is testable in
  isolation and reusable by agents. 100% line+branch test coverage.
- **`ViewHost` protocol** (`mammoth/_mixins/_host.py`) — a typing-only Protocol
  describing the `View` surface the ops mixins rely on, giving the mixins full
  static-type resolution (0 pyright errors, mypy `strict` clean) with no runtime
  effect.
- **CSV-upload integration test** (`tests/integration/test_csv_upload_e2e.py`)
  exercising the full lifecycle: upload → transform → verify transformed output
  → delete.

### Fixed
- **`convert_type(..., format=...)` now produces a valid payload.** `FORMAT` is
  emitted as `{"date_format": <fmt>}` (a dict) instead of a bare string, which
  the backend CONVERT validator requires.
- **`unnest()` and `json_extract()` no longer fail backend validation.** The
  UNNEST `LABEL`/`VALUE` output columns and each `json_extract` extraction item
  now carry an `INTERNAL_NAME` (previously omitted, causing a backend KeyError).
- **Filling empty cells with a literal no longer silently drops the value.**
  `build_fill_value_params` emits a VERSION-2 `SET` task with an `IS_EMPTY`
  condition on the target column (the FILL task ignores literal `WITH` values).

### Changed
- **Transformation mixins now delegate to `mammoth._pure`.** The eight
  `_mixins/*.py` modules build their payloads via the pure builders instead of
  inline dicts — one source of truth, no behavioral change to public method
  signatures.
- **Dependencies modernized and pinned (`==`).** `pydantic==2.12.5` (matches the
  Mammoth backend), and all runtime/dev dependencies upgraded to current releases
  with `pip-audit` reporting no known vulnerabilities. Python 3.14 is now
  supported for development; the published package continues to support 3.10+.
