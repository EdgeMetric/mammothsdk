# Mammoth CLI parity report

Generated from the reviewed manifests. Do not edit by hand.

## OpenAPI snapshot

- Source: `https://app.mammoth.io/api/v2/docs/openapi.json`
- SHA-256: `c228e9d59c4263fc746ab8873ae6a3d87c25171b6bc4e6e313f685dd0083da29`
- OpenAPI version: `3.1.0`
- Paths: `530`
- Operations: `728`
- Schemas: `1354`

## Operation dispositions

| Disposition | Count |
|---|---:|
| command | 643 |
| alias | 2 |
| protocol_only | 11 |
| internal_only | 40 |
| deprecated | 0 |
| server_unavailable | 0 |
| unmapped | 32 |
| **total** | **728** |

## Public SDK method parity

- Total public methods: `851`
- With canonical command: `760`
- Alias of another command: `38`
- Reviewed SDK-only exemptions: `53`

## Command surface

- Canonical + convenience commands: `830`

### Mutation classes

| Mutation class | Count |
|---|---:|
| read | 331 |
| benign_mutation | 228 |
| reversible_pipeline | 40 |
| destructive | 67 |
| high_impact | 122 |
| external_effect | 42 |

### Acceptance evidence

| Evidence class | Count |
|---|---:|
| contract_only_high_impact | 214 |
| contract_only_no_disposable_fixture | 148 |
| live_disposable_project | 206 |
| live_read_only | 262 |

## Protocol-only operations

- `GET /health` — Health probe, not a user command.
- `GET /unsubscribe` — Email unsubscribe browser link, not an API action.
- `GET /workspaces/{workspace_id}/projects/{project_id}/ai/connector-chat/oauth-callback` — OAuth2 authorization-code browser callback.
- `POST /dashboards/url/{url}/track-heartbeat` — Published-dashboard viewer telemetry.
- `POST /dashboards/url/{url}/track-view` — Published-dashboard viewer telemetry.
- `POST /gdpr_hooks/shopify/customers/data_request` — Shopify GDPR privacy webhook.
- `POST /gdpr_hooks/shopify/customers/redact` — Shopify GDPR privacy webhook.
- `POST /gdpr_hooks/shopify/shop/redact` — Shopify GDPR privacy webhook.
- `POST /gdpr_hooks/{integration_name}/deauthorization` — Provider deauthorization callback.
- `POST /subscription/stripe/webhook` — Inbound Stripe provider webhook.
- `POST /workspaces/{workspace_id}/mm-ue` — Mammoth user-event telemetry ingest (mm-ue).

