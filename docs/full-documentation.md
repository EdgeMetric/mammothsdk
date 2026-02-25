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
  - [Constructor](#constructor)
    - [Parameters](#parameters)
    - [Example](#example)
  - [Methods](#methods)
    - [set_project_id](#set_project_id)
    - [get_view](#get_view)
    - [find_dataset_for_dataview](#find_dataset_for_dataview)
    - [branch_out](#branch_out)
    - [test_connection](#test_connection)
  - [Context manager](#context-manager)
  - [Sub-clients](#sub-clients)
    - [Core data sub-clients](#core-data-sub-clients)
    - [Additional sub-clients](#additional-sub-clients)
    - [ViewsResource](#viewsresource)
  - [Request handling](#request-handling)
    - [Authentication headers](#authentication-headers)
    - [Error handling](#error-handling)
  - [See also](#see-also)
- [Views](#views)
  - [Getting a View](#getting-a-view)
  - [Properties](#properties)
  - [Data access](#data-access)
    - [data()](#data)
    - [get_metadata()](#get_metadata)
    - [refresh()](#refresh)
  - [Pipeline management](#pipeline-management)
    - [list_tasks()](#list_tasks)
    - [delete_task()](#delete_task)
    - [preview_task()](#preview_task)
    - [get_column_mapping()](#get_column_mapping)
  - [Draft mode](#draft-mode)
    - [draft() (context manager)](#draft-context-manager)
    - [enter_draft_mode()](#enter_draft_mode)
    - [submit_draft()](#submit_draft)
    - [discard_draft()](#discard_draft)
    - [set_auto_run()](#set_auto_run)
    - [is_draft_mode (property)](#is_draft_mode-property)
    - [Explicit draft workflow](#explicit-draft-workflow)
  - [Transformation methods](#transformation-methods)
    - [filter_rows](#filter_rows)
    - [set_values](#set_values)
    - [math](#math)
    - [join](#join)
    - [pivot](#pivot)
    - [window](#window)
    - [crosstab](#crosstab)
    - [add_column](#add_column)
    - [delete_columns](#delete_columns)
    - [copy_columns](#copy_columns)
    - [combine_columns](#combine_columns)
    - [convert_type](#convert_type)
    - [text_transform](#text_transform)
    - [replace_values](#replace_values)
    - [bulk_replace](#bulk_replace)
    - [split_column](#split_column)
    - [substring](#substring)
    - [extract_date](#extract_date)
    - [date_diff](#date_diff)
    - [increment_date](#increment_date)
    - [fill_missing](#fill_missing)
    - [limit_rows](#limit_rows)
    - [discard_duplicates](#discard_duplicates)
    - [unnest](#unnest)
    - [lookup](#lookup)
    - [json_extract](#json_extract)
    - [gen_ai](#gen_ai)
    - [generate_sql](#generate_sql)
    - [add_sql](#add_sql)
  - [Exports](#exports)
  - [See also](#see-also)
- [Conditions](#conditions)
  - [Condition](#condition)
    - [Examples](#examples)
  - [CompoundCondition](#compoundcondition)
  - [NotCondition](#notcondition)
    - [Using NotCondition with View methods](#using-notcondition-with-view-methods)
  - [Operator overloading](#operator-overloading)
  - [Using conditions with View methods](#using-conditions-with-view-methods)
    - [filter_rows](#filter_rows)
    - [set_values](#set_values)
    - [math, combine_columns, and other methods](#math-combine_columns-and-other-methods)
  - [build()](#build)
  - [All operators](#all-operators)
  - [See also](#see-also)
- [Enums & Data Classes](#enums-data-classes)
  - [Operator](#operator)
  - [ColumnType](#columntype)
  - [ValueType](#valuetype)
  - [JoinType](#jointype)
  - [TextCase](#textcase)
  - [DateComponent](#datecomponent)
    - [Basic components](#basic-components)
    - [Text-based extractions](#text-based-extractions)
    - [Composite formats](#composite-formats)
  - [DateDiffUnit](#datediffunit)
  - [AggregateFunction](#aggregatefunction)
  - [WindowFunction](#windowfunction)
  - [WindowRange](#windowrange)
  - [FillDirection](#filldirection)
  - [SortDirection](#sortdirection)
  - [MathOperator](#mathoperator)
  - [SubstringDirection](#substringdirection)
  - [JsonType](#jsontype)
  - [JsonOpType](#jsonoptype)
  - [FilterType](#filtertype)
  - [ProviderType](#providertype)
  - [TaskType](#tasktype)
  - [ExportFileType](#exportfiletype)
  - [NotCondition](#notcondition)
  - [SetValue dataclass](#setvalue-dataclass)
  - [CopySpec dataclass](#copyspec-dataclass)
  - [ConversionSpec dataclass](#conversionspec-dataclass)
  - [AggregationSpec dataclass](#aggregationspec-dataclass)
  - [CrosstabSpec dataclass](#crosstabspec-dataclass)
  - [JoinKeySpec dataclass](#joinkeyspec-dataclass)
  - [JoinSelectSpec dataclass](#joinselectspec-dataclass)
  - [SplitColumnSpec dataclass](#splitcolumnspec-dataclass)
  - [BulkReplaceMapping dataclass](#bulkreplacemapping-dataclass)
  - [DateDelta dataclass](#datedelta-dataclass)
  - [JsonExtractionSpec dataclass](#jsonextractionspec-dataclass)
  - [See also](#see-also)
- [Exceptions](#exceptions)
  - [Exception hierarchy](#exception-hierarchy)
  - [MammothError](#mammotherror)
  - [MammothAPIError](#mammothapierror)
  - [MammothAuthError](#mammothautherror)
  - [MammothJobTimeoutError](#mammothjobtimeouterror)
  - [MammothJobFailedError](#mammothjobfailederror)
  - [MammothTransformError](#mammothtransformerror)
  - [MammothColumnError](#mammothcolumnerror)
  - [Error handling patterns](#error-handling-patterns)
    - [Catch specific exceptions](#catch-specific-exceptions)
    - [Use the base class as a catch-all](#use-the-base-class-as-a-catch-all)
  - [See also](#see-also)
- [Files](#files)
  - [upload()](#upload)
    - [Examples](#examples)
    - [After upload: get a View](#after-upload-get-a-view)
  - [upload_folder()](#upload_folder)
    - [Example](#example)
  - [list()](#list)
    - [Example](#example)
  - [get()](#get)
    - [Example](#example)
  - [update()](#update)
  - [delete()](#delete)
    - [Example](#example)
  - [bulk_delete()](#bulk_delete)
    - [Example](#example)
  - [set_password()](#set_password)
  - [extract_sheets()](#extract_sheets)
    - [Example](#example)
  - [Supported file formats](#supported-file-formats)
  - [See also](#see-also)
- [Connectors](#connectors)
  - [Concepts](#concepts)
  - [Methods](#methods)
    - [list](#list)
    - [get](#get)
    - [active_connectors](#active_connectors)
    - [list_connections](#list_connections)
    - [create_connection](#create_connection)
    - [get_connection](#get_connection)
    - [update_connection](#update_connection)
    - [delete_connection](#delete_connection)
    - [list_ds_configs](#list_ds_configs)
    - [create_ds_config](#create_ds_config)
    - [get_ds_config](#get_ds_config)
    - [update_ds_config](#update_ds_config)
    - [delete_ds_config](#delete_ds_config)
  - [See also](#see-also)
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
  - [ViewExport](#viewexport)
    - [to_csv](#to_csv)
    - [to_s3](#to_s3)
    - [to_postgres](#to_postgres)
    - [to_mysql](#to_mysql)
    - [to_bigquery](#to_bigquery)
    - [to_redshift](#to_redshift)
    - [to_elasticsearch](#to_elasticsearch)
    - [to_ftp](#to_ftp)
    - [to_sftp](#to_sftp)
    - [to_email](#to_email)
    - [to_dataset](#to_dataset)
    - [publish_to_db](#publish_to_db)
    - [list](#list)
    - [delete](#delete)
  - [branch_out (View method)](#branch_out-view-method)
  - [ExportsAPI](#exportsapi)
    - [client.exports.to_csv](#clientexportsto_csv)
    - [client.exports.to_s3](#clientexportsto_s3)
    - [client.exports.to_dataset](#clientexportsto_dataset)
    - [client.exports.list](#clientexportslist)
    - [client.exports.create](#clientexportscreate)
  - [Export workflow example](#export-workflow-example)
  - [See also](#see-also)
- [Projects](#projects)
  - [Methods](#methods)
    - [list](#list)
    - [get](#get)
    - [create](#create)
    - [update](#update)
    - [delete](#delete)
    - [bulk_update](#bulk_update)
    - [bulk_delete](#bulk_delete)
    - [add_users](#add_users)
    - [remove_users](#remove_users)
    - [browse](#browse)
  - [See also](#see-also)
- [Datasets](#datasets)
  - [Methods](#methods)
    - [list](#list)
    - [get](#get)
    - [get_data](#get_data)
    - [create](#create)
    - [update](#update)
    - [delete](#delete)
    - [bulk_update](#bulk_update)
    - [bulk_delete](#bulk_delete)
    - [browse](#browse)
    - [list_batches](#list_batches)
    - [get_batch](#get_batch)
    - [get_file_settings](#get_file_settings)
  - [See also](#see-also)
- [Dataviews](#dataviews)
  - [Methods](#methods)
    - [list](#list)
    - [get](#get)
    - [create](#create)
    - [update](#update)
    - [delete](#delete)
    - [bulk_delete](#bulk_delete)
    - [get_data](#get_data)
    - [query_data](#query_data)
    - [active_users](#active_users)
    - [mark_active](#mark_active)
    - [conditional_format_list](#conditional_format_list)
    - [conditional_format_create](#conditional_format_create)
    - [conditional_format_update](#conditional_format_update)
    - [conditional_format_delete](#conditional_format_delete)
    - [draft_mode](#draft_mode)
  - [See also](#see-also)
- [Pipeline](#pipeline)
  - [Methods](#methods)
    - [get_pipeline](#get_pipeline)
    - [list_tasks](#list_tasks)
    - [add_task](#add_task)
    - [get_task](#get_task)
    - [update_task](#update_task)
    - [delete_task](#delete_task)
    - [preview_task](#preview_task)
    - [draft_mode](#draft_mode)
    - [edit_pipeline](#edit_pipeline)
    - [wait_for_pipeline](#wait_for_pipeline)
  - [Pipeline states](#pipeline-states)
  - [See also](#see-also)
- [Jobs](#jobs)
  - [Methods](#methods)
    - [get_job](#get_job)
    - [get_jobs](#get_jobs)
    - [wait_for_job](#wait_for_job)
    - [wait_for_jobs](#wait_for_jobs)
  - [Job statuses](#job-statuses)
  - [See also](#see-also)
- [Dashboards](#dashboards)
  - [Methods](#methods)
    - [list](#list)
    - [create](#create)
    - [get](#get)
    - [update](#update)
    - [delete](#delete)
    - [get_sources](#get_sources)
    - [get_analytics](#get_analytics)
    - [share](#share)
    - [action](#action)
    - [get_by_url](#get_by_url)
    - [get_draft_data](#get_draft_data)
    - [get_publish_data](#get_publish_data)
  - [See also](#see-also)
- [Webhooks](#webhooks)
  - [Methods](#methods)
    - [list](#list)
    - [create](#create)
    - [get](#get)
    - [update](#update)
    - [delete](#delete)
    - [send_data](#send_data)
    - [send_data_get](#send_data_get)
  - [See also](#see-also)
- [Automations & Schedules](#automations-schedules)
  - [AutomationsAPI](#automationsapi)
    - [Automation methods](#automation-methods)
    - [Schedule methods (via AutomationsAPI)](#schedule-methods-via-automationsapi)
  - [SchedulesAPI](#schedulesapi)
    - [list](#list)
    - [get](#get)
    - [create](#create)
    - [update](#update)
    - [delete](#delete)
  - [See also](#see-also)
- [Workspace & Users](#workspace-users)
  - [WorkspaceAPI](#workspaceapi)
    - [list](#list)
    - [get](#get)
    - [update](#update)
    - [delete](#delete)
    - [reactivate](#reactivate)
    - [list_users](#list_users)
    - [get_user](#get_user)
    - [update_user](#update_user)
  - [UserProfileAPI](#userprofileapi)
    - [get](#get)
    - [update](#update)
    - [change_password](#change_password)
    - [get_preferences](#get_preferences)
    - [update_preferences](#update_preferences)
  - [See also](#see-also)
- [Other APIs](#other-apis)
  - [FoldersAPI](#foldersapi)
    - [list](#list)
    - [create](#create)
    - [delete](#delete)
    - [move](#move)
  - [BatchesAPI](#batchesapi)
    - [list](#list)
    - [get](#get)
    - [create](#create)
    - [update](#update)
    - [delete](#delete)
  - [BrowseAPI](#browseapi)
    - [workspaces](#workspaces)
    - [projects](#projects)
    - [datasets](#datasets)
    - [dataviews](#dataviews)
  - [ClientAppsAPI](#clientappsapi)
    - [list](#list)
    - [create](#create)
    - [get](#get)
    - [update](#update)
    - [delete](#delete)
  - [ExternalKeysAPI](#externalkeysapi)
    - [list](#list)
    - [get](#get)
    - [create](#create)
    - [delete](#delete)
  - [ActivityLogsAPI](#activitylogsapi)
    - [list](#list)
    - [export](#export)
  - [AddonsAPI](#addonsapi)
    - [add_connector / remove_connector](#add_connector-remove_connector)
    - [add_storage / remove_storage](#add_storage-remove_storage)
    - [add_users / remove_users](#add_users-remove_users)
  - [ReportsAPI](#reportsapi)
    - [list](#list)
  - [AIAPI](#aiapi)
    - [generate_profile](#generate_profile)
    - [generate_data](#generate_data)
    - [get_data_gen_info](#get_data_gen_info)
    - [generate_sql](#generate_sql)
    - [get_suggestions](#get_suggestions)
    - [query_gen](#query_gen)
  - [See also](#see-also)
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

**Version 0.3.0** | Python 3.10+ | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mm-pysdk)

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
| [Enums](#enums-reference) | All enums: `Operator`, `ColumnType`, `JoinType`, and more |
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

- **SDK version**: 0.3.0
- **Python**: 3.10+
- **API version**: v2

## Support

- **Documentation**: [https://docs.mammoth.io](https://docs.mammoth.io)
- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mm-pysdk/issues)
- **Email**: support@mammoth.io


---


# Installation

## Requirements

- Python 3.10 or higher
- pip or Poetry package manager

## Install from PyPI

```bash
pip install mammoth-io==0.3.0
```

Or with Poetry:

```bash
poetry add mammoth-io==0.3.0
```

## Dependencies

The SDK has two runtime dependencies, installed automatically:

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ^2.32.0 | HTTP client for API requests |
| `pydantic` | ^2.11.0 | Data validation and response models |

## Development installation

Clone the repository and install with dev dependencies:

```bash
git clone https://github.com/EdgeMetric/mm-pysdk.git
cd mm-pysdk
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

- [Quick Start Guide](#quick-start-guide) -- create your first client and apply transformations
- [Authentication](#authentication) -- set up API credentials


---


# Quick Start Guide

Get up and running with the Mammoth Python SDK in five minutes.

## 1. Install the SDK

```bash
pip install mammoth-io==0.3.0
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
| `User-Agent` | `mammoth-io/0.3.0` |

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

## Constructor

```python
from mammoth import MammothClient

client = MammothClient(
    api_key: str,
    api_secret: str,
    workspace_id: int,
    base_url: str = "https://app.mammoth.io/api/v2",
    timeout: int = 30,
    job_timeout: int = 60,
    pipeline_timeout: int = 3600,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | Your Mammoth API key |
| `api_secret` | `str` | *required* | Your Mammoth API secret |
| `workspace_id` | `int` | *required* | Your Mammoth workspace ID |
| `base_url` | `str` | `"https://app.mammoth.io/api/v2"` | Base URL for the Mammoth API |
| `timeout` | `int` | `30` | Request timeout in seconds for individual HTTP calls |
| `job_timeout` | `int` | `60` | Maximum time in seconds to poll a job to completion |
| `pipeline_timeout` | `int` | `3600` | Maximum time in seconds to wait for pipeline tasks |

> **Note:** No retries
>
> The SDK does **not** implement automatic retries. If an API call fails, the error is raised immediately. Implement retry logic in your application if needed.
>

### Example

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

## Methods

### set_project_id

```python
client.set_project_id(project_id: int) -> None
```

Set the default project ID for the client. Required before most operations (listing datasets, working with views, running pipeline tasks, etc.).

```python
client.set_project_id(10)
```

### get_view

```python
client.get_view(view_id: int) -> View
```

Shortcut for `client.views.get(view_id)`. Returns a rich [View](#views-reference) object. The dataset is auto-detected.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `view_id` | `int` | *required* | ID of the dataview |

```python
view = client.get_view(1039)
print(view.display_names)
```

### find_dataset_for_dataview

```python
client.find_dataset_for_dataview(dataview_id: int) -> int
```

Searches all datasets in the current project to find which one contains the specified dataview. Returns the dataset ID.

```python
dataset_id = client.find_dataset_for_dataview(1039)
```

### branch_out

```python
client.branch_out(
    view_id: int,
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

Branch out (export) a view to another dataset. Convenience wrapper around `view.branch_out()`.

### test_connection

```python
client.test_connection() -> bool
```

Test connectivity and authentication. Returns `True` if the API is reachable and credentials are valid, `False` otherwise.

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

### ViewsResource

The `client.views` sub-client returns rich [View](#views-reference) objects (not raw dicts):

```python
# Get a single view
view = client.views.get(view_id=1039)

# List all views across all datasets in the project
views = client.views.list()

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)

# Delete a view
client.views.delete(view_id=1039)

# Bulk delete
client.views.bulk_delete(view_ids=[1039, 1040])
```

## Request handling

### Authentication headers

The client automatically attaches these headers to every request:

- `X-API-KEY` -- your API key
- `X-API-SECRET` -- your API secret
- `X-WORKSPACE-ID` -- your workspace ID
- `User-Agent` -- `mammoth-io/{version}`

### Error handling

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
# List all views in the project
views = client.views.list()

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

## Data access

### data()

Fetch rows from the dataview.

```python
view.data(
    limit: int = 400,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: Condition | CompoundCondition | None = None,
    sort: str | None = None,
) -> dict[str, Any]
```

Returns a dict with two keys:

- `"data"` — list of row dicts (keys are internal column names like `"column_1"`)
- `"paging"` — pagination info

```python
# Fetch first 100 rows
result = view.data(limit=100)
rows = result["data"]       # list of row dicts
print(len(rows))            # number of rows returned

# Fetch specific columns
result = view.data(columns=["Sales", "Region"])

# Fetch with a filter
result = view.data(condition=Condition("Sales", Operator.GTE, 1000))
```

### get_metadata()

Return the current column list as a list of dicts. Useful for inspecting the full column state after transformations.

```python
meta = view.get_metadata()
# [
#   {"display_name": "Sales", "internal_name": "column_1", "type": "NUMERIC"},
#   {"display_name": "Revenue", "internal_name": "column_xyzabc", "type": "NUMERIC"},
#   ...
# ]
```

### refresh()

Re-fetch metadata from the API and update local state. Returns `self` for chaining.

```python
view.refresh()
```

## Pipeline management

### list_tasks()

List all pipeline tasks on this dataview.

```python
tasks = view.list_tasks()
for task in tasks:
    print(task["id"], task["task_key"])
```

### delete_task()

Delete a pipeline task by ID. Refreshes view metadata after deletion.

```python
view.delete_task(task_id=42)
```

### preview_task()

Preview a task without applying it.

```python
preview = view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

### get_column_mapping()

Return a copy of the display-name-to-internal-name mapping.

```python
mapping = view.get_column_mapping()
# {"Sales": "column_1", "Region": "column_2", ...}
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

### enter_draft_mode()

Enter draft mode explicitly. All subsequent `_add_task()` calls skip pipeline execution.

```python
view.enter_draft_mode() -> dict[str, Any]
```

### submit_draft()

Submit queued tasks, run the pipeline, refresh metadata, and exit draft mode.

```python
view.submit_draft() -> dict[str, Any]
```

### discard_draft()

Discard all queued tasks, exit draft mode, and refresh metadata to the pre-draft state.

```python
view.discard_draft() -> dict[str, Any]
```

### set_auto_run()

Toggle auto-run on the pipeline. When disabled (``False``), the view enters draft mode and tasks are queued. When re-enabled (``True``), the view returns to auto-run mode.

```python
view.set_auto_run(enabled: bool) -> dict[str, Any]

view.set_auto_run(False)   # enter draft mode
view.set_auto_run(True)    # back to auto-run
```

### is_draft_mode (property)

Check whether the view is currently in draft mode.

```python
if view.is_draft_mode:
    print("Tasks are being queued")
```

### Explicit draft workflow

```python
view.enter_draft_mode()
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Price * 2", new_column="Double")
view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Transformation methods

All transformation methods are synchronous — they block until the operation completes and the view metadata is refreshed (unless in draft mode, where tasks are queued). Each method returns the API response dict.

### filter_rows

Filter rows by condition (SELECT task).

```python
view.filter_rows(
    condition: Condition | CompoundCondition | NotCondition,
    filter_type: FilterType = FilterType.SHOW,
    prompt: str = "",
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition` | `Condition \| CompoundCondition \| NotCondition` | *required* | Filter condition |
| `filter_type` | `FilterType` | `SHOW` | `SHOW` to keep matching rows, `REMOVE` to discard |
| `prompt` | `str` | `""` | Natural-language description of the filter intent |

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Combine conditions
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Create or update a column with conditional values (SET task).

```python
view.set_values(
    values: list[SetValue],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `values` | `list[SetValue]` | *required* | List of value specs (last one without a condition is the default) |
| `new_column` | `str \| None` | `None` | Name for a new column |
| `column_type` | `ColumnType` | `TEXT` | Type for the new column |
| `existing_column` | `str \| None` | `None` | Display name of existing column to update |
| `condition` | `Condition \| CompoundCondition \| NotCondition \| None` | `None` | Global condition applied to the whole task |

```python
from mammoth import SetValue, Condition, Operator, ColumnType

view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),  # default
    ],
)
```

### math

Apply arithmetic operations (MATH task). Accepts a string expression that is parsed automatically.

```python
view.math(
    expression: str,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
# String expression (recommended)
view.math("Price * Quantity", new_column="Total")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")

# Write to an existing column
view.math("Sales * 1.1", existing_column="Sales")
```

### join

Join with another dataview (JOIN task).

```python
view.join(
    foreign_view: int | View,
    join_type: JoinType,
    on: list[JoinKeySpec],
    select: list[str | JoinSelectSpec],
    column_prefix: str | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `foreign_view` | `int \| View` | View object or dataview ID to join with |
| `join_type` | `JoinType` | `INNER`, `LEFT`, `RIGHT`, or `OUTER` |
| `on` | `list[JoinKeySpec]` | Join keys as JoinKeySpec objects |
| `select` | `list[str \| JoinSelectSpec]` | Column names (str) or JoinSelectSpec objects |
| `column_prefix` | `str \| None` | Prefix for joined columns |

```python
from mammoth import JoinType, JoinKeySpec, JoinSelectSpec

# Join with a View object (display names everywhere)
other = client.views.get(2050)
view.join(
    foreign_view=other,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Name"],
)

# Join with a view ID (use internal names for the foreign view)
view.join(
    foreign_view=2050,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="column_1")],
    select=[JoinSelectSpec(column="column_7", alias="Category")],
)
```

### pivot

Group and aggregate (PIVOT task).

```python
view.pivot(
    group_by: list[str],
    aggregations: list[AggregationSpec],
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### window

Apply a window function (WINDOW task).

```python
view.window(
    function: WindowFunction,
    column: str | None = None,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
    range_type: WindowRange = WindowRange.UNBOUNDED,
) -> dict[str, Any]
```

```python
from mammoth import WindowFunction, SortDirection, WindowRange

# Row number per region, ordered by sales descending
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)

# Running sum
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### crosstab

Crosstab / pivot table (CROSSTAB task).

```python
view.crosstab(
    rows: list[str],
    pivot_column: str,
    select: CrosstabSpec,
) -> dict[str, Any]
```

```python
from mammoth import CrosstabSpec

view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(column="Sales", function=AggregateFunction.SUM),
)
```

### add_column

Add an empty column (ADD_COLUMN task).

```python
view.add_column(name: str, column_type: ColumnType = ColumnType.TEXT) -> dict
```

```python
view.add_column("Notes", ColumnType.TEXT)
```

### delete_columns

Remove columns (DELETE task).

```python
view.delete_columns(columns: list[str]) -> dict
```

```python
view.delete_columns(["Temp Column", "Debug"])
```

### copy_columns

Duplicate columns (COPY task).

```python
view.copy_columns(copies: list[CopySpec]) -> dict
```

```python
from mammoth import CopySpec, ColumnType

view.copy_columns([
    CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC),
])
```

### combine_columns

Concatenate columns with a separator (COMBINE task).

```python
view.combine_columns(
    sources: list[str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    separator: str = " ",
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### convert_type

Convert column data types (CONVERT task).

```python
view.convert_type(conversions: list[ConversionSpec]) -> dict
```

```python
from mammoth import ConversionSpec, ColumnType

view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Date", to=ColumnType.DATE),
])
```

### text_transform

Change text case or trim whitespace (TEXT_TRANSFORM task).

```python
view.text_transform(
    columns: list[str],
    case: TextCase | None = None,
    trim: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import TextCase

view.text_transform(columns=["Name"], case=TextCase.UPPER)
view.text_transform(columns=["Notes"], trim=True)
```

### replace_values

Find and replace text (REPLACE task).

```python
view.replace_values(
    columns: list[str],
    find: str,
    replace: str,
    match_case: bool = False,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### bulk_replace

Bulk find-and-replace with multiple mappings (REPLACE with MAPPING).

```python
view.bulk_replace(
    columns: list[str],
    mapping: list[BulkReplaceMapping],
    match_case: bool = True,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import BulkReplaceMapping

view.bulk_replace(
    columns=["Item"],
    mapping=[
        BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
        BulkReplaceMapping(search=["Small Coffee", "Large Coffee"], replace="Coffee"),
    ],
)
```

### split_column

Split a column by delimiter (SPLIT task).

```python
view.split_column(
    column: str,
    delimiter: str,
    new_columns: list[SplitColumnSpec],
) -> dict[str, Any]
```

```python
from mammoth import SplitColumnSpec

view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)
```

### substring

Extract a substring (SUBSTRING task).

```python
view.substring(
    column: str,
    direction: SubstringDirection | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Direction | Use with | Meaning |
|-----------|----------|---------|
| `START` | `num_char` | First N characters |
| `END` | `num_char` | Last N characters |
| `LEFT` | `char_position` | Characters before position |
| `RIGHT` | `char_position` | Characters after position |

```python
from mammoth import SubstringDirection

# First 3 characters
view.substring("Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

### extract_date

Extract date components (EXTRACT_DATE task).

```python
view.extract_date(
    column: str,
    component: DateComponent,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateComponent

view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")
view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
```

### date_diff

Calculate date difference (DATE_DIFF task).

```python
view.date_diff(
    component: DateDiffUnit,
    start: str,
    end: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDiffUnit

view.date_diff(
    DateDiffUnit.DAY,
    start="Start Date",
    end="End Date",
    new_column="Duration Days",
)
```

### increment_date

Add or subtract from a date (INCREMENT_DATE task).

```python
view.increment_date(
    column: str,
    delta: DateDelta,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDelta

view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended Due Date")
view.increment_date("Start Date", delta=DateDelta(months=-1, years=2), new_column="Adjusted")
```

### fill_missing

Fill missing values forward or backward (FILL task).

```python
view.fill_missing(
    column: str,
    direction: FillDirection,
    partition_by: str | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
from mammoth import FillDirection, SortDirection

view.fill_missing(
    "Price",
    direction=FillDirection.LAST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### limit_rows

Keep top or bottom N rows (LIMIT task).

```python
view.limit_rows(
    n: int,
    bottom: bool = False,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])
```

### discard_duplicates

Remove duplicate rows (DISCARD_DUPLICATES task).

```python
view.discard_duplicates(
    ignore_columns: list[str] | None = None,
) -> dict[str, Any]
```

```python
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### unnest

Unpivot columns to rows (UNNEST task).

```python
view.unnest(
    columns: list[str],
    label_column: str = "Label",
    value_column: str = "Value",
) -> dict[str, Any]
```

```python
view.unnest(
    columns=["Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"],
    label_column="Quarter",
    value_column="Sales",
)
```

### lookup

Look up values from another dataview (LOOKUP task).

```python
view.lookup(
    source: str,
    lookup_view_id: int,
    key: str,
    value: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
view.lookup(
    source="Product Code",
    lookup_view_id=2050,
    key="code",         # key column in the lookup view
    value="name",       # value column in the lookup view
    new_column="Product Name",
)
```

### json_extract

Extract data from a JSON column (JSON_HANDLE task).

```python
view.json_extract(
    column: str,
    json_type: JsonType = JsonType.OBJECT,
    keys: list[str] | None = None,
    extractions: list[JsonExtractionSpec] | None = None,
    keep_source: bool = False,
    op_type: JsonOpType | None = None,
) -> dict[str, Any]
```

```python
from mammoth import JsonType, JsonExtractionSpec, ColumnType

# Simple key extraction
view.json_extract("data", keys=["name", "email", "age"])

# Advanced with custom types
view.json_extract(
    "data",
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT),
        JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
    ],
)

# JSON list to rows
view.json_extract("items", json_type=JsonType.LIST)
```

### gen_ai

AI-powered transformation (GEN_AI task).

```python
view.gen_ai(
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    assistant_data: list[str] | None = None,
    context_columns_derivation: bool | None = None,
) -> dict[str, Any]
```

```python
view.gen_ai(
    prompt="Classify the sentiment of the review as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### generate_sql

Generate SQL from a natural language intent using Mammoth's LLM. Returns the generated SQL string. Also adds the task to the pipeline automatically.

```python
view.generate_sql(intent: str) -> str
```

```python
sql = view.generate_sql("count employees by department")
print(sql)  # "SELECT department, COUNT(*) ..."
```

### add_sql

Add a raw SQL query as a pipeline task.

```python
view.add_sql(query: str) -> dict[str, Any]
```

```python
view.add_sql("SELECT department, COUNT(*) as cnt FROM data GROUP BY department")
```

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
- [Enums](#enums-reference) -- all parameter enums
- [Exports](#exports-reference) -- export destinations
- [Transformation examples](#transformation-examples) -- practical workflows


---


# Conditions Reference

The condition module provides a Pythonic filter builder with operator overloading. Build conditions using `Condition` objects, combine them with `&` (AND), `|` (OR), and `~` (NOT), and pass them to View transformation methods.

## Condition

A single-column condition.

```python
from mammoth import Condition, Operator

Condition(
    column: str,
    operator: Operator | str,
    value: Any = None,
    case_sensitive: bool | None = None,
    value_is_column: bool = False,
    component: str | None = None,
    truncate: str | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | *required* | Display name of the column |
| `operator` | `Operator \| str` | *required* | Comparison operator (enum or raw string) |
| `value` | `Any` | `None` | Comparison value (omit for `IS_EMPTY` / `IS_NOT_EMPTY`) |
| `case_sensitive` | `bool \| None` | `None` | `None` = backend default (case-sensitive), `True` = case-sensitive, `False` = case-insensitive |
| `value_is_column` | `bool` | `False` | If `True`, `value` is treated as a column name for column-to-column comparison |
| `component` | `str \| None` | `None` | Date component for date-aware comparisons |
| `truncate` | `str \| None` | `None` | Date truncation level for date comparisons |

### Examples

```python
from mammoth import Condition, Operator

# Numeric comparisons
high_sales = Condition("Sales", Operator.GTE, 10000)
low_price = Condition("Price", Operator.LT, 5.0)

# Equality
west = Condition("Region", Operator.EQ, "West")

# List membership
selected = Condition("Region", Operator.IN_LIST, ["West", "East"])
excluded = Condition("Status", Operator.NOT_IN_LIST, ["Cancelled", "Refunded"])

# String matching
contains_corp = Condition("Name", Operator.CONTAINS, "Corp")
starts_with_a = Condition("Name", Operator.STARTS_WITH, "A")

# Null checks (no value needed)
empty = Condition("Name", Operator.IS_EMPTY)
not_empty = Condition("Email", Operator.IS_NOT_EMPTY)

# Aggregate checks
is_max = Condition("Sales", Operator.IS_MAXVAL)
is_min = Condition("Sales", Operator.IS_MINVAL)
```

## CompoundCondition

An AND/OR composition of conditions. Normally created automatically via `&` and `|` operators -- you rarely need to construct one directly.

```python
from mammoth import CompoundCondition

CompoundCondition(
    logic: str,          # "AND" or "OR"
    conditions: list[Condition | CompoundCondition | NotCondition],
)
```

## NotCondition

Negation of a condition. Created via the `~` (NOT) operator -- you rarely need to construct one directly.

```python
from mammoth import Condition, Operator

# Negate a single condition
not_closed = ~Condition("Status", Operator.EQ, "Closed")

# Negate a compound condition
not_priority = ~(Condition("Sales", Operator.GTE, 10000) & Condition("Region", Operator.EQ, "West"))

# Double negation cancels out: ~~cond returns the original condition
original = ~~not_closed  # same as Condition("Status", Operator.EQ, "Closed")

# Combine negated conditions with & and |
active = Condition("Status", Operator.EQ, "Active")
not_closed_and_active = ~Condition("Status", Operator.EQ, "Closed") & active
```

### Using NotCondition with View methods

```python
# Filter: keep rows where Status is NOT "Closed"
view.filter_rows(~Condition("Status", Operator.EQ, "Closed"))

# Set values with negated condition
view.set_values(
    new_column="Flag",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Open", condition=~Condition("Status", Operator.EQ, "Closed")),
        SetValue("Closed"),
    ],
)

# Math with negated condition
view.math("Sales * 1.1", new_column="Adjusted", condition=~Condition("Region", Operator.EQ, "East"))
```

## Operator overloading

Combine conditions with `&` (AND), `|` (OR), and `~` (NOT). Use parentheses for grouping.

```python
from mammoth import Condition, Operator

high_sales = Condition("Sales", Operator.GTE, 10000)
west = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.EQ, "Active")

# AND: all conditions must be true
both = high_sales & west

# OR: at least one must be true
either = high_sales | west

# Nested: parentheses control grouping
complex_cond = (high_sales & west) | active

# Chain multiple
all_three = high_sales & west & active
```

Chaining is flat when using the same operator:

```python
# These are equivalent:
a & b & c           # CompoundCondition("AND", [a, b, c])
(a & b) & c         # CompoundCondition("AND", [a, b, c])
```

Mixing operators creates nesting:

```python
(a & b) | c         # CompoundCondition("OR", [CompoundCondition("AND", [a, b]), c])
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

A global condition can also be applied to the entire task:

```python
view.set_values(
    existing_column="Label",
    values=[SetValue("Active")],
    condition=Condition("Status", Operator.EQ, "Active"),
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

## build()

The `build()` method converts a condition to the Mammoth API dict format. The SDK calls this automatically -- you normally do not need to call it yourself.

```python
cond = Condition("Sales", Operator.GTE, 1000)
payload = cond.build({"Sales": "column_1"})
# {"column_1": {"GTE": {"VALUE": 1000}}}

compound = cond & Condition("Region", Operator.EQ, "West")
payload = compound.build({"Sales": "column_1", "Region": "column_2"})
# {"AND": [{"column_1": {"GTE": {"VALUE": 1000}}}, {"column_2": {"EQ": {"VALUE": "West"}}}]}
```

## All operators

See the [Operator enum](#operator) for the complete list. Summary:

| Category | Operators |
|----------|-----------|
| Comparison | `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE` |
| List | `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS` |
| String | `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH` |
| Null | `IS_EMPTY`, `IS_NOT_EMPTY` |
| Aggregate | `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL` |

## See also

- [Enums](#enums-reference) -- all enum values
- [Views](#views-reference) -- transformation methods that use conditions
- [Transformation examples](#transformation-examples) -- practical workflows


---


# Enums Reference

The SDK provides enums for all transformation parameters. Import them directly from `mammoth`:

```python
from mammoth import Operator, ColumnType, JoinType, DateComponent
```

All enums are `str` subclasses (`class MyEnum(str, Enum)`) so they can be used directly as strings where needed.

---

## Operator

Filter operators for use with `Condition`.

```python
from mammoth import Operator
```

| Value | Description | Example value |
|-------|-------------|---------------|
| `Operator.GT` | Greater than | `1000` |
| `Operator.LT` | Less than | `5.0` |
| `Operator.GTE` | Greater than or equal | `1000` |
| `Operator.LTE` | Less than or equal | `100` |
| `Operator.EQ` | Equal | `"West"` |
| `Operator.NE` | Not equal | `"Cancelled"` |
| `Operator.IN_LIST` | Value is in list | `["West", "East"]` |
| `Operator.NOT_IN_LIST` | Value is not in list | `["Cancelled"]` |
| `Operator.CONTAINS` | String contains | `"Corp"` |
| `Operator.NOT_CONTAINS` | String does not contain | `"test"` |
| `Operator.STARTS_WITH` | String starts with | `"A"` |
| `Operator.ENDS_WITH` | String ends with | `"Inc"` |
| `Operator.NOT_STARTS_WITH` | String does not start with | `"X"` |
| `Operator.NOT_ENDS_WITH` | String does not end with | `"Ltd"` |
| `Operator.IS_EMPTY` | Value is null/empty | *(no value)* |
| `Operator.IS_NOT_EMPTY` | Value is not null/empty | *(no value)* |
| `Operator.IS_MAXVAL` | Value is the column max | *(no value)* |
| `Operator.IS_NOT_MAXVAL` | Value is not the column max | *(no value)* |
| `Operator.IS_MINVAL` | Value is the column min | *(no value)* |
| `Operator.IS_NOT_MINVAL` | Value is not the column min | *(no value)* |

---

## ColumnType

Column data types for new columns and type conversions.

```python
from mammoth import ColumnType
```

| Value | Description |
|-------|-------------|
| `ColumnType.TEXT` | Text/string data |
| `ColumnType.NUMERIC` | Numeric data (integers and decimals) |
| `ColumnType.DATE` | Date/datetime data |

---

## ValueType

Value types for expressions in pipeline tasks.

```python
from mammoth import ValueType
```

| Value | Description |
|-------|-------------|
| `ValueType.FIXED` | A literal value |
| `ValueType.EXPRESSION` | A system expression |
| `ValueType.COLUMN` | A column reference |
| `ValueType.NUMBER` | A numeric literal |
| `ValueType.OPERATOR` | An arithmetic operator |

---

## JoinType

Join types for combining dataviews.

```python
from mammoth import JoinType
```

| Value | Description |
|-------|-------------|
| `JoinType.INNER` | Inner join -- only matching rows |
| `JoinType.LEFT` | Left join -- all rows from left, matching from right |
| `JoinType.RIGHT` | Right join -- all rows from right, matching from left |
| `JoinType.OUTER` | Outer join -- all rows from both sides |

---

## TextCase

Text case transformations for `text_transform()`.

```python
from mammoth import TextCase
```

| Value | Description |
|-------|-------------|
| `TextCase.UPPER` | Convert to UPPERCASE |
| `TextCase.LOWER` | Convert to lowercase |
| `TextCase.TITLE` | Convert to Title Case |

---

## DateComponent

Date components for `extract_date()`. Values are lowercase to match the backend format.

```python
from mammoth import DateComponent
```

### Basic components

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR` | NUMERIC | Year (e.g., 2025) |
| `DateComponent.MONTH` | NUMERIC | Month number (1-12) |
| `DateComponent.DAY` | NUMERIC | Day of month (1-31) |
| `DateComponent.HOUR` | NUMERIC | Hour (0-23) |
| `DateComponent.MINUTE` | NUMERIC | Minute (0-59) |
| `DateComponent.SECOND` | NUMERIC | Second (0-59) |
| `DateComponent.WEEK` | NUMERIC | Week of year |
| `DateComponent.QUARTER` | NUMERIC | Quarter (1-4) |
| `DateComponent.DAY_OF_WEEK` | NUMERIC | Day of week number |
| `DateComponent.DAY_OF_YEAR` | NUMERIC | Day of year (1-366) |

### Text-based extractions

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.WEEKDAY_TEXT` | TEXT | Day name (e.g., "Monday") |
| `DateComponent.MONTH_TEXT` | TEXT | Month name (e.g., "January") |

### Composite formats

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR_MONTH` | NUMERIC | Year-month composite |
| `DateComponent.YEAR_WEEK` | NUMERIC | Year-week composite |
| `DateComponent.YEAR_QUARTER` | NUMERIC | Year-quarter composite |
| `DateComponent.MONTH_DAY` | NUMERIC | Month-day composite |
| `DateComponent.HOUR_MINUTE` | NUMERIC | Hour-minute composite |
| `DateComponent.HOUR_MINUTE_SECOND` | NUMERIC | Hour-minute-second composite |
| `DateComponent.YEAR_MONTH_DAY` | NUMERIC | Year-month-day composite |
| `DateComponent.YEAR_MONTH_DAY_AS_DATE` | TEXT | Date as formatted text |
| `DateComponent.MONTH_DAY_YEAR_HOUR_MINUTE_SECOND` | TEXT | Full datetime as text |
| `DateComponent.DATE_ONLY` | NUMERIC | Date-only component |

---

## DateDiffUnit

Units for `date_diff()` calculations. Values are UPPERCASE (distinct from `DateComponent`).

```python
from mammoth import DateDiffUnit
```

| Value | Description |
|-------|-------------|
| `DateDiffUnit.YEAR` | Difference in years |
| `DateDiffUnit.MONTH` | Difference in months |
| `DateDiffUnit.DAY` | Difference in days |
| `DateDiffUnit.HOUR` | Difference in hours |
| `DateDiffUnit.MINUTE` | Difference in minutes |
| `DateDiffUnit.SECOND` | Difference in seconds |
| `DateDiffUnit.WEEK` | Difference in weeks |
| `DateDiffUnit.QUARTER` | Difference in quarters |

---

## AggregateFunction

Aggregate functions for `pivot()` and group operations.

```python
from mammoth import AggregateFunction
```

| Value | Description |
|-------|-------------|
| `AggregateFunction.SUM` | Sum of values |
| `AggregateFunction.AVG` | Average of values |
| `AggregateFunction.MIN` | Minimum value |
| `AggregateFunction.MAX` | Maximum value |
| `AggregateFunction.COUNT` | Count of values |
| `AggregateFunction.COUNT_DISTINCT` | Count of distinct values |
| `AggregateFunction.STDDEV` | Standard deviation |
| `AggregateFunction.VARIANCE` | Variance |
| `AggregateFunction.MEDIAN` | Median value |
| `AggregateFunction.FIRST` | First value |
| `AggregateFunction.LAST` | Last value |
| `AggregateFunction.CONCAT` | Concatenate values |

---

## WindowFunction

Window functions for `window()`.

```python
from mammoth import WindowFunction
```

| Value | Description |
|-------|-------------|
| `WindowFunction.ROW_NUMBER` | Sequential row number |
| `WindowFunction.RANK` | Rank with gaps |
| `WindowFunction.DENSE_RANK` | Rank without gaps |
| `WindowFunction.LAG` | Previous row value |
| `WindowFunction.LEAD` | Next row value |
| `WindowFunction.SUM` | Window sum |
| `WindowFunction.AVG` | Window average |
| `WindowFunction.MIN` | Window minimum |
| `WindowFunction.MAX` | Window maximum |
| `WindowFunction.COUNT` | Window count |
| `WindowFunction.FIRST_VALUE` | First value in window |
| `WindowFunction.LAST_VALUE` | Last value in window |
| `WindowFunction.STDDEV` | Window standard deviation |
| `WindowFunction.VARIANCE` | Window variance |
| `WindowFunction.PERCENT_RANK` | Percent rank |
| `WindowFunction.NTILE` | N-tile distribution |

---

## WindowRange

Window range types for `window()`.

```python
from mammoth import WindowRange
```

| Value | Description |
|-------|-------------|
| `WindowRange.UNBOUNDED` | Entire partition |
| `WindowRange.RUNNING` | Running window (start of partition to current row) |

---

## FillDirection

Fill directions for `fill_missing()`.

```python
from mammoth import FillDirection
```

| Value | Description |
|-------|-------------|
| `FillDirection.FIRST_VALUE` | Fill with the first non-null value going forward |
| `FillDirection.LAST_VALUE` | Fill with the last non-null value going backward |

---

## SortDirection

Sort direction for `order_by` parameters.

```python
from mammoth import SortDirection
```

| Value | Description |
|-------|-------------|
| `SortDirection.ASC` | Ascending order |
| `SortDirection.DESC` | Descending order |

---

## MathOperator

Arithmetic operators for math expressions.

```python
from mammoth import MathOperator
```

| Value | Symbol | Description |
|-------|--------|-------------|
| `MathOperator.ADD` | `+` | Addition |
| `MathOperator.SUBTRACT` | `-` | Subtraction |
| `MathOperator.MULTIPLY` | `*` | Multiplication |
| `MathOperator.DIVIDE` | `/` | Division |
| `MathOperator.MODULO` | `%` | Modulo (remainder) |

---

## SubstringDirection

Extraction direction for `substring()`.

```python
from mammoth import SubstringDirection
```

| Value | Use with | Description |
|-------|----------|-------------|
| `SubstringDirection.START` | `num_char` | Extract first N characters |
| `SubstringDirection.END` | `num_char` | Extract last N characters |
| `SubstringDirection.LEFT` | `char_position` | Extract characters before position |
| `SubstringDirection.RIGHT` | `char_position` | Extract characters after position |

---

## JsonType

JSON structure types for `json_extract()`.

```python
from mammoth import JsonType
```

| Value | Description |
|-------|-------------|
| `JsonType.OBJECT` | JSON object (`{...}`) -- extract keys to columns |
| `JsonType.LIST` | JSON list (`[...]`) -- extract items to rows |

---

## JsonOpType

Operation types for `json_extract()`.

```python
from mammoth import JsonOpType
```

| Value | Description |
|-------|-------------|
| `JsonOpType.JSON_OBJECT_TO_COLUMNS` | Extract object keys to separate columns |
| `JsonOpType.JSON_LIST_TO_ROWS` | Extract list items to separate rows |

---

## FilterType

Filter types for `filter_rows()`.

```python
from mammoth import FilterType
```

| Value | Description |
|-------|-------------|
| `FilterType.SHOW` | Keep rows that match the condition |
| `FilterType.REMOVE` | Discard rows that match the condition |

---

## ProviderType

Value provider types for SET task values.

```python
from mammoth import ProviderType
```

| Value | Description |
|-------|-------------|
| `ProviderType.FIXED` | A literal value (e.g., `"High"`, `42`) |
| `ProviderType.EXPRESSION` | A system expression (e.g., `"__TIME__"` for current timestamp) |

---

## TaskType

Pipeline task type identifiers.

```python
from mammoth import TaskType
```

| Value | Description |
|-------|-------------|
| `TaskType.SET` | Set/label values |
| `TaskType.SELECT` | Filter rows |
| `TaskType.MATH` | Arithmetic operations |
| `TaskType.JOIN` | Join dataviews |
| `TaskType.PIVOT` | Group and aggregate |
| `TaskType.WINDOW` | Window functions |
| `TaskType.FILL` | Fill missing values |
| `TaskType.LIMIT` | Limit rows |
| `TaskType.LOOKUP` | Lookup from another view |
| `TaskType.COMBINE` | Concatenate columns |
| `TaskType.CONVERT` | Convert column types |
| `TaskType.COPY` | Copy columns |
| `TaskType.DELETE` | Delete columns |
| `TaskType.ADD_COLUMN` | Add empty column |
| `TaskType.REPLACE` | Find and replace |
| `TaskType.SPLIT` | Split column |
| `TaskType.SUBSTRING` | Extract substring |
| `TaskType.TEXT_TRANSFORM` | Text case / trim |
| `TaskType.EXTRACT_DATE` | Extract date part |
| `TaskType.DATE_DIFF` | Date difference |
| `TaskType.INCREMENT_DATE` | Add/subtract from date |
| `TaskType.UNNEST` | Unpivot columns to rows |
| `TaskType.CROSSTAB` | Crosstab / pivot table |
| `TaskType.JSON_HANDLE` | JSON extraction |
| `TaskType.GEN_AI` | AI transformation |
| `TaskType.SQL` | SQL query |
| `TaskType.DISCARD_DUPLICATES` | Remove duplicate rows |

---

## ExportFileType

File types for `to_s3()` export.

```python
from mammoth import ExportFileType
```

| Value | Description |
|-------|-------------|
| `ExportFileType.CSV` | CSV format |
| `ExportFileType.JSON` | JSON format |
| `ExportFileType.PARQUET` | Parquet format |

---

## NotCondition

Not an enum, but important to know about when building conditions. The `~` operator negates any condition.

```python
from mammoth import Condition, Operator

# Negate with ~
not_closed = ~Condition("Status", Operator.EQ, "Closed")
not_compound = ~(Condition("Sales", Operator.GTE, 10000) & Condition("Region", Operator.EQ, "West"))

# Double negation cancels: ~~cond returns original
original = ~~not_closed
```

See [Conditions reference](#notcondition) for full documentation and examples.

---

## SetValue dataclass

Not an enum, but frequently used alongside enums. A dataclass for `set_values()` value specs.

```python
from mammoth import SetValue

SetValue(
    value: Any,
    condition: Condition | CompoundCondition | NotCondition | None = None,
)
```

```python
from mammoth import SetValue, Condition, Operator

values = [
    SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
    SetValue("Low"),  # default value (no condition)
]
```

---

## CopySpec dataclass

Spec for `copy_columns()`.

```python
from mammoth import CopySpec, ColumnType

CopySpec(
    source: str,              # Source column display name
    as_name: str,             # New column display name
    type: ColumnType = ColumnType.TEXT,  # Column type
)
```

---

## ConversionSpec dataclass

Spec for `convert_type()`.

```python
from mammoth import ConversionSpec, ColumnType

ConversionSpec(
    column: str,              # Column display name
    to: ColumnType,           # Target type
    format: str | None = None,  # Date format (for TEXT→DATE)
)
```

---

## AggregationSpec dataclass

Spec for `pivot()` aggregations.

```python
from mammoth import AggregationSpec, AggregateFunction

AggregationSpec(
    column: str,                 # Column to aggregate
    function: AggregateFunction, # Aggregation function
    as_name: str | None = None,  # Output column name (auto-generated if None)
    delimiter: str | None = None,  # Delimiter for CONCAT function
)
```

---

## CrosstabSpec dataclass

Spec for `crosstab()` aggregation.

```python
from mammoth import CrosstabSpec, AggregateFunction

CrosstabSpec(
    function: AggregateFunction,  # Aggregation function
    column: str | None = None,    # Column to aggregate (None for COUNT)
)
```

---

## JoinKeySpec dataclass

Join key mapping for `join()`.

```python
from mammoth import JoinKeySpec

JoinKeySpec(
    left: str,   # Column from the left (current) view
    right: str,  # Column from the right (foreign) view
)
```

---

## JoinSelectSpec dataclass

Column selection for `join()` foreign columns.

```python
from mammoth import JoinSelectSpec

JoinSelectSpec(
    column: str,                  # Foreign column name
    alias: str | None = None,     # Alias in the joined result
)
```

---

## SplitColumnSpec dataclass

Spec for `split_column()` output columns.

```python
from mammoth import SplitColumnSpec, ColumnType

SplitColumnSpec(
    name: str,                          # New column name
    type: ColumnType = ColumnType.TEXT,  # Column type
)
```

---

## BulkReplaceMapping dataclass

Mapping for `bulk_replace()`.

```python
from mammoth import BulkReplaceMapping

BulkReplaceMapping(
    search: list[str],  # Values to search for
    replace: str,       # Replacement value
)
```

---

## DateDelta dataclass

Time delta for `increment_date()`.

```python
from mammoth import DateDelta

DateDelta(
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
)
```

```python
# Add 30 days
view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended")

# Subtract 1 month, add 2 years
view.increment_date("Start", delta=DateDelta(months=-1, years=2), new_column="Adjusted")
```

---

## JsonExtractionSpec dataclass

Spec for `json_extract()` custom extractions.

```python
from mammoth import JsonExtractionSpec, ColumnType

JsonExtractionSpec(
    key: str,                           # JSON key to extract
    as_name: str | None = None,         # Output column name (defaults to key)
    type: ColumnType = ColumnType.TEXT,  # Output column type
)
```

## See also

- [Conditions](#conditions-reference) -- using `Operator` with `Condition`
- [Views](#views-reference) -- transformation methods that use these enums


---


# Exceptions Reference

The SDK provides a hierarchy of exception classes for precise error handling.

## Exception hierarchy

```
MammothError                     # Base exception for all SDK errors
  +-- MammothAPIError            # API request failures (HTTP errors, network errors)
  |     +-- MammothAuthError     # Authentication failures (HTTP 401)
  +-- MammothJobTimeoutError     # Job polling timeout
  +-- MammothJobFailedError      # Job execution failure
  +-- MammothTransformError      # Transformation task failure
  +-- MammothColumnError         # Column name resolution failure
```

## MammothError

Base exception for all Mammoth SDK errors.

```python
class MammothError(Exception):
    message: str
    details: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error message |
| `details` | `dict` | Additional error details (default `{}`) |

```python
from mammoth import MammothError

try:
    ...
except MammothError as e:
    print(e.message)
    print(e.details)
```

## MammothAPIError

Raised for API-related errors: HTTP 4xx/5xx responses, network errors, timeouts, and invalid responses.

```python
class MammothAPIError(MammothError):
    status_code: int | None
    response_body: dict[str, Any]
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `status_code` | `int \| None` | HTTP status code (if available) |
| `response_body` | `dict` | Full API response body (default `{}`) |
| `details` | `dict` | Additional error details |

```python
from mammoth import MammothAPIError

try:
    datasets = client.datasets.list()
except MammothAPIError as e:
    print(f"API error: {e.message}")
    print(f"HTTP status: {e.status_code}")
    print(f"Response: {e.response_body}")
```

## MammothAuthError

Raised when authentication fails (HTTP 401). Subclass of `MammothAPIError`.

```python
class MammothAuthError(MammothAPIError):
    pass  # status_code is always 401
```

```python
from mammoth import MammothAuthError

try:
    client = MammothClient(api_key="bad", api_secret="bad", workspace_id=1)
    client.set_project_id(1)
    client.projects.list()
except MammothAuthError:
    print("Invalid API credentials")
```

## MammothJobTimeoutError

Raised when a job does not complete within the allowed timeout.

```python
class MammothJobTimeoutError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the timed-out job |
| `details["timeout"]` | `int` | Timeout value in seconds |

```python
from mammoth import MammothJobTimeoutError

try:
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
except MammothJobTimeoutError as e:
    job_id = e.details["job_id"]
    timeout = e.details["timeout"]
    print(f"Job {job_id} timed out after {timeout}s")
```

## MammothJobFailedError

Raised when a job completes with a failure status.

```python
class MammothJobFailedError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["job_id"]` | `int` | ID of the failed job |
| `details["failure_reason"]` | `str \| None` | Reason for failure |

```python
from mammoth import MammothJobFailedError

try:
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed: {e.details['failure_reason']}")
```

## MammothTransformError

Raised when a transformation task fails. Includes the task key for identification.

```python
class MammothTransformError(MammothError):
    task_key: str | None
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `task_key` | `str \| None` | Pipeline task key (e.g., `"SET"`, `"MATH"`) |
| `details` | `dict` | Additional error details |

```python
from mammoth import MammothTransformError

try:
    view.math("InvalidColumn * 2", new_column="Result")
except MammothTransformError as e:
    print(f"Transform failed: {e.message}")
    print(f"Task: {e.task_key}")
```

## MammothColumnError

Raised when a column display name cannot be resolved to an internal name. Includes the list of available columns for easy debugging.

```python
class MammothColumnError(MammothError):
    pass
```

| Detail key | Type | Description |
|------------|------|-------------|
| `details["column_name"]` | `str` | The column name that was not found |
| `details["available_columns"]` | `list[str] \| None` | List of valid column names |

```python
from mammoth import MammothColumnError

try:
    view.filter_rows(Condition("Nonexistent", Operator.GTE, 100))
except MammothColumnError as e:
    print(e.message)
    # "Column 'Nonexistent' not found. Available columns: ['Sales', 'Region', ...]"
```

## Error handling patterns

### Catch specific exceptions

```python
from mammoth import (
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothColumnError,
)

try:
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

except MammothAuthError:
    print("Invalid credentials -- check API key and secret")

except MammothColumnError as e:
    print(f"Column not found: {e.details['column_name']}")
    print(f"Available: {e.details['available_columns']}")

except MammothJobTimeoutError as e:
    print(f"Job {e.details['job_id']} timed out")

except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed: {e.details['failure_reason']}")

except MammothAPIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

### Use the base class as a catch-all

```python
from mammoth import MammothError

try:
    view.math("Price * Quantity", new_column="Total")
except MammothError as e:
    print(f"Mammoth error: {e.message}")
```

## See also

- [Client](#client-api-reference) -- how the client raises exceptions
- [Views](#views-reference) -- transformation methods that can raise errors


---


# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion. Access it via `client.files`.

## upload()

Upload one or more files to create datasets. Each file becomes a separate dataset.

```python
client.files.upload(
    files: list[str | Path | BinaryIO] | str | Path | BinaryIO,
    folder_resource_id: str | None = None,
    append_to_ds_id: int | None = None,
    override_target_schema: bool | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `str`, `Path`, `BinaryIO`, or list | *required* | File path(s), Path objects, or file-like objects to upload |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `append_to_ds_id` | `int` | `None` | Dataset ID to append data to (instead of creating new) |
| `override_target_schema` | `bool` | `None` | Override target schema when appending |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

**Returns:**

- Single file: `int` (the dataset ID)
- Multiple files: `list[int]` (list of dataset IDs)
- On failure or `wait_for_completion=False`: `None` or initial job ID

### Examples

```python
# Single file upload
dataset_id = client.files.upload("sales_data.csv")

# Multiple files
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx", "products.tsv"])

# Using Path objects
from pathlib import Path
dataset_id = client.files.upload(Path("data/report.csv"))

# Append to existing dataset
client.files.upload("new_rows.csv", append_to_ds_id=42)

# Upload to a specific folder
client.files.upload("data.csv", folder_resource_id="folder-abc-123")

# Non-blocking upload (returns job ID immediately)
job_id = client.files.upload("large_file.csv", wait_for_completion=False)
```

### After upload: get a View

```python
dataset_id = client.files.upload("sales_data.csv")
views = client.views.list()
# Find the view for the uploaded dataset
view = next(v for v in views if v.dataset_id == dataset_id)
print(view.display_names)  # ["Column1", "Column2", ...]
```

---

## upload_folder()

Upload all files in a folder. Calls `upload()` under the hood.

```python
client.files.upload_folder(
    folder_path: str | Path,
    folder_resource_id: str | None = None,
    wait_for_completion: bool = True,
    timeout: int = 300,
) -> list[int] | int | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | `str` or `Path` | *required* | Path to the folder containing files |
| `folder_resource_id` | `str` | `None` | Resource ID of target folder in Mammoth |
| `wait_for_completion` | `bool` | `True` | Wait for upload processing to finish |
| `timeout` | `int` | `300` | Timeout in seconds when waiting |

### Example

```python
# Upload everything in a folder
dataset_ids = client.files.upload_folder("./data/monthly_reports/")
```

---

## list()

List files in the current project with optional filtering and pagination.

```python
client.files.list(
    fields: str | None = None,
    file_ids: list[int] | None = None,
    names: list[str] | None = None,
    statuses: list[str] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> FilesList
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | `str` | `None` | Fields to return (`"__standard"`, `"__full"`, `"__min"`) |
| `file_ids` | `list[int]` | `None` | Filter by specific file IDs |
| `names` | `list[str]` | `None` | Filter by file names |
| `statuses` | `list[str]` | `None` | Filter by file statuses |
| `created_at` | `str` | `None` | Date range filter for creation date |
| `updated_at` | `str` | `None` | Date range filter for update date |
| `limit` | `int` | `50` | Maximum results (0-100) |
| `offset` | `int` | `0` | Number of results to skip |
| `sort` | `str` | `None` | Sort spec (e.g., `"(id:asc)"`, `"(name:desc)"`) |

### Example

```python
files = client.files.list()
for f in files.files:
    print(f"{f.id}: {f.name} ({f.status})")

# Filter by name
files = client.files.list(names=["sales_data.csv"])
```

---

## get()

Get detailed information about a specific file.

```python
client.files.get(
    file_id: int,
    fields: str | None = None,
) -> FileSchema
```

### Example

```python
file_info = client.files.get(file_id=123)
print(f"Name: {file_info.name}")
print(f"Status: {file_info.status}")
```

---

## update()

Update file configuration (e.g., set password, extract sheets). Waits for the job to complete.

```python
client.files.update(
    file_id: int,
    patch_request: FilePatchRequest,
) -> ObjectJobSchema
```

This is the low-level method used internally by `set_password()` and `extract_sheets()`. You rarely need to call it directly.

---

## delete()

Delete a specific file.

```python
client.files.delete(file_id: int) -> None
```

### Example

```python
client.files.delete(file_id=123)
```

---

## bulk_delete()

Delete multiple files at once.

```python
client.files.bulk_delete(file_ids: list[int]) -> None
```

### Example

```python
client.files.bulk_delete([101, 102, 103])
```

---

## set_password()

Set a password for a password-protected file (e.g., encrypted Excel).

```python
client.files.set_password(file_id: int, password: str) -> ObjectJobSchema
```

---

## extract_sheets()

Extract specific sheets from an Excel file into separate datasets.

```python
client.files.extract_sheets(
    file_id: int,
    sheets: list[str],
    delete_file_after_extract: bool = True,
    combine_after_extract: bool = False,
) -> ObjectJobSchema
```

### Example

```python
client.files.extract_sheets(
    file_id=123,
    sheets=["Sheet1", "Revenue"],
    delete_file_after_extract=True,
)
```

---

## Supported file formats

| Category | Formats |
|----------|---------|
| Tabular | CSV, TSV, PSV, XLS, XLSX |
| Compressed | ZIP, BZ2, GZ, TAR, 7Z |
| Document | PDF |
| Image | TIFF, JPEG, PNG, HEIC, WEBP |

**Maximum file size:** 50 MB

---

## See also

- [End-to-End Workflow](#end-to-end-workflow) -- upload, transform, and export
- [Client API](#client-api-reference) -- `MammothClient` and all sub-clients
- [Views](#views-reference) -- work with uploaded data


---


# Connectors API Reference

The `ConnectorsAPI` manages cloud data source connectors and their connections. Use connectors to import data from databases (PostgreSQL, MySQL, BigQuery, etc.), cloud storage, and other external sources.

**Access**: `client.connectors`

## Concepts

- **Connector**: A type of data source (e.g. `"postgres"`, `"mysql"`, `"bigquery"`)
- **Connection**: A configured instance of a connector (host, credentials, etc.)
- **Data source config**: A specific table/query within a connection to import

## Methods

### list

```python
client.connectors.list() -> list[dict[str, Any]]
```

List all available connector types.

**Returns**: List of connector dicts with keys like `key`, `name`, `type`.

```python
connectors = client.connectors.list()
for c in connectors:
    print(c["key"], c["name"])
```

### get

```python
client.connectors.get(
    connector_key: str,
) -> dict[str, Any]
```

Get details of a specific connector type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key (e.g. `"postgres"`, `"mysql"`) |

### active_connectors

```python
client.connectors.active_connectors() -> list[dict[str, Any]]
```

List connectors that have at least one established connection.

### list_connections

```python
client.connectors.list_connections(
    connector_key: str,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List connections for a connector type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |

**Returns**: List of connection dicts.

```python
connections = client.connectors.list_connections("postgres")
for conn in connections:
    print(conn["key"], conn.get("name"))
```

### create_connection

```python
client.connectors.create_connection(
    connector_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new connection for a connector.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `config` | `dict` | *required* | Connection configuration (host, port, database, credentials, etc.) |

```python
conn = client.connectors.create_connection("postgres", {
    "host": "db.example.com",
    "port": 5432,
    "database": "analytics",
    "username": "user",
    "password": "pass",
    "name": "Prod DB",
})
```

### get_connection

```python
client.connectors.get_connection(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific connection.

### update_connection

```python
client.connectors.update_connection(
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a connection's configuration.

### delete_connection

```python
client.connectors.delete_connection(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a connection.

### list_ds_configs

```python
client.connectors.list_ds_configs(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List data source configurations for a connection. Each config represents a table, query, or file to import.

### create_ds_config

```python
client.connectors.create_ds_config(
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a data source configuration to import data from a connection.

### get_ds_config

```python
client.connectors.get_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get a specific data source configuration.

### update_ds_config

```python
client.connectors.update_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a data source configuration.

### delete_ds_config

```python
client.connectors.delete_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a data source configuration.

## See also

- [Files](#files-api-reference) -- File-based data import
- [Exports](#exports-reference) -- Export data to external destinations
- [Client](#client-api-reference) -- MammothClient overview


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
- [Enums reference](#enums-reference) -- all parameter values
- [Exports reference](#exports-reference) -- all export destinations


---


# Exports Reference

The SDK provides two ways to export data:

1. **ViewExport** (`view.export`) -- export methods attached to a View object
2. **ExportsAPI** (`client.exports`) -- lower-level export operations

## ViewExport

Access via `view.export`. This is the recommended way to export data from a View.

### to_csv

Download the view data as a local CSV file.

```python
view.export.to_csv(
    output_path: str | None = None,
    timeout: int = 300,
) -> Path
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_path` | `str \| None` | `None` | Output file path (auto-generated if not provided) |
| `timeout` | `int` | `300` | Timeout in seconds for the export job |

Returns a `pathlib.Path` to the downloaded file.

```python
path = view.export.to_csv("output.csv")
print(f"Downloaded to {path}")

# Auto-generated filename
path = view.export.to_csv()
```

### to_s3

Export to S3 storage.

```python
view.export.to_s3(
    file_name: str | None = None,
    file_type: ExportFileType = ExportFileType.CSV,
    include_hidden: bool = False,
    **kwargs,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | `str \| None` | `None` | Output filename (auto-generated if not provided) |
| `file_type` | `ExportFileType` | `ExportFileType.CSV` | File format enum |
| `include_hidden` | `bool` | `False` | Include hidden columns |

```python
from mammoth import ExportFileType

result = view.export.to_s3(file_name="report.csv")
result = view.export.to_s3(file_name="data.json", file_type=ExportFileType.JSON, include_hidden=True)
```

### to_postgres

Export to a PostgreSQL database.

```python
view.export.to_postgres(
    host: str,
    port: int,
    database: str,
    table: str,
    username: str,
    password: str,
    **kwargs,
) -> dict[str, Any]
```

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

### to_mysql

Export to a MySQL database.

```python
view.export.to_mysql(
    host: str,
    port: int,
    database: str,
    table: str,
    username: str,
    password: str,
    **kwargs,
) -> dict[str, Any]
```

```python
view.export.to_mysql(
    host="mysql.example.com",
    port=3306,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

### to_bigquery

Export to Google BigQuery.

```python
view.export.to_bigquery(**kwargs) -> dict[str, Any]
```

Pass BigQuery connection and table configuration as keyword arguments.

### to_redshift

Export to Amazon Redshift.

```python
view.export.to_redshift(**kwargs) -> dict[str, Any]
```

### to_elasticsearch

Export to Elasticsearch.

```python
view.export.to_elasticsearch(**kwargs) -> dict[str, Any]
```

### to_ftp

Export to an FTP server.

```python
view.export.to_ftp(
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 21,
    **kwargs,
) -> dict[str, Any]
```

### to_sftp

Export to an SFTP server.

```python
view.export.to_sftp(
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 22,
    **kwargs,
) -> dict[str, Any]
```

### to_email

Export via email.

```python
view.export.to_email(recipients: list[str], **kwargs) -> dict[str, Any]
```

```python
view.export.to_email(recipients=["analyst@example.com", "team@example.com"])
```

### to_dataset

Export to another Mammoth dataset (branch out).

```python
view.export.to_dataset(
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

```python
view.export.to_dataset(dest_dataset_id=42)
view.export.to_dataset(
    dest_dataset_id=42,
    column_mapping={"Sales": "revenue", "Region": "area"},
)
```

### publish_to_db

Publish the dataview to a database.

```python
view.export.publish_to_db(**kwargs) -> dict[str, Any]
```

### list

List all exports for this dataview.

```python
exports = view.export.list()
for exp in exports:
    print(exp["id"], exp["handler_type"])
```

### delete

Delete an export by ID.

```python
view.export.delete(export_id=123)
```

## branch_out (View method)

Convenience method on the View itself. Equivalent to `view.export.to_dataset()`.

```python
view.branch_out(
    dest_dataset_id: int,
    column_mapping: dict[str, str] | None = None,
    **kwargs,
) -> dict[str, Any]
```

```python
view.branch_out(dest_dataset_id=42)
```

---

## ExportsAPI

Lower-level export operations available via `client.exports`. These methods require explicit IDs rather than working through a View object.

### client.exports.to_csv

Download dataview data as CSV.

```python
client.exports.to_csv(
    dataview_id: int,
    output_path: str | Path | None = None,
    timeout: int = 300,
    dataset_id: int | None = None,
) -> Path
```

```python
path = client.exports.to_csv(dataview_id=1039, output_path="export.csv")
```

### client.exports.to_s3

Create an S3 export. Waits for job completion and returns the download URL.

```python
client.exports.to_s3(
    dataview_id: int,
    file: str | None = None,
    file_type: str = "csv",
    include_hidden: bool = False,
    dataset_id: int | None = None,
    ...,
) -> dict[str, Any]
```

```python
result = client.exports.to_s3(dataview_id=1039, file="report.csv")
print(result["url"])  # download URL
```

### client.exports.to_dataset

Create an internal dataset export (branch out).

```python
client.exports.to_dataset(
    dataview_id: int,
    dataset_name: str,
    column_mapping: dict[str, Any] | None = None,
    ...,
) -> PipelineExportsModificationResp | JobResponse
```

```python
client.exports.to_dataset(dataview_id=1039, dataset_name="processed_data")
```

### client.exports.list

List exports for a dataview with filtering and pagination.

```python
client.exports.list(
    dataview_id: int,
    fields: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
    status: ExportStatus | None = None,
    handler_type: HandlerType | None = None,
    ...,
) -> PipelineExportsPaginated
```

### client.exports.create

Create a new export with full control over the export specification.

```python
from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType

spec = AddExportSpec(
    DATAVIEW_ID=1039,
    handler_type=HandlerType.S3,
    trigger_type=TriggerType.PIPELINE,
    target_properties={
        "file": "report.csv",
        "file_type": "csv",
        "include_hidden": False,
        "is_format_set": True,
        "use_format": True,
    },
    additional_properties={},
    condition={},
    run_immediately=True,
    validate_only=False,
)

result = client.exports.create(
    dataview_id=1039,
    export_spec=spec,
    dataset_id=42,
)
```

## Export workflow example

```python
from mammoth import MammothClient, Condition, Operator

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# Get a view and transform it
view = client.views.get(1039)
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Export to CSV locally
csv_path = view.export.to_csv("filtered_sales.csv")
print(f"CSV saved to {csv_path}")

# Export to S3
s3_result = view.export.to_s3(file_name="filtered_sales.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="filtered_sales",
    username="user",
    password="pass",
)

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)
```

## See also

- [Views](#views-reference) -- View object and transformation methods
- [Client](#client-api-reference) -- MammothClient and sub-clients


---


# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

## Methods

### list

```python
client.projects.list(
    workspace_id: int | None = None,
    limit: int = 100,
) -> dict[str, Any]
```

List all projects in a workspace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |
| `limit` | `int` | `100` | Maximum number of results |

**Returns**: Dict containing `projects` list with `id` and `name` fields.

```python
resp = client.projects.list()
for p in resp["projects"]:
    print(p["id"], p["name"])
```

### get

```python
client.projects.get(
    project: int | str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get a single project by ID, name, or auto-selection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | `int \| str \| None` | `None` | Project ID (int), name (str), or None for auto-selection |
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

**Behavior**:

- `project=None` -- auto-selects if only one project exists
- `project=123` -- finds project by ID
- `project="My Project"` -- finds project by name

**Returns**: Dict with `id` and `name`.

**Raises**: `ValueError` if project not found or ambiguous.

```python
# By ID
project = client.projects.get(123)

# By name
project = client.projects.get("Analytics")

# Auto-select (only works if workspace has exactly one project)
project = client.projects.get()
```

### create

```python
client.projects.create(
    name: str,
    color: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Create a new project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Name for the new project |
| `color` | `str \| None` | `None` | Color code for the project |
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

```python
project = client.projects.create(name="Q4 Analytics", color="#3498db")
print(project["id"])
```

### update

```python
client.projects.update(
    project_id: int,
    name: str | None = None,
    color: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update a project's name or color.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project to update |
| `name` | `str \| None` | `None` | New name |
| `color` | `str \| None` | `None` | New color code |
| `workspace_id` | `int \| None` | `None` | Workspace ID |

```python
client.projects.update(123, name="Q4 Analytics v2")
```

### delete

```python
client.projects.delete(
    project_id: int,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Delete a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project to delete |
| `workspace_id` | `int \| None` | `None` | Workspace ID |

### bulk_update

```python
client.projects.bulk_update(
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Bulk update multiple projects using JSON Patch operations.

### bulk_delete

```python
client.projects.bulk_delete(
    project_ids: list[int],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Bulk delete multiple projects.

```python
client.projects.bulk_delete([101, 102, 103])
```

### add_users

```python
client.projects.add_users(
    project_id: int,
    user_ids: list[str],
    role: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Add users to a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project |
| `user_ids` | `list[str]` | *required* | User email addresses or IDs |
| `role` | `str \| None` | `None` | Role to assign |

```python
client.projects.add_users(123, ["user@example.com"], role="editor")
```

### remove_users

```python
client.projects.remove_users(
    project_id: int,
    user_ids: list[str],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Remove users from a project.

### browse

```python
client.projects.browse(
    project_id: int,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse project contents (datasets, folders).

```python
contents = client.projects.browse(123)
```

## See also

- [Client](#client-api-reference) -- MammothClient and sub-clients overview
- [Datasets](#datasets-api-reference) -- Dataset management within projects


---


# Datasets API Reference

The `DatasetsAPI` manages datasets within a project. A dataset is a data table stored in Mammoth, created from file uploads, connectors, or cloning.

**Access**: `client.datasets`

> **Note:** Requires project_id
>
> Most methods require a project ID. Set it on the client with `client.set_project_id(10)` or pass `project_id` explicitly.
>

## Methods

### list

```python
client.datasets.list(
    workspace_id: int | None = None,
    project_id: int | None = None,
    limit: int = 100,
    sort: str = "(created_at:desc)",
) -> dict[str, Any]
```

List datasets in a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default) |
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |
| `limit` | `int` | `100` | Maximum number of results |
| `sort` | `str` | `"(created_at:desc)"` | Sort order |

**Returns**: Dict containing `datasets` list with `id` and `name` fields.

```python
resp = client.datasets.list()
for ds in resp["datasets"]:
    print(ds["id"], ds["name"])
```

### get

```python
client.datasets.get(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataset details by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |

**Returns**: Dict with a `"dataset"` key containing the full dataset information including metadata, column info, and settings.

```python
resp = client.datasets.get(42)
ds = resp["dataset"]
print(ds["name"], ds.get("stats", {}).get("row_count"))
```

### get_data

```python
client.datasets.get_data(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    timeout: int = 300,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Get the actual data rows from a dataset. This triggers a job and polls until completion.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `timeout` | `int` | `300` | Maximum wait time in seconds |
| `poll_interval` | `int` | `2` | Polling interval in seconds |

**Returns**: Dict with dataset data rows.

```python
data = client.datasets.get_data(42)
```

### create

```python
client.datasets.create(
    dataset_spec: dict[str, Any],
    ds_creation_type: str,
    folder_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_spec` | `dict` | *required* | Dataset specification (varies by creation type) |
| `ds_creation_type` | `str` | *required* | Type: `"clone"`, `"cloud"`, `"sketch"`, or `"weburl"` |
| `folder_resource_id` | `str \| None` | `None` | Folder to place the dataset in |

```python
# Clone an existing dataset
ds = client.datasets.create(
    dataset_spec={"source_dataset_id": 42},
    ds_creation_type="clone",
)
```

### update

```python
client.datasets.update(
    dataset_id: int,
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a dataset using JSON Patch operations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `patch_data` | `dict` | *required* | Patch operation data |

### delete

```python
client.datasets.delete(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> None
```

Delete a dataset.

### bulk_update

```python
client.datasets.bulk_update(
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update multiple datasets (bulk operation).

### bulk_delete

```python
client.datasets.bulk_delete(
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> None
```

Delete multiple datasets (bulk operation).

### browse

```python
client.datasets.browse(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Browse dataset contents (dataviews, metadata).

```python
contents = client.datasets.browse(42)
```

### list_batches

```python
client.datasets.list_batches(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List batches for a dataset. A batch represents a data upload or refresh event.

**Returns**: List of batch dicts.

### get_batch

```python
client.datasets.get_batch(
    dataset_id: int,
    batch_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific batch.

### get_file_settings

```python
client.datasets.get_file_settings(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get file settings for a dataset (delimiter, encoding, etc.).

## See also

- [Client](#client-api-reference) -- MammothClient and sub-clients overview
- [Dataviews](#dataviews-api-reference) -- Dataview management within datasets
- [Views](#views-reference) -- Rich View objects for transformations


---


# Dataviews API Reference

The `DataviewsAPI` provides low-level CRUD operations on dataviews. For rich transformation methods, use `client.views` instead (see [Views](#views-reference)).

**Access**: `client.dataviews`

> **Tip:** client.views vs client.dataviews
>
> `client.views.get(id)` returns a rich `View` object with transformation methods, data access, and export helpers. `client.dataviews` is the lower-level API returning raw dicts.
>

## Methods

### list

```python
client.dataviews.list(
    dataset_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    limit: int = 100,
    sort: str = "(created_at:desc)",
) -> dict[str, Any]
```

List dataviews in a dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `limit` | `int` | `100` | Maximum number of results |
| `sort` | `str` | `"(created_at:desc)"` | Sort order |

**Returns**: Dict containing `dataviews` list.

```python
resp = client.dataviews.list(dataset_id=42)
for dv in resp["dataviews"]:
    print(dv["id"], dv["name"])
```

### get

```python
client.dataviews.get(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataview information (raw dict).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |

### create

```python
client.dataviews.create(
    dataset_id: int,
    name: str | None = "View",
    clone_config_from: int | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create or duplicate a dataview.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `name` | `str \| None` | `"View"` | Name of the dataview |
| `clone_config_from` | `int \| None` | `None` | ID of dataview to clone pipeline from |

```python
# Create a blank view
dv = client.dataviews.create(dataset_id=42, name="Analysis")

# Clone an existing view's pipeline
dv = client.dataviews.create(dataset_id=42, name="Copy", clone_config_from=1039)
```

### update

```python
client.dataviews.update(
    dataset_id: int,
    dataview_id: int,
    patch_data: list[dict[str, Any]],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update dataview properties using JSON Patch operations.

### delete

```python
client.dataviews.delete(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a dataview.

### bulk_delete

```python
client.dataviews.bulk_delete(
    dataset_id: int,
    dataview_ids: list[int] | str,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete multiple dataviews.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_ids` | `list[int] \| str` | *required* | List of dataview IDs or comma-separated string |

### get_data

```python
client.dataviews.get_data(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Get dataview data using GET method. Automatically polls the job until completion.

### query_data

```python
client.dataviews.query_data(
    dataset_id: int,
    dataview_id: int,
    sequence: int = 0,
    offset: int = 1,
    limit: int = 400,
    columns: list[str] | None = None,
    condition: dict[str, Any] | None = None,
    sort: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get dataview data with filtering options (POST method).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |
| `sequence` | `int` | `0` | Pipeline step to fetch data at |
| `offset` | `int` | `1` | One-indexed starting row |
| `limit` | `int` | `400` | Number of rows to fetch |
| `columns` | `list[str] \| None` | `None` | Column names to fetch |
| `condition` | `dict \| None` | `None` | Filter condition dict |
| `sort` | `str \| None` | `None` | Sort specification |

### active_users

```python
client.dataviews.active_users(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get list of users currently active on this dataview.

### mark_active

```python
client.dataviews.mark_active(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Mark the current user as active on this dataview.

### conditional_format_list

```python
client.dataviews.conditional_format_list(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List conditional formatting rules for a dataview.

### conditional_format_create

```python
client.dataviews.conditional_format_create(
    dataset_id: int,
    dataview_id: int,
    rule: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a conditional formatting rule.

### conditional_format_update

```python
client.dataviews.conditional_format_update(
    dataset_id: int,
    dataview_id: int,
    rule: dict[str, Any],
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a conditional formatting rule.

### conditional_format_delete

```python
client.dataviews.conditional_format_delete(
    dataset_id: int,
    dataview_id: int,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete all conditional formatting rules for a dataview.

### draft_mode

```python
client.dataviews.draft_mode(
    dataset_id: int,
    dataview_id: int,
    command: str,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]
```

Manage draft mode for the dataview pipeline.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_id` | `int` | *required* | ID of the dataset |
| `dataview_id` | `int` | *required* | ID of the dataview |
| `command` | `str` | *required* | `"enter"`, `"commit"`, or `"discard"` |

## See also

- [Views](#views-reference) -- Rich View objects with transformation methods
- [Pipeline](#pipeline-api-reference) -- Pipeline task management
- [Datasets](#datasets-api-reference) -- Dataset management


---


# Pipeline API Reference

The `PipelineAPI` manages the transformation pipeline on dataviews. Each dataview has an ordered list of pipeline tasks (filter, join, pivot, etc.) that transform the data.

**Access**: `client.pipeline`

> **Note:** Internal use
>
> The `PipelineAPI` is primarily used internally by `View` objects. For most use cases, use `view.filter_rows()`, `view.math()`, etc. instead of calling `client.pipeline` directly.
>

## Methods

### get_pipeline

```python
client.pipeline.get_pipeline(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get the current pipeline state for a dataview.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected if not provided) |

**Returns**: Pipeline state dict including `state` (e.g. `"ready"`, `"running"`), task list, and metadata.

```python
pipeline = client.pipeline.get_pipeline(dataview_id=1039)
print(pipeline["state"])  # "ready"
```

### list_tasks

```python
client.pipeline.list_tasks(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

List all pipeline tasks for a dataview.

**Returns**: Dict with `tasks` list, each containing task type, parameters, and sequence number.

```python
resp = client.pipeline.list_tasks(dataview_id=1039)
for task in resp.get("tasks", []):
    print(task["id"], task.get("params", {}).get("TYPE"))
```

### add_task

```python
client.pipeline.add_task(
    dataview_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Add a new transformation task to the pipeline. Waits for the async job to complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `task_spec` | `dict` | *required* | Task specification (varies by task type) |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected if not provided) |

**Returns**: Dict with created task info.

### get_task

```python
client.pipeline.get_task(
    dataview_id: int,
    task_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get a specific pipeline task by ID.

### update_task

```python
client.pipeline.update_task(
    dataview_id: int,
    task_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Update an existing pipeline task. Waits for the async job to complete.

### delete_task

```python
client.pipeline.delete_task(
    dataview_id: int,
    task_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Delete a pipeline task. This is how transformations are "undone" -- each task removal is reversible.

```python
client.pipeline.delete_task(dataview_id=1039, task_id=5678)
```

### preview_task

```python
client.pipeline.preview_task(
    dataview_id: int,
    task_spec: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Preview task results without adding to the pipeline. Useful for testing transformations before committing.

### draft_mode

```python
client.pipeline.draft_mode(
    dataview_id: int,
    command: str,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Manage draft mode for a dataview pipeline. Draft mode lets you add multiple tasks before committing them all at once.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `command` | `str` | *required* | `"enter"`, `"commit"`, or `"discard"` |

### edit_pipeline

```python
client.pipeline.edit_pipeline(
    dataview_id: int,
    patches: list[dict[str, Any]],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

PATCH pipeline with operations (auto_run, run, reset, etc.).

### wait_for_pipeline

```python
client.pipeline.wait_for_pipeline(
    dataview_id: int,
    dataset_id: int | None = None,
    timeout: int | None = None,
    poll_interval: int = 3,
) -> dict[str, Any]
```

Poll pipeline state until it reaches a terminal state (`ready`, `runtime_error`, `ref_error`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataview_id` | `int` | *required* | ID of the dataview |
| `dataset_id` | `int \| None` | `None` | Dataset ID (auto-detected) |
| `timeout` | `int \| None` | `None` | Max wait time in seconds (default: `client.pipeline_timeout`) |
| `poll_interval` | `int` | `3` | Seconds between polls |

**Raises**:

- `MammothTransformError` -- if pipeline reaches `runtime_error` or `ref_error`
- `MammothJobTimeoutError` -- if timeout is exceeded

```python
# Wait for pipeline after an external change
pipeline = client.pipeline.wait_for_pipeline(dataview_id=1039, timeout=120)
print(pipeline["state"])  # "ready"
```

## Pipeline states

| State | Description |
|-------|-------------|
| `ready` | Pipeline complete, data is available |
| `running` | Pipeline is executing tasks |
| `modifying` | Pipeline is being modified |
| `modified` | Changes pending execution |
| `runtime_error` | A task failed during execution |
| `ref_error` | A dependency reference is broken |

## See also

- [Views](#views-reference) -- Rich View objects that wrap pipeline operations
- [Jobs](#jobs-api-reference) -- Job tracking for async operations
- [Dataviews](#dataviews-api-reference) -- Low-level dataview CRUD


---


# Jobs API Reference

The `JobsAPI` tracks asynchronous job status. Many Mammoth operations (data fetches, pipeline tasks, exports) create background jobs. The SDK polls these jobs automatically in most cases, but the Jobs API is available for manual control.

**Access**: `client.jobs`

## Methods

### get_job

```python
client.jobs.get_job(
    job_id: int,
    timeout: int = 300,
) -> dict[str, Any]
```

Get job status by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_id` | `int` | *required* | ID of the job |
| `timeout` | `int` | `300` | Request timeout (compatibility parameter) |

**Returns**: Dict with job information including `status`, `response`, and timestamps.

```python
job = client.jobs.get_job(12345)
print(job["status"])  # "success", "processing", "failure", "error"
```

### get_jobs

```python
client.jobs.get_jobs(
    job_ids: list[int] | str,
) -> dict[str, Any]
```

Track multiple jobs at once.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_ids` | `list[int] \| str` | *required* | List of job IDs or comma-separated string |

**Returns**: Dict containing `jobs` list with status information.

```python
result = client.jobs.get_jobs([12345, 12346])
for job in result.get("jobs", []):
    print(job["id"], job["status"])
```

### wait_for_job

```python
client.jobs.wait_for_job(
    job_id: int,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Wait for a job to complete by polling until it reaches a terminal state.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_id` | `int` | *required* | ID of the job |
| `timeout` | `int \| None` | `None` | Maximum wait time in seconds (default: `client.job_timeout`) |
| `poll_interval` | `int` | `2` | Seconds between polling attempts |

**Returns**: Dict with completed job information.

**Raises**:

- `MammothJobFailedError` -- if the job fails
- `MammothJobTimeoutError` -- if timeout is exceeded

```python
job = client.jobs.wait_for_job(12345, timeout=120)
print(job["response"])
```

### wait_for_jobs

```python
client.jobs.wait_for_jobs(
    job_ids: list[int] | str,
    timeout: int | None = None,
    poll_interval: int = 2,
) -> dict[str, Any]
```

Wait for multiple jobs to complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_ids` | `list[int] \| str` | *required* | List of job IDs or comma-separated string |
| `timeout` | `int \| None` | `None` | Maximum wait time in seconds (default: `client.job_timeout`) |
| `poll_interval` | `int` | `2` | Seconds between polling attempts |

**Returns**: Dict containing `jobs` list with all completed jobs.

**Raises**:

- `MammothJobFailedError` -- if any job fails
- `MammothJobTimeoutError` -- if timeout is exceeded

## Job statuses

| Status | Description |
|--------|-------------|
| `processing` | Job is still running |
| `success` | Job completed successfully |
| `failure` | Job failed (check `response.error` for details) |
| `error` | Job encountered an error |

## See also

- [Pipeline](#pipeline-api-reference) -- Pipeline tasks create jobs
- [Exceptions](#exceptions-reference) -- `MammothJobFailedError`, `MammothJobTimeoutError`
- [Job Lifecycle](#async-operations-timeouts) -- Detailed async operations guide


---


# Dashboards API Reference

The `DashboardsAPI` manages interactive dashboards in Mammoth. Dashboards visualize data from dataviews and can be shared with team members or embedded externally.

**Access**: `client.dashboards`

## Methods

### list

```python
client.dashboards.list() -> list[dict[str, Any]]
```

List all dashboards accessible to the current user.

**Returns**: List of dashboard dicts.

```python
dashboards = client.dashboards.list()
for d in dashboards:
    print(d["id"], d.get("name"))
```

### create

```python
client.dashboards.create(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new dashboard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Dashboard configuration (name, sources, layout, etc.) |

**Returns**: Dict with created dashboard info (may include job ID for async creation).

### get

```python
client.dashboards.get(
    dashboard_id: int,
) -> dict[str, Any]
```

Get dashboard details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |

### update

```python
client.dashboards.update(
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update a dashboard configuration.

### delete

```python
client.dashboards.delete(
    dashboard_id: int,
) -> dict[str, Any]
```

Delete a dashboard.

### get_sources

```python
client.dashboards.get_sources() -> list[dict[str, Any]]
```

Get available data sources for dashboard creation.

**Returns**: List of source dicts (dataviews available for charting).

### get_analytics

```python
client.dashboards.get_analytics(
    dashboard_id: int,
) -> dict[str, Any]
```

Get dashboard analytics including view counts and active users.

### share

```python
client.dashboards.share(
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Share a dashboard with users or generate a public link.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `config` | `dict` | *required* | Sharing configuration (users, permissions, etc.) |

### action

```python
client.dashboards.action(
    dashboard_id: int,
    action_config: dict[str, Any],
) -> dict[str, Any]
```

Perform an action on a dashboard (e.g. publish, refresh).

### get_by_url

```python
client.dashboards.get_by_url(
    url: str,
) -> dict[str, Any]
```

Get a dashboard by its URL slug.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | *required* | Dashboard URL slug |

### get_draft_data

```python
client.dashboards.get_draft_data(
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]
```

Query draft dashboard data using SQL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `sql` | `str` | *required* | SQL query to execute against draft data |

### get_publish_data

```python
client.dashboards.get_publish_data(
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]
```

Query published dashboard data using SQL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `sql` | `str` | *required* | SQL query to execute against published data |

## See also

- [Views](#views-reference) -- Data sources for dashboards
- [Exports](#exports-reference) -- Export data to files and databases


---


# Webhooks API Reference

The `WebhooksAPI` manages webhook datasets -- HTTP endpoints that receive data into the Mammoth platform. Webhooks allow external systems to push data directly into Mammoth.

**Access**: `client.webhooks`

## Methods

### list

```python
client.webhooks.list(
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]
```

List webhook datasets in the current project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |

**Returns**: List of webhook dicts.

```python
webhooks = client.webhooks.list()
for wh in webhooks:
    print(wh["id"], wh.get("name"), wh.get("uri"))
```

### create

```python
client.webhooks.create(
    name: str = "Generic Webhook",
    mode: str | WebhookMode = "replace",
    folder_resource_id: str | None = None,
    origins: str = "*",
    is_secure: bool = False,
) -> dict[str, Any]
```

Create a webhook dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"Generic Webhook"` | Name of the webhook |
| `mode` | `str \| WebhookMode` | `"replace"` | `"replace"` (overwrite on each push) or `"combine"` (append) |
| `folder_resource_id` | `str \| None` | `None` | Folder to place the webhook in |
| `origins` | `str` | `"*"` | Allowed CORS origins |
| `is_secure` | `bool` | `False` | Generate a secret for authentication |

**Returns**: Dict with created webhook info including the `uri` for sending data.

```python
from mammoth.models.webhooks import WebhookMode

wh = client.webhooks.create(
    name="Sales Events",
    mode=WebhookMode.COMBINE,
    is_secure=True,
)
print(wh["uri"])  # Use this URI to send data
```

### get

```python
client.webhooks.get(
    webhook_id: int,
) -> dict[str, Any]
```

Get webhook details.

### update

```python
client.webhooks.update(
    webhook_id: int,
    mode: str | WebhookMode | None = None,
    origins: str | None = None,
    is_secure: bool | None = None,
) -> dict[str, Any]
```

Update a webhook using JSON Patch format.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_id` | `int` | *required* | ID of the webhook |
| `mode` | `str \| WebhookMode \| None` | `None` | New data ingestion mode |
| `origins` | `str \| None` | `None` | New allowed CORS origins |
| `is_secure` | `bool \| None` | `None` | Whether the webhook requires a secret |

### delete

```python
client.webhooks.delete(
    webhook_id: int,
) -> dict[str, Any]
```

Delete a webhook.

### send_data

```python
client.webhooks.send_data(
    webhook_uri: str,
    data: dict[str, Any],
) -> dict[str, Any]
```

Send data to a webhook via POST.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_uri` | `str` | *required* | Webhook URI path (e.g. `"nHC1zIl97JzgDMopgcfpOgLV"`) |
| `data` | `dict` | *required* | Data payload to send |

```python
client.webhooks.send_data("nHC1zIl97JzgDMopgcfpOgLV", {
    "sale_id": 1001,
    "amount": 250.00,
    "region": "West",
})
```

### send_data_get

```python
client.webhooks.send_data_get(
    webhook_uri: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]
```

Send data to a webhook via GET query parameters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_uri` | `str` | *required* | Webhook URI path |
| `params` | `dict \| None` | `None` | Data as query parameters |

## See also

- [Files](#files-api-reference) -- File-based data import
- [Connectors](#connectors-api-reference) -- Database connector import


---


# Automations & Schedules API Reference

The SDK provides two sub-clients for automation workflows:

- **`client.automations`** (`AutomationsAPI`) -- manages automations and their associated schedules in a unified interface
- **`client.schedules`** (`SchedulesAPI`) -- manages schedules as a standalone resource

## AutomationsAPI

**Access**: `client.automations`

### Automation methods

#### list

```python
client.automations.list() -> list[dict[str, Any]]
```

List all automations in the current project.

```python
automations = client.automations.list()
for a in automations:
    print(a["id"], a.get("name"))
```

#### create

```python
client.automations.create(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new automation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Automation configuration (name, triggers, actions, etc.) |

#### get

```python
client.automations.get(
    automation_id: int,
) -> dict[str, Any]
```

Get automation details.

#### update

```python
client.automations.update(
    automation_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update an automation.

#### delete

```python
client.automations.delete(
    automation_id: int,
) -> dict[str, Any]
```

Delete an automation.

### Schedule methods (via AutomationsAPI)

#### list_schedules

```python
client.automations.list_schedules() -> list[dict[str, Any]]
```

List all schedules in the current project.

#### create_schedule

```python
client.automations.create_schedule(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new schedule.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Schedule configuration (cron, timezone, actions, etc.) |

#### update_schedule

```python
client.automations.update_schedule(
    schedule_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update a schedule.

#### delete_schedule

```python
client.automations.delete_schedule(
    schedule_id: int,
) -> dict[str, Any]
```

Delete a schedule.

---

## SchedulesAPI

**Access**: `client.schedules`

A standalone sub-client for schedule management with explicit project_id support.

### list

```python
client.schedules.list(
    project_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List schedules in a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |

**Returns**: Dict with `schedules` list and pagination info.

### get

```python
client.schedules.get(
    schedule_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get schedule details.

### create

```python
client.schedules.create(
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new schedule.

### update

```python
client.schedules.update(
    schedule_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a schedule.

### delete

```python
client.schedules.delete(
    schedule_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a schedule.

## See also

- [Pipeline](#pipeline-api-reference) -- Transformation tasks triggered by automations
- [Webhooks](#webhooks-api-reference) -- Event-driven data ingestion


---


# Workspace & Users API Reference

The SDK provides two sub-clients for workspace and user management:

- **`client.workspaces`** (`WorkspaceAPI`) -- workspace CRUD and user management
- **`client.user_profile`** (`UserProfileAPI`) -- current user profile and preferences

## WorkspaceAPI

**Access**: `client.workspaces`

### list

```python
client.workspaces.list(
    limit: int = 100,
) -> dict[str, Any]
```

List all accessible workspaces.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `100` | Maximum number of results |

**Returns**: Dict containing `workspaces` list with `id` and `name`.

```python
resp = client.workspaces.list()
for ws in resp.get("workspaces", []):
    print(ws["id"], ws["name"])
```

### get

```python
client.workspaces.get(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific workspace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

### update

```python
client.workspaces.update(
    config: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update workspace settings.

### delete

```python
client.workspaces.delete(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Delete a workspace.

### reactivate

```python
client.workspaces.reactivate(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Reactivate a deactivated workspace.

### list_users

```python
client.workspaces.list_users(
    workspace_id: int | None = None,
) -> list[dict[str, Any]]
```

List all users in a workspace.

**Returns**: List of user dicts.

```python
users = client.workspaces.list_users()
for u in users:
    print(u.get("email"), u.get("role"))
```

### get_user

```python
client.workspaces.get_user(
    user_id: str,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific user.

### update_user

```python
client.workspaces.update_user(
    user_id: str,
    config: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update a user's settings in the workspace.

---

## UserProfileAPI

**Access**: `client.user_profile`

Manages the current authenticated user's profile and preferences.

### get

```python
client.user_profile.get() -> dict[str, Any]
```

Get the current user's profile information.

```python
profile = client.user_profile.get()
print(profile.get("name"), profile.get("email"))
```

### update

```python
client.user_profile.update(**fields: Any) -> dict[str, Any]
```

Update the current user's profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `**fields` | `Any` | Profile fields to update (name, email, etc.) |

```python
client.user_profile.update(name="Jane Doe")
```

### change_password

```python
client.user_profile.change_password(
    current_password: str,
    new_password: str,
) -> dict[str, Any]
```

Change the current user's password.

| Parameter | Type | Description |
|-----------|------|-------------|
| `current_password` | `str` | Current password |
| `new_password` | `str` | New password |

### get_preferences

```python
client.user_profile.get_preferences() -> dict[str, Any]
```

Get user preferences (UI settings, notifications, etc.).

### update_preferences

```python
client.user_profile.update_preferences(**prefs: Any) -> dict[str, Any]
```

Update user preferences.

## See also

- [Projects](#projects-api-reference) -- Project management within workspaces
- [Authentication](#authentication) -- API credentials setup
- [Client](#client-api-reference) -- MammothClient overview


---


# Other APIs Reference

This page covers smaller utility sub-clients that provide access to folders, batches, browse, client apps, external keys, activity logs, addons, reports, and AI features.

---

## FoldersAPI

**Access**: `client.folders`

Manage folders within projects for organizing datasets and resources.

### list

```python
client.folders.list(
    workspace_id: int | None = None,
    project_id: int | None = None,
    fields: str | None = None,
    folder_ids: list[int] | None = None,
    names: list[str] | None = None,
    statuses: list[str] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    created_by: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> FoldersList
```

List folders with filtering and pagination. Returns a `FoldersList` Pydantic model.

```python
folders = client.folders.list()
```

### create

```python
client.folders.create(
    name: str,
    parent_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> FolderDetails
```

Create a new folder. Returns a `FolderDetails` Pydantic model.

```python
folder = client.folders.create(name="Reports")
```

### delete

```python
client.folders.delete(
    folder_ids: list[int],
    workspace_id: int | None = None,
    project_id: int | None = None,
    check_dependency: bool = True,
    remove_contents: bool = True,
) -> None
```

Delete folders.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_ids` | `list[int]` | *required* | List of folder IDs to delete |
| `check_dependency` | `bool` | `True` | Check for dependencies before deleting |
| `remove_contents` | `bool` | `True` | Remove folder contents before deleting |

### move

```python
client.folders.move(
    resource_ids: list[str],
    target_folder_resource_id: str | None = None,
    source_folder_resource_id: str | None = None,
    workspace_id: int | None = None,
    project_id: int | None = None,
) -> ObjectJobSchema
```

Move resources between folders. Returns an `ObjectJobSchema` with job information.

---

## BatchesAPI

**Access**: `client.batches`

Manage dataset batches (data upload/refresh events).

### list

```python
client.batches.list(
    dataset_id: int,
    project_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List batches for a dataset.

### get

```python
client.batches.get(
    dataset_id: int,
    batch_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get batch details.

### create

```python
client.batches.create(
    dataset_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new batch for a dataset.

### update

```python
client.batches.update(
    dataset_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update batches for a dataset.

### delete

```python
client.batches.delete(
    dataset_id: int,
    batch_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a batch.

---

## BrowseAPI

**Access**: `client.browse`

Quick resource discovery and navigation through the hierarchy.

### workspaces

```python
client.browse.workspaces() -> dict[str, Any]
```

Browse available workspaces.

### projects

```python
client.browse.projects(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse projects in a workspace.

### datasets

```python
client.browse.datasets(
    project_id: int | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse datasets in a project.

### dataviews

```python
client.browse.dataviews(
    dataset_id: int,
    project_id: int | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse dataviews in a dataset.

```python
# Walk the hierarchy
projects = client.browse.projects()
datasets = client.browse.datasets(project_id=10)
dataviews = client.browse.dataviews(dataset_id=42)
```

---

## ClientAppsAPI

**Access**: `client.client_apps`

Manage API tokens and client applications. Client apps generate API key/secret pairs for programmatic access.

### list

```python
client.client_apps.list(
    workspace_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
    fields: str | None = None,
    sort: str | None = None,
) -> ClientAppsListResponse
```

List client apps. Returns a `ClientAppsListResponse` Pydantic model.

### create

```python
client.client_apps.create(
    app_name: str,
    description: str | None = None,
    workspace_id: int | None = None,
) -> ClientAppPostResponse
```

Create a new client app to generate API tokens. Returns a `ClientAppPostResponse` with the app details and tokens.

```python
app = client.client_apps.create(app_name="My Integration")
print(app.api_key, app.api_secret)
```

### get

```python
client.client_apps.get(
    client_key: str,
    workspace_id: int | None = None,
    fields: str | None = None,
) -> ClientAppSchema
```

Get details of a specific client app.

### update

```python
client.client_apps.update(
    client_key: str,
    patch_request: PatchRequest,
    workspace_id: int | None = None,
) -> ClientAppSchema
```

Update client app details.

### delete

```python
client.client_apps.delete(
    client_key: str,
    workspace_id: int | None = None,
) -> None
```

Delete a client app.

---

## ExternalKeysAPI

**Access**: `client.external_keys`

Manage external API keys for workspace integrations.

### list

```python
client.external_keys.list() -> dict[str, Any]
```

List all external API keys.

### get

```python
client.external_keys.get(key_id: int) -> dict[str, Any]
```

Get external key details.

### create

```python
client.external_keys.create(config: dict[str, Any]) -> dict[str, Any]
```

Create a new external API key.

### delete

```python
client.external_keys.delete(key_id: int) -> dict[str, Any]
```

Delete an external API key.

---

## ActivityLogsAPI

**Access**: `client.activity_logs`

Query and export activity logs for audit purposes.

### list

```python
client.activity_logs.list(
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
    **filters: Any,
) -> dict[str, Any]
```

List activity logs with pagination and filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |
| `sort` | `str \| None` | `None` | Sort specification |
| `**filters` | `Any` | | Additional filters (user, action, resource, etc.) |

```python
logs = client.activity_logs.list(limit=20)
```

### export

```python
client.activity_logs.export(
    format: str = "csv",
    **filters: Any,
) -> dict[str, Any]
```

Export activity logs to a file.

---

## AddonsAPI

**Access**: `client.addons`

Manage workspace addons for connectors, storage, and user capacity.

### add_connector / remove_connector

```python
client.addons.add_connector(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_connector(config: dict[str, Any]) -> dict[str, Any]
```

### add_storage / remove_storage

```python
client.addons.add_storage(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_storage(config: dict[str, Any]) -> dict[str, Any]
```

### add_users / remove_users

```python
client.addons.add_users(config: dict[str, Any]) -> dict[str, Any]
client.addons.remove_users(config: dict[str, Any]) -> dict[str, Any]
```

---

## ReportsAPI

**Access**: `client.reports`

List workspace reports.

### list

```python
client.reports.list(
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List all reports.

---

## AIAPI

**Access**: `client.ai`

AI-powered features including profiling, data generation, SQL generation, and suggestions.

### generate_profile

```python
client.ai.generate_profile(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Generate an AI profile/summary of the dataview data. Waits for the async job.

### generate_data

```python
client.ai.generate_data(
    dataview_id: int,
    config: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Generate synthetic data for a dataview.

### get_data_gen_info

```python
client.ai.get_data_gen_info(
    dataview_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]
```

Get data generation information for a dataview.

### generate_sql

```python
client.ai.generate_sql(
    intent: str,
    sequence_number: int = 0,
) -> dict[str, Any]
```

Generate SQL from natural language intent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `intent` | `str` | *required* | Natural language description of the query |
| `sequence_number` | `int` | `0` | Sequence number for the request |

```python
result = client.ai.generate_sql("total sales by region for Q4")
```

### get_suggestions

```python
client.ai.get_suggestions() -> dict[str, Any]
```

Get AI-powered transformation suggestions for the current project.

### query_gen

```python
client.ai.query_gen(
    connector_key: str,
    connection_key: str,
    prompt: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Generate a query for a connector using AI.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `connection_key` | `str` | *required* | Connection key |
| `prompt` | `str` | *required* | Natural language prompt describing the query |

## See also

- [Client](#client-api-reference) -- Full list of sub-clients
- [Projects](#projects-api-reference) -- Project management
- [Datasets](#datasets-api-reference) -- Dataset management


---


# End-to-End Workflow

This guide walks through a complete Mammoth SDK workflow: install, authenticate, upload data, apply transformations, and export results.

## 1. Install the SDK

```bash
pip install mammoth-io
```

Requires Python 3.10+.

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
views = client.views.list()
view = next(v for v in views if v.dataset_id == dataset_id)
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
    views = client.views.list()
    view = next(v for v in views if v.dataset_id == dataset_id)
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
views = client.views.list()
view = next(v for v in views if v.dataset_id == dataset_id)
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

# List all views in the project (returns list of View objects)
views = client.views.list()
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
    view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
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
- Verify Python 3.10+: `python --version`
- Check you are importing from the correct package: `from mammoth import MammothClient`

## See also

- [Exceptions reference](#exceptions-reference) -- error class documentation
- [Configuration](#configuration) -- timeout and URL settings
- [Error handling guide](#error-handling-guide) -- handling patterns


---


# Changelog

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
