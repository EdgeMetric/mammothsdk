# Mammoth CLI parity report

Generated from the reviewed manifests. Do not edit by hand.

## OpenAPI snapshot

- Source: `https://app.mammoth.io/api/v2/docs/openapi.json`
- SHA-256: `609edd7d3d613d73ef3de5670d6916c1bcc6252833283d2f0b6fad6ae58b82dd`
- OpenAPI version: `3.1.0`
- Paths: `465`
- Operations: `651`
- Schemas: `1246`

## Operation dispositions

| Disposition | Count |
|---|---:|
| command | 598 |
| alias | 2 |
| protocol_only | 11 |
| internal_only | 40 |
| deprecated | 0 |
| server_unavailable | 0 |
| unmapped | 0 |
| **total** | **651** |

## Public SDK method parity

- Total public methods: `801`
- With canonical command: `712`
- Alias of another command: `38`
- Reviewed SDK-only exemptions: `51`

## Command surface

- Canonical + convenience commands: `784`

### Mutation classes

| Mutation class | Count |
|---|---:|
| read | 309 |
| benign_mutation | 227 |
| reversible_pipeline | 40 |
| destructive | 67 |
| high_impact | 99 |
| external_effect | 42 |

### Acceptance evidence

| Evidence class | Count |
|---|---:|
| contract_only_high_impact | 169 |
| contract_only_no_disposable_fixture | 148 |
| live_disposable_project | 205 |
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

