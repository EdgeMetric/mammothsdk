# Installation

## Requirements

- Python 3.12, 3.13, or 3.14
- pip or Poetry package manager

## Install from PyPI

```bash
pip install mammoth-io==0.7.0
```

Or with Poetry:

```bash
poetry add mammoth-io==0.7.0
```

## Dependencies

The SDK has two runtime dependencies, installed automatically:

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.32,<3 | HTTP client for API requests |
| `pydantic` | >=2.10,<3 | Data validation and response models |

## Development installation

Clone the repository and install with dev dependencies:

```bash
git clone https://github.com/EdgeMetric/mammothsdk.git
cd mammothsdk
poetry install
```

The development dependencies are a Poetry group in this repository, not a
published `dev` extra. A PyPI install supplies only runtime dependencies.

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
