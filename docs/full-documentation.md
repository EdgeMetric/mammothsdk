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
    - [`MammothClient`](#mammothclient)
    - [ViewsResource](#viewsresource)
    - [`ViewsResource`](#viewsresource)
  - [Error handling](#error-handling)
  - [See also](#see-also)
- [Views](#views)
  - [Getting a View](#getting-a-view)
  - [Properties](#properties)
  - [Draft mode](#draft-mode)
    - [draft() (context manager)](#draft-context-manager)
    - [Explicit draft workflow](#explicit-draft-workflow)
  - [Full API Reference](#full-api-reference)
    - [`View`](#view)
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
    - [`Condition`](#condition)
    - [`CompoundCondition`](#compoundcondition)
  - [See also](#see-also)
- [Enums & Data Classes](#enums-data-classes)
  - [Enums](#enums)
    - [`Operator`](#operator)
    - [`ColumnType`](#columntype)
    - [`FilterType`](#filtertype)
    - [`JoinType`](#jointype)
    - [`TextCase`](#textcase)
    - [`DateComponent`](#datecomponent)
    - [`DateDiffUnit`](#datediffunit)
    - [`AggregateFunction`](#aggregatefunction)
    - [`WindowFunction`](#windowfunction)
    - [`WindowRange`](#windowrange)
    - [`FillDirection`](#filldirection)
    - [`SortDirection`](#sortdirection)
    - [`MathOperator`](#mathoperator)
    - [`SubstringDirection`](#substringdirection)
    - [`JsonType`](#jsontype)
    - [`ProviderType`](#providertype)
    - [`TaskType`](#tasktype)
  - [Data Classes](#data-classes)
    - [`SetValue`](#setvalue)
  - [See also](#see-also)
- [Exceptions](#exceptions)
  - [Hierarchy](#hierarchy)
  - [Error handling example](#error-handling-example)
  - [Full API Reference](#full-api-reference)
    - [`MammothError`](#mammotherror)
    - [`MammothAPIError`](#mammothapierror)
    - [`MammothAuthError`](#mammothautherror)
    - [`MammothJobTimeoutError`](#mammothjobtimeouterror)
    - [`MammothJobFailedError`](#mammothjobfailederror)
    - [`MammothTransformError`](#mammothtransformerror)
    - [`MammothColumnError`](#mammothcolumnerror)
  - [See also](#see-also)
- [Files](#files)
  - [`FilesAPI`](#filesapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`bulk_delete(self, file_ids: '_list[int]') -> 'None'`](#bulk_deleteself-file_ids-_listint---none)
    - [`delete(self, file_id: 'int') -> 'None'`](#deleteself-file_id-int---none)
    - [`extract_sheets(self, file_id: 'int', sheets: '_list[str]', delete_file_after_extract: 'bool' = True, combine_after_extract: 'bool' = False) -> 'ObjectJobSchema'`](#extract_sheetsself-file_id-int-sheets-_liststr-delete_file_after_extract-bool-true-combine_after_extract-bool-false---objectjobschema)
    - [`get(self, file_id: 'int', fields: 'str | None' = None) -> 'FileSchema'`](#getself-file_id-int-fields-str-none-none---fileschema)
    - [`list(self, fields: 'str | None' = None, file_ids: '_list[int] | None' = None, names: '_list[str] | None' = None, statuses: '_list[str] | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None) -> 'FilesList'`](#listself-fields-str-none-none-file_ids-_listint-none-none-names-_liststr-none-none-statuses-_liststr-none-none-created_at-str-none-none-updated_at-str-none-none-limit-int-50-offset-int-0-sort-str-none-none---fileslist)
    - [`set_password(self, file_id: 'int', password: 'str') -> 'ObjectJobSchema'`](#set_passwordself-file_id-int-password-str---objectjobschema)
    - [`update(self, file_id: 'int', patch_request: 'FilePatchRequest') -> 'ObjectJobSchema'`](#updateself-file_id-int-patch_request-filepatchrequest---objectjobschema)
    - [`upload(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#uploadself-files-_liststr-path-binaryio-str-path-binaryio-none-none-folder_resource_id-str-none-none-append_to_ds_id-int-none-none-override_target_schema-bool-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
    - [`upload_folder(self, folder_path: 'str | Path', folder_resource_id: 'str | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#upload_folderself-folder_path-str-path-folder_resource_id-str-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
- [Connectors](#connectors)
  - [`ConnectorsAPI`](#connectorsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`active_connectors(self) -> '_list[dict[str, Any]]'`](#active_connectorsself---_listdictstr-any)
    - [`create_connection(self, connector_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#create_connectionself-connector_key-str-config-dictstr-any---dictstr-any)
    - [`create_ds_config(self, connector_key: 'str', connection_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#create_ds_configself-connector_key-str-connection_key-str-config-dictstr-any---dictstr-any)
    - [`delete_connection(self, connector_key: 'str', connection_key: 'str') -> 'dict[str, Any]'`](#delete_connectionself-connector_key-str-connection_key-str---dictstr-any)
    - [`delete_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str') -> 'dict[str, Any]'`](#delete_ds_configself-connector_key-str-connection_key-str-ds_config_key-str---dictstr-any)
    - [`get(self, connector_key: 'str') -> 'dict[str, Any]'`](#getself-connector_key-str---dictstr-any)
    - [`get_connection(self, connector_key: 'str', connection_key: 'str') -> 'dict[str, Any]'`](#get_connectionself-connector_key-str-connection_key-str---dictstr-any)
    - [`get_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str') -> 'dict[str, Any]'`](#get_ds_configself-connector_key-str-connection_key-str-ds_config_key-str---dictstr-any)
    - [`list(self) -> '_list[dict[str, Any]]'`](#listself---_listdictstr-any)
    - [`list_connections(self, connector_key: 'str') -> '_list[dict[str, Any]]'`](#list_connectionsself-connector_key-str---_listdictstr-any)
    - [`list_ds_configs(self, connector_key: 'str', connection_key: 'str') -> '_list[dict[str, Any]]'`](#list_ds_configsself-connector_key-str-connection_key-str---_listdictstr-any)
    - [`update_connection(self, connector_key: 'str', connection_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#update_connectionself-connector_key-str-connection_key-str-config-dictstr-any---dictstr-any)
    - [`update_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#update_ds_configself-connector_key-str-connection_key-str-ds_config_key-str-config-dictstr-any---dictstr-any)
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
    - [`ViewExport`](#viewexport)
  - [ExportsAPI (low-level)](#exportsapi-low-level)
    - [`ExportsAPI`](#exportsapi)
  - [See also](#see-also)
- [Projects](#projects)
  - [`ProjectsAPI`](#projectsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`add_users(self, project_id: 'int', user_ids: '_list[str]', role: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_usersself-project_id-int-user_ids-_liststr-role-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`browse(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#browseself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`bulk_delete(self, project_ids: '_list[int]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_deleteself-project_ids-_listint-workspace_id-int-none-none---dictstr-any)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none---dictstr-any)
    - [`create(self, name: 'str', color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-name-str-color-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`delete(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`get(self, project: 'int | str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-project-int-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, limit: 'int' = 100) -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-limit-int-100---dictstr-any)
    - [`remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#remove_usersself-project_id-int-user_ids-_liststr-workspace_id-int-none-none---dictstr-any)
    - [`update(self, project_id: 'int', name: 'str | None' = None, color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-project_id-int-name-str-none-none-color-str-none-none-workspace_id-int-none-none---dictstr-any)
- [Datasets](#datasets)
  - [`DatasetsAPI`](#datasetsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`browse(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#browseself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`bulk_delete(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`](#bulk_deleteself-workspace_id-int-none-none-project_id-int-none-none---none)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create(self, dataset_spec: 'dict[str, Any]', ds_creation_type: 'str', folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-dataset_spec-dictstr-any-ds_creation_type-str-folder_resource_id-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`](#deleteself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---none)
    - [`get(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_batch(self, dataset_id: 'int', batch_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_batchself-dataset_id-int-batch_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int' = 300, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-300-poll_interval-int-2---dictstr-any)
    - [`get_file_settings(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_file_settingsself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc---dictstr-any)
    - [`list_batches(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#list_batchesself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---_listdictstr-any)
    - [`update(self, dataset_id: 'int', patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-dataset_id-int-patch_data-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
- [Dataviews](#dataviews)
  - [`DataviewsAPI`](#dataviewsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`active_users(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#active_usersself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`bulk_delete(self, dataset_id: 'int', dataview_ids: '_list[int] | str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_deleteself-dataset_id-int-dataview_ids-_listint-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`conditional_format_create(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_createself-dataset_id-int-dataview_id-int-rule-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`conditional_format_delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_deleteself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`conditional_format_list(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#conditional_format_listself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---_listdictstr-any)
    - [`conditional_format_update(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_updateself-dataset_id-int-dataview_id-int-rule-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create(self, dataset_id: 'int', name: 'str | None' = 'View', clone_config_from: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-dataset_id-int-name-str-none-view-clone_config_from-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`draft_mode(self, dataset_id: 'int', dataview_id: 'int', command: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#draft_modeself-dataset_id-int-dataview_id-int-command-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`list(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`](#listself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc---dictstr-any)
    - [`mark_active(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#mark_activeself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int' = 0, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#query_dataself-dataset_id-int-dataview_id-int-sequence-int-0-offset-int-1-limit-int-400-columns-_liststr-none-none-condition-dictstr-any-none-none-sort-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`update(self, dataset_id: 'int', dataview_id: 'int', patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-dataset_id-int-dataview_id-int-patch_data-_listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
- [Pipeline](#pipeline)
  - [`PipelineAPI`](#pipelineapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_taskself-dataview_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`delete_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`draft_mode(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#draft_modeself-dataview_id-int-command-str-dataset_id-int-none-none---dictstr-any)
    - [`get_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_pipelineself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`get_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`list_tasks(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#list_tasksself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`preview_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#preview_taskself-dataview_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#update_taskself-dataview_id-int-task_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
- [Jobs](#jobs)
  - [`JobsAPI`](#jobsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`get_job(self, job_id: 'int', timeout: 'int' = 300) -> 'dict[str, Any]'`](#get_jobself-job_id-int-timeout-int-300---dictstr-any)
    - [`get_jobs(self, job_ids: 'list[int] | str') -> 'dict[str, Any]'`](#get_jobsself-job_ids-listint-str---dictstr-any)
    - [`wait_for_job(self, job_id: 'int', timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#wait_for_jobself-job_id-int-timeout-int-none-none-poll_interval-int-2---dictstr-any)
    - [`wait_for_jobs(self, job_ids: 'list[int] | str', timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#wait_for_jobsself-job_ids-listint-str-timeout-int-none-none-poll_interval-int-2---dictstr-any)
- [Dashboards](#dashboards)
  - [`DashboardsAPI`](#dashboardsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`action(self, dashboard_id: 'int', action_config: 'dict[str, Any]') -> 'dict[str, Any]'`](#actionself-dashboard_id-int-action_config-dictstr-any---dictstr-any)
    - [`create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`](#createself-config-dictstr-any---dictstr-any)
    - [`delete(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#deleteself-dashboard_id-int---dictstr-any)
    - [`get(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#getself-dashboard_id-int---dictstr-any)
    - [`get_analytics(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#get_analyticsself-dashboard_id-int---dictstr-any)
    - [`get_by_url(self, url: 'str') -> 'dict[str, Any]'`](#get_by_urlself-url-str---dictstr-any)
    - [`get_draft_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`](#get_draft_dataself-dashboard_id-int-sql-str---dictstr-any)
    - [`get_publish_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`](#get_publish_dataself-dashboard_id-int-sql-str---dictstr-any)
    - [`get_sources(self) -> '_list[dict[str, Any]]'`](#get_sourcesself---_listdictstr-any)
    - [`list(self) -> '_list[dict[str, Any]]'`](#listself---_listdictstr-any)
    - [`share(self, dashboard_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#shareself-dashboard_id-int-config-dictstr-any---dictstr-any)
    - [`update(self, dashboard_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#updateself-dashboard_id-int-config-dictstr-any---dictstr-any)
- [Webhooks](#webhooks)
  - [`WebhooksAPI`](#webhooksapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`](#createself-config-dictstr-any---dictstr-any)
    - [`delete(self, webhook_id: 'int') -> 'dict[str, Any]'`](#deleteself-webhook_id-int---dictstr-any)
    - [`get(self, webhook_id: 'int') -> 'dict[str, Any]'`](#getself-webhook_id-int---dictstr-any)
    - [`list(self) -> '_list[dict[str, Any]]'`](#listself---_listdictstr-any)
    - [`update(self, webhook_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`](#updateself-webhook_id-int-config-dictstr-any---dictstr-any)
- [Automations & Schedules](#automations-schedules)
  - [AutomationsAPI](#automationsapi)
    - [`AutomationsAPI`](#automationsapi)
  - [SchedulesAPI](#schedulesapi)
    - [`SchedulesAPI`](#schedulesapi)
- [Workspace & Users](#workspace-users)
  - [WorkspaceAPI](#workspaceapi)
    - [`WorkspaceAPI`](#workspaceapi)
  - [UserProfileAPI](#userprofileapi)
    - [`UserProfileAPI`](#userprofileapi)
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
pip install mammoth-io==0.3.5
```

Or with Poetry:

```bash
poetry add mammoth-io==0.3.5
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
pip install mammoth-io==0.3.5
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

### `MammothClient`

Main client for interacting with the Mammoth Analytics API.

Provides access to all API endpoints through organized sub-clients.

Example::

    client = MammothClient(
        api_key="your-api-key",
        api_secret="your-api-secret",
        workspace_id=11,
    )
    client.set_project_id(10)

    # Resource-based CRUD
    projects = client.projects.list()
    datasets = client.datasets.list()

    # Rich View objects with transformations
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")

#### `__init__(self, api_key: 'str', api_secret: 'str', workspace_id: 'int', base_url: 'str' = 'https://app.mammoth.io/api/v2', timeout: 'int' = 30, job_timeout: 'int' = 60) -> 'None'`

Initialize the Mammoth client.

Args:
    api_key: Your Mammoth API key.
    api_secret: Your Mammoth API secret.
    workspace_id: Your Mammoth workspace ID.
    base_url: Base URL for the Mammoth API.
    timeout: Request timeout in seconds.
    job_timeout: Job polling timeout in seconds.

#### `set_project_id(self, project_id: 'int') -> 'None'`

Set the default project ID for the client.

Args:
    project_id: ID of the project to use as default.

#### `get_view(self, view_id: 'int', dataset_id: 'int | None' = None) -> 'View'`

Get a rich View object by dataview ID.

Shortcut for ``client.views.get(view_id)``.

Args:
    view_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    View object with transformation methods and metadata.

#### `find_dataset_for_dataview(self, dataview_id: 'int') -> 'int'`

Find the dataset ID for a given dataview.

Searches all datasets in the current project to find
which dataset contains the specified dataview.

Args:
    dataview_id: ID of the dataview.

Returns:
    Dataset ID that contains the dataview.

Raises:
    MammothAPIError: If the dataview cannot be found.

#### `branch_out(self, view_id: 'int', dest_dataset_id: 'int', column_mapping: 'dict[str, str] | None' = None, dataset_id: 'int | None' = None, **kwargs: 'Any') -> 'dict[str, Any]'`

Branch out a view to another dataset.

Args:
    view_id: Source dataview ID.
    dest_dataset_id: Target dataset ID.
    column_mapping: Column mapping dict (optional).
    dataset_id: Source dataset ID (auto-detected if not provided).
    **kwargs: Additional export options.

Returns:
    Export result dict.

#### `test_connection(self) -> 'bool'`

Test the connection to Mammoth API.

Returns:
    True if connection is successful, False otherwise.

### ViewsResource

### `ViewsResource`

Resource that returns rich View objects.

Access via client.views::

    view = client.views.get(view_id)           # returns View object
    views = client.views.list(dataset_id)       # returns list of View objects
    view = client.views.create(dataset_id)      # returns View object

#### `get(self, view_id: 'int', dataset_id: 'int | None' = None) -> 'View'`

Get a rich View object for a dataview.

Args:
    view_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    View object with transformation methods and metadata.

#### `list(self, dataset_id: 'int') -> '_list[View]'`

List all dataviews in a dataset as View objects.

Args:
    dataset_id: ID of the dataset.

Returns:
    List of View objects.

#### `create(self, dataset_id: 'int', name: 'str' = 'View', clone_from: 'int | None' = None) -> 'View'`

Create a new dataview and return as View object.

Args:
    dataset_id: ID of the dataset.
    name: Name for the new dataview (default "View").
    clone_from: ID of dataview to clone config from (optional).

Returns:
    View object for the newly created dataview.

#### `delete(self, view_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a dataview.

Args:
    view_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with deletion result.

#### `bulk_delete(self, dataset_id: 'int', view_ids: '_list[int]') -> 'dict[str, Any]'`

Delete multiple dataviews.

Args:
    dataset_id: ID of the dataset.
    view_ids: List of dataview IDs to delete.

Returns:
    Dict with bulk deletion result.

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

### `View`

Rich domain object for a Mammoth dataview.

Provides access to dataview metadata, data retrieval, pipeline task
management, and 25+ transformation methods. Created via
``client.views.get()`` — not instantiated directly.

Attributes:
    id: Dataview ID (int).
    dataset_id: Parent dataset ID (int).
    name: Dataview display name.
    columns: Dict mapping display names to internal names.
    display_names: Ordered list of column display names.
    column_types: Dict mapping display names to types.
    raw: Full raw API response dict.
    export: ViewExport helper for export operations.

Transformation methods (SET, FILTER, MATH, JOIN, PIVOT, WINDOW, etc.)
send the task to the pipeline API and automatically refresh metadata.
Each method returns the API response dict.

#### `data(self, limit: 'int' = 400, offset: 'int' = 1, columns: 'list[str] | None' = None, condition: 'Condition | CompoundCondition | None' = None, sort: 'str | None' = None) -> 'dict[str, Any]'`

Fetch data from the dataview.

Args:
    limit: Number of rows to fetch (default 400).
    offset: One-indexed starting row (default 1).
    columns: List of display names to fetch (default all).
    condition: Condition object for filtering.
    sort: Sort specification string.

Returns:
    Dict with data rows, columns, and pagination info.

#### `refresh(self) -> 'View'`

Re-fetch metadata from the API and update local state.

Returns:
    self (for chaining).

#### `list_tasks(self) -> 'list[dict[str, Any]]'`

List all pipeline tasks on this dataview.

Returns:
    List of task dicts.

#### `delete_task(self, task_id: 'int') -> 'dict[str, Any]'`

Delete a pipeline task.

Args:
    task_id: ID of the task to remove.

Returns:
    Deletion confirmation dict.

#### `preview_task(self, task_spec: 'dict[str, Any]') -> 'dict[str, Any]'`

Preview a task without applying it.

Args:
    task_spec: Task specification dict.

Returns:
    Preview data dict.

#### `get_column_mapping(self) -> 'dict[str, str]'`

Return a mapping of display names to internal column names.

Returns:
    Dict mapping display names to internal names.

#### `branch_out(self, dest_dataset_id: 'int', column_mapping: 'dict[str, str] | None' = None, **kwargs: 'Any') -> 'dict[str, Any]'`

Branch out (export) this view to another dataset.

Args:
    dest_dataset_id: Target dataset ID.
    column_mapping: Column mapping dict (optional).
    **kwargs: Additional export options.

Returns:
    Export result dict.

#### `filter_rows(self, condition: 'Condition | CompoundCondition', filter_type: 'FilterType' = <FilterType.SHOW: 'SHOW'>, prompt: 'str' = '') -> 'dict[str, Any]'`

Filter rows by condition (SELECT task).

Args:
    condition: Condition or CompoundCondition object.
    filter_type: SHOW to keep matching rows, REMOVE to discard them.
    prompt: Natural-language description of the filter intent (optional).

Returns:
    API response dict.

Example::

    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.filter_rows(cond1 & cond2, filter_type=FilterType.REMOVE)

#### `set_values(self, values: 'list[SetValue | dict[str, Any]]', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Label and insert values into a new or existing column (SET task).

Creates a VERSION 2 SET payload.

Args:
    values: List of SetValue objects or dicts with ``value`` and
        optional ``condition`` keys.
    new_column: Name for a new column (mutually exclusive with existing_column).
    column_type: Type for new column (default ColumnType.TEXT).
    existing_column: Display name of existing column to update.
    condition: Global condition applied to the whole task.

Returns:
    API response dict.

Example::

    view.set_values(
        new_column="Risk Level",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )

#### `math(self, expression: 'str | list[dict[str, Any]]', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.NUMERIC: 'NUMERIC'>, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Apply arithmetic operations (MATH task).

Args:
    expression: Either a string expression (e.g. ``"Price * Quantity"``)
        that will be parsed automatically, or a raw list of expression
        parts in backend format for power users.
    new_column: Name for result column (creates new).
    column_type: Type for new column (default ColumnType.NUMERIC).
    existing_column: Existing column to overwrite.
    condition: Condition to apply.

Returns:
    API response dict.

Examples::

    # String expression (recommended)
    view.math("Price * Quantity", new_column="Total")
    view.math("(Price + Tax) * 1.1", new_column="Grand Total")

    # Raw backend format (power users)
    view.math(
        [{"TYPE": "COLUMN", "VALUE": "Price"},
         {"TYPE": "OPERATOR", "VALUE": "*"},
         {"TYPE": "COLUMN", "VALUE": "Quantity"}],
        new_column="Total",
    )

#### `join(self, foreign_view: 'int | View', join_type: 'JoinType', on: 'list[dict[str, str]]', select: 'list[str] | list[dict[str, str]]', column_prefix: 'str | None' = None) -> 'dict[str, Any]'`

Join with another dataview (JOIN task).

Args:
    foreign_view: View object or ID of the dataview to join with.
        When a View object is passed, display names in ``on.right``
        and ``select`` are resolved automatically.
    join_type: Join type.
    on: Join keys::

        [{"left": "Customer ID", "right": "Customer ID"}]

        Both sides use display names when foreign_view is a View object.
        When foreign_view is an int, ``right`` should be the internal
        column name in the foreign view.
    select: Columns to bring in from the foreign view. Simple list of
        display names (when foreign_view is a View) or list of dicts::

            ["Category", "Name"]
            [{"column": "Category", "alias": "Cat"}]

    column_prefix: Prefix for joined columns (optional).

Returns:
    API response dict.

Examples::

    # Join with View object (display names everywhere)
    other = client.views.get(2050)
    view.join(
        foreign_view=other,
        join_type=JoinType.LEFT,
        on=[{"left": "Customer ID", "right": "Customer ID"}],
        select=["Category", "Name"],
    )

    # Join with view ID (internal names for foreign view)
    view.join(
        foreign_view=2050,
        join_type=JoinType.LEFT,
        on=[{"left": "Customer ID", "right": "column_1"}],
        select=[{"column": "column_7", "alias": "Category"}],
    )

#### `pivot(self, group_by: 'list[str]', aggregations: 'list[dict[str, Any]]', condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Group / aggregate / pivot (PIVOT task).

Args:
    group_by: List of display names to group by.
    aggregations: List of aggregation specs::

        [{"column": "Sales", "function": AggregateFunction.SUM, "as": "Total Sales"}]

    condition: Condition to apply.

Returns:
    API response dict.

Example::

    view.pivot(
        group_by=["Region"],
        aggregations=[{
            "column": "Sales",
            "function": AggregateFunction.SUM,
            "as": "Total Sales",
        }],
    )

#### `window(self, function: 'WindowFunction', column: 'str | None' = None, new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.NUMERIC: 'NUMERIC'>, existing_column: 'str | None' = None, partition_by: 'list[str] | None' = None, order_by: 'list[list[str | SortDirection]] | None' = None, range_type: 'WindowRange' = <WindowRange.UNBOUNDED: 'UNBOUNDED'>) -> 'dict[str, Any]'`

Apply window function (WINDOW task).

Args:
    function: Window function to apply.
    column: Source column for aggregate window functions.
    new_column: Name for result column.
    column_type: Type for new column (default ColumnType.NUMERIC).
    existing_column: Existing column to overwrite.
    partition_by: List of display names to partition by.
    order_by: Sort spec::

        [["column_name", SortDirection.DESC]]

    range_type: Window range (default WindowRange.UNBOUNDED).

Returns:
    API response dict.

Example::

    view.window(
        function=WindowFunction.ROW_NUMBER,
        new_column="Row #",
        partition_by=["Region"],
        order_by=[["Sales", SortDirection.DESC]],
    )

#### `crosstab(self, rows: 'list[str]', pivot_column: 'str', select: 'dict[str, Any]') -> 'dict[str, Any]'`

Crosstab / pivot table (CROSSTAB task).

Args:
    rows: List of display names for row grouping.
    pivot_column: Display name of column whose values become columns.
    select: Aggregation spec::

        {"column": "Sales", "function": AggregateFunction.SUM}

Returns:
    API response dict.

#### `add_column(self, name: 'str', column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>) -> 'dict[str, Any]'`

Add an empty column (ADD_COLUMN task).

Args:
    name: Display name for the new column.
    column_type: Column type (default ColumnType.TEXT).

Returns:
    API response dict.

#### `delete_columns(self, columns: 'list[str]') -> 'dict[str, Any]'`

Remove columns (DELETE task).

Args:
    columns: List of display names to delete.

Returns:
    API response dict.

#### `copy_columns(self, copies: 'list[dict[str, Any]]') -> 'dict[str, Any]'`

Duplicate columns (COPY task).

Args:
    copies: List of copy specs::

        [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}]

Returns:
    API response dict.

#### `combine_columns(self, sources: 'list[str]', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, existing_column: 'str | None' = None, separator: 'str' = ' ', condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Concatenate columns (COMBINE task).

Args:
    sources: List of display names to combine.
    new_column: Name for result column.
    column_type: Type for new column (default ColumnType.TEXT).
    existing_column: Existing column to overwrite.
    separator: Separator between values (default space).
    condition: Condition to apply.

Returns:
    API response dict.

#### `convert_type(self, conversions: 'list[dict[str, str]]') -> 'dict[str, Any]'`

Convert column types (CONVERT task).

Args:
    conversions: List of conversion specs::

        [{"column": "Sales", "to": "NUMERIC"}]

Returns:
    API response dict.

#### `text_transform(self, columns: 'list[str]', case: 'TextCase | None' = None, trim: 'bool' = False, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Apply text case change or trim (TEXT_TRANSFORM task).

Args:
    columns: List of display names to transform.
    case: Case transformation (optional).
    trim: Whether to trim whitespace (default False).
    condition: Condition to apply.

Returns:
    API response dict.

#### `replace_values(self, columns: 'list[str]', find: 'str', replace: 'str', match_case: 'bool' = False, match_words: 'bool' = False, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Find and replace values (REPLACE task).

Args:
    columns: List of display names to search in.
    find: Text to find.
    replace: Replacement text.
    match_case: Case-sensitive matching (default False).
    match_words: Match whole words only (default False).
    condition: Condition to apply.

Returns:
    API response dict.

#### `bulk_replace(self, columns: 'list[str]', mapping: 'list[dict[str, Any]]', match_case: 'bool' = True, match_words: 'bool' = False, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Bulk find-and-replace across one or more columns (REPLACE with MAPPING).

Each mapping entry maps multiple search values to a single replacement.

Args:
    columns: Display names of columns to search in.
    mapping: List of bulk mapping dicts::

        [{"search": ["val1", "val2"], "replace": "replacement"}]

    match_case: Case-sensitive matching (default True).
    match_words: Whole-word matching (default False).
    condition: Condition to apply.

Returns:
    API response dict.

Example::

    view.bulk_replace(
        columns=["Item"],
        mapping=[
            {"search": ["6 inch CAKE", "8 inch CAKE"], "replace": "CAKE"},
        ],
    )

#### `split_column(self, column: 'str', delimiter: 'str', new_columns: 'list[dict[str, str]]') -> 'dict[str, Any]'`

Split a column by delimiter (SPLIT task).

Args:
    column: Display name of column to split.
    delimiter: Delimiter string.
    new_columns: List of new column specs::

        [{"name": "First", "type": "TEXT"}, {"name": "Last", "type": "TEXT"}]

Returns:
    API response dict.

#### `substring(self, column: 'str', direction: 'SubstringDirection | None' = None, num_char: 'int | None' = None, char_position: 'int | None' = None, regex_pattern: 'str | None' = None, regex_invert: 'bool' = False, new_column: 'str | None' = None, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Extract text from a column (SUBSTRING task).

Args:
    column: Source column display name.
    direction: Extraction direction.
        START/END with num_char (first/last N chars).
        LEFT/RIGHT with char_position (chars before/after position).
    num_char: Number of characters to extract (use with START/END).
    char_position: Character position (use with LEFT/RIGHT).
    regex_pattern: Regex pattern for extraction (alternative to direction).
    regex_invert: Invert regex match (default False).
    new_column: Name for result column.
    existing_column: Existing column to overwrite.
    condition: Condition to apply.

Returns:
    API response dict.

#### `extract_date(self, column: 'str', component: 'DateComponent', new_column: 'str | None' = None, existing_column: 'str | None' = None) -> 'dict[str, Any]'`

Extract date parts (EXTRACT_DATE task).

Args:
    column: Source date column display name.
    component: Date component to extract.
    new_column: Name for result column.
    existing_column: Existing column to overwrite.

Returns:
    API response dict.

Example::

    view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")

#### `date_diff(self, component: 'DateDiffUnit', start: 'str', end: 'str', new_column: 'str | None' = None, existing_column: 'str | None' = None) -> 'dict[str, Any]'`

Calculate date difference (DATE_DIFF task).

Args:
    component: Unit of difference (e.g. DateDiffUnit.DAY).
    start: Start date column display name.
    end: End date column display name.
    new_column: Name for result column.
    existing_column: Existing column to overwrite.

Returns:
    API response dict.

Example::

    view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date",
                   new_column="Duration")

#### `increment_date(self, column: 'str', delta: 'dict[str, int]', new_column: 'str | None' = None, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | None' = None) -> 'dict[str, Any]'`

Add or subtract from a date column (INCREMENT_DATE task).

Args:
    column: Source date column display name.
    delta: Delta spec: {"DAYS": 30} or {"MONTHS": -1, "YEARS": 2}.
    new_column: Name for result column.
    existing_column: Existing column to overwrite.
    condition: Condition to apply.

Returns:
    API response dict.

#### `fill_missing(self, column: 'str', direction: 'FillDirection', partition_by: 'str | None' = None, order_by: 'list[list[str | SortDirection]] | None' = None) -> 'dict[str, Any]'`

Fill missing values forward or backward (FILL task).

Args:
    column: Display name of column to fill.
    direction: Fill direction.
    partition_by: Column to partition by (optional).
    order_by: Sort order for fill direction (optional).

Returns:
    API response dict.

#### `limit_rows(self, n: 'int', bottom: 'bool' = False, order_by: 'list[list[str | SortDirection]] | None' = None) -> 'dict[str, Any]'`

Keep top or bottom N rows (LIMIT task).

Args:
    n: Number of rows to keep.
    bottom: If True, keep bottom N instead of top N (default False).
    order_by: Sort order before limiting (optional).

Returns:
    API response dict.

#### `discard_duplicates(self, ignore_columns: 'list[str] | None' = None) -> 'dict[str, Any]'`

Remove duplicate rows (DISCARD_DUPLICATES task).

Args:
    ignore_columns: Display names of columns to ignore when detecting
        duplicates. Empty/None means consider all columns.

Returns:
    API response dict.

Example::

    view.discard_duplicates()
    view.discard_duplicates(ignore_columns=["Notes", "Timestamp"])

#### `unnest(self, columns: 'list[str]', label_column: 'str' = 'Label', value_column: 'str' = 'Value') -> 'dict[str, Any]'`

Unpivot columns to rows (UNNEST task).

Args:
    columns: Display names of columns to unnest.
    label_column: Name for the label column (default "Label").
    value_column: Name for the value column (default "Value").

Returns:
    API response dict.

#### `lookup(self, source: 'str', lookup_view_id: 'int', key: 'str', value: 'str', new_column: 'str | None' = None, existing_column: 'str | None' = None) -> 'dict[str, Any]'`

Lookup values from another dataview (LOOKUP task).

Args:
    source: Source column display name (the key in this view).
    lookup_view_id: ID of the dataview to look up from.
    key: Key column name in the lookup view.
    value: Value column name in the lookup view.
    new_column: Name for result column.
    existing_column: Existing column to overwrite.

Returns:
    API response dict.

#### `json_extract(self, column: 'str', json_type: 'JsonType' = <JsonType.OBJECT: 'OBJECT'>, keys: 'list[str] | None' = None, extractions: 'list[dict[str, str]] | None' = None, keep_source: 'bool' = False, op_type: 'str | None' = None) -> 'dict[str, Any]'`

Extract data from JSON column (JSON_HANDLE task).

Args:
    column: Source JSON column display name.
    json_type: JSON structure type (default JsonType.OBJECT).
    keys: Simple list of keys to extract (each becomes TEXT column).
        Use for quick extraction without custom types/aliases.
    extractions: Advanced extraction specs (overrides keys)::

        [{"key": "name", "as": "Name", "type": "TEXT"}]

    keep_source: Keep the original JSON column (default False).
    op_type: Operation type override.

Returns:
    API response dict.

Example::

    # Simple key extraction
    view.json_extract("data", keys=["name", "email", "age"])

    # Advanced with custom types
    view.json_extract(
        "data",
        extractions=[
            {"key": "name", "as": "Name", "type": "TEXT"},
            {"key": "age", "as": "Age", "type": "NUMERIC"},
        ],
    )

#### `gen_ai(self, prompt: 'str', context_columns: 'list[str]', new_column: 'str' = 'AI Result', assistant_data: 'list[str] | None' = None) -> 'dict[str, Any]'`

AI-powered transformation (GEN_AI task).

Args:
    prompt: Natural language prompt for the AI.
    context_columns: Display names of columns to use as context.
    new_column: Name for the AI output column (default "AI Result").
    assistant_data: Additional assistant context strings.

Returns:
    API response dict.

Example::

    view.gen_ai(
        prompt="Classify the sentiment of the review",
        context_columns=["Review Text"],
        new_column="Sentiment",
    )

#### `generate_sql(self, intent: 'str') -> 'str'`

Generate SQL from a natural language intent using Mammoth LLM.

Calls the ``/sql_generation`` endpoint which converts the intent to SQL
and adds the resulting task to the pipeline.

Args:
    intent: Natural language description (e.g. "count employees by department").

Returns:
    The generated SQL query string.

#### `add_sql(self, query: 'str') -> 'dict[str, Any]'`

Add a raw SQL query as a pipeline task.

Args:
    query: SQL query string.

Returns:
    API response dict.

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

See the [Operator enum](#operator) for the complete list. Summary:

| Category | Operators |
|----------|-----------|
| Comparison | `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE` |
| List | `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS` |
| String | `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH` |
| Null | `IS_EMPTY`, `IS_NOT_EMPTY` |
| Aggregate | `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL` |

---

## Full API Reference

### `Condition`

Single column condition. Supports & (AND) and | (OR) operators.

Args:
    column: Display name of the column (e.g. "Sales", "Region").
    operator: Operator enum value (e.g. Operator.GTE, Operator.IN_LIST).
    value: Comparison value. Required for most operators, omit for IS_EMPTY.
    case_sensitive: Whether string comparisons are case-sensitive (default False).

Examples::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])
    Condition("Name", Operator.IS_NOT_EMPTY)
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")

#### `__init__(self, column: 'str', operator: 'str | Any', value: 'Any' = None, case_sensitive: 'bool' = False) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `build(self, column_map: 'dict[str, str] | None' = None) -> 'dict[str, Any]'`

Build API-format condition dict.

Args:
    column_map: Mapping of display names to internal names.

Returns:
    dict in Mammoth API condition format.

### `CompoundCondition`

AND/OR composition of conditions. Supports further chaining with & and |.

Created automatically when combining Conditions with & or |::

    combined = cond1 & cond2  # CompoundCondition("AND", [cond1, cond2])
    triple = combined & cond3  # Flat AND of all three

#### `__init__(self, logic: 'str', conditions: 'list[Condition | CompoundCondition]') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `build(self, column_map: 'dict[str, str] | None' = None) -> 'dict[str, Any]'`

Build API-format condition dict.

Args:
    column_map: Mapping of display names to internal names.

Returns:
    dict in Mammoth API condition format with AND/OR keys.

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

### `Operator`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `CONTAINS`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `ENDS_WITH`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `EQ`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `GT`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `GTE`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IN_LIST`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_EMPTY`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_MAXVAL`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_MINVAL`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_NOT_EMPTY`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_NOT_MAXVAL`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IS_NOT_MINVAL`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `LT`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `LTE`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `NE`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `NOT_CONTAINS`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `NOT_ENDS_WITH`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `NOT_IN_LIST`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `NOT_STARTS_WITH`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `STARTS_WITH`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

### `ColumnType`

Column data types for new columns and conversions.

#### `DATE`

Column data types for new columns and conversions.

#### `NUMERIC`

Column data types for new columns and conversions.

#### `TEXT`

Column data types for new columns and conversions.

### `FilterType`

Filter types for SELECT (filter_rows) tasks.

Controls whether matching rows are kept or removed:
    SHOW — keep rows that match the condition.
    REMOVE — discard rows that match the condition.

#### `REMOVE`

Filter types for SELECT (filter_rows) tasks.

Controls whether matching rows are kept or removed:
    SHOW — keep rows that match the condition.
    REMOVE — discard rows that match the condition.

#### `SHOW`

Filter types for SELECT (filter_rows) tasks.

Controls whether matching rows are kept or removed:
    SHOW — keep rows that match the condition.
    REMOVE — discard rows that match the condition.

### `JoinType`

Join types for combining dataviews.

#### `INNER`

Join types for combining dataviews.

#### `LEFT`

Join types for combining dataviews.

#### `OUTER`

Join types for combining dataviews.

#### `RIGHT`

Join types for combining dataviews.

### `TextCase`

Text case transformations.

#### `LOWER`

Text case transformations.

#### `TITLE`

Text case transformations.

#### `UPPER`

Text case transformations.

### `DateComponent`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `DATE_ONLY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `DAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `DAY_OF_WEEK`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `DAY_OF_YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `HOUR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `HOUR_MINUTE`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `HOUR_MINUTE_SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `MINUTE`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `MONTH`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `MONTH_DAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `MONTH_DAY_YEAR_HOUR_MINUTE_SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `MONTH_TEXT`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `QUARTER`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `WEEK`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `WEEKDAY_TEXT`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR_MONTH`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR_MONTH_DAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR_MONTH_DAY_AS_DATE`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR_QUARTER`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

#### `YEAR_WEEK`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

Basic components:
    year, month, day, hour, minute, second, week, quarter

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second

### `DateDiffUnit`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `DAY`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `HOUR`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `MINUTE`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `MONTH`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `QUARTER`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `SECOND`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `WEEK`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

#### `YEAR`

Date units for date_diff calculations.

Uses UPPERCASE values (distinct from DateComponent which is lowercase).

### `AggregateFunction`

Aggregate functions for pivot/group operations.

#### `AVG`

Aggregate functions for pivot/group operations.

#### `CONCAT`

Aggregate functions for pivot/group operations.

#### `COUNT`

Aggregate functions for pivot/group operations.

#### `COUNT_DISTINCT`

Aggregate functions for pivot/group operations.

#### `FIRST`

Aggregate functions for pivot/group operations.

#### `LAST`

Aggregate functions for pivot/group operations.

#### `MAX`

Aggregate functions for pivot/group operations.

#### `MEDIAN`

Aggregate functions for pivot/group operations.

#### `MIN`

Aggregate functions for pivot/group operations.

#### `STDDEV`

Aggregate functions for pivot/group operations.

#### `SUM`

Aggregate functions for pivot/group operations.

#### `VARIANCE`

Aggregate functions for pivot/group operations.

### `WindowFunction`

Window function types.

#### `AVG`

Window function types.

#### `COUNT`

Window function types.

#### `DENSE_RANK`

Window function types.

#### `FIRST_VALUE`

Window function types.

#### `LAG`

Window function types.

#### `LAST_VALUE`

Window function types.

#### `LEAD`

Window function types.

#### `MAX`

Window function types.

#### `MIN`

Window function types.

#### `NTILE`

Window function types.

#### `PERCENT_RANK`

Window function types.

#### `RANK`

Window function types.

#### `ROW_NUMBER`

Window function types.

#### `STDDEV`

Window function types.

#### `SUM`

Window function types.

#### `VARIANCE`

Window function types.

### `WindowRange`

Window range types.

#### `RUNNING`

Window range types.

#### `UNBOUNDED`

Window range types.

### `FillDirection`

Fill directions for missing value imputation.

#### `FIRST_VALUE`

Fill directions for missing value imputation.

#### `LAST_VALUE`

Fill directions for missing value imputation.

### `SortDirection`

Sort direction for order_by clauses.

#### `ASC`

Sort direction for order_by clauses.

#### `DESC`

Sort direction for order_by clauses.

### `MathOperator`

Arithmetic operators for math expressions.

#### `ADD`

Arithmetic operators for math expressions.

#### `DIVIDE`

Arithmetic operators for math expressions.

#### `MODULO`

Arithmetic operators for math expressions.

#### `MULTIPLY`

Arithmetic operators for math expressions.

#### `SUBTRACT`

Arithmetic operators for math expressions.

### `SubstringDirection`

Extraction direction for substring operations.

START/END: extract first/last N characters (use with num_char).
LEFT/RIGHT: extract characters before/after position (use with char_position).

#### `END`

Extraction direction for substring operations.

START/END: extract first/last N characters (use with num_char).
LEFT/RIGHT: extract characters before/after position (use with char_position).

#### `LEFT`

Extraction direction for substring operations.

START/END: extract first/last N characters (use with num_char).
LEFT/RIGHT: extract characters before/after position (use with char_position).

#### `RIGHT`

Extraction direction for substring operations.

START/END: extract first/last N characters (use with num_char).
LEFT/RIGHT: extract characters before/after position (use with char_position).

#### `START`

Extraction direction for substring operations.

START/END: extract first/last N characters (use with num_char).
LEFT/RIGHT: extract characters before/after position (use with char_position).

### `JsonType`

JSON structure types for json_extract.

#### `LIST`

JSON structure types for json_extract.

#### `OBJECT`

JSON structure types for json_extract.

*See API reference for `mammoth.models.pipeline.JsonOpType`*

*See API reference for `mammoth.models.pipeline.ExportFileType`*

### `ProviderType`

Value provider types for SET task VALUES items.

Use in set_values() value specs to control how the value is determined:
    FIXED — a literal value (e.g. "High", 42).
    EXPRESSION — a system expression (e.g. "__TIME__" for current timestamp).

#### `EXPRESSION`

Value provider types for SET task VALUES items.

Use in set_values() value specs to control how the value is determined:
    FIXED — a literal value (e.g. "High", 42).
    EXPRESSION — a system expression (e.g. "__TIME__" for current timestamp).

#### `FIXED`

Value provider types for SET task VALUES items.

Use in set_values() value specs to control how the value is determined:
    FIXED — a literal value (e.g. "High", 42).
    EXPRESSION — a system expression (e.g. "__TIME__" for current timestamp).

### `TaskType`

Pipeline task types.

#### `ADD_COLUMN`

Pipeline task types.

#### `COMBINE`

Pipeline task types.

#### `CONVERT`

Pipeline task types.

#### `COPY`

Pipeline task types.

#### `CROSSTAB`

Pipeline task types.

#### `DATE_DIFF`

Pipeline task types.

#### `DELETE`

Pipeline task types.

#### `DISCARD_DUPLICATES`

Pipeline task types.

#### `EXTRACT_DATE`

Pipeline task types.

#### `FILL`

Pipeline task types.

#### `GEN_AI`

Pipeline task types.

#### `INCREMENT_DATE`

Pipeline task types.

#### `JOIN`

Pipeline task types.

#### `JSON_HANDLE`

Pipeline task types.

#### `LIMIT`

Pipeline task types.

#### `LOOKUP`

Pipeline task types.

#### `MATH`

Pipeline task types.

#### `PIVOT`

Pipeline task types.

#### `REPLACE`

Pipeline task types.

#### `SELECT`

Pipeline task types.

#### `SET`

Pipeline task types.

#### `SPLIT`

Pipeline task types.

#### `SQL`

Pipeline task types.

#### `SUBSTRING`

Pipeline task types.

#### `TEXT_TRANSFORM`

Pipeline task types.

#### `UNNEST`

Pipeline task types.

#### `WINDOW`

Pipeline task types.

*See API reference for `mammoth.models.pipeline.DraftCommand`*

---

## Data Classes

### `SetValue`

A value specification for set_values().

Args:
    value: The literal value to set.
    condition: Optional condition — rows matching this condition get this value.

Example::

    from mammoth import SetValue, Condition, Operator

    values = [
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ]
    view.set_values(new_column="Risk", values=values)

#### `__init__(self, value: 'Any', condition: 'Condition | CompoundCondition | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

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

### `MammothError`

Base exception for Mammoth SDK errors.

#### `__init__(self, message: 'str', details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothAPIError`

Exception raised for API-related errors.

#### `__init__(self, message: 'str', status_code: 'int | None' = None, response_body: 'dict[str, Any] | None' = None, details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothAuthError`

Exception raised for authentication-related errors.

#### `__init__(self, message: 'str' = 'Authentication failed') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothJobTimeoutError`

Exception raised when a job times out.

#### `__init__(self, job_id: 'int', timeout_seconds: 'int') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothJobFailedError`

Exception raised when a job fails.

#### `__init__(self, job_id: 'int', failure_reason: 'str | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothTransformError`

Exception raised when a transformation task fails.

#### `__init__(self, message: 'str', task_key: 'str | None' = None, details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

### `MammothColumnError`

Exception raised when a column name cannot be resolved.

#### `__init__(self, column_name: 'str', available_columns: 'list[str] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `with_traceback`

Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.

## See also

- [Client](#client-api-reference) -- error handling in the client
- [Views](#views-reference) -- transformation methods that raise these exceptions


---


# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion.

**Access**: `client.files`

```python
# Upload a CSV file
result = client.files.upload("data.csv", dataset_name="Sales Data")

# Upload an Excel file
result = client.files.upload("report.xlsx", dataset_name="Report")
```

---

## `FilesAPI`

Client for interacting with Mammoth Files API.

Access via client.files:
    files = client.files.list()
    file_info = client.files.get(file_id=123)
    ds_id = client.files.upload("data.csv")
    client.files.delete(123)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `bulk_delete(self, file_ids: '_list[int]') -> 'None'`

Delete multiple files.

Args:
    file_ids: List of file IDs to delete.

### `delete(self, file_id: 'int') -> 'None'`

Delete a specific file.

Args:
    file_id: ID of the file to delete.

### `extract_sheets(self, file_id: 'int', sheets: '_list[str]', delete_file_after_extract: 'bool' = True, combine_after_extract: 'bool' = False) -> 'ObjectJobSchema'`

Extract specific sheets from an Excel file.

Args:
    file_id: ID of the Excel file.
    sheets: List of sheet names to extract.
    delete_file_after_extract: Delete main file after extraction.
    combine_after_extract: Combine sheets after extraction.

Returns:
    ObjectJobSchema with job information.

### `get(self, file_id: 'int', fields: 'str | None' = None) -> 'FileSchema'`

Get detailed information about a specific file.

Args:
    file_id: ID of the file.
    fields: Fields to return (default "__standard").

Returns:
    FileSchema with detailed file information.

### `list(self, fields: 'str | None' = None, file_ids: '_list[int] | None' = None, names: '_list[str] | None' = None, statuses: '_list[str] | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None) -> 'FilesList'`

List files in a project with optional filtering and pagination.

Args:
    fields: Fields to return (e.g., "__standard", "__full", "__min").
    file_ids: List of specific file IDs to retrieve.
    names: List of file names to filter by.
    statuses: List of statuses to filter by.
    created_at: Date range filter for creation date.
    updated_at: Date range filter for update date.
    limit: Maximum number of results (0-100, default 50).
    offset: Number of results to skip (default 0).
    sort: Sort specification (e.g., "(id:asc),(name:desc)").

Returns:
    FilesList with files and pagination info.

### `set_password(self, file_id: 'int', password: 'str') -> 'ObjectJobSchema'`

Set password for a password-protected file.

Args:
    file_id: ID of the file.
    password: Password to set.

Returns:
    ObjectJobSchema with job information.

### `update(self, file_id: 'int', patch_request: 'FilePatchRequest') -> 'ObjectJobSchema'`

Update file configuration (e.g., set password, extract sheets).

Args:
    file_id: ID of the file to update.
    patch_request: Configuration changes to apply.

Returns:
    ObjectJobSchema with job information.

### `upload(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`

Upload one or more files to create datasets.

Each file becomes a separate dataset. Folder structure is preserved.

Args:
    files: File(s) to upload — file paths, Path objects, or file-like objects.
    folder_resource_id: Resource ID of target folder.
    append_to_ds_id: Dataset ID to append to (if appending).
    override_target_schema: Override target schema when appending.
    wait_for_completion: Wait for upload processing to complete.
    timeout: Timeout in seconds when waiting for completion.

Returns:
    If wait_for_completion=False: Initial job ID.
    If wait_for_completion=True: List of dataset IDs (or single ID for one file).

### `upload_folder(self, folder_path: 'str | Path', folder_resource_id: 'str | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`

Upload all files in a folder to create datasets.

Args:
    folder_path: Path to the folder containing files.
    folder_resource_id: Resource ID of target folder in Mammoth.
    wait_for_completion: Wait for upload processing to complete.
    timeout: Timeout in seconds when waiting for completion.

Returns:
    List of dataset IDs (or single ID) if wait_for_completion=True.


---


# Connectors API Reference

The `ConnectorsAPI` manages cloud data source connectors and their connections. Use connectors to import data from databases (PostgreSQL, MySQL, BigQuery, etc.), cloud storage, and other external sources.

**Access**: `client.connectors`

---

## `ConnectorsAPI`

Client for managing cloud data source connectors and connections.

Access via client.connectors:
    connectors = client.connectors.list()
    conn = client.connectors.create_connection("postgres", config={...})
    client.connectors.delete_connection("postgres", "conn_key")

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `active_connectors(self) -> '_list[dict[str, Any]]'`

List active connectors with established connections.

Returns:
    List of active connector dicts.

### `create_connection(self, connector_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new connection for a connector.

Args:
    connector_key: Key identifying the connector type.
    config: Connection configuration (host, port, database, credentials, etc.).

Returns:
    Dict with created connection info.

### `create_ds_config(self, connector_key: 'str', connection_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    config: Data source configuration.

Returns:
    Dict with created data source config.

### `delete_connection(self, connector_key: 'str', connection_key: 'str') -> 'dict[str, Any]'`

Delete a connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.

Returns:
    Dict with deletion result.

### `delete_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str') -> 'dict[str, Any]'`

Delete a data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.

Returns:
    Dict with deletion result.

### `get(self, connector_key: 'str') -> 'dict[str, Any]'`

Get details of a specific connector.

Args:
    connector_key: Key identifying the connector type (e.g., "postgres", "mysql").

Returns:
    Dict with connector details.

### `get_connection(self, connector_key: 'str', connection_key: 'str') -> 'dict[str, Any]'`

Get details of a specific connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.

Returns:
    Dict with connection details.

### `get_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str') -> 'dict[str, Any]'`

Get a specific data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.

Returns:
    Dict with data source config details.

### `list(self) -> '_list[dict[str, Any]]'`

List all available connectors.

Returns:
    List of connector dicts.

### `list_connections(self, connector_key: 'str') -> '_list[dict[str, Any]]'`

List connections for a connector type.

Args:
    connector_key: Key identifying the connector type.

Returns:
    List of connection dicts.

### `list_ds_configs(self, connector_key: 'str', connection_key: 'str') -> '_list[dict[str, Any]]'`

List data source configurations for a connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.

Returns:
    List of data source config dicts.

### `update_connection(self, connector_key: 'str', connection_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update a connection's configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    config: Updated connection configuration.

Returns:
    Dict with updated connection info.

### `update_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update a data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.
    config: Updated data source configuration.

Returns:
    Dict with updated config.


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

### `ViewExport`

Export operations for a View. Access via view.export.

Examples::

    view.export.to_csv("output.csv")
    view.export.to_postgres(host="...", database="...", table="...")
    view.export.list()

#### `to_csv(self, output_path: 'str | None' = None, timeout: 'int' = 300) -> 'Path'`

Download dataview data as CSV file.

Args:
    output_path: Path for the output file.
    timeout: Timeout in seconds (default 300).

Returns:
    Path to the downloaded CSV file.

#### `to_s3(self, file_name: 'str | None' = None, file_type: 'str' = 'csv', include_hidden: 'bool' = False, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to S3.

Args:
    file_name: Output filename (auto-generated if not provided).
    file_type: File format (default "csv").
    include_hidden: Include hidden columns (default False).

Returns:
    Export result dict with download URL.

#### `to_postgres(self, host: 'str', port: 'int', database: 'str', table: 'str', username: 'str', password: 'str', **kwargs: 'Any') -> 'dict[str, Any]'`

Export to PostgreSQL database.

Args:
    host: Database host.
    port: Database port.
    database: Database name.
    table: Target table name.
    username: Database username.
    password: Database password.

Returns:
    Export result dict.

#### `to_mysql(self, host: 'str', port: 'int', database: 'str', table: 'str', username: 'str', password: 'str', **kwargs: 'Any') -> 'dict[str, Any]'`

Export to MySQL database.

Args:
    host: Database host.
    port: Database port.
    database: Database name.
    table: Target table name.
    username: Database username.
    password: Database password.

Returns:
    Export result dict.

#### `to_dataset(self, dest_dataset_id: 'int', column_mapping: 'dict[str, str] | None' = None, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to another Mammoth dataset (branch out).

Args:
    dest_dataset_id: Target dataset ID.
    column_mapping: Column mapping dict (optional).

Returns:
    Export result dict.

#### `to_ftp(self, host: 'str', path: 'str', username: 'str', password: 'str', port: 'int' = 21, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to FTP server.

Args:
    host: FTP host.
    path: Remote file path.
    username: FTP username.
    password: FTP password.
    port: FTP port (default 21).

Returns:
    Export result dict.

#### `to_sftp(self, host: 'str', path: 'str', username: 'str', password: 'str', port: 'int' = 22, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to SFTP server.

Args:
    host: SFTP host.
    path: Remote file path.
    username: SFTP username.
    password: SFTP password.
    port: SFTP port (default 22).

Returns:
    Export result dict.

#### `to_email(self, recipients: 'list[str]', **kwargs: 'Any') -> 'dict[str, Any]'`

Export via email.

Args:
    recipients: List of email addresses.

Returns:
    Export result dict.

#### `to_bigquery(self, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to Google BigQuery.

Args:
    **kwargs: BigQuery connection and table configuration.

Returns:
    Export result dict.

#### `to_redshift(self, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to Amazon Redshift.

Args:
    **kwargs: Redshift connection and table configuration.

Returns:
    Export result dict.

#### `to_elasticsearch(self, **kwargs: 'Any') -> 'dict[str, Any]'`

Export to Elasticsearch.

Args:
    **kwargs: Elasticsearch connection and index configuration.

Returns:
    Export result dict.

#### `publish_to_db(self, **kwargs: 'Any') -> 'dict[str, Any]'`

Publish dataview to database.

Args:
    **kwargs: Database connection and table configuration.

Returns:
    Export result dict.

#### `list(self) -> '_list[dict[str, Any]]'`

List all exports for this dataview.

Returns:
    List of export dicts.

#### `delete(self, export_id: 'int') -> 'dict[str, Any]'`

Delete an export.

Args:
    export_id: ID of the export to delete.

Returns:
    Deletion confirmation dict.

---

## ExportsAPI (low-level)

The `client.exports` sub-client provides lower-level export operations. Most users should prefer the `ViewExport` methods above.

### `ExportsAPI`

Client for interacting with Mammoth Exports API.

Access via client.exports:
    exports = client.exports.list(dataview_id=456)
    client.exports.create(dataview_id=456, export_spec=spec, dataset_id=123)
    client.exports.to_csv(dataview_id=456, output_path="output.csv")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, dataview_id: 'int', export_spec: 'AddExportSpec', dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'PipelineExportsModificationResp | JobResponse'`

Add a new export to the dataview pipeline.

Args:
    dataview_id: ID of the dataview.
    export_spec: Export specification.
    dataset_id: ID of the dataset (required).
    project_id: ID of the project (uses client default if not provided).

Returns:
    PipelineExportsModificationResp or JobResponse.

#### `list(self, dataview_id: 'int', fields: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'ExportStatus | None' = None, reordered: 'bool | None' = None, handler_type: 'HandlerType | None' = None, end_of_pipeline: 'bool | None' = None, runnable: 'bool | None' = None) -> 'PipelineExportsPaginated'`

Get dataview pipeline exports with optional filtering and pagination.

Args:
    dataview_id: ID of the dataview.
    fields: Fields to return.
    limit: Maximum number of results (0-100, default 50).
    offset: Number of results to skip (default 0).
    sort: Sort specification.
    sequence: Filter by sequence number.
    status: Filter by export status.
    reordered: Filter by reordered status.
    handler_type: Filter by handler type.
    end_of_pipeline: Filter by end of pipeline status.
    runnable: Filter by runnable status.

Returns:
    PipelineExportsPaginated with paginated list of exports.

#### `to_csv(self, dataview_id: 'int', output_path: 'str | Path | None' = None, timeout: 'int' = 300, dataset_id: 'int | None' = None) -> 'Path'`

Download dataview data as a CSV file.

Creates a CSV export job, waits for completion, and downloads the result.

Args:
    dataview_id: ID of the dataview to export.
    output_path: Path for the CSV file (auto-generated if not provided).
    timeout: Timeout in seconds (default 300).
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Path to the downloaded CSV file.

#### `to_dataset(self, dataview_id: 'int', dataset_name: 'str', column_mapping: 'dict[str, Any] | None' = None, sequence: 'int | None' = None, trigger_id: 'int | None' = None, end_of_pipeline: 'bool' = True, trigger_type: 'TriggerType' = <TriggerType.PIPELINE: 'pipeline'>, condition: 'dict[str, Any] | None' = None, run_immediately: 'bool' = True, validate_only: 'bool' = False, additional_properties: 'dict[str, Any] | None' = None) -> 'PipelineExportsModificationResp | JobResponse'`

Create an internal dataset export.

Args:
    dataview_id: ID of the dataview.
    dataset_name: Name for the created dataset.
    column_mapping: Column mapping configuration.
    sequence: Position in pipeline.
    trigger_id: Trigger ID for editing existing export.
    end_of_pipeline: Execute at end of pipeline (default True).
    trigger_type: Type of trigger (default PIPELINE).
    condition: Export conditions.
    run_immediately: Execute immediately (default True).
    validate_only: Only validate config (default False).
    additional_properties: Additional configuration.

Returns:
    PipelineExportsModificationResp or JobResponse.

#### `to_s3(self, dataview_id: 'int', file: 'str | None' = None, file_type: 'str' = 'csv', include_hidden: 'bool' = False, is_format_set: 'bool' = True, use_format: 'bool' = True, sequence: 'int | None' = None, trigger_id: 'int | None' = None, end_of_pipeline: 'bool' = True, trigger_type: 'TriggerType' = <TriggerType.PIPELINE: 'pipeline'>, condition: 'dict[str, Any] | None' = None, run_immediately: 'bool' = True, validate_only: 'bool' = False, additional_properties: 'dict[str, Any] | None' = None, dataset_id: 'int | None' = None) -> 'PipelineExportsModificationResp | JobResponse | dict[str, Any]'`

Create an S3 export with simplified parameters.

Args:
    dataview_id: ID of the dataview.
    file: Output filename (auto-generated if not provided).
    file_type: File format type (default "csv").
    include_hidden: Include hidden columns (default False).
    is_format_set: Format explicitly set (default True).
    use_format: Apply formatting (default True).
    sequence: Position in pipeline.
    trigger_id: Trigger ID for editing existing export.
    end_of_pipeline: Execute at end of pipeline (default True).
    trigger_type: Type of trigger (default PIPELINE).
    condition: Export conditions.
    run_immediately: Execute immediately (default True).
    validate_only: Only validate config (default False).
    additional_properties: Additional configuration.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with URL and trigger_id if job completes.

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

## `ProjectsAPI`

Client for interacting with Mammoth Projects API.

Access via client.projects:
    projects = client.projects.list()
    project = client.projects.get(123)
    client.projects.create(name="Analytics")
    client.projects.update(123, name="Analytics v2")
    client.projects.delete(123)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `add_users(self, project_id: 'int', user_ids: '_list[str]', role: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Add users to a project.

Args:
    project_id: ID of the project.
    user_ids: List of user email addresses or IDs.
    role: Role to assign (optional).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with result.

### `browse(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse project contents (datasets, folders).

Args:
    project_id: ID of the project.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with project contents.

### `bulk_delete(self, project_ids: '_list[int]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk delete multiple projects.

Args:
    project_ids: List of project IDs to delete.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with bulk deletion result.

### `bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk update multiple projects.

Args:
    patch_data: Patch operations for multiple projects.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with bulk update result.

### `create(self, name: 'str', color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new project.

Args:
    name: Name for the new project.
    color: Color code for the project (optional).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with created project info.

### `delete(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a project.

Args:
    project_id: ID of the project to delete.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with deletion result.

### `get(self, project: 'int | str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a single project by ID, name, or auto-selection.

Behavior:
- project=None: Auto-select if only 1 project exists.
- project=123: Find project with ID 123.
- project="My Project": Find project by name.

Args:
    project: Project ID (int), name (str), or None for auto-selection.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with project id and name.

Raises:
    ValueError: If project not found or multiple projects without specification.

### `list(self, workspace_id: 'int | None' = None, limit: 'int' = 100) -> 'dict[str, Any]'`

List all projects in a workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    limit: Maximum number of results (default 100).

Returns:
    Dict containing projects list with id and name.

### `remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Remove users from a project.

Args:
    project_id: ID of the project.
    user_ids: List of user IDs to remove.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with result.

### `update(self, project_id: 'int', name: 'str | None' = None, color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a project.

Args:
    project_id: ID of the project to update.
    name: New name (optional).
    color: New color code (optional).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated project info.


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

## `DatasetsAPI`

Client for interacting with Mammoth Datasets API.

Access via client.datasets:
    datasets = client.datasets.list()
    dataset = client.datasets.get(123)
    data = client.datasets.get_data(123)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `browse(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse dataset contents (dataviews, metadata).

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with dataset contents.

### `bulk_delete(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`

Delete multiple datasets (bulk operation).

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

### `bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update multiple datasets (bulk operation).

Args:
    patch_data: Patch operation data for multiple datasets.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with bulk update result.

### `create(self, dataset_spec: 'dict[str, Any]', ds_creation_type: 'str', folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new dataset.

Args:
    dataset_spec: Dataset specification (varies by creation type).
    ds_creation_type: Type of creation: "clone", "cloud", "sketch", "weburl".
    folder_resource_id: Optional folder resource ID.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with created dataset information.

### `delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`

Delete a dataset.

Args:
    dataset_id: ID of the dataset to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

### `get(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get dataset details by ID.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with complete dataset information.

### `get_batch(self, dataset_id: 'int', batch_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get details of a specific batch.

Args:
    dataset_id: ID of the dataset.
    batch_id: ID of the batch.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with batch details.

### `get_data(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int' = 300, poll_interval: 'int' = 2) -> 'dict[str, Any]'`

Get the actual data from a dataset. Polls the job until completion.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    timeout: Maximum wait time in seconds (default 300).
    poll_interval: Polling interval in seconds (default 2).

Returns:
    Dict with dataset data.

### `get_file_settings(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get file settings for a dataset.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with file settings.

### `list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`

Get list of datasets in a project.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    limit: Maximum number of results (default 100).
    sort: Sort order (default "(created_at:desc)").

Returns:
    Dict containing datasets list with id, name and other info.

### `list_batches(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    List of batch dicts.

### `update(self, dataset_id: 'int', patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a dataset.

Args:
    dataset_id: ID of the dataset to update.
    patch_data: Patch operation data.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with updated dataset information.


---


# Dataviews API Reference

The `DataviewsAPI` provides low-level CRUD operations on dataviews. For rich transformation methods, use `client.views` instead (see [Views](#views-reference)).

**Access**: `client.dataviews`

---

## `DataviewsAPI`

Client for interacting with Mammoth Dataviews API.

Access via client.dataviews:
    views = client.dataviews.list(dataset_id=123)
    view = client.dataviews.get(dataset_id=123, dataview_id=456)
    data = client.dataviews.get_data(dataset_id=123, dataview_id=456)

For rich View objects with transformation methods, use client.views instead.

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `active_users(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get list of active users on this dataview.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with list of active users.

### `bulk_delete(self, dataset_id: 'int', dataview_ids: '_list[int] | str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete multiple dataviews.

Args:
    dataset_id: ID of the dataset.
    dataview_ids: List of dataview IDs or comma-separated string.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with bulk deletion result.

### `conditional_format_create(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a conditional formatting rule.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    rule: Conditional format rule specification.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with created rule.

### `conditional_format_delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete all conditional formatting rules.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with deletion result.

### `conditional_format_list(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List conditional formatting rules.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    List of conditional format rule dicts.

### `conditional_format_update(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a conditional formatting rule.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    rule: Updated conditional format rule.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with updated rule.

### `create(self, dataset_id: 'int', name: 'str | None' = 'View', clone_config_from: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create or duplicate a dataview.

Args:
    dataset_id: ID of the dataset.
    name: Name of the dataview (default "View").
    clone_config_from: ID of dataview to clone config from (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with created dataview information.

### `delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a dataview.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with deletion result.

### `draft_mode(self, dataset_id: 'int', dataview_id: 'int', command: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Manage draft mode for a dataview pipeline.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    command: Draft mode command: "enter", "commit", or "discard".
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with draft mode state.

### `get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get dataview information.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with complete dataview information.

### `get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get dataview data (GET method).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with dataview data.

### `list(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`

Get list of dataviews in a dataset.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    limit: Maximum number of results (default 100).
    sort: Sort order (default "(created_at:desc)").

Returns:
    Dict containing dataviews list.

### `mark_active(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Mark current user as active on this dataview.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with updated active users.

### `query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int' = 0, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get dataview data with filtering options (POST method).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    sequence: Pipeline step to fetch data at (default 0).
    offset: One-indexed starting row (default 1).
    limit: Number of rows to fetch (default 400).
    columns: List of column names to fetch (optional).
    condition: Filter condition dict (optional).
    sort: Sort specification string (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with filtered dataview data.

### `update(self, dataset_id: 'int', dataview_id: 'int', patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update dataview properties.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview to update.
    patch_data: List of patch operations.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with update result.


---


# Pipeline API Reference

The `PipelineAPI` manages the transformation pipeline on dataviews. Each dataview has an ordered list of pipeline tasks (filter, join, pivot, etc.) that transform the data.

**Access**: `client.pipeline`

> **Tip**
>
> Most users should use the high-level `View` transformation methods (e.g. `view.filter_rows()`, `view.math()`) instead of calling `PipelineAPI` directly. The View methods call `PipelineAPI` internally and handle job waiting and metadata refresh automatically.
>

---

## `PipelineAPI`

Low-level HTTP client for pipeline task endpoints.

Used internally by View objects. Access via client.pipeline.

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Add a new transformation task to the pipeline.

Args:
    dataview_id: ID of the dataview.
    task_spec: Task specification dict (varies by task type).
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with created task info or job info.

### `delete_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a pipeline task.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task to delete.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Delete confirmation dict.

### `draft_mode(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Manage draft mode for a dataview pipeline.

Args:
    dataview_id: ID of the dataview.
    command: Draft mode command ("enter", "commit", "discard").
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Draft mode state dict.

### `get_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get pipeline state for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Pipeline state dict.

### `get_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a specific pipeline task.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Task details dict.

### `list_tasks(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

List all pipeline tasks for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with tasks list.

### `preview_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Preview task results without adding to pipeline.

Args:
    dataview_id: ID of the dataview.
    task_spec: Task specification to preview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Preview result dict with sample data.

### `update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Update an existing pipeline task.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task to update.
    task_spec: Updated task specification.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Updated task dict.


---


# Jobs API Reference

The `JobsAPI` tracks asynchronous job status. Many Mammoth operations (data fetches, pipeline tasks, exports) create background jobs. The SDK polls these jobs automatically in most cases, but the Jobs API is available for manual control.

**Access**: `client.jobs`

---

## `JobsAPI`

Client for interacting with Mammoth Jobs API.

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `get_job(self, job_id: 'int', timeout: 'int' = 300) -> 'dict[str, Any]'`

Get job status by ID.

Args:
    job_id: ID of the job to track
    timeout: Timeout for the request (unused, kept for compatibility)

Returns:
    Dict containing job information including status, response, timestamps

Raises:
    MammothAPIError: If the API request fails

### `get_jobs(self, job_ids: 'list[int] | str') -> 'dict[str, Any]'`

Track multiple job IDs.

Args:
    job_ids: List of job IDs or comma-separated string of job IDs

Returns:
    Dict containing jobs list with status information

Raises:
    MammothAPIError: If the API request fails

### `wait_for_job(self, job_id: 'int', timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`

Wait for a job to complete and return the result.

Args:
    job_id: ID of the job to wait for
    timeout: Maximum time to wait in seconds (default: client.job_timeout)
    poll_interval: Time between polling attempts in seconds (default: 2)

Returns:
    Dict containing the completed job information

Raises:
    MammothJobFailedError: If the job fails.
    MammothJobTimeoutError: If the job does not complete within timeout.
    MammothAPIError: If the API request fails.

### `wait_for_jobs(self, job_ids: 'list[int] | str', timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`

Wait for multiple jobs to complete.

Args:
    job_ids: List of job IDs or comma-separated string
    timeout: Maximum time to wait in seconds (default: client.job_timeout)
    poll_interval: Time between polling attempts in seconds (default: 2)

Returns:
    Dict containing all completed jobs information

Raises:
    MammothJobFailedError: If any job fails.
    MammothJobTimeoutError: If jobs do not complete within timeout.
    MammothAPIError: If the API request fails.


---


# Dashboards API Reference

The `DashboardsAPI` manages interactive dashboards in Mammoth. Dashboards visualize data from dataviews and can be shared with team members or embedded externally.

**Access**: `client.dashboards`

---

## `DashboardsAPI`

Client for managing Mammoth dashboards.

Access via client.dashboards:
    dashboards = client.dashboards.list()
    dashboard = client.dashboards.create(config={...})
    client.dashboards.share(dashboard_id, config={...})
    client.dashboards.delete(dashboard_id)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `action(self, dashboard_id: 'int', action_config: 'dict[str, Any]') -> 'dict[str, Any]'`

Perform an action on a dashboard.

Args:
    dashboard_id: ID of the dashboard.
    action_config: Action configuration.

Returns:
    Dict with action result.

### `create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new dashboard.

Args:
    config: Dashboard configuration (name, sources, layout, etc.).

Returns:
    Dict with created dashboard info (may include job ID for async creation).

### `delete(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Delete a dashboard.

Args:
    dashboard_id: ID of the dashboard.

Returns:
    Dict with deletion result.

### `get(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Get dashboard details.

Args:
    dashboard_id: ID of the dashboard.

Returns:
    Dict with dashboard details.

### `get_analytics(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Get dashboard analytics (views, users).

Args:
    dashboard_id: ID of the dashboard.

Returns:
    Dict with analytics data.

### `get_by_url(self, url: 'str') -> 'dict[str, Any]'`

Get dashboard by URL slug.

Args:
    url: Dashboard URL slug.

Returns:
    Dict with dashboard details.

### `get_draft_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`

Get draft data using SQL query.

Args:
    dashboard_id: ID of the dashboard.
    sql: SQL query to execute against draft data.

Returns:
    Dict with query results.

### `get_publish_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`

Get published data using SQL query.

Args:
    dashboard_id: ID of the dashboard.
    sql: SQL query to execute against published data.

Returns:
    Dict with query results.

### `get_sources(self) -> '_list[dict[str, Any]]'`

Get available dashboard data sources.

Returns:
    List of source dicts.

### `list(self) -> '_list[dict[str, Any]]'`

List all dashboards.

Returns:
    List of dashboard dicts.

### `share(self, dashboard_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Share a dashboard.

Args:
    dashboard_id: ID of the dashboard.
    config: Sharing configuration (users, permissions, etc.).

Returns:
    Dict with sharing result.

### `update(self, dashboard_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update a dashboard.

Args:
    dashboard_id: ID of the dashboard.
    config: Updated dashboard configuration.

Returns:
    Dict with updated dashboard info.


---


# Webhooks API Reference

The `WebhooksAPI` manages webhook datasets -- HTTP endpoints that receive data into the Mammoth platform. Webhooks allow external systems to push data directly into Mammoth.

**Access**: `client.webhooks`

---

## `WebhooksAPI`

Client for managing webhooks for event notifications.

Access via client.webhooks:
    webhooks = client.webhooks.list()
    webhook = client.webhooks.create(config={"name": "...", "url": "...", "events": [...]})
    client.webhooks.delete(webhook_id)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new webhook.

Args:
    config: Webhook configuration (name, url, events, secret, etc.).

Returns:
    Dict with created webhook info.

### `delete(self, webhook_id: 'int') -> 'dict[str, Any]'`

Delete a webhook.

Args:
    webhook_id: ID of the webhook.

Returns:
    Dict with deletion result.

### `get(self, webhook_id: 'int') -> 'dict[str, Any]'`

Get webhook details.

Args:
    webhook_id: ID of the webhook.

Returns:
    Dict with webhook details.

### `list(self) -> '_list[dict[str, Any]]'`

List all webhooks.

Returns:
    List of webhook dicts.

### `update(self, webhook_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update a webhook.

Args:
    webhook_id: ID of the webhook.
    config: Updated webhook configuration.

Returns:
    Dict with updated webhook info.


---


# Automations & Schedules API Reference

The SDK provides two sub-clients for automation workflows:

- **`client.automations`** (`AutomationsAPI`) -- manages automations and their associated schedules
- **`client.schedules`** (`SchedulesAPI`) -- manages scheduled operations

---

## AutomationsAPI

### `AutomationsAPI`

Client for managing automations and schedules.

Access via client.automations:
    automations = client.automations.list()
    automation = client.automations.create(config={...})
    schedules = client.automations.list_schedules()
    client.automations.create_schedule(config={...})

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new automation.

Args:
    config: Automation configuration (name, triggers, actions, etc.).

Returns:
    Dict with created automation info.

#### `create_schedule(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new schedule.

Args:
    config: Schedule configuration (cron, timezone, actions, etc.).

Returns:
    Dict with created schedule info.

#### `delete(self, automation_id: 'int') -> 'dict[str, Any]'`

Delete an automation.

Args:
    automation_id: ID of the automation.

Returns:
    Dict with deletion result.

#### `delete_schedule(self, schedule_id: 'int') -> 'dict[str, Any]'`

Delete a schedule.

Args:
    schedule_id: ID of the schedule.

Returns:
    Dict with deletion result.

#### `get(self, automation_id: 'int') -> 'dict[str, Any]'`

Get automation details.

Args:
    automation_id: ID of the automation.

Returns:
    Dict with automation details.

#### `list(self) -> '_list[dict[str, Any]]'`

List all automations.

Returns:
    List of automation dicts.

#### `list_schedules(self) -> '_list[dict[str, Any]]'`

List all schedules.

Returns:
    List of schedule dicts.

#### `update(self, automation_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update an automation.

Args:
    automation_id: ID of the automation.
    config: Updated automation configuration.

Returns:
    Dict with updated automation info.

#### `update_schedule(self, schedule_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update a schedule.

Args:
    schedule_id: ID of the schedule.
    config: Updated schedule configuration.

Returns:
    Dict with updated schedule info.

---

## SchedulesAPI

### `SchedulesAPI`

Client for managing schedules under projects.

Access via client.schedules::

    schedules = client.schedules.list()
    schedule = client.schedules.create(config={...})
    client.schedules.delete(schedule_id)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new schedule.

Args:
    config: Schedule configuration.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with created schedule info.

#### `delete(self, schedule_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a schedule.

Args:
    schedule_id: ID of the schedule.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

#### `get(self, schedule_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get schedule details.

Args:
    schedule_id: ID of the schedule.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with schedule details.

#### `list(self, project_id: 'int | None' = None, limit: 'int' = 50, offset: 'int' = 0) -> 'dict[str, Any]'`

List schedules in a project.

Args:
    project_id: Project ID (uses client default if not provided).
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).

Returns:
    Dict with schedules list and pagination info.

#### `update(self, schedule_id: 'int', config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a schedule.

Args:
    schedule_id: ID of the schedule.
    config: Updated schedule configuration.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with updated schedule info.


---


# Workspace & Users API Reference

The SDK provides two sub-clients for workspace and user management:

- **`client.workspaces`** (`WorkspaceAPI`) -- workspace CRUD and user management
- **`client.user_profile`** (`UserProfileAPI`) -- current user profile and preferences

---

## WorkspaceAPI

### `WorkspaceAPI`

Client for interacting with Mammoth Workspace API.

Access via client.workspaces:
    workspaces = client.workspaces.list()
    workspace = client.workspaces.get()
    users = client.workspaces.list_users()

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `delete(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with deletion result.

#### `get(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get details of a specific workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with workspace details.

#### `get_user(self, user_id: 'str', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get details of a specific user.

Args:
    user_id: ID of the user.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with user details.

#### `list(self, limit: 'int' = 100) -> 'dict[str, Any]'`

List all accessible workspaces.

Args:
    limit: Maximum number of results (default 100).

Returns:
    Dict containing workspaces list with id and name.

#### `list_users(self, workspace_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List all users in a workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    List of user dicts.

#### `reactivate(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Reactivate a deactivated workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with reactivation result.

#### `update(self, config: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update workspace settings.

Args:
    config: Patch operations for the workspace.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated workspace info.

#### `update_user(self, user_id: 'str', config: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a user's settings in the workspace.

Args:
    user_id: ID of the user.
    config: Patch operations for the user.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated user info.

---

## UserProfileAPI

### `UserProfileAPI`

Client for managing user profile and settings.

Access via client.user_profile::

    profile = client.user_profile.get()
    client.user_profile.update(name="New Name")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `change_password(self, current_password: 'str', new_password: 'str') -> 'dict[str, Any]'`

Change user password.

Args:
    current_password: Current password.
    new_password: New password.

Returns:
    Dict with result.

#### `get(self) -> 'dict[str, Any]'`

Get current user profile.

Returns:
    Dict with user profile information.

#### `get_preferences(self) -> 'dict[str, Any]'`

Get user preferences.

Returns:
    Dict with user preferences.

#### `update(self, **fields: 'Any') -> 'dict[str, Any]'`

Update current user profile.

Args:
    **fields: Profile fields to update (name, email, etc.).

Returns:
    Dict with updated profile.

#### `update_preferences(self, **prefs: 'Any') -> 'dict[str, Any]'`

Update user preferences.

Args:
    **prefs: Preference fields to update.

Returns:
    Dict with updated preferences.


---


# Other APIs Reference

This page covers smaller utility sub-clients that provide access to folders, batches, browse, client apps, external keys, activity logs, addons, reports, and AI features.

---

## FoldersAPI

**Access**: `client.folders`

Client for interacting with Mammoth Folders API.

Access via client.folders:
    folders = client.folders.list()
    folder = client.folders.create(name="Reports")
    client.folders.delete([folder_id])
    client.folders.move(resource_ids=[...], target_folder_resource_id="...")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, name: 'str', parent_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'FolderDetails'`

Create a new folder.

Args:
    name: Name for the new folder.
    parent_resource_id: Parent folder resource ID (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    FolderDetails with created folder info.

#### `delete(self, folder_ids: '_list[int]', workspace_id: 'int | None' = None, project_id: 'int | None' = None, check_dependency: 'bool' = True, remove_contents: 'bool' = True) -> 'None'`

Delete multiple folders.

Args:
    folder_ids: List of folder IDs to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    check_dependency: Check for dependency before deleting.
    remove_contents: Remove folder contents before deleting.

#### `list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, fields: 'str | None' = None, folder_ids: '_list[int] | None' = None, names: '_list[str] | None' = None, statuses: '_list[str] | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, created_by: '_list[str] | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None) -> 'FoldersList'`

List folders in a project with optional filtering and pagination.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    fields: Fields to return (e.g., "__standard", "__full", "__min").
    folder_ids: List of specific folder IDs to retrieve.
    names: List of folder names to filter by.
    statuses: List of statuses to filter by.
    created_at: Date range filter for creation date.
    updated_at: Date range filter for update date.
    created_by: List of user names who created folders.
    limit: Maximum number of results (0-100, default 50).
    offset: Number of results to skip (default 0).
    sort: Sort specification (e.g., "(id:asc),(name:desc)").

Returns:
    FoldersList with folders and pagination info.

#### `move(self, resource_ids: '_list[str]', target_folder_resource_id: 'str | None' = None, source_folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'ObjectJobSchema'`

Move resources between folders.

Args:
    resource_ids: List of resource IDs to move.
    target_folder_resource_id: Target folder resource ID (None for root).
    source_folder_resource_id: Source folder resource ID (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    ObjectJobSchema with job information for the move.

---

## BatchesAPI

**Access**: `client.batches`

Client for managing dataset batch operations.

Access via client.batches::

    batches = client.batches.list(dataset_id=123)
    batch = client.batches.get(dataset_id=123, batch_id=1)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, dataset_id: 'int', config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new batch for a dataset.

Args:
    dataset_id: ID of the dataset.
    config: Batch configuration.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with created batch info.

#### `delete(self, dataset_id: 'int', batch_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a batch.

Args:
    dataset_id: ID of the dataset.
    batch_id: ID of the batch.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

#### `get(self, dataset_id: 'int', batch_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get batch details.

Args:
    dataset_id: ID of the dataset.
    batch_id: ID of the batch.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with batch details.

#### `get_status(self, dataset_id: 'int', batch_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get batch processing status.

Args:
    dataset_id: ID of the dataset.
    batch_id: ID of the batch.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with batch status info.

#### `list(self, dataset_id: 'int', project_id: 'int | None' = None, limit: 'int' = 50, offset: 'int' = 0) -> 'dict[str, Any]'`

List batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    project_id: Project ID (uses client default if not provided).
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).

Returns:
    Dict with batches list and pagination info.

#### `update(self, dataset_id: 'int', batch_id: 'int', config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a batch.

Args:
    dataset_id: ID of the dataset.
    batch_id: ID of the batch.
    config: Updated batch configuration.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with updated batch info.

---

## BrowseAPI

**Access**: `client.browse`

Client for browsing and discovering resources.

Access via client.browse::

    resources = client.browse.workspaces()
    resources = client.browse.projects()
    resources = client.browse.datasets(project_id=10)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `datasets(self, project_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse datasets in a project.

Args:
    project_id: Project ID (uses client default if not provided).
    workspace_id: Workspace ID (uses client default if not provided).

Returns:
    Dict with dataset resources.

#### `dataviews(self, dataset_id: 'int', project_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse dataviews in a dataset.

Args:
    dataset_id: ID of the dataset.
    project_id: Project ID (uses client default if not provided).
    workspace_id: Workspace ID (uses client default if not provided).

Returns:
    Dict with dataview resources.

#### `projects(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse projects in a workspace.

Args:
    workspace_id: Workspace ID (uses client default if not provided).

Returns:
    Dict with project resources.

#### `workspaces(self) -> 'dict[str, Any]'`

Browse available workspaces.

Returns:
    Dict with workspace resources.

---

## ClientAppsAPI

**Access**: `client.client_apps`

Client for interacting with Mammoth Client Apps API.

Access via client.client_apps:
    apps = client.client_apps.list()
    app = client.client_apps.create(app_name="My App")
    client.client_apps.delete(client_key="...")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, app_name: 'str', description: 'str | None' = None, workspace_id: 'int | None' = None) -> 'ClientAppPostResponse'`

Create a new client app to generate API tokens.

Args:
    app_name: Name for the client app.
    description: Optional description.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    ClientAppPostResponse with created app details and tokens.

#### `delete(self, client_key: 'str', workspace_id: 'int | None' = None) -> 'None'`

Delete a client app.

Args:
    client_key: Client key/ID of the app to delete.
    workspace_id: ID of the workspace (uses client default if not provided).

#### `get(self, client_key: 'str', workspace_id: 'int | None' = None, fields: 'str | None' = None) -> 'ClientAppSchema'`

Get details of a specific client app.

Args:
    client_key: Client key/ID of the app.
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Fields to return.

Returns:
    ClientAppSchema with client app details.

#### `list(self, workspace_id: 'int | None' = None, limit: 'int' = 10, offset: 'int' = 0, fields: 'str | None' = None, sort: 'str | None' = None) -> 'ClientAppsListResponse'`

List client apps for a workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    limit: Maximum number of results (0-100, default 10).
    offset: Number of results to skip (default 0).
    fields: Fields to return (e.g., "id,app_name").
    sort: Sort specification.

Returns:
    ClientAppsListResponse with list of client apps.

#### `update(self, client_key: 'str', patch_request: 'PatchRequest', workspace_id: 'int | None' = None) -> 'ClientAppSchema'`

Update client app details.

Args:
    client_key: Client key/ID of the app.
    patch_request: PatchRequest containing patch operations.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    ClientAppSchema with updated details.

---

## ExternalKeysAPI

**Access**: `client.external_keys`

Client for managing external API keys.

Access via client.external_keys::

    keys = client.external_keys.list()
    key = client.external_keys.create(name="My Key")
    client.external_keys.delete(key_id)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, config: 'dict[str, Any]') -> 'dict[str, Any]'`

Create a new external API key.

Args:
    config: Key configuration (name, permissions, etc.).

Returns:
    Dict with created key info.

#### `delete(self, key_id: 'int') -> 'dict[str, Any]'`

Delete an external API key.

Args:
    key_id: ID of the key to delete.

Returns:
    Dict with deletion result.

#### `get(self, key_id: 'int') -> 'dict[str, Any]'`

Get external key details.

Args:
    key_id: ID of the API key.

Returns:
    Dict with key details.

#### `list(self) -> 'dict[str, Any]'`

List all external API keys.

Returns:
    Dict with API keys list.

---

## ActivityLogsAPI

**Access**: `client.activity_logs`

Client for querying and exporting activity logs.

Access via client.activity_logs::

    logs = client.activity_logs.list()
    export = client.activity_logs.export(format="csv")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `export(self, format: 'str' = 'csv', **filters: 'Any') -> 'dict[str, Any]'`

Export activity logs.

Args:
    format: Export format (default "csv").
    **filters: Filter parameters for the export.

Returns:
    Dict with export result (may include download URL or job ID).

#### `list(self, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None, **filters: 'Any') -> 'dict[str, Any]'`

List activity logs.

Args:
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).
    sort: Sort specification.
    **filters: Additional filter parameters (user, action, resource, etc.).

Returns:
    Dict with activity logs and pagination info.

---

## AddonsAPI

**Access**: `client.addons`

Client for managing workspace addons (connectors, storage, users).

Access via client.addons::

    addons = client.addons.list()
    client.addons.activate(addon_id)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `activate(self, addon_id: 'int') -> 'dict[str, Any]'`

Activate an addon.

Args:
    addon_id: ID of the addon to activate.

Returns:
    Dict with activation result.

#### `deactivate(self, addon_id: 'int') -> 'dict[str, Any]'`

Deactivate an addon.

Args:
    addon_id: ID of the addon to deactivate.

Returns:
    Dict with deactivation result.

#### `get(self, addon_id: 'int') -> 'dict[str, Any]'`

Get addon details.

Args:
    addon_id: ID of the addon.

Returns:
    Dict with addon details.

#### `get_usage(self, addon_id: 'int') -> 'dict[str, Any]'`

Get addon usage statistics.

Args:
    addon_id: ID of the addon.

Returns:
    Dict with usage statistics.

#### `list(self) -> 'dict[str, Any]'`

List available addons for the workspace.

Returns:
    Dict with addons list.

#### `update_config(self, addon_id: 'int', config: 'dict[str, Any]') -> 'dict[str, Any]'`

Update addon configuration.

Args:
    addon_id: ID of the addon.
    config: Updated configuration.

Returns:
    Dict with updated addon info.

---

## ReportsAPI

**Access**: `client.reports`

Client for listing workspace reports.

Access via client.reports::

    reports = client.reports.list()

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `list(self, limit: 'int' = 50, offset: 'int' = 0) -> 'dict[str, Any]'`

List all reports.

Args:
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).

Returns:
    Dict with reports list and pagination info.

---

## AIAPI

**Access**: `client.ai`

Client for AI-powered features: profiling, generation, suggestions, SQL generation.

Access via client.ai:
    client.ai.generate_profile(dataview_id=1039)
    client.ai.generate_sql(intent="total sales by region", dataview_ids=[1039])
    suggestions = client.ai.get_suggestions(dataview_id=1039)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `generate_data(self, dataview_id: 'int', config: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate synthetic data for a dataview.

Args:
    dataview_id: ID of the dataview.
    config: Generation configuration (rows, columns, patterns).
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with generation result or job info.

#### `generate_profile(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate an AI profile/summary of the dataview data.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with profile information.

#### `generate_sql(self, intent: 'str', dataview_ids: 'list[int] | None' = None) -> 'dict[str, Any]'`

Generate SQL from natural language intent.

Args:
    intent: Natural language description of the query.
    dataview_ids: List of dataview IDs to use as context (optional).

Returns:
    Dict with generated SQL and metadata.

#### `get_data_gen_info(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get data generation information for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with data generation info.

#### `get_suggestions(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get AI-powered transformation suggestions for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with suggested transformations.

#### `query_gen(self, connector_key: 'str', connection_key: 'str', prompt: 'str') -> 'dict[str, Any]'`

Generate a query for a connector using AI.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    prompt: Natural language prompt describing the query.

Returns:
    Dict with generated query.


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
