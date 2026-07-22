# Expected red-first baseline (Phase 1 parity freeze)
#
# Generated after committing the manifests and red-first tests.
# Each failure below is red ONLY because the corresponding typed SDK
# method (Phase 2) or CLI runtime/handler (Phase 3+) is not yet built.
# No failure indicates a manifest or inventory defect.
#
FAILED tests/contract/test_parity_manifest.py::test_every_command_disposition_has_typed_sdk_symbol - AssertionError: unresolved sdk_symbol mammoth.api.workspaces.WorkspacesAPI.accept_invite
FAILED tests/contract/test_runtime_contract.py::test_every_manifest_command_is_registered - Failed: CLI runtime not implemented yet: No module named 'mammoth_cli.app'
FAILED tests/contract/test_runtime_contract.py::test_command_paths_match_manifest_exactly - Failed: CLI runtime not implemented yet: No module named 'mammoth_cli.app'
FAILED tests/contract/test_runtime_contract.py::test_capability_registry_matches_manifests - ModuleNotFoundError: No module named 'mammoth_cli.commands.capability'
FAILED tests/contract/test_runtime_contract.py::test_schema_registry_matches_request_models - ModuleNotFoundError: No module named 'mammoth_cli.commands.schema'
FAILED tests/contract/test_runtime_contract.py::test_every_command_supports_json_no_input - ModuleNotFoundError: No module named 'mammoth_cli.testing'
FAILED tests/contract/test_runtime_contract.py::test_machine_stdout_contains_data_only - ModuleNotFoundError: No module named 'mammoth_cli.testing'
FAILED tests/contract/test_runtime_contract.py::test_agent_errors_include_executable_recovery - ModuleNotFoundError: No module named 'mammoth_cli.errors.envelope'
FAILED tests/contract/test_runtime_contract.py::test_agent_mode_never_prompts_or_pages - ModuleNotFoundError: No module named 'mammoth_cli.output.policy'
FAILED tests/contract/test_runtime_contract.py::test_timeout_results_include_resumable_identity - ModuleNotFoundError: No module named 'mammoth_cli.errors.envelope'
FAILED tests/contract/test_sdk_foundation.py::test_client_has_public_close_and_context_manager - AssertionError: MammothClient needs a public close()
FAILED tests/contract/test_sdk_foundation.py::test_public_dataview_to_dataset_resolver_exists - AssertionError: a public typed dataview->dataset resolver must exist
FAILED tests/contract/test_sdk_foundation.py::test_draft_state_survives_process_boundaries - AssertionError: PipelineAPI needs a public server-backed draft status reader
FAILED tests/contract/test_sdk_foundation.py::test_typed_pagination_page_is_public - Failed: a public typed pagination Page model must exist
14 failed, 31 passed in 4.94s
