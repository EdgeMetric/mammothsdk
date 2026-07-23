# Mammoth CLI developer tasks.
#
# `make cli-docs-check` runs the documentation gates: regeneration-diff,
# Vale (pinned 3.15.1 in CI), the STE sentence checker, and link validation.

PY ?= python
VALE ?= vale
DOCS := docs

.PHONY: check lint type test docs cli-docs-check ste vale-docs links

check: lint type test cli-docs-check

lint:
	ruff check mammoth_cli/ tests/ scripts/

type:
	mypy mammoth_cli/

test:
	$(PY) -m pytest tests -m "not live" -q -p no:cacheprovider

docs:
	$(PY) scripts/gen_docs.py

cli-docs-check: ste vale-docs links
	$(PY) scripts/gen_docs.py --check

ste:
	$(PY) scripts/check_ste.py $(DOCS)/*.md

vale-docs:
	$(VALE) $(DOCS)/

# Fail on any Markdown link whose target file is missing (relative links only).
links:
	$(PY) scripts/check_links.py $(DOCS)
