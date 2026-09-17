# CLI recipes

These are discovery-led recipes, not prescribed workflows. Replace placeholders
only with IDs, display names, and fields returned by the immediately preceding
read/schema command. Every command is illustrative and should use
`--output json --no-input`.

Each successful mutation must be verified from a remote read, terminal job,
pipeline/task definition, or exported artifact. Retain only nonsecret IDs and
hashes; stop on ambiguous schemas, authorization errors, or unknown effects.

- [auth and scope](auth-scope.md)
- [files, datasets, views and settings](resources.md)
- [typed transformations and drafts](transforms.md)
- [exports and artifacts](exports.md)
- [dashboards](dashboards.md)
- [trash, recovery and cleanup](cleanup.md)
