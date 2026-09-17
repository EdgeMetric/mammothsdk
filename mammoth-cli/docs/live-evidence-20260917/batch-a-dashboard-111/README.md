# Batch A dashboard read-only evidence — published 1.1.11

Captured 2026-09-17 against the approved `expanded-live` profile, workspace 4,
project 3, using retained dashboard48 only. Environment: published
`mammoth-cli==1.1.11` and `mammoth-io==0.7.1`, Python 3.14.4. No resources
were created or mutated, and no secrets or raw payloads are included.

Artifact hashes: CLI wheel
`25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`; SDK
wheel `41e606f1ce4705917449f6f926936abfb1f6e776b9339a42848370456fa7bf6e`.

Schema discovery succeeded for all six requested routes. `dashboard.style.token.list`
requires an opaque style ID and `dashboard.suggestion.list` requires a dataview
ID; those cases were skipped without guessing IDs. `dashboard.style.default.get`
was safe to invoke but returned a structured API `ValidationError`, so it remains
Unassessed.

Bounded positive proposals:

- REL-109 `dashboard.canvas.get 48`: exit 0; returned a canvas object with one
  page, title `Terra OWID five-source reference`, and retained source dataview46.
- REL-118 `dashboard.qa.session.list 48`: exit 0; semantic result had empty
  `mine` and `shared` session lists.
- REL-120 `dashboard.qa.settings.get 48`: exit 0; returned
  `allow_viewer_qa=true`, `can_manage=true`, `public_link=false`.

These are bounded single-dashboard reads and support Partial proposals only;
they do not establish Full support.
