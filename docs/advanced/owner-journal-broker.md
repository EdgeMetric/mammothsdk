# Owner journal broker

`scripts/owner_journal_broker.py` is a small owner-side component, separate
from the Mammoth CLI and from an agent workspace. It persists a fixed
workspace/project scope and operation allowlist once, accepts only a
secret-free intent id, operation, fixed scope, and payload SHA-256 digest, and
appends an fsynced intent record before invoking an owner-supplied transport
callback. Credentials and request payloads are deliberately out of scope.

When a callback returns, the broker appends an fsynced receipt containing only
the outcome and an optional job/resource handle. A repeated intent with a
receipt returns that receipt without another dispatch. An intent without a
receipt raises `ReconciliationRequired`; it never automatically replays.

This gives at-most-one dispatch by this broker instance per intent id. It is
not exactly-once backend execution: a crash after a backend commit and before
the receipt leaves an ambiguity that requires independent reconciliation or a
backend-supported idempotency key. An advisory owner-journal lock serializes
submissions sharing that journal. On Linux it fsyncs the parent directory after
creating the journal root, policy, or journal file; other platforms do not get
that directory-entry durability guarantee. The offline tests inject both crash
boundaries and verify no automatic replay. An intent ID is bound to the full
secret-free invocation fingerprint, so reusing it with a different operation,
scope, or payload digest is rejected.

## Fixed subprocess transport

`OwnerSubprocessSender` is the optional owner-side transport for a journal
broker. It accepts only a broker `Invocation`: its CLI executable and SHA-256
artifact digest, profile name, private configuration directory, workspace,
project, operation command, target, resource, input, confirmation decision,
and time budget are all fixed by `OwnerSubprocessPolicy`. It never accepts an
agent shell string, arbitrary environment, extra arguments, or destination.
The only supported commands are complete frozen operations selected by name;
agent-provided request bodies and external destinations are intentionally
unsupported in this slice.

The sender verifies the executable digest immediately before execution and
uses a minimal owner environment. It returns only redacted `ok`, `exit_status`,
`stdout`, and `stderr` observations (plus broker outcome fields); neither the
profile configuration nor its secrets enter the journal receipt.

Operations are one-shot by default: once a frozen operation has an intent,
another intent ID cannot dispatch it. The owner must explicitly mark a known
read operation repeatable. Fixed inputs are optional, but when used must be
private owner-controlled files outside the agent workspace with an approved
SHA-256 that is rechecked immediately before dispatch. Exit status 7 and a
structured `outcome_unknown` envelope remain `outcome_unknown`; the broker
does not reinterpret them as safe failures or replay them. Any other nonzero
result is also `outcome_unknown` unless the original private CLI error envelope
explicitly establishes `failed`/`not_started` or an authorization/usage-style
pre-dispatch failure. Classification parses the private stream before applying
presentation redaction, but does not persist that raw stream.

Output redaction is best-effort presentation hygiene, not credential isolation.
The journal never stores subprocess stdout or stderr, and protected profile
contents are kept outside the agent workspace; a production deployment still
needs an OS/process boundary appropriate to its credential store.

## Unix socket front-end

`OwnerBrokerSocketServer` is a Linux/Unix-only local front-end for a broker and
frozen sender. Its private owner-controlled directory and socket are mode 0700
and 0600. A request has exactly four strings: opaque trial handle, opaque
intent ID, allowlisted operation name, and payload digest. It cannot carry
argv, a profile/config path, credentials, environment, project/workspace, or
external destination. Invalid, oversized, malformed, and policy-denied frames
receive a generic denial response; an idle partial frame receives the same
response after a bounded receive timeout.

The successful response contains the durable receipt and, only for the initial
dispatch, a redacted process observation. Repeated receipts do not rerun the
sender or reconstruct output. Top-level `ok: true` means the broker accepted
and journaled the request, not that the remote operation succeeded; inspect
the receipt outcome and observation `ok` separately. Observation stdout/stderr
are capped with explicit `*_truncated` flags, so they never claim completeness.
This is not provider attestation, a credential
vault, or live qualification; deployment still needs peer authentication and
an appropriate protected-process boundary for its operating system.
