# CLI recipes

These are discovery-led recipes, not prescribed workflows. Replace placeholders
only with IDs, display names, and fields returned by the immediately preceding
read/schema command. Every command is illustrative; piped output is JSON
without any flag.

Verify each successful mutation from a remote read, terminal job,
pipeline/task definition, or exported artifact. Retain only nonsecret IDs and
hashes; stop on ambiguous schemas, authorization errors, or unknown effects.

- [worked example: three CSVs to a per-region summary](end-to-end.md)
- [auth and scope](auth-scope.md)
- [files, datasets, views and settings](resources.md)
- [datasets in `need_action` or `needs_view` after upload](need-action.md)
- [typed transformations and drafts](transforms.md)
- [typed ETL discovery](typed-etl-discovery.md)
- [exports and artifacts](exports.md)
- [dashboards](dashboards.md)
- [recurring work: automations and schedules](scheduling.md)
- [trash, recovery and cleanup](cleanup.md)
- [deliverable retention and cleanup authorization](../retention.md)
