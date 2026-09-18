# CLI release provenance

## 2.0.14 / SDK 0.7.6

This release closes the CLI-side defects the 2026-09-18 dashboard sweep and
the Haiku end-to-end run found on release (evidence under
`docs/capability-evidence/dashboard-sweep-20260918` and
`docs/capability-evidence/haiku-e2e-20260918`):

- Output redaction erased every key containing `token`, so `dashboard canvas
  get` returned `style_tokens: "***REDACTED***"` (breaking the documented
  canvas get → save round-trip with HTTP 400), and `dashboard style derive` /
  `dashboard style token list` returned nothing usable. Plural design-token
  keys (`tokens`, `style_tokens`, `styleTokens`) are data now; singular
  credential tokens (`token`, `access_token`, `accessToken`, `refresh_tokens`)
  stay redacted.
- `dashboard archive` reported `outcome_unknown` (exit 7) on an HTTP 200 whose
  body is a non-object JSON value, although the archive had committed. SDK
  0.7.6 accepts any 2xx JSON body on that undeclared-schema route (and on
  `share`); the CLI returns `{dashboard_id, archived, response}`.
- `dashboard data draft` / `dashboard data published` sent `{"sql": ...}`;
  the route takes a `WidgetDataSpec` (`{"params": {"widget_id", ...}}`) and
  answered HTTP 400 `params: Field required`. SDK 0.7.6 takes `widget_id`
  plus optional `global_filters` / `drilldown_filters`; the CLI input schema
  and example follow.
- `dashboard figure-intent`, `dashboard template get` and `dashboard style
  default get` failed with an empty `ValidationError` envelope because the
  live response no longer matched the generated snapshot model. Generated
  wrappers now return an unmatched 2xx body unchanged, and any remaining
  pydantic failure names the model and the failing fields.
- Examples that could not run as printed: `dashboard query` (descriptor needs
  a `kind`; the example is now `{"kind":"scalar","agg":"count"}`) and
  `dashboard update` (`path` is a bare field name, not a JSON pointer; the
  example is now a title rename and the SDK docstring says so).
- Skill recipes: fill a blank with a literal via `set-values` + `IS_EMPTY`
  (`fill-missing` only propagates neighbours); `filter_type: "REMOVE"` to drop
  rows; `file upload` takes a positional path; `dataset delete` is
  asynchronous; canvas get → save round-trip; `dashboard pdf export` /
  `video export` need a browser-hydrated payload the CLI cannot build.

Not fixed here because they are backend behaviour, recorded in the matrix:
`dashboard source list` HTTP 500; `dashboard create` retired (HTTP 409
`4DASH012`, marked Not supported; use `create-blank` / `v3 generate`);
`dashboard pdf-artifact` reports "Dashboard not found" for a missing job id;
`dashboard pdf export` requires client-hydrated data (Not supported from the
CLI). The CLI requires `mammoth-io>=0.7.6,<0.8`, adds no API bindings, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.14`
(source commit `SOURCE_COMMIT`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.14-py3-none-any.whl` sha256 `WHEEL_SHA`
- `mammoth_cli-2.0.14.tar.gz` sha256 `SDIST_SHA`

SDK 0.7.6 (`sdk-v0.7.6`): `mammoth_io-0.7.6-py3-none-any.whl` sha256
`SDK_WHEEL_SHA`; `mammoth_io-0.7.6.tar.gz` sha256 `SDK_SDIST_SHA`.

## 2.0.13 / SDK 0.7.5

This release closes the CLI-side defects the 2026-09-18 read-only sweep
found, each re-verified live on release before the fix and after it:

- `project resource-dependencies 3` failed with "No such command '3'": the
  path is also a group (`... update`), and Click resolved the positional as a
  subcommand name. Leaf groups now keep bare tokens as positionals and still
  parse the options that follow them; the subcommand is unaffected. The
  example carries integer `resource_ids`, which the backend requires.
- `view pipeline items-all VIEW_ID DATASET_ID`: the advertised trailing
  parent positional was ignored; it is honoured now and a conflicting
  `dataset_id` input field is rejected.
- `template list` and `connector ai session list` raised `api_error` on an
  HTTP 200 because those routes return a bare JSON array (SDK 0.7.5 wraps it).
