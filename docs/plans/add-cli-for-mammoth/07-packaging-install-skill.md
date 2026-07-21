# Packaging, installers, release, and skill contract

This document is normative. Workers must not choose different artifact names,
skill paths, version rules, or installation behavior.

## Package layout

Create this sibling package:

```text
mammoth-cli/
├── pyproject.toml
├── README.md
├── LICENSE
├── mammoth_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── commands/
│   ├── contracts/
│   ├── context/
│   ├── errors/
│   ├── manifest/
│   ├── messages/
│   ├── output/
│   ├── services/
│   └── bundled_skill/mammoth-cli/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/
│       └── scripts/
├── spec/
├── scripts/
└── tests/
```

`pyproject.toml` uses poetry-core, declares `requires-python = ">=3.12,<3.15"`,
and registers `mammoth = "mammoth_cli.__main__:main"`. Include the complete
canonical skill as package data. Include README and license in wheel and source
distribution. Never publish a repository-local dependency URL. Declare the
reviewed compatible `mammoth-io` release range.

Build with `poetry build`. Check wheel metadata, source contents, console and
module entry points, package data, license, and dependency resolution in clean
environments. Rebuild twice with `SOURCE_DATE_EPOCH` and compare normalized
wheel and source-distribution contents.

## Python support

The CLI supports Python 3.12 through the latest stable minor that has passed CI.
The current matrix is 3.12, 3.13, and 3.14; use Python 3.14.3 for primary local
development. A new Python minor is unsupported until dependencies resolve and
unit, type, package, installer, and live preflight checks pass. Then update CI,
classifiers, and documentation together.

The user decision sets the repository minimum to Python 3.12. Update
`mammoth-io` and `mammoth-cli` together to `>=3.12,<3.15`. Treat this as an
intentional compatibility change in release notes and version selection. Do not
silently retain or reintroduce Python 3.10 or 3.11 classifiers.

## Release identity and order

Use SemVer for the CLI. Tag CLI releases as `cli-vX.Y.Z`. Keep SDK tags and CLI
tags independent. A release that needs SDK additions publishes the compatible
`mammoth-io` version first, verifies it from PyPI, then publishes
`mammoth-cli`. The CLI version does not have to equal the SDK version.

Create releases only from a protected GitHub Actions workflow triggered by an
authorized `cli-v*` tag. Grant `contents: write` and `id-token: write` only to
the release job. All other jobs use read-only permissions. Use PyPI trusted
publishing. Do not publish, tag, push, or create a release without separate user
authorization.

Release assets use these exact names:

```text
mammoth_cli-X.Y.Z-py3-none-any.whl
mammoth_cli-X.Y.Z.tar.gz
mammoth-install.sh
mammoth-install.ps1
SHA256SUMS
SHA256SUMS.sigstore.json
```

`SHA256SUMS` uses two spaces between the lowercase SHA-256 digest and asset
name. The Sigstore bundle covers `SHA256SUMS`, uses GitHub Actions OIDC, and is
verified against this repository and the release workflow identity. Record the
exact `cosign verify-blob` command in release documentation.

## Installer platforms

Support:

- Linux glibc x86_64 and aarch64 with POSIX `sh`.
- macOS x86_64 and arm64 with POSIX `sh`.
- Windows 10 or later, x86_64 and arm64, with Windows PowerShell 5.1 or
  PowerShell 7.

Fail with a direct manual-install command on an unsupported OS, architecture,
libc, proxy failure, or offline host. Honor standard HTTP proxy variables. Do
not modify a certificate store or disable TLS verification.

Pin uv `0.11.30` in each released installer. If a compatible uv is unavailable,
download the matching immutable uv release archive from Astral's GitHub
release, verify its published SHA-256 before extraction, and place it in an
installer-owned temporary directory. Do not replace a user's uv. Map each
supported OS and architecture explicitly and reject unknown values.

Install the exact CLI version embedded in the versioned installer. A `latest`
installer first resolves one immutable `cli-vX.Y.Z` release, then downloads and
uses that release's versioned assets. It must never fetch branch content. Use
`uv tool install mammoth-cli==X.Y.Z` after PyPI publication. Prepublication
tests use a local release fixture and local wheel URLs.

Use `uv tool dir --bin` for the executable location. Add that one directory to
the user PATH only when it is missing and `--no-modify-path` is absent. Make
the edit idempotent. Print the exact manual PATH instruction when no edit is
made. Never require administrator privileges.

## Installer interfaces

Convenience paths:

```bash
curl -fsSL https://github.com/EdgeMetric/mm-pysdk/releases/latest/download/mammoth-install.sh | sh
```

```powershell
irm https://github.com/EdgeMetric/mm-pysdk/releases/latest/download/mammoth-install.ps1 | iex
```

Label these as convenience paths because the fetched script executes before
its checksum can be verified. The recommended verified flow downloads the
versioned installer, `SHA256SUMS`, and Sigstore bundle; verifies both; lets the
user inspect the installer; then executes it.

To pass options through the POSIX pipe, use:

```bash
curl -fsSL URL | sh -s -- --version X.Y.Z --cli-only --no-modify-path
```

For PowerShell options, download first and run:

```powershell
./mammoth-install.ps1 -Version X.Y.Z -CliOnly -NoModifyPath
```

Both installers support exact-version `--version` or `-Version`, CLI-only,
skills-only, no-PATH-change, noninteractive, and help modes. CLI-only and
skills-only are mutually exclusive. The default installs the CLI and the skill
for all three agents at user scope. Noninteractive mode never prompts.

## Ownership, upgrade, rollback, and uninstall

