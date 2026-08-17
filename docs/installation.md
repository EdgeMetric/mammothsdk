# Installation

## Requirements

- Python 3.12, 3.13, or 3.14 (the package declares `>=3.12,<3.15`)
- pip or Poetry package manager

The SDK and `mammoth-cli` ship from the same monorepo and deliberately support
the same interpreters, so a machine that can run one can run the other.

## Install from PyPI

```bash
pip install mammoth-io
```

Or with Poetry:

```bash
poetry add mammoth-io
```

Install the latest release rather than pinning here. If your project needs a
pin, pin it in your own dependency file against the version you tested.

## Dependencies

The SDK has two runtime dependencies, installed automatically:

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | `>=2.32,<3` | HTTP client for API requests |
| `pydantic` | `>=2.10,<3` | Data validation and response models |

These are ranges rather than exact pins on purpose: as a library, `mammoth-io`
has to compose with whatever versions the consuming application already pins.

## Development installation

Clone the repository and install with dev dependencies:

```bash
git clone https://github.com/EdgeMetric/mammothsdk.git
cd mammothsdk
poetry install
```

Or install the dev extras via pip:

```bash
pip install mammoth-io[dev]
```

### Dev tools

The project uses these development tools:

| Tool | Purpose |
|------|---------|
| `ruff` | Linting and import sorting |
| `black` | Code formatting |
| `mypy` | Static type checking |
| `pytest` | Test framework |
| `pytest-cov` | Coverage reporting |

Run the dev toolchain:

```bash
# Lint
ruff check mammoth/

# Format
black mammoth/

# Type check
mypy mammoth/

# Test
pytest
```

## Verify installation

After installation, verify the SDK is working:

```python
from mammoth import MammothClient

print("Mammoth SDK installed successfully!")
```

## Next steps

- [Quick Start Guide](quick-start.md) -- create your first client and apply transformations
- [Authentication](authentication.md) -- set up API credentials
