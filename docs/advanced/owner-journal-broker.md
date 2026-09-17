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
