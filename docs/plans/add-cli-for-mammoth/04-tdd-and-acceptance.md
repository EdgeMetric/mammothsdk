# TDD and acceptance plan

## Red-first gate

Write and review these tests before feature handlers:

```text
test_openapi_snapshot_metadata
test_openapi_inventory_has_376_operations
test_sdk_inventory_matches_public_surface
test_every_openapi_operation_has_reviewed_disposition
test_every_command_disposition_has_typed_sdk_symbol
test_every_public_sdk_method_has_command_or_alias
test_manifest_has_no_unknown_openapi_or_sdk_symbols
test_every_command_has_request_and_result_models
test_every_command_has_human_and_agent_examples
test_every_command_has_test_ids
test_every_mutation_has_safety_class
test_every_async_operation_has_wait_policy
test_every_list_operation_has_pagination_policy
test_every_secret_field_has_transport_and_redaction_policy
test_every_manifest_command_is_registered
test_generated_help_contains_every_command_example
test_cli_never_calls_private_sdk_members
test_cli_never_implements_mammoth_http
test_machine_stdout_contains_data_only
test_openapi_inventory_identity_is_method_and_path
test_openapi_inventory_digest_matches_snapshot
test_sdk_manifest_signatures_and_defaults_match_introspection
test_command_paths_are_unique
test_alias_graph_has_no_cycles
test_manifest_enum_values_match_sdk
test_manifest_request_schema_matches_registered_handler
test_manifest_sdk_conversion_matches_exact_arguments
test_all_examples_parse
test_all_input_examples_validate
test_bulk_replace_defaults_match_sdk
test_bulk_replace_shortcut_and_document_modes
test_bulk_replace_calls_public_view_method
test_draft_state_survives_process_boundaries
test_live_exemptions_have_reason_and_reviewer
test_no_command_has_unresolved_design_fields
test_every_command_supports_json_no_input
test_capability_registry_matches_manifests
test_schema_registry_matches_request_models
test_agent_errors_include_executable_recovery
test_agent_mode_never_prompts_or_pages
test_timeout_results_include_resumable_identity
```

Confirm that these tests are red only because the corresponding manifest,
typed SDK method, or command is not yet implemented. Fix inventory and test
defects before feature code.

## Per-operation test IDs

Generate these IDs from each canonical command record:

```text
UT-<OPERATION>             request validation and SDK conversion
CT-<OPERATION>-HUMAN       installed command human output
CT-<OPERATION>-JSON        JSON envelope and clean streams
CT-<OPERATION>-ERROR       validation, API mapping, and redaction
CT-<OPERATION>-WAIT        wait success where applicable
CT-<OPERATION>-NOWAIT      start result where supported
CT-<OPERATION>-TIMEOUT     stable timeout behavior
LT-<OPERATION>             guarded live operation
LT-<OPERATION>-DRAFT       draft behavior for transformations
LT-<OPERATION>-UNDO        task deletion or documented rollback
```

An alias requires a manifest test but does not duplicate the handler tests.
A `protocol_only` operation requires a disposition test and no command test.

## Unit tests

Test:

- Authentication precedence and endpoint derivation.
- Profile and keyring isolation.
- Project-context precedence.
- Strict JSON and YAML request validation.
- Flag-over-document precedence.
- Exact SDK method and argument conversion.
- Recursive conditions.
- Result normalization.
- Human, JSON, YAML, NDJSON, and plain output.
- Stdout and stderr separation.
- Exit statuses and error codes.
- Noninteractive and confirmation behavior.
- Pagination and waiting.
- Interruptions.
- Atomic downloads and overwrite protection.
- Secret redaction in output, exceptions, debug logs, and snapshots.
- Completion generation.
- Skill installation without touching real user directories.
- STE checks for documentation and extracted CLI text.

Phase 1 commits the complete manifest, registration, and command-contract test
suite and its expected red report before handler packets start. Each worker
cites assigned failing test IDs and the red baseline commit, makes them green,
and adds edge-case tests. Do not accept an implementation-only commit or a
worker-created replacement for the central contract test.

## SDK tests

For each added or repaired SDK operation:

- Validate its public request model.
- Verify the complete method, URL, path parameters, query, headers, and body.
- Validate each documented response union.
- Test API error, authentication error, network error, and timeout behavior.
- Test pagination and job continuation.
- Test redaction metadata for secrets.
- Add a guarded live test when safe.

Generated wire models require a reproducibility test. Regeneration from the
pinned snapshot must produce no diff.

## Subprocess tests

Invoke the built executable and module entry point under:

- TTY-like streams.
- Piped stdout and stderr.
- `CI=1`.
- `NO_COLOR=1`.
- `TERM=dumb`.
- `MAMMOTH_OUTPUT=json`.
- `MAMMOTH_NO_INPUT=1`.

