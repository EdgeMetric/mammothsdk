# Authentication profiles and live-test operations

## Authentication command surface

Authentication contains only API key, API secret, workspace ID, and optional
server prefix. Project, base URL, output, and timeouts are separate context or
configuration.

Canonical commands:

```text
mammoth auth login [--profile NAME] [--server-prefix PREFIX]
                   [--storage auto|keyring|file] [--from-env|--input FILE|-]
mammoth auth status [--profile NAME] [--check]
mammoth auth profile list
mammoth auth profile use NAME
mammoth auth logout [--profile NAME] [--all] --yes
```

Profile names match `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. The default profile name
is `default`. `auth profile use` changes the selected profile. `--profile` on a
command overrides selection without changing it. Environment values override
the selected profile for one process and are never saved implicitly.

Interactive login prompts for the API key and secret with hidden input. It does
not accept either secret as a normal command argument. `--from-env` reads the
four documented Mammoth variables. `--input` reads a permission-checked strict
JSON or YAML `LoginRequest`; stdin requires `--input-format`. Prompt,
`--from-env`, and `--input` modes are mutually exclusive.

`LoginRequest` contains `api_key`, `api_secret`, `workspace_id`, and optional
`server_prefix = "app-eu"`. Reject unknown fields, empty values, nonpositive
workspace IDs, and invalid prefixes before network access.

`--storage auto` prefers the OS keyring. If no keyring is available, an
interactive TTY can approve file storage. Noninteractive login must select
`--storage file` explicitly. `--storage keyring` fails with a recovery command
when unavailable.

Store nonsecret profile data in
`platformdirs.user_config_dir("mammoth-cli", "Mammoth")/profiles.toml`. Use the
keyring service `mammoth-cli` and profile name as the keyring username. Store
file fallback credentials in `credentials.toml` beside the profile file. On
POSIX, require directory mode `0700` and file mode `0600`. On Windows, apply a
DACL for the current user and SYSTEM only; fail rather than write when that
cannot be enforced. Lock and atomically replace both files.

A profile's nonsecret record contains only its name, workspace ID, server
prefix or expert base URL, and optional positive active project ID. Manage the
active project only with `context project status|use|clear` from plan 01. Do
not store a project ID in the keyring secret payload, and do not infer or save
one during login.

Login performs a lightweight typed public SDK connection check before it saves
anything. A failed check returns the mapped authentication or network error and
leaves existing profile state unchanged. `auth status` reports local state
without network access; `--check` performs the connection check. Never reveal
the key, secret, keyring item, or credential path in machine or debug output.

`auth logout` removes the profile secret and nonsecret record. `--all` and
`--profile` are mutually exclusive. If the active profile is removed, select
`default` when present; otherwise leave no selection. Missing profiles are an
idempotent success. `--yes` is required without a TTY.

Required red-first tests:

```text
AUTH-FOUR-VALUES-ONLY
AUTH-PROMPT-HIDDEN
AUTH-FROM-ENV
AUTH-INPUT-PERMISSIONS
AUTH-PRECEDENCE
AUTH-PREFIX-DEFAULT|VALIDATION
AUTH-KEYRING-AVAILABLE|UNAVAILABLE
AUTH-FILE-POSIX-MODE|WINDOWS-DACL
AUTH-VALIDATE-BEFORE-SAVE
AUTH-STATUS-LOCAL|CHECK
AUTH-PROFILE-LIST|USE|LOGOUT
AUTH-NO-SECRET-OUTPUT|LOG|SNAPSHOT
```

## Local live-test environment

The ignored root `.env.plan` contains exactly:

```text
MAMMOTH_API_KEY
MAMMOTH_API_SECRET
MAMMOTH_WORKSPACE_ID
MAMMOTH_SERVER_PREFIX
```

It uses workspace `4` and prefix `release`. Keep mode `0600`. The normal CLI
does not load `.env.plan` or any dotenv file. Only the test runner loads this
file. It parses simple quoted or unquoted values without shell evaluation.

The test-only runner contains an immutable allowlist for prefix `release`, URL
`https://release.mammoth.io/api/v2`, and workspace `4`. It compares the resolved
values before any mutation and refuses every other target. Do not add more
environment variables or an acknowledgement variable.

Canonical verification commands are defined as task-runner targets:

```text
make cli-test-unit
make cli-test-contract
make cli-test-live-preflight
make cli-test-live
make cli-typecheck
make cli-lint
make cli-generated-check
make cli-package-check
make cli-installer-check
make cli-docs-check
make cli-skill-check
make cli-all
```

Each target has a Poetry equivalent in its help output. `cli-all` excludes live
tests unless the caller adds `LIVE=1`; the live targets still enforce the
hardcoded allowlist.

## Live preflight

Use Python 3.14.3 for the primary recon runner. Preflight:

1. Load the four values.
2. Enforce prefix `release` and workspace `4`.
3. Test authentication.
4. Create a uniquely named project.
5. Write and sync its cleanup ledger record.
6. Create a two-column sketch dataset.
7. If sketch creation is unavailable, upload the repository's small CSV
   fixture.
8. Create or resolve a test view.
9. Run a read query.
10. Delete child resources in reverse order and delete the project.
11. Run the leak audit.

Stop the live suite at the first permission failure. A permission failure is a
fixture blocker, not a missing product feature and not `server_unavailable`.
Contract, unit, docs, package, installer, and skill work can continue.

The current credentials passed authentication and project create/list/delete.
They failed file upload and sketch-dataset creation. Therefore live dataset,
view, pipeline, and transformation tests remain blocked until permissions
change. Re-run preflight before resuming those families.

## Crash-safe cleanup ledger

Create one ledger in a unique operating-system temporary directory for each
run. Use schema `mammoth-cli-e2e-ledger-v1`. After every create response, append
and `fsync` a record before the next operation. Record only server prefix,
workspace ID, project ID, resource type, resource ID, generated name, creator
operation, cleanup operation, created time, and cleanup status.

Delete children in reverse dependency order, then delete the project. Retry
read-only checks. Limit deletion attempts; never retry an unknown mutation.
Preserve a sanitized ledger when cleanup fails.

At startup, scan only ledgers created by this runner. Reconcile stale projects
only when their recorded prefix and workspace match the allowlist, the ID is
present, the name has the exact `mammoth-cli-e2e-` prefix, and age exceeds the
configured test timeout. Never delete by name alone. Provide
`make cli-live-leak-audit` for independent recovery after interruption.

## Per-operation live policy

Every command manifest selects one evidence class from the parity document.
Project isolation does not authorize workspace or external effects. Default
workspace deletion, billing mutation, account deletion, ownership transfer,
user removal, password changes, outbound email, and external sends to
`contract_only_high_impact` until an explicit disposable fixture is recorded.

Resolve destructive targets through read-only calls before confirmation. A
single high-impact target confirms its immutable ID. Multiple targets confirm
the sorted comma-separated immutable ID set. Collection-wide deletion confirms
the containing project or workspace ID plus the exact phrase shown by the
command. `--yes` alone never authorizes a high-impact operation.

## Block and resume protocol

When an external fixture or permission is missing:

1. Mark exact test IDs `blocked_external` with sanitized evidence.
2. Continue unaffected unit, contract, documentation, package, installer, and
   skill work.
3. Do not convert the failure to `server_unavailable`.
4. Stop before any action that needs different authority.
5. Resume only after the ledger records the changed fixture and preflight
   passes.

Use status `implementation complete; live acceptance blocked` when all local
work passes but mandatory live evidence is blocked. Use `fully accepted` only
after all required live tests and the leak audit pass.
