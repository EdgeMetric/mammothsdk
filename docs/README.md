# Mammoth Analytics Python SDK

**Version 0.3.0** | Python 3.10+ | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mammothsdk)

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
| [Installation](installation.md) | Install the SDK and set up your environment |
| [Quick Start](quick-start.md) | Get up and running in five minutes |
| [Authentication](authentication.md) | API credentials and authentication |
| **Core** | |
| [Client API](api/client.md) | `MammothClient` constructor, sub-clients, and methods |
| [Views](api/views.md) | `View` class -- properties, transformations, data access |
| [Conditions](api/conditions.md) | `Condition`, `CompoundCondition`, and `NotCondition` filter builder |
| [Enums](api/enums.md) | All enums: `Operator`, `ColumnType`, `JoinType`, and more |
| [Exceptions](api/exceptions.md) | Error classes and handling |
| **Import** | |
| [Files](api/files.md) | `FilesAPI` -- upload, list, and manage files |
| [Connectors](api/connectors.md) | `ConnectorsAPI` -- database and cloud connectors |
| **Transform** | |
| [Transformations](examples/transformations.md) | Practical transformation workflow examples |
| **Export** | |
| [Exports](api/exports.md) | `ViewExport` and `ExportsAPI` -- CSV, S3, databases |
| **Manage** | |
| [Projects](api/projects.md) | `ProjectsAPI` -- project CRUD and user management |
| [Datasets](api/datasets.md) | `DatasetsAPI` -- dataset CRUD and data access |
| [Dataviews](api/dataviews.md) | `DataviewsAPI` -- low-level dataview operations |
| [Pipeline](api/pipeline.md) | `PipelineAPI` -- transformation pipeline management |
| [Jobs](api/jobs.md) | `JobsAPI` -- async job tracking |
| [Dashboards](api/dashboards.md) | `DashboardsAPI` -- dashboard management |
| [Webhooks](api/webhooks.md) | `WebhooksAPI` -- webhook datasets |
| [Automations](api/automations.md) | `AutomationsAPI` and `SchedulesAPI` |
| [Workspace](api/workspace.md) | `WorkspaceAPI` and `UserProfileAPI` |
| [Other APIs](api/other-apis.md) | Folders, batches, browse, client apps, addons, and more |
| **Guides** | |
| [End-to-End Workflow](guides/end-to-end-workflow.md) | Complete journey: upload, transform, export |
| [Changelog](changelog.md) | Release history |

## Version information

- **SDK version**: 0.3.0
- **Python**: 3.10+
- **API version**: v2

## Support

- **Documentation**: [https://docs.mammoth.io](https://docs.mammoth.io)
- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mammothsdk/issues)
- **Email**: support@mammoth.io