Verify `mammoth`, `mammoth --help`, `mammoth --version`, and
`python -m mammoth_cli`.

## Coverage requirements

- Every canonical command has request, SDK-call, JSON, error, and help tests.
- Every destructive command has confirmation tests.
- Every secret-bearing command has recursive leakage tests.
- Every paged list has first, middle, final, empty, and repeated-token tests.
- Every wait operation has success, failure, timeout, unknown-state, and
  interruption tests.
- CLI package line coverage must be at least 90 percent.
- Contract and parity tables must be 100 percent complete.
- Every safe transformation has guarded live output-data evidence. Category
  coverage is not a substitute for per-operation coverage.

Coverage percentage does not replace operation parity.

## Live-test guard

Use a dedicated non-production tenant. Require:

```text
MAMMOTH_API_KEY
MAMMOTH_API_SECRET
MAMMOTH_WORKSPACE_ID
MAMMOTH_SERVER_PREFIX
```

Initial authorized test target:

```text
Base URL: https://release.mammoth.io/api/v2
Normalized server prefix: release
Workspace ID: 4
```

Do not store its API key or API secret in the repository. For local work, load
the supplied test values from the ignored `.env.plan`. That file contains only
the four variables shown above and has user-only permissions. CI must load the
same four names from its secret store.

Every recon or live-test run must create a new project. Do not use an existing
project for mutations. Name it:

```text
mammoth-cli-e2e-<UTC timestamp>-<8 random lowercase hex characters>
```

Record the new project ID in the cleanup ledger before creating any child
resource. Set it as project context for the complete run. Delete the project in
the outermost `finally` block after child cleanup. If project deletion fails,
print the project ID to stderr, return failure, and preserve the sanitized
cleanup ledger as an artifact.

Before a live mutation:

1. Verify workspace ID `4` and the `release` server prefix.
2. Create a new uniquely named project.
3. Record the project ID in the cleanup ledger.
4. Set the new project as test context.
5. Generate a unique child-resource prefix.
6. Record every created resource immediately.

Always clean in `finally`. Run a final trash and resource leak audit. Store only
sanitized logs as artifacts.

The current workspace `4` test principal can create, list, and delete projects,
but live recon could not upload a file or create a sketch dataset. Both calls
returned an authorization error. Treat dataset and transformation acceptance as
blocked until the principal has dataset-creation and file-upload permission.
Project-lifecycle success is not evidence that later resource families are
authorized.

## Live acceptance flows

At minimum, execute:

- Authentication and connection diagnosis.
- Project context and URL resolution.
- Project, folder, dataset, and view lifecycle.
- Real CSV upload and data query.
- Pipeline task create, preview, update, delete, and rerun.
- Cross-process draft enter, transformation, submit, and discard.
- Every transformation category with output-data assertions.
- Checkpoint, version, and data-check lifecycles.
- Job start, poll, completion, failure, and timeout.
- CSV export and atomic download.
- Safe connector, webhook, automation, workflow, parameter, snippet, trash,
  notification, annotation, derivative, and data-app operations when fixtures
  exist.
- Human and JSON command forms.

Do not live-test workspace deletion, account deletion, password changes,
billing mutations, user removal, outbound email, or external exports without
dedicated disposable fixtures and explicit test configuration.

Contract-test all unavailable external destinations. Run their live tests only
with dedicated credentials.

## Packaging and installer tests

- Build wheel and source distribution.
- Install the wheel into a clean environment.
- Verify dependency metadata and entry points.
- Verify bundled skill and completion.
- Verify upgrade and uninstall ownership behavior.
- Test POSIX installation on Linux and macOS.
- Test PowerShell installation on Windows.
- Verify checksums and provenance.
- Verify that software installation never requests Mammoth credentials.

## Documentation and skill tests

- Generate command reference and request schemas from manifests.
- Fail when generated documentation has a diff.
- Run Vale with the Mammoth STE profile.
- Extract help, prompts, warnings, errors, and hints for the same checks.
- Validate `SKILL.md` and `agents/openai.yaml`.
- Assert that the skill has only `name` and `description` frontmatter fields,
  uses the exact `mammoth-cli` folder name, stays under 500 lines, and has no
  unreferenced or duplicate resource files.
- Verify Codex, Claude Code, and Cursor user-scope and project-scope install,
  update, and uninstall paths in isolated homes.
- Forward-test the skill with fresh low-context agents for read, mutation,
  draft, export, error recovery, and cleanup tasks. Give them the raw skill and
  realistic requests. Do not give them expected commands or known defects.
- Fail a forward test when the agent emits a non-existent command, writes a
  secret to an argument, mixes human text into JSON stdout, skips a required
  confirmation, or cannot recover from an ambiguous project.
