# Mammoth CLI parity report

Generated from the reviewed manifests. Do not edit by hand.

## OpenAPI snapshot

- Source: `https://app.mammoth.io/api/v2/docs/openapi.json`
- SHA-256: `0c7c777f36cd81f48fe676c04f5cb06c74163081c0870c775a57da8dff4a5f04`
- OpenAPI version: `3.1.0`
- Paths: `234`
- Operations: `376`
- Schemas: `770`

## Operation dispositions

| Disposition | Count |
|---|---:|
| command | 364 |
| alias | 1 |
| protocol_only | 11 |
| deprecated | 0 |
| server_unavailable | 0 |
| **total** | **376** |

## Public SDK method parity

- Total public methods: `242`
- With canonical command: `184`
- Alias of another command: `54`
- Reviewed SDK-only exemptions: `4`

## Command surface

- Canonical + convenience commands: `435`

### Mutation classes

| Mutation class | Count |
|---|---:|
| read | 137 |
| benign_mutation | 115 |
| reversible_pipeline | 35 |
| destructive | 43 |
| high_impact | 90 |
| external_effect | 15 |

### Acceptance evidence

| Evidence class | Count |
|---|---:|
| contract_only_high_impact | 117 |
| live_disposable_project | 172 |
| live_read_only | 146 |

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

