# Developer Guide

Development workflows for the mammoth-io SDK.

## Setup

```bash
git clone git@github.com:EdgeMetric/mm-pysdk.git
cd mm-pysdk
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
# or with poetry:
poetry install
```

## Running Tests

```bash
# Unit tests (no API calls)
pytest tests/unit/ -v

# Integration tests (requires live API credentials)
pytest tests/integration/ -v

# With coverage
pytest tests/unit/ --cov=mammoth --cov-report=term-missing
```

## Linting & Formatting

```bash
# Format
black mammoth/ tests/

# Lint
ruff check mammoth/

# Lint with auto-fix
ruff check mammoth/ --fix

# Type check
mypy mammoth/
```

## Project Structure

```
mammoth/                  # SDK package (published to PyPI)
  __init__.py             # Public API — all user-facing exports
  client.py               # MammothClient entry point
  view.py                 # View + ViewExport domain objects
  condition.py            # Condition builder with & | ~ operators
  models/pipeline.py      # Enums, dataclasses, Pydantic response models
  _mixins/                # View transformation methods (one file per category)
  _param_templates.py     # Low-level payload builders
  _expression_parser.py   # Math expression → token list parser
  api/                    # REST API sub-clients (CRUD)
  helpers.py              # URL parser, utilities
  exceptions.py           # Exception hierarchy
  py.typed                # PEP 561 marker for type checkers

mammoth-mcp/              # MCP server (separate package, not published here)
tests/
  unit/                   # Fast, no network — mock everything
  integration/            # Live API tests against release.mammoth.io
```

## Publishing to PyPI

### Prerequisites

1. [Create a PyPI account](https://pypi.org/account/register/)
2. [Create an API token](https://pypi.org/manage/account/token/) (scope: project `mammoth-io`)
3. Store the token — you'll use it during upload

### Test on TestPyPI first

```bash
# Build
poetry build
# or: python -m build

# Inspect the wheel to verify contents
unzip -l dist/mammoth_io-*.whl | head -30

# Upload to TestPyPI
poetry publish -r testpypi
# or: twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mammoth-io
python -c "from mammoth import MammothClient; print('OK')"
```

### Publish to PyPI

```bash
# Bump version in pyproject.toml
# e.g. version = "0.2.1"

# Build fresh
rm -rf dist/
poetry build

# Upload to PyPI
poetry publish
# or: twine upload dist/*

# Verify
pip install mammoth-io --upgrade
python -c "from mammoth import MammothClient, __version__; print(__version__)"
```

### Using twine instead of poetry

If you prefer twine (works without poetry installed):

```bash
pip install build twine

python -m build                  # creates dist/
twine check dist/*               # validates metadata
twine upload --repository testpypi dist/*   # TestPyPI
twine upload dist/*              # PyPI (production)
```

### Configure credentials

**Poetry** — run once:
```bash
poetry config pypi-token.pypi pypi-XXXX...
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi pypi-XXXX...
```

**Twine** — create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-XXXX...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-XXXX...
```

### Release checklist

1. All tests pass: `pytest tests/unit/ -q`
2. Type check clean: `mypy mammoth/`
3. Lint clean: `ruff check mammoth/`
4. Bump version in `pyproject.toml` and `mammoth/__init__.py`
5. Build: `poetry build`
6. Inspect wheel: `unzip -l dist/mammoth_io-*.whl` — verify `py.typed` is included
7. Test on TestPyPI first
8. Publish to PyPI
9. Tag the release: `git tag v0.2.1 && git push --tags`

## Version Bumping

Version is set in two places — keep them in sync:
- `pyproject.toml` → `version = "0.2.0"`
- `mammoth/__init__.py` → `__version__ = "0.2.0"`

## Adding a New Transformation

1. Add the method to the appropriate mixin in `mammoth/_mixins/`
2. If it takes structured parameters, add a dataclass to `mammoth/models/pipeline.py`
3. Export the dataclass from `mammoth/__init__.py`
4. Add a payload builder to `mammoth/_param_templates.py`
5. Add unit tests to `tests/unit/test_transformations.py`
6. Add an integration test to `tests/integration/test_transformations.py`
