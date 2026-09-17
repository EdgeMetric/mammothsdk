# Workflow graph navigation projection

`workflow graph` preserves the backend graph response and appends
`cli_navigation` (or the first free deterministic `cli_navigation_vN` key).
The projection is version 1 and only recognizes `nodes` entries with `id` and
`edges` entries with `source`/`target`; it never fetches additional resources.

`complete: false` means navigation is incomplete. `unknown_shape`,
`invalid_node`, `duplicate_node`, `invalid_edge`, and
`unresolved_edge_endpoint` are structural limits, not authorization claims.
