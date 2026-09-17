# CLI 2.0.0 release-readiness audit

Audit date: 2026-09-17. This is a bounded, read-only source and artifact
review. It records evidence for selected safety boundaries; it is not a claim
that every API operation, provider integration, or autonomous workflow is
production-qualified.

## Release identity

- Source tag: `cli-v2.0.0`, dereferencing to
  `da626f863bb37f92b5001de24e36d199100326aa`.
- The tagged source was confirmed to be an ancestor of `origin/main`.
- PyPI artifact hashes were checked against the locally audited artifacts:

| Distribution | Artifact | SHA-256 |
| --- | --- | --- |
| `mammoth-io` 0.7.2 | wheel | `981118484ee7a858d234a62daecc7a79d636073f5c79c742fb3ba16b08d41901` |
| `mammoth-io` 0.7.2 | sdist | `40774c593af28536260e6707e903b1caafd9e77a42dd3dd286ce6e42225680b7` |
| `mammoth-cli` 2.0.0 | wheel | `98b8bd291e3b5564f849a5e8889c6a0ea4682b171dde2d56fe5d21518a120cac` |
| `mammoth-cli` 2.0.0 | sdist | `1aa833e1e1257bea1613754c0c0aaa9bc719035ad10dcbca4a69ef57324bed1d` |

The CLI wheel contained the bundled skill, OpenAPI metadata, and command
manifests. Its 204 packaged source/assets matched the corresponding current
tracked files in the audited source tree.

## Checked safety boundaries

- Authenticated SDK requests reject redirects and cross-origin endpoints;
  signed downloads use a distinct session without API credential headers.
- Mutation timeouts, gateway errors, malformed successful responses, and
  effectful webhook `GET` failures retain `outcome_unknown`; CLI mapping does
  not recommend mutation replay for an uncertain effect.
- Single and multi-job waits use a monotonic deadline, pass the remaining
  observation budget to transport, and require every requested job ID before
  reporting completion.
- Recovery command generation retains a resolved non-default profile.
- Download delivery uses a temporary file/atomic replacement and rejects an
  existing symlink destination.
- Installer and skill tests cover owner-managed destinations, failure handling,
  version pin validation, and bundled catalog/recipe integrity.

Focused commands completed:

```text
.venv/bin/pytest -q tests/unit/test_client_safety.py tests/unit/test_m4_recovery.py
# 52 passed

cd mammoth-cli && .venv/bin/pytest -q \
  tests/unit/services/test_mapping.py tests/unit/runtime/test_execute_validation.py \
  tests/installer/test_installer_ownership.py tests/installer/test_installer_posix.py \
  tests/unit/context/test_credentials.py tests/unit/context/test_resolver.py
# 62 passed

cd mammoth-cli && .venv/bin/pytest -q \
  tests/installer/test_installer_local_source.py tests/installer/test_installer_skill_failure.py \
  tests/installer/test_installer_uv_prerelease.py tests/installer/test_installer_uv_version.py \
  tests/unit/commands/test_skill.py tests/unit/test_bundled_skill_recipes.py \
  tests/contract/test_skill_catalog.py tests/contract/test_skill_recipe_contracts.py
# 37 passed, 2 skipped (environment-dependent)

.venv/bin/pytest -q tests/unit/test_owner_journal_broker.py
# 31 passed
```

## Result and limits

No reproducible P0 or P1 defect was found within these checked boundaries.

The isolated fresh-wheel smoke was attempted but could not finish because the
audit host exhausted its disk quota while pip installed third-party
dependencies (`OSError: [Errno 122] Disk quota exceeded`). That environmental
failure is not evidence of a package defect, but means this audit does not add
a fresh-install result beyond the exact artifact/hash and packaged-file checks.

This audit does not qualify live API behavior, redirect behavior at real
providers, complete command/API coverage, external export destinations,
credential-vault/provider attestation, or autonomous agent operation. Those
remain separate live and capability-matrix qualification work.
