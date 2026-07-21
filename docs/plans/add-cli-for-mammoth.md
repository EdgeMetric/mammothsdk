# Mammoth CLI implementation plan

Status: implementation plan audited and ready; pre-code parity freeze and
implementation not started

Target branch: `add-cli-for-mammoth`

Plan owner: primary implementation agent

Last audited: 2026-07-21

This document is the entry point for the complete Mammoth CLI plan. Read every
linked document before implementation. The linked documents are normative.

## Goal

Build a typed, production-ready `mammoth` command that exposes all applicable
production operations in the official Mammoth OpenAPI document. Add missing
typed operations to `mammoth-io` before the CLI uses them. The CLI must not
implement a second Mammoth HTTP client.

The CLI must work for developers, shell scripts, CI, Codex, Claude Code,
Cursor, and other agents. It must include quick installation, complete
documentation, and an installable agent skill.

## Authoritative sources

Use these sources in this order:

1. Production OpenAPI: <https://app.mammoth.io/api/v2/docs/openapi.json>
2. Public typed `mammoth-io` behavior and tests
3. Guarded tests against the dedicated Mammoth test tenant
4. Product documentation and the transformation manifesto

The OpenAPI snapshot inspected on 2026-07-21 has:

- OpenAPI version `3.1.0`.
- API version `0.1.0`.
- 234 paths.
- 376 HTTP operations.
- SHA-256 `6b2c8647afa9f83c7a742e4279f0407f33bd1325f43acb1efa2cf411d64acb54`.

The repository audit found 242 public SDK class methods. SDK parity is not the
same as Mammoth API parity. Every OpenAPI operation and public SDK method must
have an explicit disposition in the generated parity manifest.

## Document index

1. [Product contract and decisions](add-cli-for-mammoth/01-product-contract.md)
2. [Architecture and CLI contract](add-cli-for-mammoth/02-architecture-and-cli-contract.md)
3. [OpenAPI, SDK, and command parity](add-cli-for-mammoth/03-operation-parity.md)
4. [TDD and acceptance plan](add-cli-for-mammoth/04-tdd-and-acceptance.md)
5. [Autonomous implementation runbook](add-cli-for-mammoth/05-implementation-runbook.md)
6. [Audit, notes, blockers, and TODO ledger](add-cli-for-mammoth/06-audit-notes-todo.md)
7. [Packaging, installers, release, and skill](add-cli-for-mammoth/07-packaging-install-skill.md)
8. [Authentication profiles and live-test operations](add-cli-for-mammoth/08-auth-and-live-operations.md)
9. SDK command catalogs: [resources](add-cli-for-mammoth/09-sdk-resource-command-catalog.md),
   [views and transforms](add-cli-for-mammoth/10-sdk-view-transform-command-catalog.md),
   and [I/O and integrations](add-cli-for-mammoth/11-sdk-io-integration-command-catalog.md)
10. [Complete 376-operation OpenAPI inventory](add-cli-for-mammoth/12-openapi-operation-inventory.md)
11. [Complete 242-method public SDK inventory](add-cli-for-mammoth/13-sdk-public-method-inventory.md)
12. [SDK client and AI command catalog](add-cli-for-mammoth/14-sdk-client-ai-command-catalog.md)

## Mandatory implementation order

Do not implement feature commands out of order.

1. Commit this plan.
2. Complete the pre-code specification freeze: fetch and pin the OpenAPI
   snapshot.
3. Generate the normalized 376-operation inventory.
4. Generate the 242-method SDK inventory.
5. Create the operation-disposition and command-spec manifests.
6. Have the primary agent review and sign every disposition and exact command
   specification. A worker must not resolve an ambiguous API contract by
   guessing.
7. Write the parity, schema, registration, safety, and SDK-call tests.
8. Confirm that the new tests fail for the expected missing work. This is the
   first code change after the specification freeze.
9. Add or repair typed public SDK operations.
10. Implement the shared CLI runtime.
11. Implement command batches only against green SDK contracts.
12. Complete live tests, documentation, skills, installers, and release checks.

No SDK or CLI production handler may start before steps 1 through 8 are
complete. Steps 2 through 7 are specification and test-contract work, not
feature implementation.

Planning validation is complete. Live view and transformation validation is
blocked by the current test principal's dataset permissions. Do not claim
operational parity or full acceptance until that blocker is cleared.

## Top-level completion checklist

- [ ] This plan is committed as the first branch change.
- [ ] The OpenAPI and SDK inventories are reproducible.
- [ ] All 376 OpenAPI operations have reviewed dispositions.
- [ ] All 242 SDK methods have canonical-command or alias records.
- [ ] Every CLI operation has an exact typed command specification.
- [ ] All red-first contract tests exist before handlers.
- [ ] Missing public SDK operations are implemented and tested.
- [ ] No CLI Mammoth request bypasses `mammoth-io`.
- [ ] Authentication requires only key, secret, and workspace ID.
- [ ] The default server prefix is `app-eu`.
- [ ] Human and machine output contracts pass.
- [ ] Secret and destructive-operation audits pass.
- [ ] Linux, macOS, and Windows pass on the supported Python matrix (currently
  3.12, 3.13, and 3.14).
- [ ] Dedicated-tenant live tests and the leak audit pass.
- [ ] Documentation passes the Mammoth STE house profile.
- [ ] The bundled agent skill passes validation and forward tests.
- [ ] Wheel, source distribution, and quick installers pass.
- [ ] No package or release is published without separate authorization.

## Definition of done

The work is complete only when the generated parity report contains no
unreviewed operation, no applicable production operation lacks a typed SDK
method and CLI command, and no public SDK method lacks a canonical command or
documented alias. All required tests and live gates must pass. The primary
agent must update the audit and TODO ledger before handoff.