Store installation state with `platformdirs.user_data_dir("mammoth-cli",
"Mammoth")` in `install-state-v1.json`. Record schema version, installer
version, CLI version, uv version and path, executable directory, installed skill
targets, SHA-256 for each owned file, prior version, and timestamp. Never record
Mammoth credentials.

`mammoth self update [--version X.Y.Z]` installs to a staging location, verifies
`mammoth --version` and `mammoth doctor --local`, updates skills atomically, and
then updates state. If validation fails, restore the previous CLI version and
skill directories. Preserve a sanitized failure report.

`mammoth self uninstall [--keep-skills] [--keep-config] --yes` removes only
files whose current digest matches the ownership record. Report modified files
and leave them in place. It never removes a user-provided uv. Remove a PATH
entry only when the ownership record proves the installer added it and no
remaining owned executable needs it.

## Canonical skill and destinations

Keep one canonical packaged skill. Copy it; do not symlink it. Install targets:

| Agent | User scope | Project scope |
|---|---|---|
| Codex | `$HOME/.agents/skills/mammoth-cli` | `<project>/.agents/skills/mammoth-cli` |
| Claude Code | `$HOME/.claude/skills/mammoth-cli` | `<project>/.claude/skills/mammoth-cli` |
| Cursor | `$HOME/.cursor/skills/mammoth-cli` | `<project>/.cursor/skills/mammoth-cli` |

Codex paths follow the current [Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).
Claude paths follow [Anthropic's Agent Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
Cursor paths follow [Cursor's Agent Skills documentation](https://cursor.com/docs/skills).
Recheck all three at release lock and record any change.

For project scope, use the Git root. If no Git root exists, use the current
directory. The defaults are `--agent all --scope user`. `--agent` is repeatable.
The installer never edits agent settings files.

Before copying, compare canonical and installed hashes. An identical install is
a success. An owned older install updates atomically. An unowned or locally
modified destination fails with code `skill_conflict`; `--force` first moves it
to a timestamped sibling backup and records that backup. Update and uninstall
use the same ownership rules. Package data lookup must work offline.

The skill name is `mammoth-cli`. Its frontmatter contains only `name` and
`description`. Keep `SKILL.md` under 500 lines and put detail in directly linked
one-level references. Include exact patterns for auth, project selection,
machine output, safe mutation, jobs, draft mode, bulk replace, cleanup, and
error recovery. Do not include credentials or duplicate generated reference
documentation.

## Red-first package, installer, and skill tests

Create these test families before implementation:

```text
PKG-WHEEL-PY312|PY313|PY314
PKG-SDIST-CONTENTS
PKG-ENTRYPOINTS
PKG-SKILL-DATA
PKG-NO-LOCAL-URL
INS-POSIX-EXISTING-UV|NO-UV
INS-POWERSHELL-EXISTING-UV|NO-UV
INS-UNSUPPORTED-OS|ARCH|LIBC
INS-CHECKSUM-MISMATCH|SIGSTORE-MISMATCH
INS-PINNED-VERSION|NO-PATH|NONINTERACTIVE
INS-CLI-ONLY|SKILLS-ONLY
INS-UPGRADE-ROLLBACK|UNINSTALL-OWNERSHIP
SKILL-CODEX-USER|PROJECT
SKILL-CLAUDE-USER|PROJECT
SKILL-CURSOR-USER|PROJECT
SKILL-MODIFIED-CONFLICT|FORCE-BACKUP|OFFLINE
```

Use isolated HOME, XDG, APPDATA, LOCALAPPDATA, and PATH values. Do not touch a
real user directory. Test LF/CRLF, executable bits, Unicode paths, concurrent
state-file locking, Windows-safe atomic replacement, and Bash, Zsh, Fish, and
PowerShell completion installation.

Test public release URLs only after publication authorization. Before that,
test the same paths against a local immutable release fixture.

## Documentation language tooling

Generate `docs/llms.txt` as a compact index of every CLI guide, command family,
schema, skill, and canonical source link. Generate `docs/llms-full.txt` as the
complete agent-readable reference. Link the index from every documentation
page. Keep both deterministic and fail CI on a generated diff. This adopts the
useful discovery pattern shown by the [Loops skill documentation](https://loops.so/docs/skills)
without copying its product structure.

Pin Vale `3.15.1`. Store configuration in `mammoth-cli/.vale.ini`, custom rules
in `mammoth-cli/styles/MammothSTE/`, and approved and prohibited terms in
`mammoth-cli/styles/config/vocabularies/Mammoth/`. Cite the
[ASD-STE100 home page](https://www.asd-ste100.org/) as the house profile's
inspiration. Do not copy its dictionary or claim compliance or certification.

Use these reviewed rule IDs:

```text
MammothSTE.Terms                 error
MammothSTE.ProhibitedTerms      error
MammothSTE.SentenceLength       warning
MammothSTE.PassiveVoice         warning
MammothSTE.OneInstruction       warning
MammothSTE.Headings             warning
```

Exclude fenced and inline code, command flags, environment names, API fields,
JSON/YAML keys, URLs, paths, and quoted server text from lexical replacement.
`scripts/extract_cli_text.py` extracts Typer help, prompts, warnings, errors,
and hints to a deterministic temporary corpus. `scripts/check_ste.py` applies
the 20-word procedural and 25-word descriptive sentence checks that Vale cannot
classify alone. `make cli-docs-check` runs generation-diff checks, Vale, the
custom checker, and link validation.

Add pass/fail fixtures for every rule and exclusion. New warnings fail CI; do
not create an unchecked baseline. A human reviewer records terminology and
instruction-clarity approval in the audit ledger.
