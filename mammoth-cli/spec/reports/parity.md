# Mammoth CLI parity report

Generated from the reviewed manifests. Do not edit by hand.

## OpenAPI snapshot

- Source: `https://app.mammoth.io/api/v2/docs/openapi.json`
- SHA-256: `c2f78e5858044fae2d739a53defbaaddeae52ed79d6e38c4431fce3199547782`
- OpenAPI version: `3.1.0`
- Paths: `426`
- Operations: `603`
- Schemas: `1152`

## Operation dispositions

| Disposition | Count |
|---|---:|
| command | 567 |
| alias | 2 |
| protocol_only | 11 |
| internal_only | 23 |
| deprecated | 0 |
| server_unavailable | 0 |
| unmapped | 0 |
| **total** | **603** |

## Public SDK method parity

- Total public methods: `765`
- With canonical command: `675`
- Alias of another command: `38`
- Reviewed SDK-only exemptions: `52`

## Command surface

- Canonical + convenience commands: `740`

### Mutation classes

| Mutation class | Count |
|---|---:|
| read | 288 |
| benign_mutation | 214 |
| reversible_pipeline | 39 |
| destructive | 65 |
| high_impact | 97 |
| external_effect | 37 |

### Acceptance evidence

| Evidence class | Count |
|---|---:|
| contract_only_high_impact | 162 |
| contract_only_no_disposable_fixture | 136 |
| live_disposable_project | 201 |
| live_read_only | 241 |

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

