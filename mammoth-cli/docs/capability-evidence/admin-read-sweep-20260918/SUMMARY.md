# Admin/billing read-only sweep — release, CLI 2.0.15

30 GET-only command ids from `COMMANDS.txt`, run read-only with the published CLI 2.0.15 (`--profile release`, `--project 3` where a project is required). Results in `results.jsonl`.

The CLI classes every `support.*` and `billing.*` command as `confirm_target`, so even these GETs refuse without `--yes --confirm 4`. The delegated agent recorded those refusals (`confirmation_required`, exit 2, no request sent); the gated GETs were then re-run by the operator with the confirmation flags, reads only. No mutating command was run at any point.

## Verdict counts

| Verdict | Count |
|---|---|
| ok | 13 |
| forbidden | 6 |
| backend_error | 6 |
| blocked_missing_fixture | 5 |

## Non-ok commands

- `client-app.list` — HTTP 403 `4GENR012` INVALID_TOKEN_FOR_CLIENT_APPS (API keys cannot read client apps); `client-app.get` blocked (no key observed).
- `billing.stripe.get` — HTTP 403 `4PERM001` PERMISSION_UNDEFINED.
- `support.plan.get 4`, `support.workspace.get 4`, `support.subscription.get 4`, `support.workspace.user.list 4` — HTTP 403 (`4PERM002` / `4PERM001`) although the corresponding list routes succeed.
- `billing.chargebee-plan` — HTTP 400 `4SUBS014` Chargebee plan not found (workspace not on Chargebee).
- `billing.stripe.preview-invoice` — HTTP 400 `4SUBS037`; `billing.stripe.upcoming-invoice` — HTTP 400 `4SUBS074` (no active Stripe subscription); `billing.stripe.usage` — HTTP 400 `5GENR010` UNKNOWN_ERROR.
- `billing.invoice.list` — HTTP 500 empty body; `billing.invoice.get` blocked (no invoice id).
- `schedule.list --project 3` — HTTP 400 `5GENR011` NOT_IMPLEMENTED; `schedule.get` blocked.
- `automation.get` blocked (`automation list --project 3` empty); `agent.session.messages` blocked (`agent session list` empty).

## Observation for the CLI

`support workspace list` returns a bare JSON array; the SDK wraps it as `{"status_code": 200, "response": [...]}`. Functional, but the CLI could unwrap it.

Statement: no create/update/trash/delete command was executed; the only flags added were `--yes --confirm 4` on GET routes.
