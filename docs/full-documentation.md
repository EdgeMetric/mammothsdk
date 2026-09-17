# Mammoth Analytics Python SDK — Complete Documentation

> Official Python SDK for the Mammoth Analytics platform. Build data pipelines, apply transformations, and export results from Python.

> This file is auto-generated from the MkDocs source. Run `python scripts/build_full_docs.py` to regenerate.


# Table of Contents

- [Home](#home)
  - [Features](#features)
  - [Quick example](#quick-example)
  - [Documentation](#documentation)
  - [Version information](#version-information)
  - [Support](#support)
- [Installation](#installation)
  - [Requirements](#requirements)
  - [Install from PyPI](#install-from-pypi)
  - [Dependencies](#dependencies)
  - [Development installation](#development-installation)
    - [Dev tools](#dev-tools)
  - [Verify installation](#verify-installation)
  - [Next steps](#next-steps)
- [Quick Start](#quick-start)
  - [1. Install the SDK](#1-install-the-sdk)
  - [2. Get your API credentials](#2-get-your-api-credentials)
  - [3. Create a client](#3-create-a-client)
  - [4. Get a View](#4-get-a-view)
  - [5. Apply transformations](#5-apply-transformations)
  - [6. Export data](#6-export-data)
  - [7. Work with resources](#7-work-with-resources)
  - [Complete example](#complete-example)
  - [Key concepts](#key-concepts)
  - [Next steps](#next-steps)
- [Authentication](#authentication)
  - [Getting API credentials](#getting-api-credentials)
  - [Client setup](#client-setup)
    - [Direct authentication](#direct-authentication)
    - [Environment variables (recommended)](#environment-variables-recommended)
    - [Configuration file](#configuration-file)
  - [How authentication works](#how-authentication-works)
  - [Error handling](#error-handling)
  - [Security best practices](#security-best-practices)
  - [Next steps](#next-steps)
- [Client](#client)
  - [Quick start](#quick-start)
  - [Context manager](#context-manager)
  - [Sub-clients](#sub-clients)
    - [Core data sub-clients](#core-data-sub-clients)
    - [Additional sub-clients](#additional-sub-clients)
  - [Full API Reference](#full-api-reference)
    - [ViewsResource](#viewsresource)
  - [Error handling](#error-handling)
  - [See also](#see-also)
- [Views](#views)
  - [Getting a View](#getting-a-view)
  - [Properties](#properties)
  - [Draft mode](#draft-mode)
    - [draft() (context manager)](#draft-context-manager)
    - [Explicit draft workflow](#explicit-draft-workflow)
  - [Full API Reference](#full-api-reference)
  - [Exports](#exports)
  - [See also](#see-also)
- [Conditions](#conditions)
  - [Quick examples](#quick-examples)
  - [Operator overloading](#operator-overloading)
  - [Using conditions with View methods](#using-conditions-with-view-methods)
    - [filter_rows](#filter_rows)
    - [set_values](#set_values)
    - [math, combine_columns, and other methods](#math-combine_columns-and-other-methods)
  - [All operators](#all-operators)
  - [Full API Reference](#full-api-reference)
  - [See also](#see-also)
- [Enums & Data Classes](#enums-data-classes)
  - [Enums](#enums)
  - [Data Classes](#data-classes)
  - [See also](#see-also)
- [Exceptions](#exceptions)
  - [Hierarchy](#hierarchy)
  - [Error handling example](#error-handling-example)
  - [Full API Reference](#full-api-reference)
  - [See also](#see-also)
- [Files](#files)
- [Connectors](#connectors)
- [Transformation Reference](#transformation-reference)
  - [Setup](#setup)
  - [Filtering and labeling](#filtering-and-labeling)
    - [Filter to high-value rows](#filter-to-high-value-rows)
    - [Filter with multiple conditions](#filter-with-multiple-conditions)
    - [Create a label column](#create-a-label-column)
    - [Flag rows with a boolean column](#flag-rows-with-a-boolean-column)
  - [Math and calculations](#math-and-calculations)
    - [Compute a new column](#compute-a-new-column)
    - [Update an existing column](#update-an-existing-column)
    - [Conditional math](#conditional-math)
  - [Joining views](#joining-views)
    - [Left join with a View object](#left-join-with-a-view-object)
    - [Join with column prefix](#join-with-column-prefix)
  - [Aggregation](#aggregation)
    - [Group by with multiple aggregations](#group-by-with-multiple-aggregations)
    - [Crosstab / pivot table](#crosstab-pivot-table)
  - [Window functions](#window-functions)
    - [Row number / ranking](#row-number-ranking)
    - [Running total](#running-total)
    - [Lag / lead](#lag-lead)
  - [Column operations](#column-operations)
    - [Rename by copy-and-delete](#rename-by-copy-and-delete)
    - [Combine columns](#combine-columns)
    - [Split a column](#split-a-column)
    - [Convert column types](#convert-column-types)
  - [Text operations](#text-operations)
    - [Change text case](#change-text-case)
    - [Trim whitespace](#trim-whitespace)
    - [Find and replace](#find-and-replace)
    - [Bulk replace](#bulk-replace)
    - [Substring extraction](#substring-extraction)
  - [Date operations](#date-operations)
    - [Extract date parts](#extract-date-parts)
    - [Date difference](#date-difference)
    - [Increment a date](#increment-a-date)
  - [Row operations](#row-operations)
    - [Remove duplicates](#remove-duplicates)
    - [Limit rows](#limit-rows)
    - [Fill missing values](#fill-missing-values)
    - [Unnest (unpivot)](#unnest-unpivot)
  - [Advanced operations](#advanced-operations)
    - [Lookup from another view](#lookup-from-another-view)
    - [JSON extraction](#json-extraction)
    - [AI-powered transformation](#ai-powered-transformation)
    - [SQL](#sql)
  - [Draft mode (batch transformations)](#draft-mode-batch-transformations)
    - [Context manager (recommended)](#context-manager-recommended)
    - [Explicit enter/submit](#explicit-entersubmit)
    - [Discard on error](#discard-on-error)
    - [Toggle auto-run](#toggle-auto-run)
  - [End-to-end workflow](#end-to-end-workflow)
  - [See also](#see-also)
- [Exports](#exports)
  - [Quick examples](#quick-examples)
  - [ViewExport API Reference](#viewexport-api-reference)
  - [ExportsAPI (low-level)](#exportsapi-low-level)
  - [See also](#see-also)
- [Projects](#projects)
- [Datasets](#datasets)
- [Dataviews](#dataviews)
- [Pipeline](#pipeline)
- [Jobs](#jobs)
- [Dashboards](#dashboards)
- [Webhooks](#webhooks)
- [Automations & Schedules](#automations-schedules)
  - [AutomationsAPI](#automationsapi)
  - [SchedulesAPI](#schedulesapi)
- [Workspace & Users](#workspace-users)
  - [WorkspaceAPI](#workspaceapi)
  - [UserProfileAPI](#userprofileapi)
- [Other APIs](#other-apis)
  - [FoldersAPI](#foldersapi)
  - [BatchesAPI](#batchesapi)
  - [BrowseAPI](#browseapi)
  - [ClientAppsAPI](#clientappsapi)
  - [ExternalKeysAPI](#externalkeysapi)
  - [ActivityLogsAPI](#activitylogsapi)
  - [AddonsAPI](#addonsapi)
  - [ReportsAPI](#reportsapi)
  - [AIAPI](#aiapi)
- [Reference Coverage](#reference-coverage)
- [End-to-End Workflow](#end-to-end-workflow)
  - [1. Install the SDK](#1-install-the-sdk)
  - [2. Authenticate](#2-authenticate)
  - [3. Upload a file](#3-upload-a-file)
  - [4. Inspect the View](#4-inspect-the-view)
  - [5. Apply transformations](#5-apply-transformations)
    - [Filter rows](#filter-rows)
    - [Add computed columns](#add-computed-columns)
    - [Aggregate with pivot](#aggregate-with-pivot)
    - [Other common transformations](#other-common-transformations)
  - [6. Export results](#6-export-results)
    - [Download as CSV](#download-as-csv)
    - [Export to S3](#export-to-s3)
    - [Export to a database](#export-to-a-database)
    - [Other export targets](#other-export-targets)
  - [Complete script](#complete-script)
  - [See also](#see-also)
- [Basic Usage](#basic-usage)
  - [Client setup](#client-setup)
  - [Parse a Mammoth URL](#parse-a-mammoth-url)
  - [Upload files](#upload-files)
  - [List resources](#list-resources)
  - [Get a View and inspect it](#get-a-view-and-inspect-it)
  - [Fetch data](#fetch-data)
  - [Apply a transformation](#apply-a-transformation)
  - [Export to CSV](#export-to-csv)
  - [Context manager](#context-manager)
  - [Pipeline management](#pipeline-management)
  - [Create and clone views](#create-and-clone-views)
  - [Complete workflow](#complete-workflow)
  - [See also](#see-also)
- [Error Handling](#error-handling)
  - [Exception hierarchy](#exception-hierarchy)
  - [Handling specific exceptions](#handling-specific-exceptions)
    - [Authentication errors](#authentication-errors)
    - [API errors](#api-errors)
    - [Column errors](#column-errors)
    - [Job timeout](#job-timeout)
    - [Job failure](#job-failure)
    - [Transform errors](#transform-errors)
  - [Recommended pattern](#recommended-pattern)
  - [Logging errors](#logging-errors)
  - [Increasing timeouts](#increasing-timeouts)
  - [See also](#see-also)
- [Configuration](#configuration)
  - [Client parameters](#client-parameters)
  - [Custom instance URLs](#custom-instance-urls)
  - [Timeout tuning](#timeout-tuning)
    - [Request timeout](#request-timeout)
    - [Job timeout](#job-timeout)
  - [No automatic retries](#no-automatic-retries)
  - [Environment-based configuration](#environment-based-configuration)
  - [See also](#see-also)
- [Job Lifecycle](#job-lifecycle)
  - [Timeouts](#timeouts)
  - [Pipeline tasks](#pipeline-tasks)
  - [Draft mode](#draft-mode)
  - [See also](#see-also)
- [Integrations](#integrations)
  - [Export to PostgreSQL](#export-to-postgresql)
  - [Export to MySQL](#export-to-mysql)
  - [Export to S3](#export-to-s3)
  - [Export to BigQuery](#export-to-bigquery)
  - [Import from external sources](#import-from-external-sources)
  - [Branch out to another dataset](#branch-out-to-another-dataset)
  - [Webhook integration](#webhook-integration)
  - [Scheduled automation](#scheduled-automation)
  - [See also](#see-also)
- [Owner Journal Broker](#owner-journal-broker)
  - [Fixed subprocess transport](#fixed-subprocess-transport)
  - [Unix socket front-end](#unix-socket-front-end)
- [Troubleshooting](#troubleshooting)
  - [Authentication errors](#authentication-errors)
  - [Column not found](#column-not-found)
  - [Job timeout](#job-timeout)
  - [Job failed](#job-failed)
  - [project_id not set](#project_id-not-set)
  - [Date columns not working](#date-columns-not-working)
  - [Network / connection errors](#network-connection-errors)
  - [Import errors](#import-errors)
  - [See also](#see-also)
- [Changelog](#changelog)
  - [v0.7.2](#v072)
  - [v0.7.1](#v071)
  - [v0.7.0](#v070)
  - [v0.3.0](#v030)
    - [Breaking changes](#breaking-changes)
    - [Added](#added)
  - [v0.2.4](#v024)
    - [Added](#added)
    - [Fixed](#fixed)
  - [v0.2.3](#v023)
    - [Fixed](#fixed)
  - [v0.2.2](#v022)
    - [Fixed](#fixed)
    - [Added](#added)
  - [v0.2.0](#v020)
    - [Added](#added)
    - [Changed](#changed)
  - [v0.1.0](#v010)
    - [Added](#added)

---


---


# Mammoth Analytics Python SDK

**Version 0.7.2** | Python 3.12–3.14 | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mammothsdk)

The official Python SDK for the [Mammoth Analytics](https://mammoth.io) platform. Build data pipelines, apply transformations, and export results -- all from Python.

## Features

- **MammothClient** -- single entry point with organized sub-clients for every API resource
- **View objects** -- rich domain objects with 25+ transformation methods (filter, set, join, pivot, window, math, and more)
- **Condition builder** -- Pythonic filter conditions with `&` (AND), `|` (OR), and `~` (NOT) operator overloading
- **Export helpers** -- download CSV, push to S3, PostgreSQL, BigQuery, and other destinations
- **Type safety** -- full type hints, enums for all parameters, Pydantic models for responses
- **MCP server** -- optional Model Context Protocol server for AI-assisted analytics (separate package)

## Quick example

```python
from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

# Get a View and apply transformations
view = client.views.get(1039)
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Export results
view.export.to_csv("output.csv")
```

## Documentation

| Section | Description |
|---------|-------------|
| [Installation](#installation) | Install the SDK and set up your environment |
| [Quick Start](#quick-start-guide) | Get up and running in five minutes |
| [Authentication](#authentication) | API credentials and authentication |
| **Core** | |
| [Client API](#client-api-reference) | `MammothClient` constructor, sub-clients, and methods |
| [Views](#views-reference) | `View` class -- properties, transformations, data access |
| [Conditions](#conditions-reference) | `Condition`, `CompoundCondition`, and `NotCondition` filter builder |
| [Enums](#enums-data-classes-reference) | All enums: `Operator`, `ColumnType`, `JoinType`, and more |
| [Exceptions](#exceptions-reference) | Error classes and handling |
| **Import** | |
| [Files](#files-api-reference) | `FilesAPI` -- upload, list, and manage files |
| [Connectors](#connectors-api-reference) | `ConnectorsAPI` -- database and cloud connectors |
| **Transform** | |
| [Transformations](#transformation-examples) | Practical transformation workflow examples |
| **Export** | |
| [Exports](#exports-reference) | `ViewExport` and `ExportsAPI` -- CSV, S3, databases |
| **Manage** | |
| [Projects](#projects-api-reference) | `ProjectsAPI` -- project CRUD and user management |
| [Datasets](#datasets-api-reference) | `DatasetsAPI` -- dataset CRUD and data access |
| [Dataviews](#dataviews-api-reference) | `DataviewsAPI` -- low-level dataview operations |
| [Pipeline](#pipeline-api-reference) | `PipelineAPI` -- transformation pipeline management |
| [Jobs](#jobs-api-reference) | `JobsAPI` -- async job tracking |
| [Dashboards](#dashboards-api-reference) | `DashboardsAPI` -- dashboard management |
| [Webhooks](#webhooks-api-reference) | `WebhooksAPI` -- webhook datasets |
| [Automations](#automations-schedules-api-reference) | `AutomationsAPI` and `SchedulesAPI` |
| [Workspace](#workspace-users-api-reference) | `WorkspaceAPI` and `UserProfileAPI` |
| [Other APIs](#other-apis-reference) | Folders, batches, browse, client apps, addons, and more |
| **Guides** | |
| [End-to-End Workflow](#end-to-end-workflow) | Complete journey: upload, transform, export |
| [Changelog](#changelog) | Release history |

## Version information

- **SDK version**: 0.7.2
- **Python**: 3.12–3.14
- **API version**: v2

## Support

- **Documentation**: [https://docs.mammoth.io](https://docs.mammoth.io)
- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mammothsdk/issues)
- **Email**: support@mammoth.io


---


# Installation

## Requirements

- Python 3.12, 3.13, or 3.14
- pip or Poetry package manager

## Install from PyPI

```bash
pip install mammoth-io==0.7.2
```

Or with Poetry:

```bash
poetry add mammoth-io==0.7.2
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

The development dependencies are a standard `[dependency-groups].dev` group
in this repository, not a published `dev` extra. A PyPI install supplies only
runtime dependencies.

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

- [Quick Start Guide](#quick-start-guide) -- create your first client and apply transformations
- [Authentication](#authentication) -- set up API credentials


---


# Quick Start Guide

Get up and running with the Mammoth Python SDK in five minutes.

## 1. Install the SDK

```bash
pip install mammoth-io==0.7.2
```

## 2. Get your API credentials

Log in to your Mammoth Analytics dashboard, navigate to your profile settings, and generate an API key and secret.

## 3. Create a client

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,  # your workspace ID
)

# Set the project you want to work with
client.set_project_id(10)
```

The `workspace_id` is required at client creation. The `project_id` must be set before performing most operations.

> **Tip:** Extract IDs from a Mammoth URL
>
> Use `parse_path()` to extract IDs from a browser URL:
>
> ```python
> from mammoth import parse_path
>
> ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
> # {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
> ```
>

## 4. Get a View

A **View** is the central object in the SDK. It wraps a Mammoth dataview and provides transformation methods, data access, and export helpers.

```python
view = client.views.get(1039)

print(view.name)           # "My View"
print(view.display_names)  # ["Sales", "Region", "Date", ...]
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", ...}
```

## 5. Apply transformations

Transformations are applied in-place. Each method sends a task to the Mammoth pipeline, waits for it to complete, and refreshes the view metadata.

```python
from mammoth import Condition, Operator, ColumnType, SetValue

# Filter rows
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Add a computed column
view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Math expression
view.math("Price * Quantity", new_column="Total")
```

## 6. Export data

```python
# Download as CSV
view.export.to_csv("output.csv")

# Export to S3
view.export.to_s3(file_name="report.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

## 7. Work with resources

The client provides sub-clients for every Mammoth API resource:

```python
# List projects — returns {"projects": [...], "offset": 0, ...}
resp = client.projects.list()
for p in resp["projects"]:      # plain dicts: p["id"], p["name"]
    print(p["id"], p["name"])

# List datasets in a project
datasets = client.datasets.list()

# Upload a file
client.files.upload("data.csv")
```

## Complete example

```python
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(10)

try:
    # Get a view
    view = client.views.get(1039)
    print(f"Working with: {view.name} ({len(view.display_names)} columns)")

    # Filter to high-value rows
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))

    # Add a label column
    view.set_values(
        new_column="Tier",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Standard"),
        ],
    )

    # Export
    path = view.export.to_csv("output.csv")
    print(f"Exported to {path}")

except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## Key concepts

| Concept | Description |
|---------|-------------|
| **Workspace** | Top-level organization unit tied to your subscription |
| **Project** | Siloed area within a workspace for data management |
| **Dataset** | A data table stored in Mammoth (created from file uploads or connectors) |
| **Dataview** | A view of a dataset, with its own pipeline of transformations |
| **View** | The SDK's rich object wrapping a dataview -- the main interface for transformations |
| **Pipeline** | The ordered list of transformation tasks applied to a dataview |

## Next steps

- [Views reference](#views-reference) -- all transformation methods with signatures and examples
- [Conditions reference](#conditions-reference) -- filter builder with operator overloading
- [Exports reference](#exports-reference) -- all export destinations
- [Transformation examples](#transformation-examples) -- practical workflow examples


---


# Authentication

The Mammoth SDK uses API key and secret-based authentication. Every request includes your credentials in HTTP headers automatically.

## Getting API credentials

1. Log in to your Mammoth Analytics dashboard
2. Navigate to your profile settings
3. Generate or retrieve your API key and secret
4. Store these credentials securely

## Client setup

### Direct authentication

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)
```

### Environment variables (recommended)

Store credentials in environment variables for better security:

```bash
export MAMMOTH_API_KEY="your-api-key"
export MAMMOTH_API_SECRET="your-api-secret"
```

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
```

### Configuration file

For projects with multiple environments:

```python
# config.py
import os

MAMMOTH_CONFIG = {
    "api_key": os.getenv("MAMMOTH_API_KEY"),
    "api_secret": os.getenv("MAMMOTH_API_SECRET"),
    "workspace_id": int(os.getenv("MAMMOTH_WORKSPACE_ID", "11")),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
}
```

```python
from mammoth import MammothClient
from config import MAMMOTH_CONFIG

client = MammothClient(**MAMMOTH_CONFIG)
```

## How authentication works

The client adds these headers to every request automatically:

| Header | Value |
|--------|-------|
| `X-API-KEY` | Your API key |
| `X-API-SECRET` | Your API secret |
| `X-WORKSPACE-ID` | Your workspace ID |
| `User-Agent` | `mammoth-io/0.7.2` |

## Error handling

Authentication errors raise `MammothAuthError` (HTTP 401):

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(
        api_key="invalid-key",
        api_secret="invalid-secret",
        workspace_id=1,
    )
    projects = client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API credentials")
```

## Security best practices

**Never hardcode credentials** -- use environment variables or a secrets manager:

```python
# Do not do this:
client = MammothClient(api_key="pk_live_123456789", ...)

# Do this instead:
client = MammothClient(api_key=os.getenv("MAMMOTH_API_KEY"), ...)
```

**Use different credentials per environment** -- separate dev, staging, and production keys.

**Rotate credentials regularly** -- regenerate API keys periodically and invalidate old ones.

**Do not commit credentials** -- add `.env` and config files with secrets to `.gitignore`.

## Next steps

- [Quick Start Guide](#quick-start-guide)
- [Client API Reference](#client-api-reference)


---


# Client API Reference

The `MammothClient` is the single entry point for all Mammoth API interactions. It manages authentication, provides organized sub-clients for every resource, and supports context manager usage.

## Quick start

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
    timeout=60,
    job_timeout=120,
)
client.set_project_id(10)
```

> **Note:** No retries
>
> The SDK does **not** implement automatic retries. If an API call fails, the error is raised immediately. Implement retry logic in your application if needed.
>

## Context manager

The client supports Python's context manager protocol. The HTTP session is closed automatically on exit:

```python
with MammothClient(
    api_key="...", api_secret="...", workspace_id=11
) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.export.to_csv("output.csv")
# Session closed automatically
```

## Sub-clients

All API resources are accessible as attributes on the client. Each sub-client handles a specific area of the Mammoth API.

### Core data sub-clients

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.views` | `ViewsResource` | Rich View objects with transformations (see [Views](#views-reference)) |
| `client.datasets` | `DatasetsAPI` | Dataset CRUD operations (see [Datasets](#datasets-api-reference)) |
| `client.dataviews` | `DataviewsAPI` | Low-level dataview operations (see [Dataviews](#dataviews-api-reference)) |
| `client.pipeline` | `PipelineAPI` | Pipeline task management (see [Pipeline](#pipeline-api-reference)) |
| `client.files` | `FilesAPI` | File upload and management (see [Files](#files-api-reference)) |
| `client.exports` | `ExportsAPI` | Export operations (see [Exports](#exports-reference)) |
| `client.jobs` | `JobsAPI` | Asynchronous job tracking (see [Jobs](#jobs-api-reference)) |
| `client.projects` | `ProjectsAPI` | Project CRUD (see [Projects](#projects-api-reference)) |

### Additional sub-clients

| Attribute | Type | Description |
|-----------|------|-------------|
| `client.ai` | `AIAPI` | AI/LLM operations (see [Other APIs](#other-apis-reference)) |
| `client.connectors` | `ConnectorsAPI` | Data source connectors (see [Connectors](#connectors-api-reference)) |
| `client.dashboards` | `DashboardsAPI` | Dashboard management (see [Dashboards](#dashboards-api-reference)) |
| `client.webhooks` | `WebhooksAPI` | Webhook configuration (see [Webhooks](#webhooks-api-reference)) |
| `client.automations` | `AutomationsAPI` | Automation workflows (see [Automations](#automations-schedules-api-reference)) |
| `client.schedules` | `SchedulesAPI` | Scheduled operations (see [Automations](#automations-schedules-api-reference)) |
| `client.batches` | `BatchesAPI` | Batch operations (see [Other APIs](#other-apis-reference)) |
| `client.folders` | `FoldersAPI` | Folder management (see [Other APIs](#other-apis-reference)) |
| `client.workspaces` | `WorkspaceAPI` | Workspace operations (see [Workspace](#workspace-users-api-reference)) |
| `client.user_profile` | `UserProfileAPI` | User profile (see [Workspace](#workspace-users-api-reference)) |
| `client.activity_logs` | `ActivityLogsAPI` | Activity logs (see [Other APIs](#other-apis-reference)) |
| `client.browse` | `BrowseAPI` | Browse/search API (see [Other APIs](#other-apis-reference)) |
| `client.external_keys` | `ExternalKeysAPI` | External key management (see [Other APIs](#other-apis-reference)) |
| `client.client_apps` | `ClientAppsAPI` | Client app management (see [Other APIs](#other-apis-reference)) |
| `client.addons` | `AddonsAPI` | Addons (see [Other APIs](#other-apis-reference)) |
| `client.reports` | `ReportsAPI` | Reports (see [Other APIs](#other-apis-reference)) |

---

## Full API Reference

*See API reference for `mammoth.client.MammothClient`*

### ViewsResource

*See API reference for `mammoth.client.ViewsResource`*

---

## Error handling

The client raises specific exceptions for different error types:

| Exception | Trigger |
|-----------|---------|
| `MammothAuthError` | HTTP 401 (invalid credentials) |
| `MammothAPIError` | HTTP 4xx/5xx responses, network errors, timeouts |

See [Exceptions](#exceptions-reference) for the full error hierarchy.

```python
from mammoth import MammothClient, MammothAPIError, MammothAuthError

try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)
    datasets = client.datasets.list()
except MammothAuthError:
    print("Invalid credentials")
except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## See also

- [Views](#views-reference) -- View object and transformation methods
- [Exports](#exports-reference) -- Export operations
- [Exceptions](#exceptions-reference) -- Error handling
- [Quick Start](#quick-start-guide) -- Getting started


---


# Views Reference

The `View` class is the central interface for data transformations in the Mammoth SDK. It wraps a single dataview and provides 25+ transformation methods, data access, pipeline management, and export helpers.

## Getting a View

Views are created via `client.views.get()` -- not instantiated directly:

```python
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

view = client.views.get(1039)
```

You can also list, create, and delete views:

```python
# List all views in a dataset
views = client.views.list(dataset_id=42)

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Create by cloning
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `int` | Dataview ID |
| `name` | `str` | Dataview display name |
| `dataset_id` | `int` | Parent dataset ID |
| `columns` | `dict[str, str]` | Mapping of display names to internal names |
| `display_names` | `list[str]` | Ordered list of column display names |
| `column_types` | `dict[str, str]` | Mapping of display names to types (`TEXT`, `NUMERIC`, `DATE`) |
| `raw` | `dict` | Full raw API response dict |
| `export` | `ViewExport` | Export helper (see [Exports](#exports-reference)) |

After every transformation, `display_names`, `columns`, and `column_types` are automatically refreshed — including columns added by pipeline tasks (`math`, `set_values`, `add_column`, etc.).

```python
view = client.views.get(1039)

print(view.id)             # 1039
print(view.name)           # "Sales Data"
print(view.display_names)  # ["Sales", "Region", "Date"]
print(view.columns)        # {"Sales": "column_1", "Region": "column_2", ...}
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", "Date": "DATE"}

# After a transform, new columns appear immediately:
view.math("Sales * 1.1", new_column="Revenue")
print("Revenue" in view.display_names)   # True
```

## Draft mode

By default, each transformation triggers an immediate pipeline run (auto-run mode). For large datasets or multi-step workflows, use **draft mode** to queue tasks and run the pipeline once.

### draft() (context manager)

The recommended approach. Enters draft mode on entry, submits and runs on clean exit, discards on exception:

```python
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
    view.add_column("Notes")
# Pipeline runs once for all 3 tasks, metadata refreshed
```

If an exception occurs inside the block, all queued tasks are discarded:

```python
try:
    with view.draft():
        view.add_column("Temp")
        raise ValueError("something went wrong")
except ValueError:
    pass  # "Temp" column was NOT added — draft was discarded
```

### Explicit draft workflow

```python
view.enter_draft_mode()
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Price * 2", new_column="Double")
view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Full API Reference

*See API reference for `mammoth.view.View`*

---

## Exports

Export operations are accessed via `view.export`. See the [Exports reference](#exports-reference) for full documentation.

```python
view.export.to_csv("output.csv")
view.export.to_s3(file_name="report.csv")
view.export.to_postgres(host="...", port=5432, database="...", table="...", username="...", password="...")
view.branch_out(dest_dataset_id=42)
```

## See also

- [Conditions](#conditions-reference) -- filter builder
- [Enums](#enums-data-classes-reference) -- all parameter enums
- [Exports](#exports-reference) -- export destinations
- [Transformation examples](#transformation-examples) -- practical workflows


---


# Conditions Reference

The condition module provides a Pythonic filter builder with operator overloading. Build conditions using `Condition` objects, combine them with `&` (AND), `|` (OR), and `~` (NOT), and pass them to View transformation methods.

## Quick examples

```python
from mammoth import Condition, Operator

# Numeric comparisons
high_sales = Condition("Sales", Operator.GTE, 10000)

# List membership
selected = Condition("Region", Operator.IN_LIST, ["West", "East"])

# Null checks (no value needed)
empty = Condition("Name", Operator.IS_EMPTY)

# Combine with & (AND), | (OR), ~ (NOT)
both = high_sales & selected
negated = ~Condition("Status", Operator.EQ, "Closed")
complex_cond = (high_sales & selected) | negated
```

## Operator overloading

Combine conditions with `&` (AND), `|` (OR), and `~` (NOT). Use parentheses for grouping.

```python
high_sales = Condition("Sales", Operator.GTE, 10000)
west = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.EQ, "Active")

# AND: all conditions must be true
both = high_sales & west

# OR: at least one must be true
either = high_sales | west

# Nested: parentheses control grouping
complex_cond = (high_sales & west) | active

# Chain multiple — flat when using the same operator
all_three = high_sales & west & active  # AND of all three
```

## Using conditions with View methods

### filter_rows

```python
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Conditions can be attached to individual `SetValue` items to create conditional columns:

```python
from mammoth import SetValue, ColumnType

view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),  # default (no condition)
    ],
)
```

### math, combine_columns, and other methods

Many transformation methods accept an optional `condition` parameter:

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
```

## All operators

See the [Operator enum](#enums-data-classes-reference) for the complete list. Summary:

| Category | Operators |
|----------|-----------|
| Comparison | `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE` |
| List | `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS` |
| String | `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH` |
| Null | `IS_EMPTY`, `IS_NOT_EMPTY` |
| Aggregate | `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL` |

---

## Full API Reference

*See API reference for `mammoth.condition.Condition`*

*See API reference for `mammoth.condition.CompoundCondition`*

*See API reference for `mammoth.condition.NotCondition`*

## See also

- [Enums](#enums-data-classes-reference) -- all enum values
- [Views](#views-reference) -- transformation methods that use conditions
- [Transformation examples](#transformation-examples) -- practical workflows


---


# Enums & Data Classes Reference

The SDK provides enums for all transformation parameters. Import them directly from `mammoth`:

```python
from mammoth import Operator, ColumnType, JoinType, DateComponent
```

All enums are `str` subclasses (`class MyEnum(str, Enum)`) so they can be used directly as strings where needed.

---

## Enums

*See API reference for `mammoth.models.pipeline.Operator`*

*See API reference for `mammoth.models.pipeline.ColumnType`*

*See API reference for `mammoth.models.pipeline.FilterType`*

*See API reference for `mammoth.models.pipeline.JoinType`*

*See API reference for `mammoth.models.pipeline.TextCase`*

*See API reference for `mammoth.models.pipeline.DateComponent`*

*See API reference for `mammoth.models.pipeline.DateDiffUnit`*

*See API reference for `mammoth.models.pipeline.AggregateFunction`*

*See API reference for `mammoth.models.pipeline.WindowFunction`*

*See API reference for `mammoth.models.pipeline.WindowRange`*

*See API reference for `mammoth.models.pipeline.FillDirection`*

*See API reference for `mammoth.models.pipeline.SortDirection`*

*See API reference for `mammoth.models.pipeline.MathOperator`*

*See API reference for `mammoth.models.pipeline.SubstringDirection`*

*See API reference for `mammoth.models.pipeline.JsonType`*

*See API reference for `mammoth.models.pipeline.JsonOpType`*

*See API reference for `mammoth.models.pipeline.ExportFileType`*

*See API reference for `mammoth.models.pipeline.ProviderType`*

*See API reference for `mammoth.models.pipeline.TaskType`*

*See API reference for `mammoth.models.pipeline.DraftCommand`*

---

## Data Classes

*See API reference for `mammoth.models.pipeline.SetValue`*

*See API reference for `mammoth.models.pipeline.CopySpec`*

*See API reference for `mammoth.models.pipeline.ConversionSpec`*

*See API reference for `mammoth.models.pipeline.SplitColumnSpec`*

*See API reference for `mammoth.models.pipeline.BulkReplaceMapping`*

*See API reference for `mammoth.models.pipeline.DateDelta`*

*See API reference for `mammoth.models.pipeline.AggregationSpec`*

*See API reference for `mammoth.models.pipeline.JoinKeySpec`*

*See API reference for `mammoth.models.pipeline.JoinSelectSpec`*

*See API reference for `mammoth.models.pipeline.JsonExtractionSpec`*

*See API reference for `mammoth.models.pipeline.CrosstabSpec`*

## See also

- [Conditions](#conditions-reference) -- how to use Operator with Condition
- [Views](#views-reference) -- transformation methods that use these enums


---


# Exceptions Reference

All SDK exceptions inherit from `MammothError`. Import them from `mammoth`:

```python
from mammoth import (
    MammothError,
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothTransformError,
    MammothColumnError,
)
```

## Hierarchy

```
MammothError
├── MammothAPIError
│   └── MammothAuthError
├── MammothJobTimeoutError
├── MammothJobFailedError
├── MammothTransformError
└── MammothColumnError
```

## Error handling example

```python
from mammoth import MammothClient, MammothAPIError, MammothAuthError

try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)
    view = client.get_view(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothAuthError:
    print("Invalid credentials")
except MammothAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
    print(f"Response: {e.response_body}")
except MammothColumnError as e:
    print(f"Column {e.details['column_name']} not found")
    print(f"Available: {e.details['available_columns']}")
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out after {e.details['timeout']}s")
```

---

## Full API Reference

*See API reference for `mammoth.exceptions.MammothError`*

*See API reference for `mammoth.exceptions.MammothAPIError`*

*See API reference for `mammoth.exceptions.MammothAuthError`*

*See API reference for `mammoth.exceptions.MammothJobTimeoutError`*

*See API reference for `mammoth.exceptions.MammothJobFailedError`*

*See API reference for `mammoth.exceptions.MammothTransformError`*

*See API reference for `mammoth.exceptions.MammothColumnError`*

## See also

- [Client](#client-api-reference) -- error handling in the client
- [Views](#views-reference) -- transformation methods that raise these exceptions


---


# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion.

**Access**: `client.files`

```python
# Upload a CSV file
result = client.files.upload("data.csv")

# Upload an Excel file
result = client.files.upload("report.xlsx")
```

---

*See API reference for `mammoth.api.files.FilesAPI`*


---


# Connectors API Reference

The `ConnectorsAPI` manages cloud data source connectors and their connections. Use connectors to import data from databases (PostgreSQL, MySQL, BigQuery, etc.), cloud storage, and other external sources.

**Access**: `client.connectors`

---

*See API reference for `mammoth.api.connectors.ConnectorsAPI`*


---


# Transformation Examples

Practical examples of common data transformation workflows using the Mammoth SDK.

## Setup

All examples assume the following setup:

```python
from mammoth import (
    MammothClient, Condition, CompoundCondition, Operator,
    ColumnType, SetValue, JoinType, JoinKeySpec, JoinSelectSpec,
    AggregateFunction, AggregationSpec, CrosstabSpec, CopySpec,
    ConversionSpec, SplitColumnSpec, BulkReplaceMapping, DateDelta,
    WindowFunction, SortDirection, WindowRange, DateComponent,
    DateDiffUnit, TextCase, FillDirection, SubstringDirection,
    FilterType, JsonType, JsonExtractionSpec, ExportFileType,
)

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

view = client.views.get(1039)
```

---

## Filtering and labeling

### Filter to high-value rows

```python
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
```

### Filter with multiple conditions

```python
# Keep rows where Sales >= 1000 AND Region is "West"
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)

# Remove rows where Status is empty
view.filter_rows(
    Condition("Status", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)
```

### Create a label column

```python
view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)
```

### Flag rows with a boolean column

```python
view.set_values(
    new_column="Is High Value",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Yes", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("No"),
    ],
)
```

---

## Math and calculations

### Compute a new column

```python
view.math("Price * Quantity", new_column="Total")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")
```

### Update an existing column

```python
view.math("Sales * 1.1", existing_column="Sales")
```

### Conditional math

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
```

---

## Joining views

### Left join with a View object

When you pass a View object, you can use display names for both sides:

```python
customers = client.views.get(2050)

view.join(
    foreign_view=customers,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Customer Name", "Email", "Segment"],
)
```

### Join with column prefix

```python
products = client.views.get(2051)

view.join(
    foreign_view=products,
    join_type=JoinType.INNER,
    on=[JoinKeySpec(left="Product Code", right="Product Code")],
    select=["Product Name", "Category"],
    column_prefix="Product_",
)
```

---

## Aggregation

### Group by with multiple aggregations

```python
view.pivot(
    group_by=["Region", "Category"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.AVG, as_name="Avg Sale"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### Crosstab / pivot table

```python
view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(column="Sales", function=AggregateFunction.SUM),
)
```

---

## Window functions

### Row number / ranking

```python
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

### Running total

```python
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### Lag / lead

```python
view.window(
    function=WindowFunction.LAG,
    column="Sales",
    new_column="Previous Sales",
    partition_by=["Region"],
    order_by=[["Date", SortDirection.ASC]],
)
```

---

## Column operations

### Rename by copy-and-delete

The SDK does not have a direct `rename_column` task. To rename, copy the column with a new name, then delete the original:

```python
view.copy_columns([CopySpec(source="old_name", as_name="new_name")])
view.delete_columns(["old_name"])
```

### Combine columns

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### Split a column

```python
view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)
```

### Convert column types

```python
view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Order Date", to=ColumnType.DATE),
])
```

---

## Text operations

### Change text case

```python
view.text_transform(columns=["Name"], case=TextCase.UPPER)
view.text_transform(columns=["Description"], case=TextCase.TITLE)
```

### Trim whitespace

```python
view.text_transform(columns=["Name", "Email"], trim=True)
```

### Find and replace

```python
view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### Bulk replace

```python
view.bulk_replace(
    columns=["Item"],
    mapping=[
        BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE", "10 inch CAKE"], replace="CAKE"),
        BulkReplaceMapping(search=["Small Coffee", "Large Coffee", "Iced Coffee"], replace="Coffee"),
    ],
)
```

### Substring extraction

```python
# First 3 characters
view.substring("Product Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

---

## Date operations

### Extract date parts

```python
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
view.extract_date("Order Date", DateComponent.QUARTER, new_column="Quarter")
```

### Date difference

```python
view.date_diff(
    DateDiffUnit.DAY,
    start="Ship Date",
    end="Delivery Date",
    new_column="Delivery Days",
)
```

### Increment a date

```python
view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended Due")
```

---

## Row operations

### Remove duplicates

```python
view.discard_duplicates()

# Ignore specific columns when checking for duplicates
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### Limit rows

```python
# Top 100 by sales
view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])

# Bottom 10
view.limit_rows(10, bottom=True, order_by=[["Sales", SortDirection.ASC]])
```

### Fill missing values

```python
view.fill_missing(
    "Price",
    direction=FillDirection.LAST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### Unnest (unpivot)

```python
view.unnest(
    columns=["Q1", "Q2", "Q3", "Q4"],
    label_column="Quarter",
    value_column="Revenue",
)
```

---

## Advanced operations

### Lookup from another view

```python
view.lookup(
    source="Product Code",
    lookup_view_id=2050,
    key="code",
    value="name",
    new_column="Product Name",
)
```

### JSON extraction

```python
# Object keys to columns
view.json_extract("data", keys=["name", "email", "age"])

# With type control
view.json_extract(
    "data",
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT),
        JsonExtractionSpec(key="score", as_name="Score", type=ColumnType.NUMERIC),
    ],
)

# JSON list to rows
view.json_extract("items", json_type=JsonType.LIST)
```

### AI-powered transformation

```python
view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### SQL

```python
# Generate SQL from natural language
sql = view.generate_sql("count employees by department and sort by count descending")
print(sql)

# Add raw SQL
view.add_sql("SELECT region, SUM(sales) as total FROM data GROUP BY region")
```

---

## Draft mode (batch transformations)

By default each transformation runs the pipeline immediately. Use draft mode to queue multiple tasks and run the pipeline once -- much faster for large datasets.

### Context manager (recommended)

```python
with view.draft():
    view.text_transform(columns=["Name", "Email"], trim=True)
    view.convert_type([
        ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
        ConversionSpec(column="Order Date", to=ColumnType.DATE),
    ])
    view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))
    view.math("Price * Quantity", new_column="Revenue")
# Pipeline runs once for all 4 tasks
```

### Explicit enter/submit

```python
view.enter_draft_mode()
view.add_column("Notes")
view.set_values(
    new_column="Flag",
    column_type=ColumnType.TEXT,
    values=[SetValue("Yes", condition=Condition("Sales", Operator.GTE, 10000)), SetValue("No")],
)
view.submit_draft()  # runs pipeline, refreshes metadata
```

### Discard on error

If an exception occurs inside `with view.draft():`, queued tasks are automatically discarded. You can also discard explicitly:

```python
view.enter_draft_mode()
view.add_column("Temp")
view.discard_draft()  # reverts, "Temp" is not added
```

### Toggle auto-run

```python
view.set_auto_run(False)   # enters draft mode, tasks queue without running
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Sales * 1.1", new_column="Adjusted")
view.set_auto_run(True)    # re-enables auto-run
```

---

## End-to-end workflow

A complete example: load data, clean it, transform it, and export.

```python
from mammoth import (
    MammothClient, Condition, Operator, ColumnType,
    SetValue, AggregateFunction, AggregationSpec,
    ConversionSpec, SortDirection, TextCase,
)

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# 1. Get the view
view = client.views.get(1039)
print(f"Starting with {len(view.display_names)} columns")

# 2. Clean: trim whitespace, convert types
view.text_transform(columns=["Customer Name", "Region"], trim=True)
view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Order Date", to=ColumnType.DATE),
])

# 3. Filter: remove empty sales
view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))

# 4. Transform: add calculated columns
view.math("Price * Quantity", new_column="Revenue")
view.set_values(
    new_column="Segment",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)

# 5. Aggregate
view.pivot(
    group_by=["Region", "Segment"],
    aggregations=[
        AggregationSpec(column="Revenue", function=AggregateFunction.SUM, as_name="Total Revenue"),
        AggregationSpec(column="Revenue", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)

# 6. Export
view.export.to_csv("revenue_summary.csv")
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="revenue_summary",
    username="user", password="pass",
)

print("Done!")
```

## See also

- [Views reference](#views-reference) -- all method signatures
- [Conditions reference](#conditions-reference) -- filter builder
- [Enums reference](#enums-data-classes-reference) -- all parameter values
- [Exports reference](#exports-reference) -- all export destinations


---


# Exports Reference

The SDK provides two ways to export data:

1. **ViewExport** (`view.export`) -- export methods attached to a View object
2. **ExportsAPI** (`client.exports`) -- lower-level export operations

## Quick examples

```python
# Download as CSV
path = view.export.to_csv("output.csv")

# Export to S3
view.export.to_s3(file_name="report.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales",
    username="user", password="pass",
)

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)

# List and delete exports
exports = view.export.list()
view.export.delete(exports[0]["id"])
```

> **Note:** External service exports
>
> Methods like `to_postgres`, `to_mysql`, `to_ftp`, `to_sftp`, `to_email`, `to_bigquery`, `to_redshift`, and `to_elasticsearch` require pre-configured external services accessible from the Mammoth platform.
>

---

## ViewExport API Reference

*See API reference for `mammoth.view.ViewExport`*

---

## ExportsAPI (low-level)

The `client.exports` sub-client provides lower-level export operations. Most users should prefer the `ViewExport` methods above.

*See API reference for `mammoth.api.exports.ExportsAPI`*

## See also

- [Views](#views-reference) -- View object and transformation methods
- [Client](#client-api-reference) -- sub-client overview


---


# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

```python
# List all projects
projects = client.projects.list()

# Get a specific project
project = client.projects.get(project_id=10)

# Create a new project
client.projects.create(name="My Project", properties={"description": "..."})
```

---

*See API reference for `mammoth.api.projects.ProjectsAPI`*


---


# Datasets API Reference

The `DatasetsAPI` manages datasets within a project. A dataset is a data table stored in Mammoth, created from file uploads, connectors, or cloning.

**Access**: `client.datasets`

```python
# List datasets in the current project
datasets = client.datasets.list()

# Get a specific dataset
ds = client.datasets.get(dataset_id=42)
```

---

*See API reference for `mammoth.api.datasets.DatasetsAPI`*


---


# Dataviews API Reference

The `DataviewsAPI` provides low-level CRUD operations on dataviews. For rich transformation methods, use `client.views` instead (see [Views](#views-reference)).

**Access**: `client.dataviews`

---

*See API reference for `mammoth.api.dataviews.DataviewsAPI`*


---


# Pipeline API Reference

The `PipelineAPI` manages the transformation pipeline on dataviews. Each dataview has an ordered list of pipeline tasks (filter, join, pivot, etc.) that transform the data.

**Access**: `client.pipeline`

> **Tip**
>
> Most users should use the high-level `View` transformation methods (e.g. `view.filter_rows()`, `view.math()`) instead of calling `PipelineAPI` directly. The View methods call `PipelineAPI` internally and handle job waiting and metadata refresh automatically.
>

---

*See API reference for `mammoth.api.pipeline.PipelineAPI`*


---


# Jobs API Reference

The `JobsAPI` tracks asynchronous job status. Many Mammoth operations (data fetches, pipeline tasks, exports) create background jobs. The SDK polls these jobs automatically in most cases, but the Jobs API is available for manual control.

**Access**: `client.jobs`

---

*See API reference for `mammoth.api.jobs.JobsAPI`*


---


# Dashboards API Reference

The `DashboardsAPI` manages interactive dashboards in Mammoth. Dashboards visualize data from dataviews and can be shared with team members or embedded externally.

**Access**: `client.dashboards`

---

*See API reference for `mammoth.api.dashboards.DashboardsAPI`*


---


# Webhooks API Reference

The `WebhooksAPI` manages webhook datasets -- HTTP endpoints that receive data into the Mammoth platform. Webhooks allow external systems to push data directly into Mammoth.

**Access**: `client.webhooks`

---

*See API reference for `mammoth.api.webhooks.WebhooksAPI`*


---


# Automations & Schedules API Reference

The SDK provides two sub-clients for automation workflows:

- **`client.automations`** (`AutomationsAPI`) -- manages automations and their associated schedules
- **`client.schedules`** (`SchedulesAPI`) -- manages scheduled operations

---

## AutomationsAPI

*See API reference for `mammoth.api.automations.AutomationsAPI`*

---

## SchedulesAPI

*See API reference for `mammoth.api.schedules.SchedulesAPI`*


---


# Workspace & Users API Reference

The SDK provides two sub-clients for workspace and user management:

- **`client.workspaces`** (`WorkspaceAPI`) -- workspace CRUD and user management
- **`client.user_profile`** (`UserProfileAPI`) -- current user profile and preferences

---

## WorkspaceAPI

*See API reference for `mammoth.api.workspace.WorkspaceAPI`*

---

## UserProfileAPI

*See API reference for `mammoth.api.user_profile.UserProfileAPI`*


---


# Other APIs Reference

This page covers smaller utility sub-clients that provide access to folders, batches, browse, client apps, external keys, activity logs, addons, reports, and AI features.

---

## FoldersAPI

**Access**: `client.folders`

*See API reference for `mammoth.api.folders.FoldersAPI`*

---

## BatchesAPI

**Access**: `client.batches`

*See API reference for `mammoth.api.batches.BatchesAPI`*

---

## BrowseAPI

**Access**: `client.browse`

*See API reference for `mammoth.api.browse.BrowseAPI`*

---

## ClientAppsAPI

**Access**: `client.client_apps`

*See API reference for `mammoth.api.clientapps.ClientAppsAPI`*

---

## ExternalKeysAPI

**Access**: `client.external_keys`

*See API reference for `mammoth.api.external_keys.ExternalKeysAPI`*

---

## ActivityLogsAPI

**Access**: `client.activity_logs`

*See API reference for `mammoth.api.activity_logs.ActivityLogsAPI`*

---

## AddonsAPI

**Access**: `client.addons`

*See API reference for `mammoth.api.addons.AddonsAPI`*

---

## ReportsAPI

**Access**: `client.reports`

*See API reference for `mammoth.api.reports.ReportsAPI`*

---

## AIAPI

**Access**: `client.ai`

*See API reference for `mammoth.api.ai.AIAPI`*


---


# SDK API documentation coverage

This page does not claim that the SDK reference is complete. The checked-in
inventory tool reports every public method declared on `MammothClient`,
`ViewsResource`, and API client classes, then records either its owning MkDocs
source page or the explicit `no_owner_page` gap. It does **not** verify that a
specific method is rendered, visible, or linked by an individual HTML anchor.

Run it from the repository root:

```bash
python scripts/sdk_docs_inventory.py --output sdk-docs-inventory.json
```

The report is deterministic and includes its denominator, owner-page mapping
count, owner-page gap count, and an entry for every symbol. On the current
source it inventories 432 methods; 250 map to an owning reference page and
182 have no owning page. Per-method rendered anchors are unassessed for all
432 methods. These numbers are observations of this revision, not a support or
qualification claim. CI tests ensure the inventory remains deterministic and
that gaps stay visible when the public surface changes.

The safe setup, URL parsing, view-list, and file-upload examples are also
signature-validated in `tests/unit/test_sdk_docs_inventory.py`. That limited
suite does not exercise remote API calls or prove every rendered code block.


---


# End-to-End Workflow

This guide walks through a complete Mammoth SDK workflow: install, authenticate, upload data, apply transformations, and export results.

## 1. Install the SDK

```bash
pip install mammoth-io
```

Requires Python 3.12, 3.13, or 3.14.

## 2. Authenticate

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,  # your workspace ID
)

# Set the project to work in
client.set_project_id(42)
```

> **Tip:** Extract IDs from a Mammoth URL
>
> ```python
> from mammoth import parse_path
>
> ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/42/views/1039")
> # {"workspace_id": 11, "project_id": 42, "dataview_id": 1039}
> ```
>

## 3. Upload a file

```python
# Upload a CSV file -- returns the new dataset ID
dataset_id = client.files.upload("sales_data.csv")
print(f"Created dataset: {dataset_id}")

# Get the default View for the uploaded dataset
views = client.views.list(dataset_id=dataset_id)
view = views[0]
```

Other upload options:

```python
# Multiple files at once
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx"])

# Upload an entire folder
dataset_ids = client.files.upload_folder("./data/")

# Append to an existing dataset
client.files.upload("new_rows.csv", append_to_ds_id=dataset_id)
```

See the [Files API reference](#files-api-reference) for the full `upload()` signature.

## 4. Inspect the View

```python
print(f"View: {view.name}")
print(f"Columns: {view.display_names}")
# e.g., ["Customer", "Region", "Sales", "Order Date"]

print(f"Types: {view.column_types}")
# e.g., {"Customer": "TEXT", "Region": "TEXT", "Sales": "NUMERIC", "Order Date": "TEXT"}

# Preview the data — returns {"data": [rows...], "paging": {...}}
result = view.data(limit=5)
rows = result["data"]
```

> **Note:** CSV dates upload as TEXT
>
> Date columns in CSV files are uploaded as TEXT type. Use `convert_type()` to convert them before applying date operations:
>
> ```python
> from mammoth import ConversionSpec
>
> from mammoth import ColumnType
> view.convert_type([ConversionSpec(column="Order Date", to=ColumnType.DATE, format="MM/DD/YYYY")])
> ```
>

## 5. Apply transformations

### Filter rows

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Negate a condition with ~
view.filter_rows(~Condition("Status", Operator.EQ, "Cancelled"))
```

### Add computed columns

```python
from mammoth import ColumnType, SetValue

# Conditional labeling
view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),
    ],
)

# Math expression
view.math("Price * Quantity", new_column="Revenue")
```

### Aggregate with pivot

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.AVG, as_name="Avg Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### Other common transformations

```python
from mammoth import TextCase, DateComponent, WindowFunction, SortDirection

# Text: change case
view.text_transform(["Customer"], case=TextCase.UPPER)

# Date: extract year
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")

# Window: rank within groups
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

See the [Views reference](#views-reference) for all 25+ transformation methods.

## 6. Export results

### Download as CSV

```python
path = view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

### Export to S3

```python
result = view.export.to_s3(file_name="monthly_report.csv")
```

### Export to a database

```python
# PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_summary",
    username="user",
    password="pass",
)

# MySQL
view.export.to_mysql(
    host="db.example.com",
    port=3306,
    database="analytics",
    table="sales_summary",
    username="user",
    password="pass",
)
```

### Other export targets

```python
view.export.to_bigquery(...)
view.export.to_redshift(...)
view.export.to_sftp(host="sftp.example.com", path="/exports/data.csv", username="user", password="pass")
view.export.to_email(recipients=["team@example.com"])
```

See the [Exports reference](#exports-reference) for all destinations.

## Complete script

Here's a full, copy-paste-ready script:

```python
import os
from mammoth import (
    MammothClient,
    Condition,
    Operator,
    ColumnType,
    SetValue,
    AggregateFunction,
    AggregationSpec,
    FilterType,
    MammothAPIError,
)

# 1. Authenticate
client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(42)

try:
    # 2. Upload data
    dataset_id = client.files.upload("sales_data.csv")
    views = client.views.list(dataset_id=dataset_id)
    view = views[0]
    print(f"Uploaded: {view.name} ({len(view.display_names)} columns)")

    # 3. Clean data
    view.filter_rows(
        Condition("Region", Operator.IS_EMPTY),
        filter_type=FilterType.REMOVE,
    )
    view.filter_rows(Condition("Sales", Operator.GTE, 0))

    # 4. Transform
    view.set_values(
        new_column="Tier",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
            SetValue("Basic"),
        ],
    )
    view.math("Price * Quantity", new_column="Revenue")

    # 5. Export
    path = view.export.to_csv("output.csv")
    print(f"Exported to {path}")

except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## See also

- [Quick Start](#quick-start-guide) -- shorter getting-started guide
- [Files API](#files-api-reference) -- full upload/file management reference
- [Views API](#views-reference) -- all transformation methods
- [Conditions](#conditions-reference) -- filter builder with `&`, `|`, `~`
- [Exports](#exports-reference) -- all export destinations
- [Transformation examples](#transformation-examples) -- more transformation workflows


---


# Basic Usage Examples

Practical examples to get started with the Mammoth Python SDK.

## Client setup

```python
import os
from mammoth import MammothClient, parse_path

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(10)
```

## Parse a Mammoth URL

Extract IDs from a browser URL:

```python
from mammoth import parse_path

ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
print(ids)
# {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
```

## Upload files

```python
# Upload a single CSV file (returns dataset ID)
dataset_id = client.files.upload("sales_data.csv")

# Upload multiple files at once
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx"])

# Upload all files in a folder
dataset_ids = client.files.upload_folder("./data/")

# After upload, get the view for the new dataset
views = client.views.list(dataset_id=dataset_id)
view = views[0]
print(view.display_names)
```

## List resources

```python
# List projects — returns envelope dict, unwrap "projects" key
resp = client.projects.list()
projects = resp["projects"]                 # list of plain dicts
for p in projects:
    print(p["id"], p["name"])               # dict access, NOT p.id / p.name

# List datasets
datasets = client.datasets.list()

# List all views in a dataset (returns list of View objects)
views = client.views.list(dataset_id=42)
for v in views:
    print(f"{v.id}: {v.name} ({len(v.display_names)} columns)")
```

## Get a View and inspect it

```python
view = client.views.get(1039)

print(f"Name: {view.name}")
print(f"Columns: {view.display_names}")
print(f"Types: {view.column_types}")
print(f"Column mapping: {view.columns}")
```

## Fetch data

```python
# First 100 rows
result = view.data(limit=100)

# Specific columns
result = view.data(columns=["Sales", "Region"], limit=50)

# With a condition
from mammoth import Condition, Operator
result = view.data(
    condition=Condition("Sales", Operator.GTE, 1000),
    limit=200,
)
```

## Apply a transformation

```python
from mammoth import Condition, Operator

view.filter_rows(Condition("Sales", Operator.GTE, 1000))
print(f"Columns after filter: {view.display_names}")
```

## Export to CSV

```python
path = view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

## Context manager

```python
with MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.export.to_csv("output.csv")
# Session closed automatically
```

## Pipeline management

```python
# List tasks on a view
tasks = view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key', 'unknown')}")

# Delete a task
view.delete_task(task_id=42)

# Preview a task before applying
preview = view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

## Create and clone views

```python
# Create a new empty view
new_view = client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
clone = client.views.create(dataset_id=42, name="Copy of Analysis", clone_from=1039)

# Delete a view
client.views.delete(view_id=new_view.id)
```

## Complete workflow

```python
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

def main():
    client = MammothClient(
        api_key=os.getenv("MAMMOTH_API_KEY"),
        api_secret=os.getenv("MAMMOTH_API_SECRET"),
        workspace_id=11,
    )
    client.set_project_id(10)

    try:
        view = client.views.get(1039)
        print(f"View: {view.name} ({len(view.display_names)} columns)")

        # Filter
        view.filter_rows(Condition("Sales", Operator.GTE, 1000))

        # Add a label
        view.set_values(
            new_column="Tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
                SetValue("Standard"),
            ],
        )

        # Export
        path = view.export.to_csv("output.csv")
        print(f"Exported to {path}")

    except MammothAPIError as e:
        print(f"Error: {e.message} (HTTP {e.status_code})")

if __name__ == "__main__":
    main()
```

## See also

- [Transformation examples](#transformation-examples) -- 25+ transformation workflows
- [Error handling](#error-handling-guide) -- handling errors gracefully
- [Views reference](#views-reference) -- complete View API


---


# Error Handling Guide

The Mammoth SDK provides specific exception types for different error scenarios. This guide shows how to handle them.

## Exception hierarchy

```
MammothError                     # Base -- catch-all for any SDK error
  +-- MammothAPIError            # HTTP errors, network errors, invalid responses
  |     +-- MammothAuthError     # HTTP 401 (bad credentials)
  +-- MammothJobTimeoutError     # Job polling exceeded timeout
  +-- MammothJobFailedError      # Job completed with failure status
  +-- MammothTransformError      # Transformation task failure
  +-- MammothColumnError         # Column name not found
```

## Handling specific exceptions

### Authentication errors

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(api_key="bad", api_secret="bad", workspace_id=1)
    client.set_project_id(1)
    client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API key and secret")
```

### API errors

```python
from mammoth import MammothAPIError

try:
    datasets = client.datasets.list()
except MammothAPIError as e:
    print(f"API error: {e.message}")
    print(f"HTTP status: {e.status_code}")
    print(f"Response body: {e.response_body}")

    if e.status_code == 404:
        print("Resource not found")
    elif e.status_code and e.status_code >= 500:
        print("Server error -- try again later")
```

### Column errors

```python
from mammoth import MammothColumnError, Condition, Operator

try:
    view.filter_rows(Condition("Nonexistent Column", Operator.GTE, 100))
except MammothColumnError as e:
    print(e.message)
    # "Column 'Nonexistent Column' not found. Available columns: ['Sales', 'Region', ...]"
    print(f"Available columns: {e.details['available_columns']}")
```

### Job timeout

```python
from mammoth import MammothJobTimeoutError

try:
    view.pivot(
        group_by=["Region"],
        aggregations=[{"column": "Sales", "function": "SUM", "as": "Total"}],
    )
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out after {e.details['timeout']}s")
    print("The job may still be processing -- check the Mammoth dashboard")
```

### Job failure

```python
from mammoth import MammothJobFailedError

try:
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed")
    print(f"Reason: {e.details.get('failure_reason', 'Unknown')}")
```

### Transform errors

```python
from mammoth import MammothTransformError

try:
    view.math("InvalidExpr @@@ 2", new_column="Result")
except MammothTransformError as e:
    print(f"Transformation failed: {e.message}")
    print(f"Task key: {e.task_key}")
```

## Recommended pattern

Handle exceptions from most specific to least specific:

```python
from mammoth import (
    MammothAuthError,
    MammothColumnError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothTransformError,
    MammothAPIError,
    MammothError,
)

try:
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

except MammothAuthError:
    print("Bad credentials")

except MammothColumnError as e:
    print(f"Column not found: {e.details['column_name']}")

except MammothJobTimeoutError as e:
    print(f"Job timed out: {e.details['job_id']}")

except MammothJobFailedError as e:
    print(f"Job failed: {e.details.get('failure_reason')}")

except MammothTransformError as e:
    print(f"Transform error: {e.message}")

except MammothAPIError as e:
    print(f"API error ({e.status_code}): {e.message}")

except MammothError as e:
    print(f"SDK error: {e.message}")
```

## Logging errors

```python
import logging
from mammoth import MammothAPIError, MammothJobFailedError

logger = logging.getLogger("mammoth_app")

try:
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothJobFailedError as e:
    logger.error(
        "Pipeline job failed",
        extra={
            "job_id": e.details.get("job_id"),
            "reason": e.details.get("failure_reason"),
        },
    )
    raise
except MammothAPIError as e:
    logger.error(f"API error ({e.status_code}): {e.message}")
    raise
```

## Increasing timeouts

If jobs time out, increase the `job_timeout` on the client:

```python
client = MammothClient(
    api_key="...",
    api_secret="...",
    workspace_id=11,
    job_timeout=300,  # 5 minutes instead of default 60s
)
```

Or increase the timeout for CSV exports:

```python
view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

## See also

- [Exceptions reference](#exceptions-reference) -- full exception class documentation
- [Client API](#client-api-reference) -- timeout configuration


---


# Configuration

Advanced configuration options for the Mammoth SDK client.

## Client parameters

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
    base_url="https://app.mammoth.io/api/v2",
    timeout=30,
    job_timeout=60,
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `"https://app.mammoth.io/api/v2"` | API base URL. Change for custom Mammoth deployments. |
| `timeout` | `30` | HTTP request timeout in seconds. Applies to each individual API call. |
| `job_timeout` | `60` | Maximum time in seconds to poll a job to completion. Used by `jobs.wait_for_job()` and internally by View transformation methods. |

## Custom instance URLs

If your organization uses a custom Mammoth deployment:

```python
client = MammothClient(
    api_key="...",
    api_secret="...",
    workspace_id=11,
    base_url="https://your-instance.mammoth.io/api/v2",
)
```

The SDK normalizes the URL: if you pass `"https://your-instance.mammoth.io"` without the `/api/v2` suffix, it is appended automatically.

## Timeout tuning

### Request timeout

The `timeout` parameter controls how long each HTTP request waits before raising `MammothAPIError`. Increase it for slow networks:

```python
client = MammothClient(..., timeout=120)  # 2 minutes per request
```

### Job timeout

The `job_timeout` parameter controls how long the SDK polls when waiting for a job to complete. Increase it for large datasets or complex transformations:

```python
client = MammothClient(..., job_timeout=300)  # 5 minutes for jobs
```

Note that CSV exports have their own timeout parameter:

```python
view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

## No automatic retries

The SDK does not implement retries. If an API call fails due to a transient error, the exception is raised immediately. Implement retry logic at the application level if needed:

```python
import time
from mammoth import MammothAPIError

def with_retry(fn, max_retries=3, backoff=2):
    for attempt in range(max_retries):
        try:
            return fn()
        except MammothAPIError as e:
            if e.status_code and 400 <= e.status_code < 500:
                raise  # Do not retry client errors
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff ** attempt)
```

## Environment-based configuration

```python
import os

config = {
    "api_key": os.environ["MAMMOTH_API_KEY"],
    "api_secret": os.environ["MAMMOTH_API_SECRET"],
    "workspace_id": int(os.environ["MAMMOTH_WORKSPACE_ID"]),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
    "timeout": int(os.getenv("MAMMOTH_TIMEOUT", "30")),
    "job_timeout": int(os.getenv("MAMMOTH_JOB_TIMEOUT", "60")),
}

client = MammothClient(**config)
```

## See also

- [Client API](#client-api-reference) -- full client reference
- [Authentication](#authentication) -- credential management


---


# Async Operations & Timeouts

All SDK operations are **synchronous** — transformation methods block until the operation completes and view metadata is refreshed. The backend processes tasks asynchronously, but the SDK handles this transparently.

## Timeouts

The `job_timeout` and `pipeline_timeout` client parameters control how long the SDK waits:

```python
client = MammothClient(
    ...,
    job_timeout=300,  # Wait up to 5 minutes for jobs
)
```

If a job does not complete in time, `MammothJobTimeoutError` is raised:

```python
from mammoth import MammothJobTimeoutError, AggregateFunction, AggregationSpec

try:
    view.pivot(
        group_by=["Region"],
        aggregations=[AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total")],
    )
except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} is still running")
```

## Pipeline tasks

Each View maintains an ordered list of pipeline tasks. You can inspect and manage them:

```python
# List all tasks
tasks = view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key')} (seq {task.get('sequence')})")

# Delete a task (re-runs the pipeline without it)
view.delete_task(task_id=42)

# Preview a task before applying
preview = view.preview_task(task_spec)
```

## Draft mode

By default, each transformation triggers an immediate pipeline run. For batch operations on large datasets, use **draft mode** to queue tasks and run the pipeline once:

```python
from mammoth import Condition, Operator, SetValue, ColumnType

# Context manager approach (recommended)
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
# Pipeline runs once for both tasks

# Explicit approach
view.enter_draft_mode()
view.add_column("Notes")
view.set_values(new_column="Flag", column_type=ColumnType.TEXT, values=[SetValue("x")])
view.submit_draft()  # runs pipeline, refreshes metadata, exits draft mode
```

If an exception occurs inside the `with view.draft():` block, all queued tasks are discarded automatically. You can also discard explicitly with `view.discard_draft()`.

See [Views reference](#draft-mode) for the full API.

## See also

- [Views](#views-reference) -- transformation methods
- [Exceptions](#exceptions-reference) -- job-related exceptions
- [Configuration](#configuration) -- timeout settings


---


# Integrations

This guide demonstrates how to integrate the Mammoth SDK with external systems.

## Export to PostgreSQL

Use the View export to push data directly to a PostgreSQL database:

```python
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

## Export to MySQL

```python
view.export.to_mysql(
    host="mysql.example.com",
    port=3306,
    database="warehouse",
    table="processed_data",
    username="user",
    password="pass",
)
```

## Export to S3

```python
result = view.export.to_s3(file_name="report.csv")
```

## Export to BigQuery

```python
view.export.to_bigquery(
    project="my-gcp-project",
    dataset="analytics",
    table="results",
    # additional BigQuery configuration as needed
)
```

## Import from external sources

Pull data from an external database and upload to Mammoth:

```python
import pandas as pd
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# 1. Export from your source database to CSV
df = pd.read_sql("SELECT * FROM customers WHERE status = 'active'", connection)
df.to_csv("customers.csv", index=False)

# 2. Upload to Mammoth
client.files.upload("customers.csv")
```

## Branch out to another dataset

Send processed data from one view to another Mammoth dataset:

```python
view.branch_out(dest_dataset_id=42)

# With column mapping
view.branch_out(
    dest_dataset_id=42,
    column_mapping={"Sales": "revenue", "Region": "area"},
)
```

## Webhook integration

Set up webhooks to receive notifications on pipeline events:

```python
webhooks = client.webhooks.list()
```

## Scheduled automation

Use automations and schedules for recurring workflows:

```python
schedules = client.schedules.list()
automations = client.automations.list()
```

## See also

- [Exports reference](#exports-reference) -- all export destinations
- [Client API](#client-api-reference) -- sub-clients for webhooks, automations, schedules


---


# Owner journal broker

`scripts/owner_journal_broker.py` is a small owner-side component, separate
from the Mammoth CLI and from an agent workspace. It persists a fixed
workspace/project scope and operation allowlist once, accepts only a
secret-free intent id, operation, fixed scope, and payload SHA-256 digest, and
appends an fsynced intent record before invoking an owner-supplied transport
callback. Credentials and request payloads are deliberately out of scope.

When a callback returns, the broker appends an fsynced receipt containing only
the outcome and an optional job/resource handle. A repeated intent with a
receipt returns that receipt without another dispatch. An intent without a
receipt raises `ReconciliationRequired`; it never automatically replays.

This gives at-most-one dispatch by this broker instance per intent id. It is
not exactly-once backend execution: a crash after a backend commit and before
the receipt leaves an ambiguity that requires independent reconciliation or a
backend-supported idempotency key. An advisory owner-journal lock serializes
submissions sharing that journal. On Linux it fsyncs the parent directory after
creating the journal root, policy, or journal file; other platforms do not get
that directory-entry durability guarantee. The offline tests inject both crash
boundaries and verify no automatic replay. An intent ID is bound to the full
secret-free invocation fingerprint, so reusing it with a different operation,
scope, or payload digest is rejected.

## Fixed subprocess transport

`OwnerSubprocessSender` is the optional owner-side transport for a journal
broker. It accepts only a broker `Invocation`: its CLI executable and SHA-256
artifact digest, profile name, private configuration directory, workspace,
project, operation command, target, resource, input, confirmation decision,
and time budget are all fixed by `OwnerSubprocessPolicy`. It never accepts an
agent shell string, arbitrary environment, extra arguments, or destination.
The only supported commands are complete frozen operations selected by name;
agent-provided request bodies and external destinations are intentionally
unsupported in this slice.

The sender verifies the executable digest immediately before execution and
uses a minimal owner environment. It returns only redacted `ok`, `exit_status`,
`stdout`, and `stderr` observations (plus broker outcome fields); neither the
profile configuration nor its secrets enter the journal receipt.

Operations are one-shot by default: once a frozen operation has an intent,
another intent ID cannot dispatch it. The owner must explicitly mark a known
read operation repeatable. Fixed inputs are optional, but when used must be
private owner-controlled files outside the agent workspace with an approved
SHA-256 that is rechecked immediately before dispatch. Exit status 7 and a
structured `outcome_unknown` envelope remain `outcome_unknown`; the broker
does not reinterpret them as safe failures or replay them. Any other nonzero
result is also `outcome_unknown` unless the original private CLI error envelope
explicitly establishes `failed`/`not_started` or an authorization/usage-style
pre-dispatch failure. Classification parses the private stream before applying
presentation redaction, but does not persist that raw stream.

Output redaction is best-effort presentation hygiene, not credential isolation.
The journal never stores subprocess stdout or stderr, and protected profile
contents are kept outside the agent workspace; a production deployment still
needs an OS/process boundary appropriate to its credential store.

## Unix socket front-end

`OwnerBrokerSocketServer` is a Linux/Unix-only local front-end for a broker and
frozen sender. Its private owner-controlled directory and socket are mode 0700
and 0600. A request has exactly four strings: opaque trial handle, opaque
intent ID, allowlisted operation name, and payload digest. It cannot carry
argv, a profile/config path, credentials, environment, project/workspace, or
external destination. Invalid, oversized, malformed, and policy-denied frames
receive a generic denial response; an idle partial frame receives the same
response after a bounded receive timeout.

The successful response contains the durable receipt and, only for the initial
dispatch, a redacted process observation. Repeated receipts do not rerun the
sender or reconstruct output. Top-level `ok: true` means the broker accepted
and journaled the request, not that the remote operation succeeded; inspect
the receipt outcome and observation `ok` separately. Observation stdout/stderr
are capped with explicit `*_truncated` flags, so they never claim completeness.
This is not provider attestation, a credential
vault, or live qualification; deployment still needs peer authentication and
an appropriate protected-process boundary for its operating system.


---


# Troubleshooting

Common issues and their solutions.

## Authentication errors

**Symptom**: `MammothAuthError: Authentication failed`

**Solutions**:

- Verify your API key and secret are correct
- Confirm the `workspace_id` matches your account
- Check that the `base_url` points to the correct Mammoth instance
- Ensure your API credentials have not been revoked or rotated

```python
# Verify your credentials
try:
    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    if client.test_connection():
        print("Credentials are valid")
except MammothAuthError:
    print("Credentials are invalid")
```

## Column not found

**Symptom**: `MammothColumnError: Column 'X' not found. Available columns: [...]`

**Solutions**:

- Check the exact column display name (case-sensitive)
- Call `view.refresh()` if the view was modified externally
- Print `view.display_names` to see available columns

```python
print(view.display_names)
# ['Sales Amount', 'Region', 'Order Date']
# Note: "Sales" vs "Sales Amount" matters
```

## Job timeout

**Symptom**: `MammothJobTimeoutError: Job X timed out after Y seconds`

**Solutions**:

- Increase `job_timeout` on the client for large datasets
- For CSV exports, increase the `timeout` parameter on `to_csv()`
- Check the Mammoth dashboard to see if the job is still running

```python
# Increase job timeout
client = MammothClient(..., job_timeout=300)

# Increase CSV export timeout
view.export.to_csv("output.csv", timeout=600)
```

## Job failed

**Symptom**: `MammothJobFailedError: Job X failed: <reason>`

**Solutions**:

- Read the failure reason in `e.details["failure_reason"]`
- Check the Mammoth dashboard for detailed error logs
- Common causes: invalid column types for operations, data format issues

```python
try:
    from mammoth import ColumnType, ConversionSpec

    view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])
except MammothJobFailedError as e:
    print(f"Reason: {e.details['failure_reason']}")
```

## project_id not set

**Symptom**: `ValueError: project_id must be set on the client using client.set_project_id()`

**Solution**: Call `client.set_project_id(id)` before performing operations:

```python
client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)  # Required before most operations
```

## Date columns not working

**Symptom**: Date operations fail on columns uploaded from CSV.

**Cause**: CSV date columns are uploaded as TEXT type by default.

**Solution**: Convert to DATE type first:

```python
view.convert_type([{"column": "Order Date", "to": "DATE"}])
# Now date operations work
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
```

## Network / connection errors

**Symptom**: `MammothAPIError: Connection error: ...` or `Request timeout: ...`

**Solutions**:

- Check your network connectivity
- Verify the `base_url` is reachable
- Increase the `timeout` for slow networks

```python
client = MammothClient(..., timeout=120)  # 2 minutes per request
```

## Import errors

**Symptom**: `ImportError` or `ModuleNotFoundError` when importing from mammoth

**Solutions**:

- Ensure the package is installed: `pip install mammoth-io`
- Verify Python 3.12–3.14: `python --version`
- Check you are importing from the correct package: `from mammoth import MammothClient`

## See also

- [Exceptions reference](#exceptions-reference) -- error class documentation
- [Configuration](#configuration) -- timeout and URL settings
- [Error handling guide](#error-handling-guide) -- handling patterns


---


# Changelog

## v0.7.2

The current SDK release. It requires Python 3.12, 3.13, or 3.14 and improves
response outcome classification, effectful webhook GET metadata, and bounded
job waiting behavior.

## v0.7.1

The current SDK release. It includes the current transformation and pipeline
reliability fixes and requires Python 3.12, 3.13, or 3.14.

## v0.7.0

The current SDK release. It requires Python 3.12, 3.13, or 3.14. Transformation
arguments use the typed specifications and enums documented in the API
reference; the bundled `mammoth-cli` release is 1.1.3 and depends on SDK 0.7.x.

## v0.3.0

### Breaking changes

- **Removed `dataset_id` from ViewsResource methods** — `views.get()`, `views.list()`, `views.delete()`, `views.bulk_delete()`, `get_view()`, and `branch_out()` no longer accept a `dataset_id` parameter. The dataset is auto-detected via the pipeline API. `views.create()` still requires `dataset_id`.
- **Dict fallback paths removed** — all transformation methods now accept only typed dataclasses, not raw dicts:
    - `copy_columns()`: `list[CopySpec]` (not `list[dict]`)
    - `convert_type()`: `list[ConversionSpec]` (not `list[dict]`)
    - `set_values()`: `list[SetValue]` (not `list[dict]`)
    - `pivot()`: `list[AggregationSpec]` (not `list[dict]`)
    - `crosstab()`: `CrosstabSpec` (not `dict`)
    - `split_column()`: `list[SplitColumnSpec]` (not `list[dict]`)
    - `bulk_replace()`: `list[BulkReplaceMapping]` (not `list[dict]`)
    - `increment_date()`: `DateDelta` (not `dict`)
    - `join()`: `list[JoinKeySpec]` and `list[JoinSelectSpec]` (not `list[dict]`)
    - `json_extract()`: `list[JsonExtractionSpec]` and `JsonOpType` (not `list[dict]` and `str`)
    - `math()`: `str` only (removed `list[dict]` expression format)
- **String fields changed to enums** in dataclasses:
    - `CopySpec.type`: `ColumnType` (was `str`)
    - `ConversionSpec.to`: `ColumnType` (was `str`)
    - `AggregationSpec.function`: `AggregateFunction` (was `str | AggregateFunction`)
    - `CrosstabSpec.function`: `AggregateFunction` (was `str | AggregateFunction`)
    - `JsonExtractionSpec.type`: `ColumnType` (was `str`)
- **`to_s3()` file_type** — now `ExportFileType` enum (was `str`)

### Added

- **`SplitColumnSpec`** dataclass for `split_column()` new column specs
- **`BulkReplaceMapping`** dataclass for `bulk_replace()` search/replace mappings
- **`DateDelta`** dataclass for `increment_date()` with named fields (`years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`)
- **`JsonOpType`** enum — `JSON_OBJECT_TO_COLUMNS`, `JSON_LIST_TO_ROWS`
- **`ExportFileType`** enum — `CSV`, `JSON`, `PARQUET`
- **`HandlerType`** and **`TriggerType`** enums re-exported from top-level `mammoth` package

---

## v0.2.4

### Added

- **Draft mode** — batch multiple transformations and run the pipeline once:
    - `view.draft()` context manager (recommended): enters draft on entry, submits on clean exit, discards on exception
    - `view.enter_draft_mode()`, `view.submit_draft()`, `view.discard_draft()` for explicit control
    - `view.set_auto_run(enabled)` to toggle auto-run
    - `view.is_draft_mode` property to check current state
- **`DraftCommand` enum** — `ENTER`, `SUBMIT`, `DISCARD`, `EXIT` values for draft mode operations

### Fixed

- **`draft_mode()` API payload** — both `PipelineAPI.draft_mode()` and `DataviewsAPI.draft_mode()` now send `{"draft_operation": command}` instead of the incorrect `{"command": command}`

---

## v0.2.3

### Fixed

- **`_build_column_maps` now uses `taskwise_info` exclusively** — removed incorrect use of `dependencies_info.dependents` for column metadata resolution. `taskwise_info[last_seq]["metadata"]` is the authoritative post-pipeline column list; falls back to top-level `metadata` only for fresh views with no tasks.

---

## v0.2.2

### Fixed

- **`display_names` not updated after transforms** — `_build_column_maps` now reads column metadata from `taskwise_info[last_seq]["metadata"]` (the authoritative post-pipeline column list), so columns added by `math`, `set_values`, `add_column`, and other transforms appear immediately in `view.display_names`, `view.columns`, and `view.column_types`.

### Added

- **`view.get_metadata()`** — returns the current column list as `[{"display_name", "internal_name", "type"}, ...]`. Useful for inspecting all columns (including pipeline-added ones) after transforms.

---

## v0.2.0

Major release with rich View objects, transformation methods, and the condition builder.

### Added

- **View objects** -- rich domain objects wrapping Mammoth dataviews with 25+ transformation methods:
    - Filter: `filter_rows`, `set_values`
    - Math: `math` (string expression parser)
    - Column ops: `add_column`, `delete_columns`, `copy_columns`, `combine_columns`, `convert_type`
    - Text: `text_transform`, `replace_values`, `bulk_replace`, `split_column`, `substring`
    - Date: `extract_date`, `date_diff`, `increment_date`
    - Aggregation: `pivot`, `window`, `crosstab`
    - Row ops: `fill_missing`, `limit_rows`, `discard_duplicates`, `unnest`
    - Advanced: `join`, `lookup`, `json_extract`, `gen_ai`, `generate_sql`, `add_sql`, `sql`
- **Condition builder** -- `Condition` and `CompoundCondition` classes with `&` (AND) and `|` (OR) operator overloading
- **Enums** for all transformation parameters: `Operator`, `ColumnType`, `JoinType`, `TextCase`, `DateComponent`, `DateDiffUnit`, `WindowFunction`, `WindowRange`, `FillDirection`, `AggregateFunction`, `SortDirection`, `MathOperator`, `SubstringDirection`, `JsonType`, `FilterType`, `ProviderType`, `TaskType`, `ValueType`
- **SetValue dataclass** for conditional value specifications
- **ViewExport** class with export methods: `to_csv`, `to_s3`, `to_postgres`, `to_mysql`, `to_bigquery`, `to_redshift`, `to_elasticsearch`, `to_ftp`, `to_sftp`, `to_email`, `to_dataset`, `publish_to_db`
- **ViewsResource** (`client.views`) for get, list, create, delete, and bulk_delete operations returning rich View objects
- **MCP server** for Model Context Protocol integration with AI assistants
- **New exceptions**: `MammothTransformError`, `MammothColumnError`
- **New sub-clients**: `ai`, `connectors`, `dashboards`, `webhooks`, `automations`, `schedules`, `batches`, `browse`, `activity_logs`, `external_keys`, `client_apps`, `addons`, `reports`, `user_profile`, `workspaces`, `folders`
- `workspace_id` as a required constructor parameter on `MammothClient`
- `set_project_id()` method on the client
- `get_view()` convenience method on the client
- `find_dataset_for_dataview()` method on the client
- `parse_path()` helper for extracting IDs from Mammoth URLs
- Type hints throughout the codebase
- Pydantic response models for pipeline tasks and exports

### Changed

- `MammothClient` constructor now requires `workspace_id`
- Default `base_url` is now `"https://app.mammoth.io/api/v2"`
- `DEFAULT_TIMEOUT` is 30 seconds; `DEFAULT_JOB_TIMEOUT` is 60 seconds

## v0.1.0

Initial release.

### Added

- `MammothClient` with API key/secret authentication
- File upload and management via `client.files`
- Job tracking and polling via `client.jobs`
- CSV and S3 export via `client.exports`
- Dataset and dataview CRUD via `client.datasets` and `client.dataviews`
- Pipeline task management via `client.pipeline`
- Project management via `client.projects`
- Exception hierarchy: `MammothError`, `MammothAPIError`, `MammothAuthError`, `MammothJobTimeoutError`, `MammothJobFailedError`
- Context manager support for automatic session cleanup