- `dashboard og-card` and the other artifact reads raised `JSONDecodeError` on
  a 200 PNG/PDF/MP4/HTML body (SDK 0.7.5 returns a described body with
  `content_type`, `size_bytes`, `sha256`, and `text` or `content_base64`).

Not fixed here because they are backend behaviour, recorded in the matrix:
`browse folder 0` returns 400 although `folder root` reports id 0 and
`browse project` returns 500, so the project root cannot be browsed;
`schedule list` 400 "Not implemented"; `workspace user get` 405;
`connector get bigquery` rejects a key `connector list` returned;
`dashboard rls value list` and `dashboard data draft` reject inputs the
schema admits. The CLI requires `mammoth-io>=0.7.5,<0.8`, adds no API
bindings, and makes no capability-status or autonomous-workflow
qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.13`
(source commit `4600720`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `2818c1dbc767205531e5c82ab24abdbb0a4df8f9e81437db6201433f7b4a1219` |
| Source distribution | `cc37db4906529c890c89346c3197d5bfc5a0fd3a0beeb2f9660ce903aa831800` |

Before upload, the full non-live suite at the release source recorded
3,881 passed plus the 6 tests touched afterwards re-run green (3,887 total),
2 skipped, 7 deselected; SDK unit suite 1,824 passed; Ruff, mypy, and
`twine check` passed.

## 2.0.12 / SDK 0.7.4

This release exists to pick up mammoth-io 0.7.4, which fixes `dataset
rename`: the SDK sent a `rename_dataset` operation on the plural datasets
route that the server rejected with HTTP 400 for every caller, including the
documented CLI example. The SDK now sends the OpenAPI `DatasetPatchOperation`
(`replace`/`name`) to `PATCH /datasets/{dataset_id}`; the fix was verified live
on the release environment by creating, renaming, reading back, and deleting a
throwaway dataset. The CLI requires `mammoth-io>=0.7.4,<0.8`.

The bundled skill gains a `need_action` recipe: an uploaded CSV with
ambiguous dates stops in `status: need_action` with no views, and an agent
without guidance handed that to the operator's UI. The recipe shows the
CLI path observed live on release: `dataset file-settings get` (reports
`has_ambiguous_dates`), then `dataset file-settings update` echoing the
detected settings plus `date_format`, then polling `dataset get` until
`ready`.

The exact-parent rule now covers every non-read view command. In 2.0.8 it
was applied to the `view.py` family only; `view transform *` and `view draft
*` still fell back to the SDK's project-wide parent discovery when
`dataset_id` was omitted. On a large production project that discovery
browsed a folder that returned HTTP 500 (surfaced from a join) and, when it
did not find the view, raised a bare `ValueError` that the CLI flattened into
`api_error: The Mammoth operation failed unexpectedly` (surfaced from filter
and math with valid inputs). These commands now fail closed with
`missing_argument` and the `view get` read that supplies the parent; the
`dataset_id` input field is admitted for `view draft *` as it already was for
transforms; every generated transform/draft example carries `dataset_id`;
a join or lookup whose foreign view is given without `foreign_dataset_id` /
`lookup_dataset_id` is refused the same way instead of discovering it; and a
discovery miss on a read maps to `resource_not_found` with the reason and
recovery reads instead of the opaque failure. Verified live on release:
a transform without the parent is refused before any request, and with
`dataset_id` in `--input` it submits.

Two read-only local commands are new: `dataset find NAME_SUBSTRING` and
`folder find NAME_SUBSTRING` search every project the credential can see
(or only `--project`) by case-insensitive name substring and return
`project_id`, `project_name`, `id`, `name` per match plus
`projects_searched` and `projects_truncated` (the projects endpoint returns at
most 100). Both were exercised live on release. The bundled skill also states
the dataset-to-view hop (`view list DATASET_ID`), that no dataset-level
union/append transform exists (append is `file upload` with
`append_to_ds_id`), that `schema find` is local while `dataset list` is
per-project, and the three response shapes agents most often misread. The
release adds no API bindings and makes no capability-status or
autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.12`
(source commit `a4175d5`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b42434869c55593c44d45d1f3c01bea2628fe4ee3e837a13f193f12884f073c7` |
| Source distribution | `206fcd4881abe2e5438d2be3011382671b0df204341fd15ba8c9ff42443fe7d1` |

Before upload, the full non-live suite at the release source recorded
3,884 passed, 2 skipped, 7 deselected; Ruff, mypy, and `twine check` passed.
The read-only capability sweep evidence (`docs/capability-evidence/read-sweep-20260918`)
and matrix update were committed after this tag and ship with the next release.

## 2.0.11 / SDK 0.7.3

This CLI-only diagnostics addition makes `doctor` answer "where can this
credential work", not only "does it authenticate". After the connection
check it reports a `projects` check listing the projects visible in the
workspace (id and name, first 20) and a `project_context` check stating
whether `--project` or the selected project is among them; a selected
project outside that list fails the run and recommends `project list`. No
selected project is reported but is not a failure, because every command
accepts `--project`. The API exposes no role or permission data, so the
check states that write access is not verifiable and is proven by the
first write. It retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.11`
(source commit `ac1806a`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `577f86b333981d72e7c19fa2e349a84e35ae0dde10c069ba709b369bdced7165` |
| Source distribution | `68249f9dcefcdd7e401e17b3a65dc959d8b2680792b706f2907ddf8ff958f8be` |

Before upload, the full non-live suite at the release source recorded
3,861 passed, 2 skipped, 7 deselected; Ruff, mypy, and `twine check` passed.

## 2.0.10 / SDK 0.7.3

This CLI-only interactive-login correction responds to a field report that
the hidden prompts gave no feedback and a rejected pair gave no clue what
had been sent. Each hidden entry now strips surrounding whitespace (a pasted
newline no longer becomes part of the secret), rejects an empty entry before
any request, and prints a masked receipt to stderr (length and last four
characters, never the value). A rejected login now reports the endpoint base
URL, the workspace id, and a credential receipt in `details`, and its hint
states that credentials are per environment. Values are never echoed; the
output redactor still masks any credential-shaped field. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.10`
(source commit `052445a`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `a1c9faeee9e6ea4cd6ab097b0c220c5c49053633e3319800f0a6b4ec3be64fdf` |
| Source distribution | `ac52c6a8a11a9916d5cd60c0471fee7f4ced2759900b28c31202f8cc16a21812` |

Before upload, the full non-live suite at the release source recorded
3,860 passed, 2 skipped, 7 deselected; Ruff, mypy, `twine check`, and the
generated-doc check passed.

## 2.0.9 / SDK 0.7.3

The full non-live suite for the 2.0.9 source later completed with
3,857 passed, 2 skipped, 7 deselected.

This CLI-only login-persistence and onboarding correction responds to a
reproduced field report: after a successful `auth login`, `doctor` reported
`credentials present` but `no profile`, because the profile record and the
selection pointer were persisted in separate writes and the record was lost.
`auth login` now writes the profile record and the selection pointer in one
atomic write, before the secret is stored, and reads the record back; if it
is not readable the command fails with `profile_write_failed` instead of
reporting success. `set_selected` refuses a profile that has no record
(`profile_not_found`). The bundled skill and agent guide now give the
minimal production login (`mammoth auth login`; `--server-prefix release`
only for release) and state that credentials are per environment. It
retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.9`
(source commit `6548a67`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b944024049a4e47207a748093fdb1866e23026e43e9edf96cdc08ff16507a3dd` |
| Source distribution | `887d38a51fa9838b78a26ed0e6281c210efe1bc583b051daa2c87894d47fa056` |

Published at the operator's request before the full non-live suite
completed; focused auth/context/config/doctor tests (114), skill and doc
contract tests (716), Ruff, mypy, and `twine check` passed first. The full
suite result is recorded in the next entry when available.

## 2.0.8 / SDK 0.7.3

This CLI-only safety change closes the P0 from the 2026-09-17 systemic scope
audit. Thirty-nine `view` commands that change, export, or delete data
(16 benign mutations, 16 external-effect exports, 6 destructive commands, and
`view.exportable-config.apply`) previously accepted an omitted `DATASET_ID`
and fell back to the project-wide browse-and-probe parent resolver before
acting. They now fail closed with `missing_argument` (exit 2) and a
`recovery_commands` entry naming the `view get` read that supplies the
parent; `view.delete` fails with `resource_identity_required`. The
seventeen read commands keep parent discovery. The `DATASET_ID` help text
and generated reference say so for every affected command, and the bundled
skill and agent guide state the rule. Typed `view transform` commands keep
their existing SDK-side resolution when the parent is omitted; that path is
reversible and is unchanged in this release. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.8`
(source commit `1fa4ec0`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `c8d08c1ab4fe228d80ff20dbbb0b8265f4cd6815693b039235304894c90c44f9` |
| Source distribution | `e20bc5c80de52ec3e813baf23435b5ba711ea52e7ab4b49b6560ea5a29015143` |

Before upload, the full non-live suite at the release source recorded
3,852 passed, 2 skipped, 7 deselected; Ruff on `mammoth_cli/`, mypy,
`twine check`, and the generated-doc check passed. A fresh Python 3.14
environment installed the exact wheel, passed `pip check`, reported version
2.0.8, and returned the required-parent help from `schema get view.trash`.

## 2.0.7 / SDK 0.7.3

This CLI-only discovery-contract correction makes `schema get` and the
generated reference publish a protected `--input /private/path/request.json`
reference, instead of an inline `replace-with-secret` JSON body, for the
fourteen commands whose required request fields carry a secret
(`file.set-password`, `user.change-password`, `workspace.accept-invite`, and
eleven credentialed `view.export.*` targets). It also corrects the recorded
SDK signatures of `JobsAPI.get_job` and `JobsAPI.get_jobs` to the published
`mammoth-io` 0.7.3 (`timeout: float | None = None`), so discovery output and
introspection agree. Contract tests now accept the deliberate schema hand-off
example for blocked raw-patch commands (`dataset.update`, `view.update`) and
the manual-dispatch publication policy. It retains `mammoth-io>=0.7.3,<0.8`,
adds no API bindings or request-execution path, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.7`
(source commit `f4bf6c1`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `7b646c52737857ed90b38c4e633cc51f5cc44a1b26567aad8a6b964064780ca6` |
| Source distribution | `ac976b2e15f8e1aac5ca4cdb6be25d1ad0d1fa165449a180a573bb3c1bf8395b` |

Before upload, the full non-live suite at the release source recorded
3,846 passed, 2 skipped, 7 deselected, with the only failure being the
in-flight version-metadata check that passed after reinstalling; Ruff,
mypy, `twine check`, and the generated-doc check passed. A fresh Python 3.14
environment installed the exact wheel, passed `pip check`, reported version
2.0.7, and returned the protected-file example from
`schema get file.set-password`.

## 2.0.6 / SDK 0.7.3

This CLI-only bundled-skill and documentation correction closes the agent
credential hand-off gap. A fresh agent given the onboarding prompt found no
sanctioned way to obtain credentials from its operator, so it invented one
("environment credentials", which the CLI never reads). The skill, the
`agents`/`authentication`/`quickstart` guides, and the copy-paste onboarding
prompt now instruct an agent to stop, hand the operator the exact
hidden-prompt `mammoth auth login` command to run in their own terminal, and
wait; they state that the CLI reads credentials only from the current login or
the selected profile store. The evaluation-harness "controller broker/sidecar"
instructions are removed from the shipped skill and public docs. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings or request-execution path, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.6`
(source commit `bd14538`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `769d04236c3bf3518fbe8c8731cbb6695891e8c540897baad225e2a803b5360f` |
| Source distribution | `5921d27dfe5f30ef00e12fba8efdb5cf6631a7dc92a655b13d5af453bfedd8a9` |

Before upload: skill/packaging/README-doc contract tests (87), the
doc-example, STE, and version tests (711), Ruff on `mammoth_cli/`, mypy, and
`twine check` passed. A fresh Python 3.14 environment installed the exact
wheel, passed `pip check`, reported version 2.0.6, and returned
`has_credentials=false` from `auth status` for an empty home. The full
non-live suite at the parent commit had four unrelated pre-existing failures
(manifest example drift in `dataset.update`/`file.set-password`, SDK
introspection for `JobsAPI.get_job`, and the release-workflow trigger test);
they are recorded, not fixed, in this release.

## 2.0.5 / SDK 0.7.3

This CLI-only documentation and bundled-skill correction makes the secure
authentication preflight and schema-first command discovery explicit, repairs
stale release-evidence navigation, and corrects manifest metadata examples for
secret-bearing input. It retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings
or API request-execution path, and makes no capability-status or
autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.5`
(source commit `2a62d1c`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `6f20d4329d5e2f1d879fc9a3c2c394c840e63f6e1994a312e1308470a069539c` |
| Source distribution | `f3b23b9c1efa68a096d8fd38484099af5293fed86c419e0d966d8169b7cddb95` |

## 2.0.4 / SDK 0.7.3

Published from deterministic local artifacts built from tag `cli-v2.0.4`
(source commit `6714f90`). This security maintenance release hardens the
explicit file-backed credential fallback on POSIX. Every file read, update,
and delete now rejects unsafe directory or file ownership and permissions,
symlinks, non-regular files, and file-entry replacement before parsing
secrets. It retains `mammoth-io>=0.7.3,<0.8`, makes no API-binding or
capability-status change, and does not qualify autonomous workflows or backend
behavior.

PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `e62246975d559246e079c04f118cbafb31678f05ecc1fc04ab7308eb139e89b3` |
| Source distribution | `eb893be416b7d0c3dfde089550d17068601f939bd506ceb5d64e607973fbd759` |

Focused credential tests (14), Ruff, mypy, lock validation, build, and Twine
metadata validation passed. A fresh Python 3.14 environment installed the
exact published wheel, passed `pip check`, reported version 2.0.4, and ran a
bundled schema command. These checks do not constitute a full-suite or CI run.

## 2.0.3 / SDK 0.7.3

This CLI-only documentation correction makes every `mammoth-cli` README link
absolute, so the package README rendered on PyPI reaches the repository guides,
reference, and bundled skill. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no capability-status
or autonomous-workflow qualification claim.

## 2.0.2 / SDK 0.7.3

This CLI-only maintenance release updates the packaged agent skill, installation
guidance, and release-capability documentation. It keeps the published SDK
requirement at `mammoth-io>=0.7.3,<0.8` and does not add API bindings, promote
capability statuses, or qualify autonomous workflows. The 2.0.1 API evidence
below remains historical evidence for that published release. Its relative
README documentation links do not resolve in PyPI's package rendering; 2.0.3
corrects that presentation defect.

## 2.0.1 / SDK 0.7.3

Published from deterministic local artifacts built from annotated tag
`cli-v2.0.1` (source commit `9243430`). This maintenance release restores the
CLI static release gates and requires `mammoth-io>=0.7.3,<0.8` for the SDK
security release.

PyPI JSON metadata reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `001ed77409aa44f405f47694ba9af0ad66cfd69b937a4860c3855fa66abe966d` |
| Source distribution | `61ece65817b0769cab788ae7594fe8528b456ffad41c9780167d6cae2f956f73` |

The lockfile resolves published SDK `0.7.3` and its wheel/sdist hashes;
`poetry check --lock`, focused contracts, Ruff, and mypy passed before upload.
An independent no-cache public-PyPI Python 3.14 install passed dependency
checks, CLI/SDK version checks, NDJSON lifecycle framing, and bundled skill
list checks. These checks do not qualify all API operations, autonomous
workflows, or untested backend behavior.

## 2.0.0 / SDK 0.7.2

Published from deterministic local artifacts built from annotated tag
`cli-v2.0.0` (source commit `da626f8`). This is a breaking release for the
versioned NDJSON lifecycle framing. The CLI requires
`mammoth-io>=0.7.2,<0.8`; SDK `0.7.2` was published first.

PyPI JSON metadata reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `98b8bd291e3b5564f849a5e8889c6a0ea4682b171dde2d56fe5d21518a120cac` |
| Source distribution | `1aa833e1e1257bea1613754c0c0aaa9bc719035ad10dcbca4a69ef57324bed1d` |

The lockfile resolves the published SDK `0.7.2` wheel hash and passed
`poetry check --lock`. Focused output, schema/discovery, identity, workflow,
and installer-document contracts passed before upload. Exact-artifact and
independent public-PyPI Python 3.14 installs passed `pip check`, reported CLI
`2.0.0` and SDK `0.7.2`, and exercised NDJSON lifecycle framing plus bundled
skill install/list checks. These checks do not qualify all API operations,
autonomous workflows, or untested backend behavior.

## 1.1.12

Published from deterministic **local** artifacts built from immutable tag
`cli-v1.1.12` (commit `7d02afa`). This is a fail-closed contract correction:
`view update` rejects arbitrary raw patch data until the API publishes a typed
request contract. It does not claim support for arbitrary view patches.

The artifact bytes were reviewed before the authorized local Twine upload; they
are not CI-built artifacts. PyPI JSON metadata reports the same SHA-256
digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e` |
| Source distribution | `a8caf87591e02bb06b130e20b6eebe1d92ec8b65a31db528b52ab77ae20138af` |

Focused local prechecks passed for the selected view/dataset tests (162), four
B09 no-dispatch regressions, Ruff, mypy, lock, generated-document check, links,
and the bundled skill catalog. Vale reported zero errors and existing warnings.
The full non-live CLI suite was not run for this release, so this release makes
no full-suite-pass claim. GitHub Actions remain disabled repository-wide at the
user's request, so no CI artifact, workflow, GitHub release asset, or signing
claim applies.

A fresh isolated Python 3.14 install of the exact local wheel passed `pip
check`, `mammoth --version`, `schema get view.update`, and the installed B09
no-dispatch smoke (`unsupported_contract`, exit 2) with an empty home directory.
A fresh isolated Python 3.14 public-PyPI install passed the same `pip check`,
version, schema, and B09 smoke checks after Simple-index propagation. These
checks do not qualify autonomous workflows, dashboard runtime behavior, or all
API operations.

An isolated published-skill smoke used a literal, prevalidated temporary
`HOME`, `CODEX_HOME`, and `XDG_DATA_HOME`. `skill path` resolved all three
agent destinations beneath that temporary root; the first install wrote three
owned copies, the repeat reported all three as identical, and `skill list`
reported all copies present and intact. Sixty bundled catalog and recipe links
resolved. The smoke found that the 1.1.12 generated catalog described the
fail-closed B07/B09 patch commands as runnable; that documentation defect is
corrected only in unreleased 1.1.13 source and does not change 1.1.12 behavior.

## 1.1.11

Published from deterministic **local** artifacts built from immutable tag
`cli-v1.1.11` (commit `ab0f898`). The artifact bytes were reviewed before the
authorized local Twine upload; they are not CI-built artifacts. PyPI JSON
metadata reports the same SHA-256 digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962` |
| Source distribution | `c5339664d5be43a27cd43c15414c5ef896fb0ae229fd135845aa1f96aa765a7e` |

Local prechecks passed for the lock, Ruff, mypy, generated-document check,
links, and Vale (zero errors). The full non-live CLI suite was explicitly
cancelled at the release owner's direction and is therefore unconfirmed; this
release makes no full-suite-pass claim. GitHub Actions were disabled
repository-wide at the user's request, so no release workflow, CI artifact,
GitHub release asset, or signing claim applies to this release.

A fresh isolated, no-cache Python 3.14 install from PyPI passed `pip check`,
`mammoth --version`, `schema get dataset.create`, and an installed bundled
`SKILL.md` resource check. These checks do not qualify autonomous ETL,
dashboard runtime behavior, or all API operations.

An additional isolated Python 3.14 probe exercised installed public
`mammoth-cli` 1.1.11 and `mammoth-io` 0.7.1 with mocked transports only. A
cross-origin `302` made one original-origin request and was not followed;
empty and partial multi-job responses timed out rather than reporting success;
and a mutation `502` or malformed `200` produced `outcome_unknown`. The probe
used no live service or credentials and is focused regression evidence, not a
full-suite result.

## 1.1.10

Published from the exact `dist` artifact downloaded from successful CI
build-and-verify job [`105174083438`](https://github.com/EdgeMetric/mammothsdk/actions/runs/35212798832/job/105174083438)
for tag `cli-v1.1.10` (commit `20430eb`). Trusted Publishing failed, so the
authorized local Twine fallback uploaded only those downloaded bytes. PyPI's
JSON metadata reports the same SHA-256 digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `7b31296f1d2227791533a76cee1eb32a29eda4a344b4650f7aa3a0be556ddf4c` |
| Source distribution | `cfd7cab3e4d11f1b261805d5fdd9b149e83df8dfcacf2e5aa6a8abe0bdfc977a` |

A fresh Python 3.14 install from PyPI passed `mammoth --version`,
`schema get dataset.create` (including the documented `weburl` path and CLI
wait policy), and a bundled-skill recipe check. The GitHub-release job was
skipped; no signed GitHub release, Sigstore bundle, or signing claim is made.
These checks do not qualify autonomous ETL, dashboard runtime behavior, or all
API operations.

## 1.1.9

Published from the exact distribution files downloaded from successful CI
build job [`105151237784`](https://github.com/EdgeMetric/mammothsdk/actions/runs/35205826645/job/105151237784).
Trusted Publishing again failed with `invalid-publisher`; the authorized local
Twine fallback uploaded only those downloaded bytes. The PyPI downloads match
the CI hashes exactly:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b15822ee3bbd00b201c2c49292fec8a10b7cae36df60082f29f2919b6f89e86e` |
| Source distribution | `6b63b21b6d57a5697e8a186f4ad3eb2240182c61d1c95a3d78a0d8a7f315aa67` |

A fresh Python 3.12 PyPI install passed `mammoth --version`, `schema list`
(547 commands), `pip check`, project-scope Codex skill installation (60 files),
and typed `fill missing`/`duplicate` discovery. The matching GitHub release
ships SHA256SUMS, wheel/sdist, and installers, but is explicitly unsigned: no
Sigstore bundle or signing claim is made. These release checks do not qualify
autonomous ETL, dashboard runtime behavior, or all API operations.

Dashboard release evidence remains a backend boundary, not a CLI/SDK defect
claim. Against an owned disposable dataview, the current-engine blank-create
route returned HTTP 403 with the server's `AUTHORIZATION_ERROR` (`4RESO001`),
which establishes only that this credential/request was denied; it does not
identify the missing entitlement. The legacy create route returned HTTP 409
`DASHBOARD_LEGACY_CREATION_RETIRED` (`4DASH012`), so retrying that route or
changing its payload cannot create a dashboard. The documented source-list
route returned HTTP 500 with an empty response body, a known server-variance
boundary. The CLI preserved each status and server detail in its structured
error envelope; no permission bypass, retry, or readiness promotion follows.
The retained release-evidence archive is indexed in
[capability evidence](capability-evidence/README.md); it does not contain a
dashboard-specific fixture directory.

The immutable PyPI 1.1.9 description retains its pre-publication README
snapshot of **7 Partial / 521 Unassessed**. Read the canonical
[machine-readable matrix](release-capability-matrix.json) for current counts,
rather than that immutable package description.

## 1.1.8

Not published. Its CI full gate failed before artifact construction because a
Python 3.10-compatible evidence-script change was introduced after the local
lint check and triggered Ruff's Python-3.11-only `UP017` suggestion. The
1.1.9 follow-up keeps the compatibility behavior and suppresses that specific
non-applicable suggestion.

## 1.1.7

PyPI 1.1.7 was uploaded through the authorized local Twine fallback after the
trusted-publisher exchange failed with `invalid-publisher`. Its local upload
bytes did not match the later-downloaded CI artifact bytes, so it must not be
treated as CI-byte-identical. No GitHub release assets were created for 1.1.7.

The recorded hashes are:

| Artifact | PyPI/local upload | CI artifact |
| --- | --- | --- |
| Wheel | `1c27140eec8663adf4109bea9812d22226c47d0ce14d031e769e8073e6622c48` | `cf280cfc86f190b28dbed5173a96b67f2305d8da85b12c36930fcd7cc9bf43f2` |
| Source distribution | `5df4f4ecec839cf2ebd0be0507e09cb6c0a02f2db0fddfcc2c696f8c77a69bb0` | `1fe28c03a17abddeeb9750be38eff08b0a81d6638310c61c6b0adc9a8d095dcc` |

The 1.1.7 release CI build-and-verify job passed; Trusted Publishing failed
because PyPI has no matching publisher configuration. This is a provenance
correction, not an ETL qualification or a claim that all API operations are
verified.
