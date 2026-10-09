# Pull data from a REST API (or Elasticsearch) on a schedule

REST connection -> dataset -> scheduled refresh. Every connector command runs
in a project (`--project PROJECT_ID`). The connector key is `generic_rest_api`.
Creates and refreshes are writes: get the user's confirmation first.

```bash
mammoth connector get generic_rest_api         # spec.connection_config / spec.data_source_config = the two shapes (empty on a backend without the spec change; use the shapes below)
mammoth connector connection list generic_rest_api   # reuse a connection if one fits
```

## 1. Connection

The body goes under `config`, with **flat** auth fields: `auth_type` (`none`,
`api_key`, `bearer`, `basic`), then `username` +
`password`, or `token`, or `key_name` + `key_value` + `inject_into`
(`header|query_param`). Do not send a nested `auth` object: an older backend
drops it and saves the connection as `auth_type: none` (the target API then
answers 401 at sample time); a backend with the fix rejects it. The base URL must be
a public host; localhost and private addresses are refused (SSRF guard).

```bash
# request.json (mode 0600): {"config": {"name": "My API", "base_url": "https://api.example.com/v1", "auth_type": "basic", "username": "u", "password": "p"}}
mammoth connector connection create generic_rest_api --input request.json --yes
```

The reply holds `identity_key`: that is CONNECTION_KEY below. To change
credentials later use `connector connection update ... --input` with
`{"credentials": {...}}`, not `config`. Error 4SUBS007 means the workspace plan
does not include this connector (or its paid addon is not active).

## 2. Try the data-source config (creates no dataset)

`query` is a **JSON string** (not an object) of the data-source config:
`endpoint_path`, `http_method` (`GET|POST`), `request_body`, `query_params`,
`data_root_path` (JSONPath to the records; `[*]` is supported), `pagination`,
`flatten_nested_json`, `max_pages`.

```bash
# sample.json: {"query": "{\"endpoint_path\": \"/posts\", \"data_root_path\": \"$\", \"max_pages\": 1}", "validate": false, "data_sample": true}
mammoth connector ds-config create generic_rest_api CONNECTION_KEY --input sample.json --yes
```

Read the column names from `data.data_sample.dataschema`. `ds-config list` and
`ds-config get` are not usable for this connector; find the result with
`dataset list`.

## 3. Dataset with a refresh schedule

`schedule_properties` and `recurrence_info` are required; without them the job
fails with "Invalid parameters". `on_refresh_action` is `replace` (swap the
rows each refresh) or `combine` (append: every refresh re-adds every row the
API returns, so rows duplicate).

```bash
# dataset.json
# {"ds_creation_type": "cloud", "dataset_spec": {"connector_key": "generic_rest_api",
#   "connection_key": "CONNECTION_KEY",
#   "query_properties": {"ds_name": "My data", "table_name": "posts", "query": "<same JSON string as step 2>"},
#   "schedule_properties": {"schedule_type": "moment", "first_pull_at": "now", "on_refresh_action": "replace"},
#   "recurrence_info": {"interval": 1, "start_at": "2027-01-01T02:00:00"}}}
mammoth dataset create --input dataset.json
```

## 4. Refresh automatically

```bash
# auto.json: {"description": "Refresh My data", "tasks": [{"task_type": "run_data_retrieval", "details": {"ds_details": [{"ds_id": DATASET_ID}]}}],
#   "conditions": [{"condition_type": "at_specific_time", "details": {"frequency": "daily", "interval": 1, "start_at": "2027-01-01T02:00:00Z"}}]}
mammoth automation create 'Refresh My data' --input auto.json --yes
mammoth automation update AUTOMATION_ID --yes --input '{"patch": [{"op": "command", "path": "run", "value": {}}]}'   # run now
```

More on automations: [recurring work](scheduling.md).

## Elasticsearch

Use the connection above with `base_url` of the cluster and `POST` on
`/INDEX/_search`. Name the fields you need in `_source`: a field such as
`asctime` ("2026-10-09 15:52:46,290", comma before the millis) breaks the load.

- Documents: `"request_body": {"size": 500, "_source": ["@timestamp", "task"]}`,
  `"data_root_path": "$.hits.hits[*]._source"`.
- Counts per bucket: `"request_body": {"size": 0, "aggs": {"c": {"composite": {"size": 10000, "sources": [...]}}}}`,
  `"data_root_path": "$.aggregations.c.buckets[*]"` gives columns `doc_count`,
  `key.<source>`.
