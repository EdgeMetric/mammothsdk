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
