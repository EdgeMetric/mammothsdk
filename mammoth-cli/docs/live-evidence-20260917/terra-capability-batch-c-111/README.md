# Capability batch C — bounded read evidence

Date: 2026-09-17. Scope: approved saved `expanded-live` profile, workspace 4,
project 3. The client was an isolated public PyPI Python 3.14 installation of
`mammoth-cli` 1.1.11 with `mammoth-io` 0.7.1. `pip check` and `doctor` returned
success. This record contains no profile material, response body, filename, or
live resource ID.

All commands used `--output json --no-input --profile expanded-live`. The
locally generated schema documents marked every listed command as `effects:
read` before its live use. The first batch-list form established that its first
positional argument is a dataset parent: an attempted retained-project value
selected a different dataset and returned a scoped 403. It made no mutation.
The subsequent calls used retained dataset 29 and explicit project 3.

| Read | Sanitized invocation | Exit | Structural result | Raw envelope SHA-256 |
| --- | --- | ---: | --- | --- |
| batch list | `batch list 29 --project 3` | 0 | one batch; no pending batches | `81ac96698b4b956866f54547ee4605c31c2067d812ce36d5d64a2b7d27560333` |
| batch get | `batch get 29 <observed-batch-id> --project 3` | 0 | top-level `batch` object | `39dc9d1fb110fb73b79ea60963171f017f64656979e72378a821378b18f5f5cd` |
| dataset batch-data | `dataset batch-data 29 <observed-batch-id> --project 3` | 0 | 50-row bounded page; four metadata entries; paging present | `903ba4961966cacb5c115eaf68b5f75678881288cd43297ace61a0c3a9beb088` |
| file list | `file list --project 3` | 0 | 12 files; one observed ID selected | `2431e55ca27a6fbb675f42ebc2559e5a913085fcb1338f394800451d561c00b6` |
| file get | `file get <observed-file-id> --project 3` | 0 | metadata keys only; no content download | `1845ce69819421be46a900e56196cbbdb0e88e664d112abde1aa813e4b7f5d04` |
| project resource-status | `project resource-status 3` | 0 | `app_update` and `status`; no dependency resource ID | `a87b5932057d889d9b1d948ac1248bb982a29cbf6beee1cedb8e9b2d5d761f0a` |

No job handle appeared in the approved discovery responses, so `job get-many`
and `job get` were not called. `project resource-dependencies` requires a
nonempty observed resource-ID list; resource status did not supply one, so it
was not called. No ID, endpoint, or payload was guessed.

## Schema hashes

| Command | Schema SHA-256 |
| --- | --- |
| `job get-many` | `84d8171e53fc3c0534dd2b799f4e64f92fedfb590977b103292029427cd3e029` |
| `job get` | `527648e20a29dc851a70e85656a828300cb165c5579c74fda83958e84d79121f` |
| `batch list` | `d4a8e515ea9ffe050b2fbd5e67a61d0675378d6026960023e7166a85a1556f81` |
| `batch get` | `e60b617d40775e66927c2cc6cef37362f35ef03907a940197870410d43831a84` |
| `dataset batch-data` | `0a83384c78137c6c80127a4e7e242a21d69f3cb1ea4ca435db2695088fc5c1bf` |
| `file list` | `56566593741b59551638d38fd15a9a4767210a3067df0515ebdda7ebbfc9a497` |
| `file get` | `a532f8c7dad44aea0da1dff2e3682d24c059f882c83dd7460eef7633720b1283` |
| `project resource-dependencies` | `365549cfa58576349def8a89b9f7c5e3e147c2e31fb1c3867003c81df040587f` |

## Matrix proposals (not applied)

Propose `Partial` only for REL-194 (`batch get`), REL-195 (`dataset
batch-data`), and REL-222 (`file get`): each has one bounded, read-only success
against an ID discovered in the immediately preceding scoped list. These are
not Full claims: pagination, empty/error variants, lifecycle behavior, content
download semantics, and other IDs remain unqualified.

Keep REL-134 (`job get-many`), REL-135 (`job get`), and REL-227 (`project
resource-dependencies`) `Unassessed`. Their required identifiers were not
observed, and no request was invented merely to collect evidence.
