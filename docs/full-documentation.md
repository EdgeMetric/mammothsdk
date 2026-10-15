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
  - [Getting an API token](#getting-an-api-token)
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
  - [Rename and sort (view settings)](#rename-and-sort-view-settings)
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
    - [`NotCondition`](#notcondition)
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
    - [`JsonOpType`](#jsonoptype)
    - [`ExportFileType`](#exportfiletype)
    - [`ProviderType`](#providertype)
    - [`TaskType`](#tasktype)
    - [`DraftCommand`](#draftcommand)
  - [Data Classes](#data-classes)
    - [`SetValue`](#setvalue)
    - [`CopySpec`](#copyspec)
    - [`ConversionSpec`](#conversionspec)
    - [`SplitColumnSpec`](#splitcolumnspec)
    - [`BulkReplaceMapping`](#bulkreplacemapping)
    - [`DateDelta`](#datedelta)
    - [`AggregationSpec`](#aggregationspec)
    - [`JoinKeySpec`](#joinkeyspec)
    - [`JoinSelectSpec`](#joinselectspec)
    - [`JsonExtractionSpec`](#jsonextractionspec)
    - [`CrosstabSpec`](#crosstabspec)
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
    - [`create_datasets_from_multi_sheet(self, file_id: 'int', tables: '_list[dict[str, Any]]', delete_file_after_extract: 'bool' = True) -> 'dict[str, Any]'`](#create_datasets_from_multi_sheetself-file_id-int-tables-_listdictstr-any-delete_file_after_extract-bool-true---dictstr-any)
    - [`delete(self, file_id: 'int') -> 'None'`](#deleteself-file_id-int---none)
    - [`extract_sheets(self, file_id: 'int', sheets: '_list[str]', delete_file_after_extract: 'bool' = True, combine_after_extract: 'bool' = False) -> 'ObjectJobSchema'`](#extract_sheetsself-file_id-int-sheets-_liststr-delete_file_after_extract-bool-true-combine_after_extract-bool-false---objectjobschema)
    - [`get(self, file_id: 'int', fields: 'str | None' = None) -> 'FileSchema'`](#getself-file_id-int-fields-str-none-none---fileschema)
    - [`list(self, fields: 'str | None' = None, file_ids: '_list[int] | None' = None, names: '_list[str] | None' = None, statuses: '_list[str] | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None) -> 'FilesList'`](#listself-fields-str-none-none-file_ids-_listint-none-none-names-_liststr-none-none-statuses-_liststr-none-none-created_at-str-none-none-updated_at-str-none-none-limit-int-50-offset-int-0-sort-str-none-none---fileslist)
    - [`preview_multi_sheet(self, file_id: 'int', sheet_name: 'str', block_id: 'str | None' = None, user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`](#preview_multi_sheetself-file_id-int-sheet_name-str-block_id-str-none-none-user_instruction-str-none-none-structure_map-dictstr-any-none-none---dictstr-any)
    - [`set_password(self, file_id: 'int', password: 'str') -> 'ObjectJobSchema'`](#set_passwordself-file_id-int-password-str---objectjobschema)
    - [`update(self, file_id: 'int', patch_request: 'FilePatchRequest') -> 'ObjectJobSchema'`](#updateself-file_id-int-patch_request-filepatchrequest---objectjobschema)
    - [`upload(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | int | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#uploadself-files-_liststr-path-binaryio-str-path-binaryio-none-none-folder_resource_id-str-int-none-none-append_to_ds_id-int-none-none-override_target_schema-bool-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
    - [`upload_folder(self, folder_path: 'str | Path', folder_resource_id: 'str | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#upload_folderself-folder_path-str-path-folder_resource_id-str-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
    - [`upload_result(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | int | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> 'dict[str, Any]'`](#upload_resultself-files-_liststr-path-binaryio-str-path-binaryio-none-none-folder_resource_id-str-int-none-none-append_to_ds_id-int-none-none-override_target_schema-bool-none-none-wait_for_completion-bool-true-timeout-int-300---dictstr-any)
- [Connectors](#connectors)
  - [`ConnectorsAPI`](#connectorsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`active_connectors(self) -> '_list[dict[str, Any]]'`](#active_connectorsself---_listdictstr-any)
    - [`create_connection(self, connector_key: 'str', config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#create_connectionself-connector_key-str-config-dictstr-any-project_id-int-none-none---dictstr-any)
    - [`create_ds_config(self, connector_key: 'str', connection_key: 'str', *, query: 'str | None' = None, file_source: 'str | None' = None, table: 'str | None' = None, profile: 'str | None' = None, validate: 'bool' = True, data_sample: 'bool' = False, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#create_ds_configself-connector_key-str-connection_key-str-query-str-none-none-file_source-str-none-none-table-str-none-none-profile-str-none-none-validate-bool-true-data_sample-bool-false-project_id-int-none-none---dictstr-any)
    - [`delete_connection(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_connectionself-connector_key-str-connection_key-str-project_id-int-none-none---dictstr-any)
    - [`delete_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_ds_configself-connector_key-str-connection_key-str-ds_config_key-str-project_id-int-none-none---dictstr-any)
    - [`ds_config_delete_all(self, connector_key: 'str', connection_key: 'str', config_ids: '_list[str] | str', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#ds_config_delete_allself-connector_key-str-connection_key-str-config_ids-_liststr-str-project_id-int-none-none---dictstr-any)
    - [`get(self, connector_key: 'str') -> 'dict[str, Any]'`](#getself-connector_key-str---dictstr-any)
    - [`get_connection(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_connectionself-connector_key-str-connection_key-str-project_id-int-none-none---dictstr-any)
    - [`get_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_ds_configself-connector_key-str-connection_key-str-ds_config_key-str-project_id-int-none-none---dictstr-any)
    - [`list(self) -> '_list[dict[str, Any]]'`](#listself---_listdictstr-any)
    - [`list_connections(self, connector_key: 'str', project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#list_connectionsself-connector_key-str-project_id-int-none-none---_listdictstr-any)
    - [`list_ds_configs(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#list_ds_configsself-connector_key-str-connection_key-str-project_id-int-none-none---_listdictstr-any)
    - [`query_connection(self, connector_key: 'str', connection_key: 'str', query: 'str', *, table: 'str | None' = None, profile: 'str | None' = None, project_id: 'int | None' = None, timeout: 'float' = 60.0) -> 'dict[str, Any]'`](#query_connectionself-connector_key-str-connection_key-str-query-str-table-str-none-none-profile-str-none-none-project_id-int-none-none-timeout-float-600---dictstr-any)
    - [`update_connection(self, connector_key: 'str', connection_key: 'str', credentials: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#update_connectionself-connector_key-str-connection_key-str-credentials-dictstr-any-project_id-int-none-none---dictstr-any)
    - [`update_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', patch: '_list[DsConfigPatchOp]', project_id: 'int | None' = None) -> 'dict[str, Any]'`](#update_ds_configself-connector_key-str-connection_key-str-ds_config_key-str-patch-_listdsconfigpatchop-project_id-int-none-none---dictstr-any)
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
    - [`add_agent_memory(self, project_id: 'int', text: 'str', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_agent_memoryself-project_id-int-text-str-workspace_id-int-none-none---dictstr-any)
    - [`add_users(self, project_id: 'int', user_ids: '_list[int]', role: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_usersself-project_id-int-user_ids-_listint-role-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`browse(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, name: 'str | None' = None, browse_type: 'str | None' = None, sort: 'str | None' = None, offset: 'int | None' = None, limit: 'int | None' = None) -> 'dict[str, Any]'`](#browseself-project_id-int-workspace_id-int-none-none-fields-str-none-none-name-str-none-none-browse_type-str-none-none-sort-str-none-none-offset-int-none-none-limit-int-none-none---dictstr-any)
    - [`bulk_delete(self, project_ids: '_list[int]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_deleteself-project_ids-_listint-workspace_id-int-none-none---dictstr-any)
    - [`bulk_delete_and_verify(self, project_ids: '_list[int]', workspace_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0) -> 'dict[str, Any]'`](#bulk_delete_and_verifyself-project_ids-_listint-workspace_id-int-none-none-timeout-int-none-none-poll_interval-float-20---dictstr-any)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none---dictstr-any)
    - [`checkpoint_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#checkpoint_listself-project_id-int-workspace_id-int-none-none-fields-str-none-none-sort-str-none-none-dataview_id-int-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`copy(self, project_id: 'int', name: 'str', dataset_ids: '_list[int] | None' = None, include_dashboards: 'bool' = False, exclude_data: 'bool' = False, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#copyself-project_id-int-name-str-dataset_ids-_listint-none-none-include_dashboards-bool-false-exclude_data-bool-false-workspace_id-int-none-none---dictstr-any)
    - [`create(self, name: 'str', color: 'str | None' = None, project_access: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-name-str-color-str-none-none-project_access-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`data_check_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#data_check_listself-project_id-int-workspace_id-int-none-none-fields-str-none-none-sort-str-none-none-dataview_id-int-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`delete(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`delete_and_verify(self, project_id: 'int', workspace_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0) -> 'dict[str, Any]'`](#delete_and_verifyself-project_id-int-workspace_id-int-none-none-timeout-int-none-none-poll_interval-float-20---dictstr-any)
    - [`get(self, project: 'int | str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-project-int-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0, fields: 'str' = 'id,name', include_non_members: 'bool' = False) -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-limit-int-100-offset-int-0-fields-str-idname-include_non_members-bool-false---dictstr-any)
    - [`list_agent_memory(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#list_agent_memoryself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`list_all(self, workspace_id: 'int | None' = None, fields: 'str' = 'id,name', include_non_members: 'bool' = False) -> '_list[dict[str, Any]]'`](#list_allself-workspace_id-int-none-none-fields-str-idname-include_non_members-bool-false---_listdictstr-any)
    - [`needs_attention(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#needs_attentionself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`pending_changes(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#pending_changesself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`publish_credentials(self, project_id: 'int', odbc_type: "Literal['postgres', 'bigquery']", workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#publish_credentialsself-project_id-int-odbc_type-literalpostgres-bigquery-workspace_id-int-none-none---dictstr-any)
    - [`remove_agent_memory(self, project_id: 'int', index: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#remove_agent_memoryself-project_id-int-index-int-workspace_id-int-none-none---dictstr-any)
    - [`remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#remove_usersself-project_id-int-user_ids-_liststr-workspace_id-int-none-none---dictstr-any)
    - [`resource_dependencies(self, project_id: 'int', resource_ids: '_list[str]', is_recursive: 'bool | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#resource_dependenciesself-project_id-int-resource_ids-_liststr-is_recursive-bool-none-none-workspace_id-int-none-none---dictstr-any)
    - [`resource_dependencies_update(self, project_id: 'int', patches: '_list[DataSyncPatchItem]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#resource_dependencies_updateself-project_id-int-patches-_listdatasyncpatchitem-workspace_id-int-none-none---dictstr-any)
    - [`resource_status(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#resource_statusself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`sample_flow(self, project_id: 'int', label_resource_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#sample_flowself-project_id-int-label_resource_id-int-none-none-workspace_id-int-none-none---dictstr-any)
    - [`update(self, project_id: 'int', name: 'str | None' = None, color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-project_id-int-name-str-none-none-color-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`user_update(self, project_id: 'int', role: "Literal['project_admin', 'project_analyst']", user_id: 'int | None' = None, invite_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#user_updateself-project_id-int-role-literalproject_admin-project_analyst-user_id-int-none-none-invite_id-int-none-none-workspace_id-int-none-none---dictstr-any)
- [Datasets](#datasets)
  - [`DatasetsAPI`](#datasetsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`add_definition(self, dataset_id: 'int', term: 'str', definition: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_definitionself-dataset_id-int-term-str-definition-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`bulk_delete(self, dataset_ids: '_list[int] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`](#bulk_deleteself-dataset_ids-_listint-none-none-workspace_id-int-none-none-project_id-int-none-none---none)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`column_stats(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#column_statsself-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`confirm_interpretation(self, dataset_id: 'int', instruction: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#confirm_interpretationself-dataset_id-int-instruction-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create(self, dataset_spec: 'dict[str, Any]', ds_creation_type: 'str', folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-dataset_spec-dictstr-any-ds_creation_type-str-folder_resource_id-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create_from_pdf(self, file_object_id: 'int', file_name: 'str', file_id: 'str | None' = None, table_list: '_list[int] | None' = None, delete_file_after_extract: 'bool' = False, is_preview_needed: 'bool | None' = None, user_instruction: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#create_from_pdfself-file_object_id-int-file_name-str-file_id-str-none-none-table_list-_listint-none-none-delete_file_after_extract-bool-false-is_preview_needed-bool-none-none-user_instruction-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete_and_verify(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0, dependencies: 'Sequence[str] | None' = None) -> 'dict[str, Any]'`](#delete_and_verifyself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-float-20-dependencies-sequencestr-none-none---dictstr-any)
    - [`file_settings_undo(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#file_settings_undoself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`file_settings_update(self, dataset_id: 'int', delimiter: 'str', has_header: 'bool', initial_skip_count: 'int', quotechar: 'str', date_format: 'str | None' = None, preview_mode: 'bool' = False, skip_auto_process_check: 'bool' = True, date_formats: 'dict[str, str] | None' = None, set_project_level_date_format: 'bool' = False, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#file_settings_updateself-dataset_id-int-delimiter-str-has_header-bool-initial_skip_count-int-quotechar-str-date_format-str-none-none-preview_mode-bool-false-skip_auto_process_check-bool-true-date_formats-dictstr-str-none-none-set_project_level_date_format-bool-false-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-fields-str-none-none---dictstr-any)
    - [`get_batch(self, dataset_id: 'int', batch_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_batchself-dataset_id-int-batch_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_batch_data(self, dataset_id: 'int', batch_id: 'int', columns: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`](#get_batch_dataself-dataset_id-int-batch_id-int-columns-str-none-none-limit-int-50-offset-int-0-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-float-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int' = 300, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-300-poll_interval-float-none-none---dictstr-any)
    - [`get_file_settings(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_file_settingsself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_unstructured_rows(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_unstructured_rowsself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`interpretation_confirm(self, dataset_id: 'int', user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None, destination_dataset_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, mode: 'str | None' = None) -> 'dict[str, Any]'`](#interpretation_confirmself-dataset_id-int-user_instruction-str-none-none-structure_map-dictstr-any-none-none-destination_dataset_id-int-none-none-workspace_id-int-none-none-project_id-int-none-none-mode-str-none-none---dictstr-any)
    - [`interpretation_preview(self, dataset_id: 'int', user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None, destination_dataset_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#interpretation_previewself-dataset_id-int-user_instruction-str-none-none-structure_map-dictstr-any-none-none-destination_dataset_id-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0, sort: 'str' = '(created_at:desc)', fields: 'str' = 'id,name') -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-offset-int-0-sort-str-created_atdesc-fields-str-idname---dictstr-any)
    - [`list_all(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)', max_pages: 'int' = 1000, fields: 'str' = 'id,name') -> 'dict[str, Any]'`](#list_allself-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc-max_pages-int-1000-fields-str-idname---dictstr-any)
    - [`list_batches(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#list_batchesself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---_listdictstr-any)
    - [`list_definitions(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#list_definitionsself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`preview_interpretation(self, dataset_id: 'int', instruction: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#preview_interpretationself-dataset_id-int-instruction-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`remove_definition(self, dataset_id: 'int', definition_id: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#remove_definitionself-dataset_id-int-definition_id-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`rename(self, dataset_id: 'int', name: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None, unique: 'bool' = False) -> 'dict[str, Any]'`](#renameself-dataset_id-int-name-str-workspace_id-int-none-none-project_id-int-none-none-unique-bool-false---dictstr-any)
    - [`resolve_unstructured_rows(self, dataset_id: 'int', op: "Literal['add', 'remove']", batch_id: 'int', rows: 'list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#resolve_unstructured_rowsself-dataset_id-int-op-literaladd-remove-batch_id-int-rows-listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`restore(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#restoreself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`search(self, term: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#searchself-term-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`trash(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#trashself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`update(self, patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-patch_data-_listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
- [Dataviews](#dataviews)
  - [`DataviewsAPI`](#dataviewsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`active_users(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#active_usersself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`aggregate(self, dataset_id: 'int', dataview_id: 'int', aggregations: '_list[dict[str, Any]] | None' = None, group_by: '_list[str | dict[str, Any]] | None' = None, metric: 'dict[str, Any] | None' = None, condition: 'dict[str, Any] | None' = None, sequence: 'int | None' = None, limit: 'int | None' = None, sort: '_list[_list[str]] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#aggregateself-dataset_id-int-dataview_id-int-aggregations-_listdictstr-any-none-none-group_by-_liststr-dictstr-any-none-none-metric-dictstr-any-none-none-condition-dictstr-any-none-none-sequence-int-none-none-limit-int-none-none-sort-_list_liststr-none-none-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-int-2---dictstr-any)
    - [`analysis(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#analysisself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`apply_exportable_config(self, dataset_id: 'int', dataview_id: 'int', *, items: '_list[dict[str, Any]] | None' = None, config: 'dict[str, Any] | None' = None, insert_after_sequence: 'int | None' = None, is_paste_mode: 'bool' = False, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#apply_exportable_configself-dataset_id-int-dataview_id-int-items-_listdictstr-any-none-none-config-dictstr-any-none-none-insert_after_sequence-int-none-none-is_paste_mode-bool-false-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`bulk_delete(self, dataset_id: 'int', dataview_ids: '_list[int] | str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_deleteself-dataset_id-int-dataview_ids-_listint-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`compare(self, pairs: '_list[_list[int]]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#compareself-pairs-_list_listint-workspace_id-int-none-none---dictstr-any)
    - [`conditional_format_create(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_createself-dataset_id-int-dataview_id-int-rule-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`conditional_format_delete(self, dataset_id: 'int', dataview_id: 'int', rule_id: 'str | int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_deleteself-dataset_id-int-dataview_id-int-rule_id-str-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`conditional_format_list(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#conditional_format_listself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---_listdictstr-any)
    - [`conditional_format_update(self, dataset_id: 'int', dataview_id: 'int', rule: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#conditional_format_updateself-dataset_id-int-dataview_id-int-rule-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create(self, dataset_id: 'int', name: 'str | None' = 'View', clone_config_from: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-dataset_id-int-name-str-none-view-clone_config_from-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete_impact(self, dataset_id: 'int', dataview_id: 'int', scope: 'str', task_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_impactself-dataset_id-int-dataview_id-int-scope-str-task_id-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`draft_mode(self, dataset_id: 'int', dataview_id: 'int', command: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#draft_modeself-dataset_id-int-dataview_id-int-command-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`explore(self, dataset_id: 'int', dataview_id: 'int', column: 'str', column_type: 'str | None' = None, level: 'str | None' = None, metric: 'dict[str, Any] | None' = None, condition: 'dict[str, Any] | None' = None, sequence: 'int | None' = None, limit: 'int | None' = None, offset: 'int | None' = None, sort: 'str | None' = None, cumulative: 'bool' = False, percentage_of: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#exploreself-dataset_id-int-dataview_id-int-column-str-column_type-str-none-none-level-str-none-none-metric-dictstr-any-none-none-condition-dictstr-any-none-none-sequence-int-none-none-limit-int-none-none-offset-int-none-none-sort-str-none-none-cumulative-bool-false-percentage_of-str-none-none-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-int-2---dictstr-any)
    - [`explore_panel(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#explore_panelself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, sequence: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none-sequence-int-none-none-fields-str-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'float | None' = None, sequence: 'int | None' = None, raw: 'bool' = False) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-float-none-none-sequence-int-none-none-raw-bool-false---dictstr-any)
    - [`get_exportable_config(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_exportable_configself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`list(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)', offset: 'int' = 0) -> 'dict[str, Any]'`](#listself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc-offset-int-0---dictstr-any)
    - [`mark_active(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#mark_activeself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`optimize(self, dataset_id: 'int', dataview_id: 'int', apply_rules: '_list[str] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#optimizeself-dataset_id-int-dataview_id-int-apply_rules-_liststr-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`parameter_context(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#parameter_contextself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`preview(self, dataset_id: 'int', dataview_id: 'int', rows: 'int | None' = None, cols: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#previewself-dataset_id-int-dataview_id-int-rows-int-none-none-cols-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int | None' = None, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, raw: 'bool' = False) -> 'dict[str, Any]'`](#query_dataself-dataset_id-int-dataview_id-int-sequence-int-none-none-offset-int-1-limit-int-400-columns-_liststr-none-none-condition-dictstr-any-none-none-sort-str-none-none-workspace_id-int-none-none-project_id-int-none-none-raw-bool-false---dictstr-any)
    - [`restore(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#restoreself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`set_explore_panel(self, dataset_id: 'int', dataview_id: 'int', panel: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#set_explore_panelself-dataset_id-int-dataview_id-int-panel-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`summary(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#summaryself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`trash(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#trashself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`update(self, dataset_id: 'int', dataview_id: 'int', patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-dataset_id-int-dataview_id-int-patch_data-_listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
- [Pipeline](#pipeline)
  - [`PipelineAPI`](#pipelineapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any] | list[dict[str, Any]]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_taskself-dataview_id-int-task_spec-dictstr-any-listdictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`command(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#commandself-dataview_id-int-command-str-dataset_id-int-none-none---dictstr-any)
    - [`delete_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`draft_mode(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#draft_modeself-dataview_id-int-command-str-dataset_id-int-none-none---dictstr-any)
    - [`edit_pipeline(self, dataview_id: 'int', patches: '_list[dict[str, Any]]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#edit_pipelineself-dataview_id-int-patches-_listdictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`find_dataset_for_dataview(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`](#find_dataset_for_dataviewself-dataview_id-int-dataset_id-int-none-none---int)
    - [`get_draft_status(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_draft_statusself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`get_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_pipelineself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`get_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`items(self, dataview_id: 'int', dataset_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#itemsself-dataview_id-int-dataset_id-int-none-none-fields-str-none-none-limit-int-none-none-offset-int-none-none-sort-str-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`items_all(self, dataview_id: 'int', dataset_id: 'int', fields: 'str | None' = None, limit: 'int' = 100, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'str | None' = None, max_pages: 'int' = 1000) -> 'dict[str, Any]'`](#items_allself-dataview_id-int-dataset_id-int-fields-str-none-none-limit-int-100-sort-str-none-none-sequence-int-none-none-status-str-none-none-max_pages-int-1000---dictstr-any)
    - [`latest_task_sequence(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`](#latest_task_sequenceself-dataview_id-int-dataset_id-int-none-none---int)
    - [`list_tasks(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#list_tasksself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`preview_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None, sample_size: 'int | None' = None) -> 'dict[str, Any]'`](#preview_taskself-dataview_id-int-task_spec-dictstr-any-dataset_id-int-none-none-sample_size-int-none-none---dictstr-any)
    - [`reconcile_draft_submission(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#reconcile_draft_submissionself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`rerun(self, dataview_id: 'int', from_sequence: 'int | None' = None, dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#rerunself-dataview_id-int-from_sequence-int-none-none-dataset_id-int-none-none---dictstr-any)
    - [`update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any] | None' = None, dataset_id: 'int | None' = None, patches: 'list[dict[str, Any]] | None' = None, skip_validation: 'bool | None' = None) -> 'dict[str, Any]'`](#update_taskself-dataview_id-int-task_id-int-task_spec-dictstr-any-none-none-dataset_id-int-none-none-patches-listdictstr-any-none-none-skip_validation-bool-none-none---dictstr-any)
    - [`wait_for_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None, timeout: 'float | None' = None, poll_interval: 'float' = 0.5) -> 'dict[str, Any]'`](#wait_for_pipelineself-dataview_id-int-dataset_id-int-none-none-timeout-float-none-none-poll_interval-float-05---dictstr-any)
- [Jobs](#jobs)
  - [`JobsAPI`](#jobsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`get_job(self, job_id: 'int', timeout: 'float | None' = None) -> 'dict[str, Any]'`](#get_jobself-job_id-int-timeout-float-none-none---dictstr-any)
    - [`get_jobs(self, job_ids: 'list[int] | str', timeout: 'float | None' = None) -> 'dict[str, Any]'`](#get_jobsself-job_ids-listint-str-timeout-float-none-none---dictstr-any)
    - [`wait_for_job(self, job_id: 'int', timeout: 'float | None' = None, poll_interval: 'float | None' = None, fetch: 'Callable[[int, float], Awaitable[dict[str, Any]]] | None' = None) -> 'dict[str, Any]'`](#wait_for_jobself-job_id-int-timeout-float-none-none-poll_interval-float-none-none-fetch-callableint-float-awaitabledictstr-any-none-none---dictstr-any)
    - [`wait_for_jobs(self, job_ids: 'list[int] | str', timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#wait_for_jobsself-job_ids-listint-str-timeout-int-none-none-poll_interval-int-2---dictstr-any)
- [Dashboards](#dashboards)
  - [`DashboardsAPI`](#dashboardsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`action(self, dashboard_id: 'int', action: 'DashboardActionType', params_enabled: 'bool | None' = None, params_view_id: 'int | None' = None, params_sequence: 'int | None' = None, params_filter_column: 'str | None' = None) -> 'dict[str, Any]'`](#actionself-dashboard_id-int-action-dashboardactiontype-params_enabled-bool-none-none-params_view_id-int-none-none-params_sequence-int-none-none-params_filter_column-str-none-none---dictstr-any)
    - [`add_pages(self, dashboard_id: 'int', body: 'AddPagesSpec') -> 'AddPagesResponse'`](#add_pagesself-dashboard_id-int-body-addpagesspec---addpagesresponse)
    - [`analytics(self: 'Any', dashboard_id: 'int') -> 'DashboardAnalyticsResponse'`](#analyticsself-any-dashboard_id-int---dashboardanalyticsresponse)
    - [`append_figure(self, dashboard_id: 'int', dataview_id: 'int', figure: 'dict[str, Any]', banded: 'dict[str, Any] | None' = None, page_id: 'str | None' = None, page_new_title: 'str | None' = None) -> 'dict[str, Any]'`](#append_figureself-dashboard_id-int-dataview_id-int-figure-dictstr-any-banded-dictstr-any-none-none-page_id-str-none-none-page_new_title-str-none-none---dictstr-any)
    - [`archive(self, dashboard_id: 'int', archived: 'bool') -> 'Any'`](#archiveself-dashboard_id-int-archived-bool---any)
    - [`assess_pbix(self, file: 'str | Path') -> 'PbixAssessResponse'`](#assess_pbixself-file-str-path---pbixassessresponse)
    - [`assess_twb(self, file: 'str | Path') -> 'TwbAssessResponse'`](#assess_twbself-file-str-path---twbassessresponse)
    - [`attachment_assess(self, attachment_id: 'int') -> 'dict[str, Any]'`](#attachment_assessself-attachment_id-int---dictstr-any)
    - [`attachment_create(self, file: 'str | Path') -> 'dict[str, Any]'`](#attachment_createself-file-str-path---dictstr-any)
    - [`attachment_intent(self, attachment_id: 'int', target_dataview_id: 'int') -> 'dict[str, Any]'`](#attachment_intentself-attachment_id-int-target_dataview_id-int---dictstr-any)
    - [`audience(self, dashboard_id: 'int', days: 'int' = 7) -> 'dict[str, Any]'`](#audienceself-dashboard_id-int-days-int-7---dictstr-any)
    - [`audience_digest_get(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#audience_digest_getself-dashboard_id-int---dictstr-any)
    - [`audience_digest_set(self, dashboard_id: 'int', enabled: 'bool | None') -> 'dict[str, Any]'`](#audience_digest_setself-dashboard_id-int-enabled-bool-none---dictstr-any)
    - [`audience_get(self: 'Any', dashboard_id: 'int', days: 'int | None' = None) -> 'AudienceResponse'`](#audience_getself-any-dashboard_id-int-days-int-none-none---audienceresponse)
    - [`audience_summary(self, dashboard_ids: '_list[int]') -> 'dict[str, Any]'`](#audience_summaryself-dashboard_ids-_listint---dictstr-any)
    - [`bi_preflight(self: 'Any', dashboard_id: 'int') -> 'PowerBiPreflightResponse'`](#bi_preflightself-any-dashboard_id-int---powerbipreflightresponse)
    - [`cancel_generation(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#cancel_generationself-dashboard_id-int---dictstr-any)
    - [`canvas_get(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None, rls_preview_value: 'str | None' = None) -> 'CanvasResponse'`](#canvas_getself-any-dashboard_id-int-sequence-int-none-none-rls_preview_value-str-none-none---canvasresponse)
    - [`canvas_restore(self: 'Any', dashboard_id: 'int', body: 'RestoreCanvasSpec') -> 'ObjectJobSchema | JobResponse'`](#canvas_restoreself-any-dashboard_id-int-body-restorecanvasspec---objectjobschema-jobresponse)
    - [`canvas_save(self: 'Any', dashboard_id: 'int', body: 'SaveCanvasSpec') -> 'SaveCanvasResponse'`](#canvas_saveself-any-dashboard_id-int-body-savecanvasspec---savecanvasresponse)
    - [`chat_edit(self: 'Any', dashboard_id: 'int', body: 'ChatEditSpec') -> 'ObjectJobSchema | JobResponse'`](#chat_editself-any-dashboard_id-int-body-chateditspec---objectjobschema-jobresponse)
    - [`chat_history(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'mmai_dashboards_v3_schema_ChatHistoryResponse'`](#chat_historyself-any-dashboard_id-int-sequence-int-none-none---mmai_dashboards_v3_schema_chathistoryresponse)
    - [`column_roster(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#column_rosterself-dashboard_id-int---dictstr-any)
    - [`columns(self: 'Any', dashboard_id: 'int') -> 'ColumnRoster'`](#columnsself-any-dashboard_id-int---columnroster)
    - [`context_apply(self, dashboard_id: 'int', review_id: 'str', keep: '_list[str] | None' = None, base_sequence: 'int | None' = None) -> 'ObjectJobSchema'`](#context_applyself-dashboard_id-int-review_id-str-keep-_liststr-none-none-base_sequence-int-none-none---objectjobschema)
    - [`context_create(self: 'Any', body: 'ContextSpec') -> 'ContextResponse'`](#context_createself-any-body-contextspec---contextresponse)
    - [`context_delete(self: 'Any', context_id: 'str') -> 'OkResponse'`](#context_deleteself-any-context_id-str---okresponse)
    - [`context_extract(self: 'Any', body: 'ContextExtractSpec') -> 'ContextExtractResponse'`](#context_extractself-any-body-contextextractspec---contextextractresponse)
    - [`context_list(self: 'Any') -> 'ContextListResponse'`](#context_listself-any---contextlistresponse)
    - [`context_review(self, dashboard_id: 'int', scope: 'str | None' = None, note: 'str | None' = None, fresh: 'bool' = False) -> 'ObjectJobSchema'`](#context_reviewself-dashboard_id-int-scope-str-none-none-note-str-none-none-fresh-bool-false---objectjobschema)
    - [`context_update(self: 'Any', context_id: 'str', body: 'ContextSpec') -> 'ContextResponse'`](#context_updateself-any-context_id-str-body-contextspec---contextresponse)
    - [`create_blank(self, params: 'CreateBlankParams') -> 'dict[str, Any]'`](#create_blankself-params-createblankparams---dictstr-any)
    - [`data_draft(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`](#data_draftself-any-dashboard_id-int-body-widgetdataspec---widgetdataresponse-objectjobschema-jobresponse)
    - [`data_published(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`](#data_publishedself-any-dashboard_id-int-body-widgetdataspec---widgetdataresponse-objectjobschema-jobresponse)
    - [`delete(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#deleteself-dashboard_id-int---dictstr-any)
    - [`delete_tag(self, tag_id: 'int') -> 'dict[str, Any] | None'`](#delete_tagself-tag_id-int---dictstr-any-none)
    - [`descriptor_data(self: 'Any', dashboard_id: 'int', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`](#descriptor_dataself-any-dashboard_id-int-body-descriptordataspec---objectjobschema-jobresponse)
    - [`duplicate(self, dashboard_id: 'int', project_id: 'int | None' = None, target_dataview_id: 'int | None' = None) -> 'DuplicateDashboardResponse'`](#duplicateself-dashboard_id-int-project_id-int-none-none-target_dataview_id-int-none-none---duplicatedashboardresponse)
    - [`email_updates_get(self: 'Any', dashboard_id: 'int') -> 'EmailUpdatesOut'`](#email_updates_getself-any-dashboard_id-int---emailupdatesout)
    - [`email_updates_list(self: 'Any') -> 'EmailUpdateSummaryList'`](#email_updates_listself-any---emailupdatesummarylist)
    - [`email_updates_me_get(self: 'Any', dashboard_id: 'int') -> 'EmailUpdateSubscriptionOut'`](#email_updates_me_getself-any-dashboard_id-int---emailupdatesubscriptionout)
    - [`email_updates_me_set(self: 'Any', dashboard_id: 'int', body: 'EmailUpdateSubscriptionBody') -> 'EmailUpdateSubscriptionOut'`](#email_updates_me_setself-any-dashboard_id-int-body-emailupdatesubscriptionbody---emailupdatesubscriptionout)
    - [`email_updates_set(self: 'Any', dashboard_id: 'int', body: 'EmailUpdateSettingsBody') -> 'EmailUpdatesOut'`](#email_updates_setself-any-dashboard_id-int-body-emailupdatesettingsbody---emailupdatesout)
    - [`email_updates_test(self: 'Any', dashboard_id: 'int') -> 'EmailUpdateTestOut'`](#email_updates_testself-any-dashboard_id-int---emailupdatetestout)
    - [`embed_config_get(self, dashboard_id: 'int') -> 'EmbedConfigResponse'`](#embed_config_getself-dashboard_id-int---embedconfigresponse)
    - [`embed_config_set(self, dashboard_id: 'int', mode: "Literal['key', 'signed']" = 'key', allow_any_origin: 'bool' = True, allowed_origins: '_list[str] | None' = None, appearance: 'dict[str, Any] | None' = None, snippet: 'dict[str, Any] | None' = None) -> 'EmbedConfigResponse'`](#embed_config_setself-dashboard_id-int-mode-literalkey-signed-key-allow_any_origin-bool-true-allowed_origins-_liststr-none-none-appearance-dictstr-any-none-none-snippet-dictstr-any-none-none---embedconfigresponse)
    - [`embed_key_rotate(self, dashboard_id: 'int', keep_previous: 'bool' = True) -> 'EmbedKeyResponse'`](#embed_key_rotateself-dashboard_id-int-keep_previous-bool-true---embedkeyresponse)
    - [`embed_lifetime_set(self, workspace_id: 'int', token_ttl: 'int') -> 'EmbedLifetimeResponse'`](#embed_lifetime_setself-workspace_id-int-token_ttl-int---embedlifetimeresponse)
    - [`embed_origin_revoke(self, dashboard_id: 'int', origin: 'str') -> 'EmbedConfigResponse'`](#embed_origin_revokeself-dashboard_id-int-origin-str---embedconfigresponse)
    - [`embed_preview_token_create(self, dashboard_id: 'int', claims: 'dict[str, Any] | None' = None) -> 'EmbedPreviewTokenResponse'`](#embed_preview_token_createself-dashboard_id-int-claims-dictstr-any-none-none---embedpreviewtokenresponse)
    - [`embed_secret_rotate(self, workspace_id: 'int') -> 'EmbedSecretResponse'`](#embed_secret_rotateself-workspace_id-int---embedsecretresponse)
    - [`embed_usage_get(self, dashboard_id: 'int') -> 'EmbedUsageResponse'`](#embed_usage_getself-dashboard_id-int---embedusageresponse)
    - [`embed_usage_summary(self, dashboard_ids: '_list[int]') -> 'dict[str, Any]'`](#embed_usage_summaryself-dashboard_ids-_listint---dictstr-any)
    - [`engagement(self, dashboard_id: 'int', days: 'int' = 30, viewers: 'str' = 'all') -> 'dict[str, Any]'`](#engagementself-dashboard_id-int-days-int-30-viewers-str-all---dictstr-any)
    - [`engagement_get(self: 'Any', dashboard_id: 'int', days: 'int | None' = None, viewers: "Literal['all', 'named', 'anonymous'] | None" = None) -> 'EngagementResponse'`](#engagement_getself-any-dashboard_id-int-days-int-none-none-viewers-literalall-named-anonymous-none-none---engagementresponse)
    - [`engagement_person(self, dashboard_id: 'int', user_id: 'int', days: 'int' = 30) -> 'dict[str, Any]'`](#engagement_personself-dashboard_id-int-user_id-int-days-int-30---dictstr-any)
    - [`engagement_remind(self, dashboard_id: 'int', user_ids: '_list[int]') -> 'dict[str, Any]'`](#engagement_remindself-dashboard_id-int-user_ids-_listint---dictstr-any)
    - [`exemplar_extract(self: 'Any', body: 'ExemplarExtractSpec') -> 'ExemplarExtractResponse'`](#exemplar_extractself-any-body-exemplarextractspec---exemplarextractresponse)
    - [`export_powerbi(self, dashboard_id: 'int', output_path: 'str | Path | None' = None) -> 'Path'`](#export_powerbiself-dashboard_id-int-output_path-str-path-none-none---path)
    - [`export_tableau(self, dashboard_id: 'int', output_path: 'str | Path | None' = None) -> 'Path'`](#export_tableauself-dashboard_id-int-output_path-str-path-none-none---path)
    - [`extract_context(self, body: 'ContextExtractSpec') -> 'dict[str, Any]'`](#extract_contextself-body-contextextractspec---dictstr-any)
    - [`extract_exemplar(self, body: 'ExemplarExtractSpec') -> 'dict[str, Any]'`](#extract_exemplarself-body-exemplarextractspec---dictstr-any)
    - [`figure_add(self: 'Any', dashboard_id: 'int', body: 'AppendFigureSpec') -> 'AppendFigureResponse'`](#figure_addself-any-dashboard_id-int-body-appendfigurespec---appendfigureresponse)
    - [`figure_intent(self: 'Any', dashboard_id: 'int', body: 'FigureIntentSpec') -> 'FigureIntentResponse'`](#figure_intentself-any-dashboard_id-int-body-figureintentspec---figureintentresponse)
    - [`format_preview(self, dashboard_id: 'int', style: 'str') -> 'dict[str, Any]'`](#format_previewself-dashboard_id-int-style-str---dictstr-any)
    - [`gallery_get(self, slug: 'str') -> 'dict[str, Any]'`](#gallery_getself-slug-str---dictstr-any)
    - [`gallery_list(self, function: 'str | None' = None, industry: 'str | None' = None) -> 'dict[str, Any]'`](#gallery_listself-function-str-none-none-industry-str-none-none---dictstr-any)
    - [`generate_v3(self, params: 'GenerateV3Params | dict[str, Any]') -> 'dict[str, Any]'`](#generate_v3self-params-generatev3params-dictstr-any---dictstr-any)
    - [`get(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#getself-dashboard_id-int---dictstr-any)
    - [`get_analytics(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#get_analyticsself-dashboard_id-int---dictstr-any)
    - [`get_by_url(self, url: 'str') -> 'dict[str, Any]'`](#get_by_urlself-url-str---dictstr-any)
    - [`get_draft_data(self, dashboard_id: 'int', widget_id: 'str', global_filters: 'dict[str, Any] | None' = None, drilldown_filters: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`](#get_draft_dataself-dashboard_id-int-widget_id-str-global_filters-dictstr-any-none-none-drilldown_filters-dictstr-any-none-none---dictstr-any)
    - [`get_publish_data(self, dashboard_id: 'int', widget_id: 'str', global_filters: 'dict[str, Any] | None' = None, drilldown_filters: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`](#get_publish_dataself-dashboard_id-int-widget_id-str-global_filters-dictstr-any-none-none-drilldown_filters-dictstr-any-none-none---dictstr-any)
    - [`get_sources(self) -> '_list[dict[str, Any]]'`](#get_sourcesself---_listdictstr-any)
    - [`import_workbook(self, file: 'str | Path', project_id: 'int | None' = None) -> 'ImportDatasetResponse'`](#import_workbookself-file-str-path-project_id-int-none-none---importdatasetresponse)
    - [`job_by_url(self, url: 'str', job_id: 'int') -> 'dict[str, Any]'`](#job_by_urlself-url-str-job_id-int---dictstr-any)
    - [`list(self, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#listself-project_id-int-none-none---_listdictstr-any)
    - [`list_tags(self) -> 'dict[str, Any]'`](#list_tagsself---dictstr-any)
    - [`live_chart_audience(self: 'Any', dashboard_id: 'int', body: 'ChangeAudienceSpec') -> 'LiveChartResponse'`](#live_chart_audienceself-any-dashboard_id-int-body-changeaudiencespec---livechartresponse)
    - [`live_chart_create(self: 'Any', body: 'CreateLiveChartSpec', project_id: 'int | None' = None) -> 'CreateLiveChartResponse'`](#live_chart_createself-any-body-createlivechartspec-project_id-int-none-none---createlivechartresponse)
    - [`live_chart_get(self: 'Any', dashboard_id: 'int') -> 'LiveChartResponse'`](#live_chart_getself-any-dashboard_id-int---livechartresponse)
    - [`live_chart_list(self: 'Any', session_id: 'str') -> 'LiveChartListResponse'`](#live_chart_listself-any-session_id-str---livechartlistresponse)
    - [`live_chart_placement(self: 'Any', dashboard_id: 'int', body: 'RecordPlacementSpec') -> 'dict[str, Any]'`](#live_chart_placementself-any-dashboard_id-int-body-recordplacementspec---dictstr-any)
    - [`live_chart_usage(self: 'Any', dashboard_id: 'int') -> 'LiveChartUsageResponse'`](#live_chart_usageself-any-dashboard_id-int---livechartusageresponse)
    - [`merge_tag(self, tag_id: 'int', target_id: 'int') -> 'dict[str, Any]'`](#merge_tagself-tag_id-int-target_id-int---dictstr-any)
    - [`oembed(self: 'Any', url: 'str | None' = None, maxwidth: 'str | None' = None, maxheight: 'str | None' = None, format: 'str | None' = None) -> 'dict[str, Any]'`](#oembedself-any-url-str-none-none-maxwidth-str-none-none-maxheight-str-none-none-format-str-none-none---dictstr-any)
    - [`og_card(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`](#og_cardself-any-dashboard_id-int---dictstr-any)
    - [`own_data_accept(self, dashboard_id: 'int', choice: 'str' = 'proposal', exclude: '_list[str] | None' = None) -> 'ObjectJobSchema'`](#own_data_acceptself-dashboard_id-int-choice-str-proposal-exclude-_liststr-none-none---objectjobschema)
    - [`own_data_dismiss(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#own_data_dismissself-dashboard_id-int---dictstr-any)
    - [`own_data_preview(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#own_data_previewself-dashboard_id-int---dictstr-any)
    - [`own_data_start(self, dashboard_id: 'int', ingest_job_id: 'int | None' = None, dataset_id: 'int | None' = None, dataview_id: 'int | None' = None, file_name: 'str | None' = None) -> 'dict[str, Any]'`](#own_data_startself-dashboard_id-int-ingest_job_id-int-none-none-dataset_id-int-none-none-dataview_id-int-none-none-file_name-str-none-none---dictstr-any)
    - [`own_data_status(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#own_data_statusself-dashboard_id-int---dictstr-any)
    - [`page_plan(self: 'Any', dashboard_id: 'int', body: 'PlanPageSpec') -> 'PlanPageResponse'`](#page_planself-any-dashboard_id-int-body-planpagespec---planpageresponse)
    - [`pages_add(self: 'Any', dashboard_id: 'int', body: 'AddPagesSpec') -> 'AddPagesResponse'`](#pages_addself-any-dashboard_id-int-body-addpagesspec---addpagesresponse)
    - [`pbix_assess(self: 'Any', attachment_id: 'int') -> 'AttachmentJob'`](#pbix_assessself-any-attachment_id-int---attachmentjob)
    - [`pbix_intent(self: 'Any', attachment_id: 'int', body: 'AttachmentIntentForm') -> 'AttachmentJob'`](#pbix_intentself-any-attachment_id-int-body-attachmentintentform---attachmentjob)
    - [`pdf_artifact(self: 'Any', dashboard_id: 'int', job_id: 'int') -> 'dict[str, Any]'`](#pdf_artifactself-any-dashboard_id-int-job_id-int---dictstr-any)
    - [`pdf_export(self: 'Any', dashboard_id: 'int', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`](#pdf_exportself-any-dashboard_id-int-body-pdfexportspec---objectjobschema-jobresponse)
    - [`powerbi_export_artifact(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#powerbi_export_artifactself-dashboard_id-int---dictstr-any)
    - [`powerbi_preflight(self, dashboard_id: 'int') -> 'PowerBiPreflightResponse'`](#powerbi_preflightself-dashboard_id-int---powerbipreflightresponse)
    - [`published_canvas(self: 'Any', url: 'str') -> 'CanvasResponse'`](#published_canvasself-any-url-str---canvasresponse)
    - [`published_data(self: 'Any', url: 'str', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`](#published_dataself-any-url-str-body-descriptordataspec---objectjobschema-jobresponse)
    - [`published_data_by_url(self, url: 'str', body: 'dict[str, Any]') -> 'dict[str, Any]'`](#published_data_by_urlself-url-str-body-dictstr-any---dictstr-any)
    - [`published_og_card(self: 'Any', url: 'str') -> 'dict[str, Any]'`](#published_og_cardself-any-url-str---dictstr-any)
    - [`published_pdf_artifact(self: 'Any', url: 'str', job_id: 'int') -> 'dict[str, Any]'`](#published_pdf_artifactself-any-url-str-job_id-int---dictstr-any)
    - [`published_pdf_export(self: 'Any', url: 'str', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`](#published_pdf_exportself-any-url-str-body-pdfexportspec---objectjobschema-jobresponse)
    - [`published_share_page(self: 'Any', url: 'str') -> 'dict[str, Any]'`](#published_share_pageself-any-url-str---dictstr-any)
    - [`published_video_artifact(self: 'Any', url: 'str') -> 'dict[str, Any]'`](#published_video_artifactself-any-url-str---dictstr-any)
    - [`published_video_export(self: 'Any', url: 'str') -> 'ObjectJobSchema | JobResponse'`](#published_video_exportself-any-url-str---objectjobschema-jobresponse)
    - [`qa_ask(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'AskSpec') -> 'ObjectJobSchema | JobResponse'`](#qa_askself-any-dashboard_id-int-session_id-int-body-askspec---objectjobschema-jobresponse)
    - [`qa_comment_create(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'CommentSpec') -> 'SessionResponse'`](#qa_comment_createself-any-dashboard_id-int-session_id-int-body-commentspec---sessionresponse)
    - [`qa_comment_delete(self: 'Any', dashboard_id: 'int', session_id: 'int', comment_id: 'int') -> 'SessionResponse'`](#qa_comment_deleteself-any-dashboard_id-int-session_id-int-comment_id-int---sessionresponse)
    - [`qa_feedback(self: 'Any', dashboard_id: 'int', session_id: 'int', message_id: 'int', body: 'FeedbackSpec') -> 'SessionResponse'`](#qa_feedbackself-any-dashboard_id-int-session_id-int-message_id-int-body-feedbackspec---sessionresponse)
    - [`qa_insights(self, dashboard_id: 'int', days: 'int' = 7) -> 'dict[str, Any]'`](#qa_insightsself-dashboard_id-int-days-int-7---dictstr-any)
    - [`qa_session_create(self: 'Any', dashboard_id: 'int', body: 'CreateSessionSpec') -> 'SessionResponse'`](#qa_session_createself-any-dashboard_id-int-body-createsessionspec---sessionresponse)
    - [`qa_session_delete(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'dict[str, Any]'`](#qa_session_deleteself-any-dashboard_id-int-session_id-int---dictstr-any)
    - [`qa_session_fork(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'SessionResponse'`](#qa_session_forkself-any-dashboard_id-int-session_id-int---sessionresponse)
    - [`qa_session_get(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'SessionResponse'`](#qa_session_getself-any-dashboard_id-int-session_id-int---sessionresponse)
    - [`qa_session_list(self: 'Any', dashboard_id: 'int') -> 'SessionListResponse'`](#qa_session_listself-any-dashboard_id-int---sessionlistresponse)
    - [`qa_session_rename(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'RenameSessionSpec') -> 'SessionResponse'`](#qa_session_renameself-any-dashboard_id-int-session_id-int-body-renamesessionspec---sessionresponse)
    - [`qa_session_set_visibility(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'VisibilitySpec') -> 'SessionResponse'`](#qa_session_set_visibilityself-any-dashboard_id-int-session_id-int-body-visibilityspec---sessionresponse)
    - [`qa_settings_get(self: 'Any', dashboard_id: 'int') -> 'QaSettingsResponse'`](#qa_settings_getself-any-dashboard_id-int---qasettingsresponse)
    - [`qa_settings_set(self: 'Any', dashboard_id: 'int', body: 'QaSettingsSpec') -> 'QaSettingsResponse'`](#qa_settings_setself-any-dashboard_id-int-body-qasettingsspec---qasettingsresponse)
    - [`query(self: 'Any', dashboard_id: 'int', body: 'AdhocQuerySpec') -> 'AdhocQueryResponse'`](#queryself-any-dashboard_id-int-body-adhocqueryspec---adhocqueryresponse)
    - [`rename_tag(self, tag_id: 'int', name: 'str') -> 'dict[str, Any]'`](#rename_tagself-tag_id-int-name-str---dictstr-any)
    - [`render_figure_svg(self, spec: 'dict[str, Any]', style_id: 'str | None' = None) -> 'str'`](#render_figure_svgself-spec-dictstr-any-style_id-str-none-none---str)
    - [`restore(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#restoreself-dashboard_id-int---dictstr-any)
    - [`rls_assignment_list(self: 'Any', dashboard_id: 'int') -> 'RlsAssignmentsResponse'`](#rls_assignment_listself-any-dashboard_id-int---rlsassignmentsresponse)
    - [`rls_assignment_set(self: 'Any', dashboard_id: 'int', body: 'RlsAssignmentsSpec') -> 'dict[str, Any]'`](#rls_assignment_setself-any-dashboard_id-int-body-rlsassignmentsspec---dictstr-any)
    - [`rls_column_list(self: 'Any', dashboard_id: 'int') -> 'RlsColumnsResponse'`](#rls_column_listself-any-dashboard_id-int---rlscolumnsresponse)
    - [`rls_value_list(self: 'Any', dashboard_id: 'int', column: 'str', search: 'str | None' = None) -> 'RlsDistinctValuesResponse'`](#rls_value_listself-any-dashboard_id-int-column-str-search-str-none-none---rlsdistinctvaluesresponse)
    - [`set_tags(self, dashboard_id: 'int', tags: 'builtins.list[str]') -> 'dict[str, Any]'`](#set_tagsself-dashboard_id-int-tags-builtinsliststr---dictstr-any)
    - [`share(self, dashboard_id: 'int', type_of_auth: 'DashboardAuthType', users: '_list[DashboardShareUser] | None' = None) -> 'dict[str, Any]'`](#shareself-dashboard_id-int-type_of_auth-dashboardauthtype-users-_listdashboardshareuser-none-none---dictstr-any)
    - [`signature_create(self: 'Any', body: 'SignatureSpec') -> 'SignatureResponse'`](#signature_createself-any-body-signaturespec---signatureresponse)
    - [`signature_delete(self: 'Any', signature_id: 'str') -> 'OkResponse'`](#signature_deleteself-any-signature_id-str---okresponse)
    - [`signature_list(self: 'Any') -> 'SignatureListResponse'`](#signature_listself-any---signaturelistresponse)
    - [`signature_update(self: 'Any', signature_id: 'str', body: 'SignatureSpec') -> 'SignatureResponse'`](#signature_updateself-any-signature_id-str-body-signaturespec---signatureresponse)
    - [`source_list(self: 'Any') -> 'DashboardSourcesType'`](#source_listself-any---dashboardsourcestype)
    - [`style_custom_create(self: 'Any', body: 'CustomStyleSpec') -> 'StyleResponse'`](#style_custom_createself-any-body-customstylespec---styleresponse)
    - [`style_custom_delete(self: 'Any', style_id: 'str') -> 'OkResponse'`](#style_custom_deleteself-any-style_id-str---okresponse)
    - [`style_custom_list(self: 'Any') -> 'StyleListResponse'`](#style_custom_listself-any---stylelistresponse)
    - [`style_custom_update(self: 'Any', style_id: 'str', body: 'CustomStyleSpec') -> 'StyleResponse'`](#style_custom_updateself-any-style_id-str-body-customstylespec---styleresponse)
    - [`style_default_get(self: 'Any') -> 'DefaultStyleResponse'`](#style_default_getself-any---defaultstyleresponse)
    - [`style_default_set(self: 'Any', body: 'DefaultStyleSpec') -> 'DefaultStyleResponse'`](#style_default_setself-any-body-defaultstylespec---defaultstyleresponse)
    - [`style_derive(self: 'Any', body: 'DeriveStyleSpec') -> 'dict[str, Any] | DeriveStyleResponse'`](#style_deriveself-any-body-derivestylespec---dictstr-any-derivestyleresponse)
    - [`style_extract_brand(self: 'Any', body: 'ExtractBrandSpec') -> 'ObjectJobSchema | JobResponse'`](#style_extract_brandself-any-body-extractbrandspec---objectjobschema-jobresponse)
    - [`style_preset_list(self: 'Any') -> 'StylePresetsResponse'`](#style_preset_listself-any---stylepresetsresponse)
    - [`style_token_list(self: 'Any', id: 'str') -> 'StyleTokensResponse'`](#style_token_listself-any-id-str---styletokensresponse)
    - [`suggestion_list(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`](#suggestion_listself-any-dataview_id-int-table_item_id-int-none-none---objectjobschema-jobresponse)
    - [`swap_data(self, dashboard_id: 'int', body: 'SwapDataSpec') -> 'ObjectJobSchema'`](#swap_dataself-dashboard_id-int-body-swapdataspec---objectjobschema)
    - [`swap_fit(self, source_dashboard_id: 'int', target_dataview_ids: '_list[int]', include_over_budget: 'bool' = False, seconds_budget: 'float | None' = None) -> 'dict[str, Any]'`](#swap_fitself-source_dashboard_id-int-target_dataview_ids-_listint-include_over_budget-bool-false-seconds_budget-float-none-none---dictstr-any)
    - [`tableau_export_artifact(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#tableau_export_artifactself-dashboard_id-int---dictstr-any)
    - [`tableau_preflight(self, dashboard_id: 'int') -> 'TableauPreflightResponse'`](#tableau_preflightself-dashboard_id-int---tableaupreflightresponse)
    - [`tags_delete(self: 'Any', tag_id: 'int') -> 'dict[str, Any]'`](#tags_deleteself-any-tag_id-int---dictstr-any)
    - [`tags_list(self: 'Any') -> 'dict[str, Any]'`](#tags_listself-any---dictstr-any)
    - [`tags_merge(self: 'Any', tag_id: 'int', body: 'TagMergeParams') -> 'dict[str, Any]'`](#tags_mergeself-any-tag_id-int-body-tagmergeparams---dictstr-any)
    - [`tags_rename(self: 'Any', tag_id: 'int', body: 'TagRenameParams') -> 'dict[str, Any]'`](#tags_renameself-any-tag_id-int-body-tagrenameparams---dictstr-any)
    - [`tags_set(self: 'Any', dashboard_id: 'int', body: 'DashboardTagsParams') -> 'dict[str, Any]'`](#tags_setself-any-dashboard_id-int-body-dashboardtagsparams---dictstr-any)
    - [`take_pending_template(self) -> 'dict[str, Any]'`](#take_pending_templateself---dictstr-any)
    - [`template_apply(self: 'Any', body: 'ApplyTemplateSpec', project_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`](#template_applyself-any-body-applytemplatespec-project_id-int-none-none---objectjobschema-jobresponse)
    - [`template_create(self: 'Any', body: 'SaveTemplateSpec') -> 'TemplateDetailResponse'`](#template_createself-any-body-savetemplatespec---templatedetailresponse)
    - [`template_delete(self: 'Any', template_id: 'str') -> 'OkResponse'`](#template_deleteself-any-template_id-str---okresponse)
    - [`template_fit(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'TemplateFitResponse'`](#template_fitself-any-dataview_id-int-table_item_id-int-none-none---templatefitresponse)
    - [`template_get(self: 'Any', template_id: 'str') -> 'TemplateDetailResponse'`](#template_getself-any-template_id-str---templatedetailresponse)
    - [`template_list(self: 'Any') -> 'TemplateListResponse'`](#template_listself-any---templatelistresponse)
    - [`template_preview(self: 'Any', body: 'PreviewTemplateSpec') -> 'PreviewTemplateResponse'`](#template_previewself-any-body-previewtemplatespec---previewtemplateresponse)
    - [`template_rename(self: 'Any', template_id: 'str', body: 'RenameTemplateSpec') -> 'TemplateDetailResponse'`](#template_renameself-any-template_id-str-body-renametemplatespec---templatedetailresponse)
    - [`template_resolve_mapping(self: 'Any', body: 'ResolveTemplateMappingSpec') -> 'ResolveTemplateMappingResponse'`](#template_resolve_mappingself-any-body-resolvetemplatemappingspec---resolvetemplatemappingresponse)
    - [`template_thumbnail_clear(self, template_id: 'str') -> 'dict[str, Any]'`](#template_thumbnail_clearself-template_id-str---dictstr-any)
    - [`template_thumbnail_get(self, template_id: 'str') -> 'dict[str, Any]'`](#template_thumbnail_getself-template_id-str---dictstr-any)
    - [`template_thumbnail_set(self, template_id: 'str', file: 'str | Path') -> 'dict[str, Any]'`](#template_thumbnail_setself-template_id-str-file-str-path---dictstr-any)
    - [`templates_pending(self: 'Any') -> 'PendingTemplateResponse'`](#templates_pendingself-any---pendingtemplateresponse)
    - [`templates_use(self: 'Any', slug: 'str', body: 'UseTemplateSpec') -> 'ObjectJobSchema | JobResponse'`](#templates_useself-any-slug-str-body-usetemplatespec---objectjobschema-jobresponse)
    - [`trash(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#trashself-dashboard_id-int---dictstr-any)
    - [`update(self, dashboard_id: 'int', patch: '_list[DashboardPatchItem]') -> 'dict[str, Any]'`](#updateself-dashboard_id-int-patch-_listdashboardpatchitem---dictstr-any)
    - [`use_template(self, slug: 'str', body: 'UseTemplateSpec') -> 'ObjectJobSchema | JobResponse'`](#use_templateself-slug-str-body-usetemplatespec---objectjobschema-jobresponse)
    - [`v3_generate(self: 'Any', body: 'GenerateDashboardV3Spec', project_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`](#v3_generateself-any-body-generatedashboardv3spec-project_id-int-none-none---objectjobschema-jobresponse)
    - [`video_export(self: 'Any', dashboard_id: 'int') -> 'ObjectJobSchema | JobResponse'`](#video_exportself-any-dashboard_id-int---objectjobschema-jobresponse)
    - [`video_state(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`](#video_stateself-any-dashboard_id-int---dictstr-any)
    - [`wait_for_job_by_url(self, url: 'str', job_id: 'int', timeout: 'float | None' = None, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`](#wait_for_job_by_urlself-url-str-job_id-int-timeout-float-none-none-poll_interval-float-none-none---dictstr-any)
    - [`widget_data(self, dashboard_id: 'int', body: 'dict[str, Any]') -> 'dict[str, Any]'`](#widget_dataself-dashboard_id-int-body-dictstr-any---dictstr-any)
    - [`widget_data_by_url(self, url: 'str', body: 'dict[str, Any]') -> 'dict[str, Any]'`](#widget_data_by_urlself-url-str-body-dictstr-any---dictstr-any)
- [Webhooks](#webhooks)
  - [`WebhooksAPI`](#webhooksapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`create(self, name: 'str' = 'Generic Webhook', mode: 'str | WebhookMode' = 'replace', folder_resource_id: 'str | None' = None, origins: 'str' = '*', is_secure: 'bool' = False) -> 'dict[str, Any]'`](#createself-name-str-generic-webhook-mode-str-webhookmode-replace-folder_resource_id-str-none-none-origins-str-is_secure-bool-false---dictstr-any)
    - [`delete(self, webhook_id: 'int') -> 'dict[str, Any]'`](#deleteself-webhook_id-int---dictstr-any)
    - [`get(self, webhook_id: 'int') -> 'dict[str, Any]'`](#getself-webhook_id-int---dictstr-any)
    - [`list(self, limit: 'int' = 50, offset: 'int' = 0) -> '_list[dict[str, Any]]'`](#listself-limit-int-50-offset-int-0---_listdictstr-any)
    - [`send_data(self, webhook_uri: 'str', data: 'dict[str, Any]') -> 'dict[str, Any]'`](#send_dataself-webhook_uri-str-data-dictstr-any---dictstr-any)
    - [`send_data_get(self, webhook_uri: 'str', params: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`](#send_data_getself-webhook_uri-str-params-dictstr-any-none-none---dictstr-any)
    - [`update(self, webhook_id: 'int', mode: 'str | WebhookMode | None' = None, origins: 'str | None' = None, is_secure: 'bool | None' = None) -> 'dict[str, Any]'`](#updateself-webhook_id-int-mode-str-webhookmode-none-none-origins-str-none-none-is_secure-bool-none-none---dictstr-any)
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
  - [v0.8.0](#v080)
    - [Changed — breaking](#changed-breaking)
    - [Added](#added)
    - [Fixed](#fixed)
  - [v0.7.18](#v0718)
    - [Fixed](#fixed)
  - [v0.7.17](#v0717)
    - [Added](#added)
    - [Fixed](#fixed)
  - [v0.7.16](#v0716)
    - [Added](#added)
  - [v0.7.15](#v0715)
    - [Added](#added)
  - [v0.7.14](#v0714)
    - [Fixed](#fixed)
  - [v0.7.13](#v0713)
  - [v0.7.12](#v0712)
    - [Fixed](#fixed)
  - [v0.7.11](#v0711)
    - [Added](#added)
  - [v0.7.10](#v0710)
    - [Added](#added)
  - [v0.7.9](#v079)
    - [Fixed](#fixed)
  - [v0.7.8](#v078)
    - [Changed](#changed)
  - [v0.7.7](#v077)
    - [Changed](#changed)
    - [Fixed](#fixed)
  - [v0.7.6](#v076)
    - [Changed](#changed)
    - [Fixed](#fixed)
  - [v0.7.5](#v075)
    - [Fixed](#fixed)
  - [v0.7.4](#v074)
    - [Fixed](#fixed)
  - [v0.7.3](#v073)
    - [Security](#security)
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

**Python SDK** | Python 3.12–3.14 | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mammothsdk)

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
    api_token="mm_your-token",
)
client.set_project_id(10)

# Get a View and apply transformations
view = await client.views.get(1039)
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
await view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Export results
await view.export.to_csv("output.csv")
```

The SDK is async: await every call that reaches the API. The snippet uses top-level `await`, as in a Jupyter cell; in a script, run it inside an `async def` with `asyncio.run` (see [Quick Start](#quick-start-guide)).

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

- **SDK version**: see `mammoth.__version__` (the [changelog](#changelog) lists releases)
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
pip install -U mammoth-io
```

Or with Poetry:

```bash
poetry add mammoth-io
```

## Dependencies

The SDK has two runtime dependencies, installed automatically:

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | >=0.28,<0.29 | Async HTTP client for API requests |
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
pip install -U mammoth-io
```

## 2. Get your API credentials

Log in to your Mammoth Analytics dashboard, navigate to your profile settings, and create an API token: **Workspace settings → API Tokens → Create token**. It starts with `mm_` and is shown once.

## 3. Create a client

```python
from mammoth import MammothClient

client = MammothClient(
    api_token="mm_your-token",
)

# Set the project you want to work with
client.set_project_id(10)
```

The token names its own workspace, so the client needs nothing else. The `project_id` must be set before performing most operations.

> **Note:** The SDK is async
>
> Every call that reaches the API is a coroutine and must be awaited. The rest of this guide
> uses top-level `await`, as in a Jupyter cell or `python -m asyncio`. In a script, run the
> calls inside an `async def` with `asyncio.run`:
>
> ```python
> import asyncio
>
> from mammoth import MammothClient
>
>
> async def main() -> None:
>     async with MammothClient(api_token="mm_your-token") as client:
>         client.set_project_id(10)
>         view = await client.views.get(1039)
>         print(view.display_names)
>
>
> asyncio.run(main())
> ```
>

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
view = await client.views.get(1039)

print(view.name)           # "My View"
print(view.display_names)  # ["Sales", "Region", "Date", ...]
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", ...}
```

## 5. Apply transformations

Transformations are applied in-place. Each method sends a task to the Mammoth pipeline, waits for it to complete, and refreshes the view metadata.

```python
from mammoth import Condition, Operator, ColumnType, SetValue

# Filter rows
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Add a computed column
await view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Math expression
await view.math("Price * Quantity", new_column="Total")
```

## 6. Export data

```python
# Download as CSV
await view.export.to_csv("output.csv")

# Export to S3
await view.export.to_s3(file_name="report.csv")

# Export to PostgreSQL
await view.export.to_postgres(
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
resp = await client.projects.list()
for p in resp["projects"]:      # plain dicts: p["id"], p["name"]
    print(p["id"], p["name"])

# List datasets in a project
datasets = await client.datasets.list()

# Upload a file
await client.files.upload("data.csv")
```

## Complete example

```python
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

client = MammothClient(
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
)
client.set_project_id(10)

try:
    # Get a view
    view = await client.views.get(1039)
    print(f"Working with: {view.name} ({len(view.display_names)} columns)")

    # Filter to high-value rows
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))

    # Add a label column
    await view.set_values(
        new_column="Tier",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Standard"),
        ],
    )

    # Export
    path = await view.export.to_csv("output.csv")
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

The Mammoth SDK authenticates with an API token, sent as `Authorization: Bearer mm_...` on every request.

## Getting an API token

1. Log in to the Mammoth web app
2. Open **Workspace settings → API Tokens** and choose **Create token**
3. Copy the token (it starts with `mm_`); it is shown only once
4. Store it securely; it works only in that workspace and on that server

A token can be limited to one project when it is created. Such a token works
only in that project: it gets HTTP 403 in any other project, even one it has
just created. Create the token without a project if your code must create or
switch projects.

## Client setup

### Direct authentication

```python
from mammoth import MammothClient

client = MammothClient(
    api_token="mm_your-token",
)
client.set_project_id(10)
```

### Environment variables (recommended)

Store credentials in environment variables for better security:

```bash
export MAMMOTH_API_TOKEN="mm_your-token"
```

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
)
```

### Configuration file

For projects with multiple environments:

```python
# config.py
import os

MAMMOTH_CONFIG = {
    "api_token": os.getenv("MAMMOTH_API_TOKEN"),
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
| `Authorization` | `Bearer mm_...` (your API token) |
| `User-Agent` | `mammoth-io/<version>` |

## Error handling

Authentication errors raise `MammothAuthError` (HTTP 401):

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(api_token="mm_invalid")
    projects = await client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API credentials")
```

## Security best practices

**Never hardcode credentials** -- use environment variables or a secrets manager:

```python
# Do not do this:
client = MammothClient(api_token="mm_live_123456789", ...)

# Do this instead:
client = MammothClient(api_token=os.getenv("MAMMOTH_API_TOKEN"), ...)
```

**Use different credentials per environment** -- separate dev, staging, and production tokens.

**Rotate credentials regularly** -- create new API tokens periodically and delete old ones.

**Do not commit credentials** -- add `.env` and config files with secrets to `.gitignore`.

**Use HTTPS API endpoints** -- the client rejects non-HTTPS API base URLs by
default. Local HTTP development requires the explicit
`allow_insecure_loopback_http=True` opt-in and is restricted to loopback hosts.

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
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
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

The client is an async context manager (`async with`). The HTTP session is closed automatically on exit; without it, call `await client.close()`:

```python
async with MammothClient(
    api_token="mm_..."
) as client:
    client.set_project_id(10)
    view = await client.views.get(1039)
    await view.export.to_csv("output.csv")
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

    client = MammothClient(api_token="mm_...")
    client.set_project_id(10)

    # Resource-based CRUD
    projects = await client.projects.list()
    datasets = await client.datasets.list()

    # Rich View objects with transformations
    view = await client.views.get(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.export.to_csv("output.csv")

#### `__init__(self, api_key: 'str | None' = None, api_secret: 'str | None' = None, workspace_id: 'int | None' = None, base_url: 'str' = 'https://app.mammoth.io/api/v2', timeout: 'float' = 30, job_timeout: 'float' = 60, job_poll_seconds: 'float' = 2, pipeline_timeout: 'float' = 3600, allow_insecure_loopback_http: 'bool' = False, *, api_token: 'str | None' = None, api_root: 'str | None' = '/api/v2', retry_gateway_errors: 'bool' = True, token_provider: 'Callable[[], str] | None' = None, user_agent: 'str | None' = None) -> 'None'`

Initialize the Mammoth client.

Pass either ``api_token`` (the ``mm_...`` token from Workspace settings
-> API Tokens, sent as ``Authorization: Bearer``) or the deprecated
``api_key`` + ``api_secret`` pair, never both.

Args:
    api_key: Deprecated API key; use ``api_token``.
    api_secret: Deprecated API secret; use ``api_token``.
    workspace_id: Your Mammoth workspace ID. Only for the deprecated
        ``api_key`` + ``api_secret`` pair; an ``api_token`` names its
        own workspace and rejects this argument.
    base_url: Base URL for the Mammoth API.
    timeout: Request timeout in seconds.
    job_timeout: Job polling timeout in seconds.
    job_poll_seconds: How long to wait between polls of a running
        job. Lower it when a person is waiting on the answer.
    pipeline_timeout: Pipeline readiness polling timeout in seconds.
    allow_insecure_loopback_http: Permit HTTP only for an explicit
        loopback development endpoint. Production API credentials must
        use HTTPS.
    api_token: Your Mammoth API token (``mm_...``).
    api_root: The path the API is served under, appended to
        ``base_url`` when it is not already there. ``None`` takes
        ``base_url`` exactly as given, which is what a caller inside
        the network needs: the server mounts these routes at their own
        paths, and whatever sits in front of it adds the prefix.
    token_provider: A callable returning the current ``mm_...`` token. It
        is called for every request, so a short-lived token that is
        refreshed elsewhere is always sent fresh. Use it instead of
        ``api_token``; ``workspace_id`` is optional and, when absent,
        is learned from the token the provider returns.
    user_agent: A product token such as ``my-tool/1.2`` placed before the
        SDK's own ``mammoth-io/<version>`` in the ``User-Agent`` header,
        so the server can tell a caller built on the SDK from a direct
        SDK call.
    retry_gateway_errors: Retry a read that got a 429/502/503/504, twice.
        Turn it off when the server answering is the process making
        the call: a retry then adds load to the very worker that is
        overloaded. Connection errors are still retried.

#### `set_project_id(self, project_id: 'int') -> 'None'`

Set the active project for subsequent API calls.

Most operations (datasets, views, pipeline) require a project context.
Call this once after creating the client.

Args:
    project_id: ID of the project to use.

Example::

    client.set_project_id(1134)

#### `get_view(self, view_id: 'int') -> 'View'`

Get a rich View object by dataview ID.

Shortcut for ``client.views.get(view_id)``. Automatically finds
the parent dataset.

Args:
    view_id: ID of the dataview.

Returns:
    :class:`~mammoth.view.View` with transformation methods and
    metadata.

Example::

    view = await client.get_view(1039)
    print(view.display_names)

#### `find_dataset_for_dataview(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`

Find the parent dataset ID for a given dataview.

Searches all datasets in the current project to locate which
dataset contains the specified dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Known parent dataset ID. When supplied, no unrelated
        dataset is probed.

Returns:
    Dataset ID that contains the dataview.

Raises:
    MammothAPIError: If the dataview cannot be found in any dataset.

Example::

    dataset_id = await client.find_dataset_for_dataview(1039)

#### `branch_out(self, view_id: 'int', dataset_name: 'str', *, target_ds_id: 'int | None' = None, column_mapping: 'dict[str, str] | None' = None, **kwargs: 'Any') -> 'int'`

Branch out a view — save its data as a Mammoth dataset.

Args:
    view_id: Source dataview ID.
    dataset_name: Name for the new dataset (display name when writing
        into an existing one).
    target_ds_id: Existing dataset to write into; None creates a new one.
    column_mapping: Source -> destination column-name map (optional).
    **kwargs: Additional options forwarded to :meth:`View.branch_out`
        (``save_as_mode``, ``label_ids``, ``condition``, ``timeout``).

Returns:
    The id of the dataset written to (new when ``target_ds_id`` is None,
    otherwise ``target_ds_id``).

#### `test_connection(self) -> 'bool'`

Test the connection to the Mammoth API.

Makes a lightweight API call to verify credentials and network
connectivity.

Returns:
    ``True`` if credentials are valid and API is reachable,
    ``False`` otherwise.

Example::

    if await client.test_connection():
        print("Connected!")

### ViewsResource

### `ViewsResource`

Resource that returns rich View objects.

Access via client.views::

    view = await client.views.get(view_id)           # returns View object
    views = await client.views.list()                 # returns list of View objects
    view = await client.views.create(dataset_id)      # returns View object

#### `get(self, view_id: 'int', dataset_id: 'int | None' = None) -> 'View'`

Get a rich View object for a dataview.

Args:
    view_id: ID of the dataview.
    dataset_id: Known parent dataset ID. When supplied, the SDK uses
        that exact parent and does not probe other datasets.

Returns:
    View object with transformation methods and metadata.

#### `list(self, dataset_id: 'int') -> '_list[View]'`

List all dataviews in a dataset as View objects.

Args:
    dataset_id: ID of the dataset to list views from.

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
    dataset_id: Known parent dataset ID. When supplied, deletion is
        sent directly to that nested endpoint and parent discovery is
        skipped; API errors (including 403) are preserved.

Returns:
    Dict with deletion result.

#### `bulk_delete(self, view_ids: '_list[int]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete multiple dataviews.

Args:
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
    client = MammothClient(api_token="mm_...")
    client.set_project_id(10)
    datasets = await client.datasets.list()
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

client = MammothClient(api_token="mm_...")
client.set_project_id(10)

view = await client.views.get(1039)
```

You can also list, create, and delete views:

```python
# List all views in a dataset
views = await client.views.list(dataset_id=42)

# Create a new view
view = await client.views.create(dataset_id=42, name="My Analysis")

# Create by cloning
view = await client.views.create(dataset_id=42, name="Copy", clone_from=1039)
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
view = await client.views.get(1039)

print(view.id)             # 1039
print(view.name)           # "Sales Data"
print(view.display_names)  # ["Sales", "Region", "Date"]
print(view.columns)        # {"Sales": "column_1", "Region": "column_2", ...}
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", "Date": "DATE"}

# After a transform, new columns appear immediately:
await view.math("Sales * 1.1", new_column="Revenue")
print("Revenue" in view.display_names)   # True
```

## Draft mode

By default, each transformation triggers an immediate pipeline run (auto-run mode). For large datasets or multi-step workflows, use **draft mode** to queue tasks and run the pipeline once.

### draft() (context manager)

The recommended approach. Enters draft mode on entry, submits and runs on clean exit, discards on exception:

```python
async with view.draft():
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.math("Price * 2", new_column="Double")
    await view.add_column("Notes")
# Pipeline runs once for all 3 tasks, metadata refreshed
```

If an exception occurs inside the block, all queued tasks are discarded:

```python
try:
    async with view.draft():
        await view.add_column("Temp")
        raise ValueError("something went wrong")
except ValueError:
    pass  # "Temp" column was NOT added — draft was discarded
```

### Explicit draft workflow

```python
await view.enter_draft_mode()
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
await view.math("Price * 2", new_column="Double")
await view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Rename and sort (view settings)

`rename_columns` and `sort_rows` change how the view shows its rows, like a
column-header rename or a grid sort in the web app. They add no pipeline
task, and later operations, data reads and exports use the result.

```python
await view.rename_columns({"cust_id": "Customer ID"})
await view.sort_rows([["Revenue", "DESC"], ["Region", "ASC"]])  # at most three; [] clears
```

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

#### `data(self, limit: 'int' = 400, offset: 'int' = 1, columns: 'list[str] | None' = None, condition: 'Condition | CompoundCondition | None' = None, sort: 'str | None' = None, sequence: 'int | None' = None) -> 'dict[str, Any]'`

Fetch data rows from the dataview.

Args:
    limit: Maximum number of rows to return (default 400).
    offset: One-indexed starting row (default 1).
    columns: List of display names to fetch. ``None`` fetches all.
    condition: Filter condition — only matching rows are returned.
    sort: Sort specification string.
    sequence: Pipeline step to read at (default: latest, so rows
        include every pipeline-derived column; pass ``0`` for the
        original dataset).

Returns:
    Dict with ``data`` (list of row dicts), ``columns``, and
    pagination info (``total``, ``limit``, ``offset``).

Examples::

    rows = await view.data(limit=10)
    rows = await view.data(columns=["Name", "Sales"], limit=50)
    rows = await view.data(
        condition=Condition("Sales", Operator.GTE, 1000),
        limit=100,
    )

#### `refresh(self) -> 'View'`

Re-fetch metadata from the API and update local state.

Updates ``columns``, ``display_names``, ``column_types``, and ``raw``
to reflect any changes (e.g. columns added by pipeline tasks).

.. note::

    Pipeline-derived columns (from add_column, math, etc.) are
    included only when the server response contains ``taskwise_info``.
    If a column is missing after refresh, call ``await view.data(limit=1)``
    to verify the column exists in the output, or re-get the view
    with ``await client.views.get(view.id)``.

Returns:
    self (for chaining).

Example::

    await view.refresh()
    print(view.display_names)  # updated column list

#### `get_metadata(self) -> 'list[dict[str, Any]]'`

Return current column metadata as a list of dicts.

Each dict has keys ``display_name``, ``internal_name``, and ``type``.
Reflects all columns including those added by pipeline transformations.

Returns:
    List of column metadata dicts.

Example::

    meta = view.get_metadata()
    for col in meta:
        print(f"{col['display_name']} ({col['type']})")

#### `list_tasks(self) -> 'list[dict[str, Any]]'`

List all pipeline tasks on this dataview.

Returns:
    List of task dicts, each with ``id``, ``sequence``,
    ``task_key``, ``params``, etc.

Example::

    tasks = await view.list_tasks()
    for t in tasks:
        print(f"#{t['sequence']} {t['task_key']}")

#### `delete_task(self, task_id: 'int') -> 'dict[str, Any]'`

Delete a pipeline task and re-run the pipeline.

Removes the task, waits for the pipeline to settle, then refreshes
column metadata.

Args:
    task_id: ID of the task to remove (from ``list_tasks()``).

Returns:
    Deletion confirmation dict.

Example::

    tasks = await view.list_tasks()
    await view.delete_task(tasks[-1]["id"])  # remove last task

#### `preview_task(self, task_spec: 'dict[str, Any]') -> 'dict[str, Any]'`

Preview the result of a task without applying it to the pipeline.

Args:
    task_spec: Task specification dict (same format as ``_add_task``
        payloads).

Returns:
    Preview data dict showing what the data would look like.

Example::

    preview = await view.preview_task({"DELETE": ["column_abc123"]})

#### `get_column_mapping(self) -> 'dict[str, str]'`

Return a copy of the display-name-to-internal-name mapping.

Returns:
    Dict mapping display names to internal names (e.g.
    ``{"Sales": "column_abc123", ...}``).

Example::

    mapping = view.get_column_mapping()
    print(mapping)  # {"Sales": "column_abc123", "Region": "column_xyz"}

#### `draft(self) -> '_DraftContext'`

Context manager for draft mode.

Enters draft mode on ``__aenter__``, submits on clean exit,
discards on exception::

    async with view.draft():
        await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
        await view.math("Price * 2", new_column="Double")
    # Pipeline runs once for both tasks

#### `enter_draft_mode(self) -> 'dict[str, Any]'`

Enter draft mode — tasks are queued without pipeline execution.

If already in draft mode, returns immediately without making an API call.

Returns:
    Draft mode state dict from the API, or a status dict if already in
    draft mode.

#### `submit_draft(self) -> 'dict[str, Any]'`

Submit queued draft tasks, run the pipeline, and exit draft mode.

Executes all queued tasks, refreshes column metadata, then
exits draft mode.

Returns:
    Pipeline state dict after execution.

#### `discard_draft(self) -> 'dict[str, Any]'`

Discard queued draft tasks and exit draft mode.

Reverts all tasks added since ``enter_draft_mode()``, refreshes
metadata to the pre-draft state.

Returns:
    Draft mode state dict from the discard call.

#### `set_auto_run(self, enabled: 'bool') -> 'dict[str, Any]'`

Toggle auto-run on the pipeline.

When auto-run is enabled (default), each transformation triggers
immediate pipeline execution. When disabled, the view enters draft
mode and tasks are queued.

Args:
    enabled: ``True`` to enable auto-run, ``False`` to disable.

Returns:
    Updated pipeline state dict.

#### `is_draft_mode` *property*

Whether the server says this view is currently in draft mode.

Every read goes through the pipeline status endpoint, which makes a
freshly created ``View`` in another process observe existing draft
state.  ``_draft_mode`` is only a compatibility fallback for test or
legacy client doubles that do not implement the status seam.

#### `branch_out(self, dataset_name: 'str | None' = None, *, target_ds_id: 'int | None' = None, save_as_mode: 'SaveAsDatasetMode' = <SaveAsDatasetMode.REPLACE: 'REPLACE_IN_DS'>, column_mapping: 'dict[str, str] | None' = None, label_ids: 'list[int] | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None, timeout: 'int | None' = None, target_project_id: 'int | None' = None) -> 'int'`

Branch out — save this view's data as a Mammoth dataset.

Shortcut for :meth:`ViewExport.to_dataset`. ``target_ds_id`` None
creates a new dataset named *dataset_name*; an int replaces/appends
into that existing dataset (per *save_as_mode*).

Args:
    dataset_name: Name for the new dataset (display name when writing
        into an existing one); omit to use the product default 'Result Dataset'
        (what the app's Branch out form uses).
    target_ds_id: Existing dataset to write into; None creates a new one.
    save_as_mode: Replace or append when writing the output dataset.
    column_mapping: Source -> destination column-name map (empty = all).
    label_ids: Folder/label ids for the new dataset.
    condition: Optional row filter applied before copying.
    timeout: Max seconds to wait for the job.
    target_project_id: Send the dataset into another project (see
        :meth:`ViewExport.to_dataset`).

Returns:
    The id of the dataset written to (new when ``target_ds_id`` is None,
    otherwise ``target_ds_id``).

Example::

    new_id = await view.branch_out(dataset_name="Q1 snapshot")

#### `filter_rows(self, condition: 'Condition | CompoundCondition | NotCondition', filter_type: 'FilterType' = <FilterType.SHOW: 'SHOW'>, prompt: 'str' = '') -> 'dict[str, Any]'`

Filter rows by condition (SELECT task).

Args:
    condition: Condition or CompoundCondition object.
    filter_type: SHOW to keep matching rows, REMOVE to discard them.
    prompt: Natural-language description of the filter intent (optional).

Returns:
    API response dict.

Example::

    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.filter_rows(cond1 & cond2, filter_type=FilterType.REMOVE)

#### `set_values(self, values: 'list[SetValue]', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Label and insert values into a new or existing column (SET task).

Creates a VERSION 2 SET payload.

Args:
    values: List of SetValue objects.
    new_column: Name for a new column (mutually exclusive with existing_column).
    column_type: Type for new column (default ColumnType.TEXT).
    existing_column: Display name of existing column to update.
    condition: Global condition applied to the whole task.

Returns:
    API response dict.

Example::

    await view.set_values(
        new_column="Risk Level",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )

#### `math(self, expression: 'str', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.NUMERIC: 'NUMERIC'>, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Apply arithmetic operations (MATH task).

Args:
    expression: A string expression (e.g. ``"Price * Quantity"``)
        that will be parsed automatically.
    new_column: Name for result column (creates new).
    column_type: Type for new column (default ColumnType.NUMERIC).
    existing_column: Existing column to overwrite.
    condition: Condition to apply.

Returns:
    API response dict.

Examples::

    await view.math("Price * Quantity", new_column="Total")
    await view.math("(Price + Tax) * 1.1", new_column="Grand Total")

#### `join(self, foreign_view: 'int | View', join_type: 'JoinType', on: 'list[JoinKeySpec]', select: 'list[str | JoinSelectSpec]', column_prefix: 'str | None' = None, foreign_dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Join with another dataview (JOIN task).

Args:
    foreign_view: View object or ID of the dataview to join with.
        When a View object is passed, display names in ``on.right``
        and ``select`` are resolved automatically.
    join_type: Join type.
    on: Join keys as JoinKeySpec objects::

        [JoinKeySpec(left="Customer ID", right="Customer ID")]

    select: Columns to bring in from the foreign view. Simple list of
        display names or JoinSelectSpec objects::

            ["Category", "Name"]
            [JoinSelectSpec(column="Category", alias="Cat")]

    column_prefix: Prefix for joined columns (optional).
    foreign_dataset_id: Parent dataset for an ID-only foreign view.
        When supplied, metadata is fetched in that exact dataset so
        display-name resolution never probes unrelated parents.

Returns:
    API response dict.

Examples::

    # Join with View object (display names everywhere)
    other = await client.views.get(2050)
    await view.join(
        foreign_view=other,
        join_type=JoinType.LEFT,
        on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
        select=["Category", "Name"],
    )

    # Join with view ID (internal names for foreign view)
    await view.join(
        foreign_view=2050,
        join_type=JoinType.LEFT,
        on=[JoinKeySpec(left="Customer ID", right="column_1")],
        select=[JoinSelectSpec(column="column_7", alias="Category")],
    )

#### `pivot(self, group_by: 'list[str]', aggregations: 'list[AggregationSpec]', condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Group / aggregate / pivot (PIVOT task).

Args:
    group_by: List of display names to group by.
    aggregations: List of :class:`AggregationSpec` objects::

            [AggregationSpec(
                column="Sales", function=AggregateFunction.SUM,
                as_name="Total",
            )]

    condition: Condition to apply.

Returns:
    API response dict.

Example::

    await view.pivot(
        group_by=["Region"],
        aggregations=[AggregationSpec(
            column="Sales",
            function=AggregateFunction.SUM,
            as_name="Total Sales",
        )],
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

    await view.window(
        function=WindowFunction.ROW_NUMBER,
        new_column="Row #",
        partition_by=["Region"],
        order_by=[["Sales", SortDirection.DESC]],
    )

#### `crosstab(self, rows: 'list[str]', pivot_column: 'str', select: 'CrosstabSpec | list[CrosstabSpec]', *, dataset_name: 'str', save_as_mode: 'SaveAsDatasetMode' = <SaveAsDatasetMode.REPLACE: 'REPLACE_IN_DS'>, target_ds_id: 'int | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None, timeout: 'int | None' = None) -> 'int'`

Crosstab / group-and-pivot — materialise a new pivoted dataset.

Row grouping columns define the rows, the ``pivot_column``'s distinct
values become new columns, and cells hold the aggregated result.

Unlike standard transforms, a crosstab produces a NEW dataset, so it is
submitted through the internal-dataset export handler and run as an
async job. The awaited call returns only once the dataset is materialised.

Args:
    rows: Display names of the row-grouping columns.
    pivot_column: Display name of the column whose distinct values
        become the output columns.
    select: A :class:`CrosstabSpec` (or list of them) defining each
        aggregation function and (except for COUNT) its value column.
    dataset_name: Name for the dataset the crosstab creates.
    save_as_mode: Whether to replace or append when writing the output
        dataset (defaults to :attr:`SaveAsDatasetMode.REPLACE`).
    target_ds_id: Existing dataset to write into; ``None`` creates a
        new one.
    condition: Optional row filter applied before aggregating.
    timeout: Max seconds to wait for the job (defaults to the client's
        ``job_timeout``).

Returns:
    The id of the dataset the crosstab wrote to (the new dataset when
    ``target_ds_id`` is None, otherwise ``target_ds_id``).

Example::

    from mammoth import CrosstabSpec, AggregateFunction

    await view.crosstab(
        rows=["Region"],
        pivot_column="Product",
        select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"),
        dataset_name="Sales by Region x Product",
    )

#### `add_column(self, name: 'str', column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>) -> 'dict[str, Any]'`

Add an empty column (ADD_COLUMN task).

Args:
    name: Display name for the new column.
    column_type: Column type (default ``ColumnType.TEXT``).

Returns:
    API response dict.

Examples::

    await view.add_column("Notes")
    await view.add_column("Score", column_type=ColumnType.NUMERIC)
    await view.add_column("Created", column_type=ColumnType.DATE)

#### `delete_columns(self, columns: 'list[str]') -> 'dict[str, Any]'`

Remove one or more columns (DELETE task).

Args:
    columns: List of display names to delete.

Returns:
    API response dict.

Examples::

    await view.delete_columns(["Temp"])
    await view.delete_columns(["Notes", "Internal ID", "Debug"])

#### `copy_columns(self, copies: 'list[CopySpec]') -> 'dict[str, Any]'`

Duplicate columns (COPY task).

Args:
    copies: List of :class:`CopySpec` objects::

            [CopySpec(source="Sales", as_name="Sales Copy")]

Returns:
    API response dict.

#### `rename_columns(self, renames: 'dict[str, str]') -> 'dict[str, Any]'`

Rename columns (the web grid's rename; not a pipeline task).

The new name is a view display property (``COLUMN_NAMES``), the same
change as renaming a column header in the web app. The column keeps
its internal name, so pipeline tasks that use it keep working, and
later operations, data reads, exports and dashboards use the new name.

Args:
    renames: ``{current display name: new display name}``.

Returns:
    ``{"renamed": {old: new}, "columns": [display names after]}``.

Raises:
    MammothColumnError: A current name is not a column of the view.
    MammothError: A new name is not among the view's columns after the
        rename (the server accepted the change but did not apply it).
    ValueError: ``renames`` is empty, a new name is blank, or two
        columns would end up with the same name.

Example::

    await view.rename_columns({"cust_id": "Customer ID", "amt": "Amount"})

#### `combine_columns(self, sources: 'list[str]', new_column: 'str | None' = None, column_type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, existing_column: 'str | None' = None, separator: 'str' = ' ', condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Concatenate multiple columns into one (COMBINE task).

Args:
    sources: List of display names to combine (in order).
    new_column: Name for a new result column. Mutually exclusive with
        ``existing_column``.
    column_type: Type for the new column (default ``ColumnType.TEXT``).
    existing_column: Display name of an existing column to overwrite
        with the combined values.
    separator: String inserted between each column's value
        (default ``" "``).
    condition: Only combine in rows matching this condition.

Returns:
    API response dict.

Examples::

    # Combine first + last name into a new column
    await view.combine_columns(
        ["First Name", "Last Name"],
        new_column="Full Name", separator=" ",
    )

    # Combine with custom separator, overwrite existing column
    await view.combine_columns(
        ["City", "State", "Zip"],
        existing_column="Address", separator=", ",
    )

#### `convert_type(self, conversions: 'list[ConversionSpec]') -> 'dict[str, Any]'`

Convert column data types (CONVERT task).

Args:
    conversions: List of :class:`ConversionSpec` objects::

            [ConversionSpec(column="Sales", to=ColumnType.NUMERIC)]

Returns:
    API response dict.

Examples::

    from mammoth import ConversionSpec, ColumnType

    # Text to numeric
    await view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])

    # Text to date (specify the source format)
    await view.convert_type([
        ConversionSpec(column="Order Date", to=ColumnType.DATE,
                       format="MM/DD/YYYY"),
    ])

#### `text_transform(self, columns: 'list[str]', case: 'TextCase | None' = None, trim: 'bool' = False, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Apply text case change or trim (TEXT_TRANSFORM task).

Args:
    columns: List of display names to transform.
    case: Case transformation (e.g. ``TextCase.UPPER``). Optional if
        ``trim=True``.
    trim: Whether to trim leading/trailing whitespace (default False).
    condition: Only transform rows matching this condition.

Returns:
    API response dict.

Examples::

    await view.text_transform(["Name"], case=TextCase.UPPER)
    await view.text_transform(["City", "State"], case=TextCase.TITLE)
    await view.text_transform(["Notes"], trim=True)
    await view.text_transform(
        ["Name"], case=TextCase.LOWER,
        condition=Condition("Region", Operator.EQ, "West"),
    )

#### `replace_values(self, columns: 'list[str]', find: 'str', replace: 'str', match_case: 'bool' = False, match_words: 'bool' = False, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Find and replace values in one or more columns (REPLACE task).

Args:
    columns: List of display names to search in.
    find: Text to find.
    replace: Replacement text.
    match_case: Case-sensitive matching (default False).
    match_words: Match whole words only (default False).
    condition: Only replace in rows matching this condition.

Returns:
    API response dict.

Examples::

    await view.replace_values(["City"], find="NYC", replace="New York")
    await view.replace_values(
        ["Name"], find="Jr", replace="Junior",
        match_case=True, match_words=True,
    )

#### `bulk_replace(self, columns: 'list[str]', mapping: 'list[BulkReplaceMapping]', match_case: 'bool' = True, match_words: 'bool' = False, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Bulk find-and-replace across one or more columns (REPLACE with MAPPING).

Each mapping entry maps multiple search values to a single replacement.

Args:
    columns: Display names of columns to search in.
    mapping: List of :class:`BulkReplaceMapping` objects::

            [BulkReplaceMapping(search=["val1", "val2"], replace="replacement")]

    match_case: Case-sensitive matching (default True).
    match_words: Whole-word matching (default False).
    condition: Condition to apply.

Returns:
    API response dict.

Example::

    await view.bulk_replace(
        columns=["Item"],
        mapping=[
            BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
        ],
    )

#### `split_column(self, column: 'str', delimiter: 'str', new_columns: 'list[SplitColumnSpec]') -> 'dict[str, Any]'`

Split a column into multiple columns by delimiter (SPLIT task).

Each new column receives the Nth segment after splitting. If a row
has fewer segments than columns, the extra columns are empty.

Args:
    column: Display name of column to split.
    delimiter: Delimiter string (e.g. ``" "``, ``","``).
    new_columns: List of :class:`SplitColumnSpec` objects::

            [SplitColumnSpec("First"), SplitColumnSpec("Last")]

Returns:
    API response dict.

Example::

    from mammoth import SplitColumnSpec

    await view.split_column(
        "Full Name", " ",
        [SplitColumnSpec("First Name"), SplitColumnSpec("Last Name")],
    )

#### `substring(self, column: 'str', direction: 'SubstringDirection | None' = None, num_char: 'int | None' = None, char_position: 'int | None' = None, regex_pattern: 'str | None' = None, regex_invert: 'bool' = False, new_column: 'str | None' = None, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Extract a substring from a column (SUBSTRING task).

Two modes of extraction:

**Position-based** — use ``direction`` with either ``num_char`` or
``char_position``:

- ``START`` + ``num_char``: first N characters.
- ``END`` + ``num_char``: last N characters.
- ``LEFT`` + ``char_position``: characters before position N.
- ``RIGHT`` + ``char_position``: characters from position N onward.

**Regex-based** — use ``regex_pattern`` (and optionally
``regex_invert``) instead of direction.

Args:
    column: Source column display name.
    direction: Extraction direction (see above).
    num_char: Number of characters (use with ``START`` / ``END``).
    char_position: Character position (use with ``LEFT`` / ``RIGHT``).
    regex_pattern: Regex pattern string for extraction (alternative to
        direction). Pass the raw pattern, not a dict.
    regex_invert: If True, return the part that does *not* match the
        regex (default False).
    new_column: Name for a new result column.
    existing_column: Display name of existing column to overwrite.
    condition: Only apply to rows matching this condition.

Returns:
    API response dict.

Examples::

    from mammoth import SubstringDirection

    # First 3 characters
    await view.substring("Code", direction=SubstringDirection.START,
                   num_char=3, new_column="Prefix")

    # Last 4 characters
    await view.substring("Phone", direction=SubstringDirection.END,
                   num_char=4, new_column="Last4")

    # Characters before position 5
    await view.substring("SKU", direction=SubstringDirection.LEFT,
                   char_position=5, new_column="Category")

    # Regex extraction
    await view.substring("Email", regex_pattern=r"@(.+)",
                   new_column="Domain")

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

    await view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")

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

    await view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date",
                   new_column="Duration")

#### `increment_date(self, column: 'str', delta: 'DateDelta', new_column: 'str | None' = None, existing_column: 'str | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> 'dict[str, Any]'`

Add or subtract from a date column (INCREMENT_DATE task).

Args:
    column: Source date column display name.
    delta: :class:`DateDelta` specifying the increment. Use negative
        values to subtract::

            DateDelta(days=30)
            DateDelta(years=1, months=-3)

    new_column: Name for a new result column.
    existing_column: Display name of existing column to overwrite.
    condition: Only apply to rows matching this condition.

Returns:
    API response dict.

Examples::

    from mammoth import DateDelta

    # Add 30 days
    await view.increment_date("Order Date", DateDelta(days=30),
                        new_column="Due Date")

    # Subtract 1 year, add 6 months
    await view.increment_date("Start Date", DateDelta(years=-1, months=6),
                        new_column="Adjusted Date")

    # Conditional increment
    await view.increment_date(
        "Ship Date", DateDelta(days=7),
        existing_column="Ship Date",
        condition=Condition("Priority", Operator.EQ, "Low"),
    )

#### `fill_missing(self, column: 'str', direction: 'FillDirection', partition_by: 'str | None' = None, order_by: 'list[list[str | SortDirection]] | None' = None) -> 'dict[str, Any]'`

Fill missing (null/empty) values using adjacent rows (FILL task).

Args:
    column: Display name of column to fill.
    direction: Fill direction — ``FillDirection.FIRST_VALUE``
        fills downward (forward-fill: a blank takes the previous
        row's value), ``FillDirection.LAST_VALUE`` fills upward
        (back-fill: a blank takes the next row's value).
    partition_by: Display name of column to partition by (optional).
        Fill restarts at each partition boundary.
    order_by: Sort order applied before filling (optional)::

            [["Date", SortDirection.ASC]]

Returns:
    API response dict.

Examples::

    from mammoth import FillDirection, SortDirection

    # Forward-fill missing values (carry the previous value down)
    await view.fill_missing("Price", FillDirection.FIRST_VALUE)

    # Forward-fill within partitions, ordered by date
    await view.fill_missing(
        "Metric", FillDirection.FIRST_VALUE,
        partition_by="Region",
        order_by=[["Date", SortDirection.ASC]],
    )

#### `limit_rows(self, n: 'int', bottom: 'bool' = False, order_by: 'list[list[str | SortDirection]] | None' = None) -> 'dict[str, Any]'`

Keep top or bottom N rows (LIMIT task).

Args:
    n: Number of rows to keep.
    bottom: If True, keep bottom N rows instead of top N
        (default False).
    order_by: Sort order applied *before* limiting (optional)::

            [["Sales", SortDirection.DESC]]

Returns:
    API response dict.

Examples::

    from mammoth import SortDirection

    await view.limit_rows(100)
    await view.limit_rows(10, order_by=[["Sales", SortDirection.DESC]])
    await view.limit_rows(5, bottom=True)

#### `sort_rows(self, order_by: 'list[list[str | SortDirection]]') -> 'dict[str, Any]'`

Set the view's row order (the web grid's sort; not a pipeline task).

The order is a view display property (``SORT``), the same change as
sorting in the web app. Data reads and exports return rows in this
order. It does not add a pipeline task; to keep only the top N rows,
use :meth:`limit_rows` with ``order_by``.

Args:
    order_by: Up to three ``[display name, direction]`` pairs, where
        direction is ``"ASC"`` or ``"DESC"`` (default ``"ASC"``). An
        empty list clears the sort.

Returns:
    ``{"sort": [[display name, direction], ...]}``.

Raises:
    MammothColumnError: A column is not in the view.
    ValueError: More than three columns, a column listed twice, or a
        direction other than ASC/DESC.

Example::

    await view.sort_rows([["Revenue", "DESC"], ["Region", "ASC"]])

#### `discard_duplicates(self, ignore_columns: 'list[str] | None' = None) -> 'dict[str, Any]'`

Remove duplicate rows (DISCARD_DUPLICATES task).

Args:
    ignore_columns: Display names of columns to ignore when detecting
        duplicates. Empty/None means consider all columns.

Returns:
    API response dict.

Example::

    await view.discard_duplicates()
    await view.discard_duplicates(ignore_columns=["Notes", "Timestamp"])

#### `unnest(self, columns: 'list[str]', label_column: 'str' = 'Label', value_column: 'str' = 'Value', value_type: 'str | None' = None) -> 'dict[str, Any]'`

Unpivot (melt) columns to rows (UNNEST task).

Converts multiple columns into rows. Each original column becomes a
label/value pair, multiplying the row count accordingly.

Args:
    columns: Display names of columns to unnest.
    label_column: Name for the new label column that holds the
        original column names (default ``"Label"``).
    value_column: Name for the new value column that holds the
        original cell values (default ``"Value"``).
    value_type: Type of the value column. Left unset (the default) the type is
        derived — when every unnested column shares one type the value column
        gets that type, and only genuinely mixed inputs fall back to TEXT.
        Previously this was always TEXT, so melting numeric columns produced
        a string column that would not sum or sort numerically.

Returns:
    API response dict.

Example::

    # Columns "Q1", "Q2", "Q3", "Q4" → rows with Label/Value
    await view.unnest(["Q1", "Q2", "Q3", "Q4"],
                label_column="Quarter", value_column="Revenue")

#### `lookup(self, source: 'str', lookup_view_id: 'int | View', key: 'str', value: 'str', new_column: 'str | None' = None, new_column_type: 'str' = 'TEXT', existing_column: 'str | None' = None, lookup_dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

VLOOKUP-style value lookup from another dataview (LOOKUP task).

For each row, matches ``source`` against ``key`` in the lookup view
and returns the corresponding ``value``.

Args:
    source: Display name of the key column in *this* view.
    lookup_view_id: ID of the dataview to look up from.
    key: Column name of the key in the lookup view (display name
        or internal name — both are accepted).
    value: Column name of the value in the lookup view (display name
        or internal name — both are accepted).
    new_column: Name for a new result column.
    new_column_type: Type of that new column, i.e. the type of ``value`` in
        the LOOKUP view. Defaults to TEXT, which is what this always used to
        emit unconditionally — pass the real type when looking up numbers or
        dates, otherwise they arrive as strings and will not sum or sort.
        It is not derived here because ``value`` lives in a different view,
        whose metadata this call does not fetch.
    existing_column: Display name of existing column to overwrite.
    lookup_dataset_id: Parent dataset for an ID-only lookup view. If
        provided, the foreign view metadata is fetched in that exact
        dataset before resolving ``key`` and ``value``.

Returns:
    API response dict.

Example::

    await view.lookup(
        source="Product ID",
        lookup_view_id=2055,
        key="column_abc123",
        value="column_xyz789",
        new_column="Product Name",
    )

#### `json_extract(self, column: 'str', json_type: 'JsonType' = <JsonType.OBJECT: 'OBJECT'>, keys: 'list[str] | None' = None, extractions: 'list[JsonExtractionSpec] | None' = None, keep_source: 'bool' = False, op_type: 'JsonOpType | None' = None) -> 'dict[str, Any]'`

Extract data from JSON column (JSON_HANDLE task).

Args:
    column: Source JSON column display name.
    json_type: JSON structure type (default JsonType.OBJECT).
    keys: Simple list of keys to extract (each becomes TEXT column).
        Use for quick extraction without custom types/aliases.
    extractions: Advanced extraction specs as JsonExtractionSpec objects
        (overrides keys)::

        [JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT)]

    keep_source: Keep the original JSON column (default False).
    op_type: Operation type override.

Returns:
    API response dict.

Example::

    # Simple key extraction
    await view.json_extract("data", keys=["name", "email", "age"])

    # Advanced with custom types
    await view.json_extract(
        "data",
        extractions=[
            JsonExtractionSpec(key="name", as_name="Name"),
            JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
        ],
    )

#### `gen_ai(self, prompt: 'str', context_columns: 'list[str]', new_column: 'str' = 'AI Result', assistant_data: 'list[str] | None' = None, context_columns_derivation: 'bool | None' = None) -> 'dict[str, Any]'`

AI-powered transformation (GEN_AI task).

Args:
    prompt: Natural language prompt for the AI.
    context_columns: Display names of columns to use as context.
    new_column: Name for the AI output column (default "AI Result").
    assistant_data: Additional assistant context strings.
    context_columns_derivation: Whether to derive from context columns.

Returns:
    API response dict.

Example::

    await view.gen_ai(
        prompt="Classify the sentiment of the review",
        context_columns=["Review Text"],
        new_column="Sentiment",
    )

#### `generate_sql(self, intent: 'str') -> 'str'`

Generate SQL from natural language using the Mammoth LLM.

Calls the ``/sql_generation`` endpoint, which converts the intent
into SQL and validates it against the view, waits for the job, and
returns the query. It does not change the view: no task is added
(verified on release, 2026-09-25). To apply the query, pass it to
:meth:`add_sql`.

Args:
    intent: Natural language description of the desired query
        (e.g. ``"count employees by department"``).

Returns:
    The generated SQL query string.

Example::

    sql = await view.generate_sql("show total sales by region")
    print(sql)  # "SELECT region, SUM(sales) FROM ... GROUP BY region"
    await view.add_sql(sql)  # apply it (replaces the view's columns)

#### `add_sql(self, query: 'str') -> 'dict[str, Any]'`

Add a raw SQL query as a pipeline task (SQL task).

The query runs against the dataview's current output. Reference the
view as the quoted table ``"view:<dataview_id>"`` (or its quoted
display name, e.g. ``"View 1"``) and columns by display name. An
unquoted or placeholder table name (``data``, ``__TABLE__``) is
rejected by the backend; the SQL task replaces the view's columns
with the query's result, so select everything you still need.

.. note::

    Requires the SQL addon to be enabled on the workspace.

Args:
    query: A single SELECT statement.

Returns:
    API response dict.

Example::

    await view.add_sql(
        'SELECT region, SUM(revenue) AS revenue FROM "view:123" GROUP BY region'
    )

---

## Exports

Export operations are accessed via `view.export`. See the [Exports reference](#exports-reference) for full documentation.

```python
await view.export.to_csv("output.csv")
await view.export.to_s3(file_name="report.csv")
await view.export.to_postgres(host="...", port=5432, database="...", table="...", username="...", password="...")
await view.branch_out(dest_dataset_id=42)
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
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
await view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Conditions can be attached to individual `SetValue` items to create conditional columns:

```python
from mammoth import SetValue, ColumnType

await view.set_values(
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
await view.math(
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

Single column condition. Supports ``&`` (AND), ``|`` (OR), ``~`` (NOT).

Args:
    column: Display name of the column (e.g. "Sales", "Region").
    operator: Operator enum value (e.g. Operator.GTE, Operator.IN_LIST).
    value: Comparison value. Required for most operators, omit for IS_EMPTY.
        For IN_RANGE, pass a 2-element list: ``[lower_bound, upper_bound]``.
        For date-relative functions, pass a ``DateFunction`` with
        ``value_is_date_fn=True``.
    case_sensitive: Controls string comparison case sensitivity.
        ``None`` (default) — don't emit STRING_PROP (backend default: case-sensitive).
        ``True`` — emit CASE-SENSITIVE.
        ``False`` — emit CASE-INSENSITIVE.
    value_is_column: If ``True``, ``value`` names another column (column-to-column
        comparison) rather than a literal.
    component: Date component string (e.g. "year", "month") for date component
        filtering.
    truncate: Date truncation unit (e.g. "DAY", "MONTH") for truncated date
        comparison.
    value_is_date_fn: If ``True``, ``value`` is a ``DateFunction`` enum member and
        is emitted as ``{"VALUE": {"FUNCTION": "<fn>"}}`` in the wire payload.

Examples::

    # Basic comparisons
    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])
    Condition("Name", Operator.IS_NOT_EMPTY)

    # Range filter (numeric or date, not TEXT)
    Condition("Amount", Operator.IN_RANGE, [100, 500])

    # Case-insensitive contains (always case-insensitive, no STRING_PROP needed)
    Condition("City", Operator.ICONTAINS, "york")

    # Combine with & (AND), | (OR), ~ (NOT)
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
    ~Condition("Status", Operator.EQ, "Closed")

    # Column-to-column comparison
    Condition("Revenue", Operator.GT, "Cost", value_is_column=True)

    # Date component filter (e.g. year of a date column)
    Condition("Order Date", Operator.EQ, 2024, component="year")

    # Date truncation filter (compare truncated dates)
    Condition("Timestamp", Operator.GTE, "2024-01-01", truncate="day")

    # Case-insensitive string matching
    Condition("City", Operator.EQ, "new york", case_sensitive=False)

    # Date-relative function operand
    Condition("Order Date", Operator.GT, DateFunction.TODAY, value_is_date_fn=True)
    Condition("Date", Operator.GTE, DateFunction.NOW, value_is_date_fn=True)

Raises:
    ValueError: If column is empty, a non-null operator is used without a value,
        or IN_RANGE is not given exactly 2 bounds.

#### `__init__(self, column: 'str', operator: 'str | Any', value: 'Any' = None, case_sensitive: 'bool | None' = None, value_is_column: 'bool' = False, component: 'str | None' = None, truncate: 'str | None' = None, value_is_date_fn: 'bool' = False) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `build(self, column_map: 'dict[str, str] | None' = None, column_types: 'dict[str, str] | None' = None) -> 'dict[str, Any]'`

Build API-format condition dict.

Args:
    column_map: Mapping of display names to internal names.
    column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

Returns:
    dict in Mammoth API condition format.

### `CompoundCondition`

AND/OR composition of conditions. Supports further chaining with ``&``, ``|``, ``~``.

Created automatically when combining Conditions with & or |::

    combined = cond1 & cond2  # CompoundCondition("AND", [cond1, cond2])
    triple = combined & cond3  # Flat AND of all three

Raises:
    ValueError: If logic is not AND/OR or conditions has fewer than 2 elements.
    TypeError: If any element is not a valid condition type.

#### `__init__(self, logic: 'str', conditions: 'list[Condition | CompoundCondition | NotCondition]') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `build(self, column_map: 'dict[str, str] | None' = None, column_types: 'dict[str, str] | None' = None) -> 'dict[str, Any]'`

Build API-format condition dict.

Args:
    column_map: Mapping of display names to internal names.
    column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

Returns:
    dict in Mammoth API condition format with AND/OR keys.

### `NotCondition`

Negation of a condition. Created via ``~condition``.

Examples::

    ~Condition("Status", Operator.EQ, "Closed")
    ~(cond1 & cond2)  # NOT of an AND

Raises:
    TypeError: If the inner condition is not a valid condition type.

#### `__init__(self, condition: 'ConditionType') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `build(self, column_map: 'dict[str, str] | None' = None, column_types: 'dict[str, str] | None' = None) -> 'dict[str, Any]'`

Build API-format condition dict.

Args:
    column_map: Mapping of display names to internal names.
    column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

Returns:
    dict with NOT key wrapping the inner condition.

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

#### `ICONTAINS`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IN_LIST`

Filter operators for conditions.

Use with Condition to build row filters::

    Condition("Sales", Operator.GTE, 1000)
    Condition("Region", Operator.IN_LIST, ["West", "East"])

#### `IN_RANGE`

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

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `DAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `DAY_OF_YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `HOUR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `HOUR_MINUTE_SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `HOUR_MINUTE_SECOND_MILLISECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MILLISECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MINUTE`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MONTH`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MONTH_DAY_YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MONTH_DAY_YEAR_HOUR_MINUTE_SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MONTH_TEXT`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `MONTH_YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `QUARTER`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `SECOND`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `WEEK`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `WEEKDAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `WEEKDAY_TEXT`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `YEAR`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `YEAR_MONTH`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `YEAR_MONTH_DAY`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `YEAR_MONTH_DAY_AS_DATE`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

#### `YEAR_MONTH_NUMBER`

Date components for extraction.

Backend uses lowercase values. The enum values are lowercase
to match the expected COMPONENT payload format.

The members are exactly the keys of the backend's
``EXTRACT_DATE_FORMAT_MAPS`` (mvc-service
``CommonConstants/dba_const.py``); any other component is rejected.

Basic components:
    year, month, day, hour, minute, second, week, quarter, weekday,
    day_of_year, millisecond

Text-based extractions (return TEXT columns):
    weekday_text, month_text

Composite date formats (return DATE or TEXT):
    year_month_day_as_date, month_day_year_hour_minute_second, month_year

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

``FIRST_VALUE`` is a forward fill: a blank takes the previous row's value
in the ``order_by`` order. ``LAST_VALUE`` is a back-fill: a blank takes the
next row's value (verified on release, 2026-09-25).

#### `FIRST_VALUE`

Fill directions for missing value imputation.

``FIRST_VALUE`` is a forward fill: a blank takes the previous row's value
in the ``order_by`` order. ``LAST_VALUE`` is a back-fill: a blank takes the
next row's value (verified on release, 2026-09-25).

#### `LAST_VALUE`

Fill directions for missing value imputation.

``FIRST_VALUE`` is a forward fill: a blank takes the previous row's value
in the ``order_by`` order. ``LAST_VALUE`` is a back-fill: a blank takes the
next row's value (verified on release, 2026-09-25).

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

### `JsonOpType`

JSON operation types for json_extract.

#### `JSON_LIST_TO_ROWS`

JSON operation types for json_extract.

#### `JSON_OBJECT_TO_COLUMNS`

JSON operation types for json_extract.

### `ExportFileType`

File types for S3 and file-based exports.

#### `CSV`

File types for S3 and file-based exports.

#### `JSON`

File types for S3 and file-based exports.

#### `PARQUET`

File types for S3 and file-based exports.

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

### `DraftCommand`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    async with view.draft():  # preferred
        await view.filter_rows(...)

    await view.enter_draft_mode()   # uses DraftCommand.ENTER
    await view.submit_draft()       # uses SUBMIT then EXIT
    await view.discard_draft()      # uses DISCARD then EXIT

#### `DISCARD`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    async with view.draft():  # preferred
        await view.filter_rows(...)

    await view.enter_draft_mode()   # uses DraftCommand.ENTER
    await view.submit_draft()       # uses SUBMIT then EXIT
    await view.discard_draft()      # uses DISCARD then EXIT

#### `ENTER`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    async with view.draft():  # preferred
        await view.filter_rows(...)

    await view.enter_draft_mode()   # uses DraftCommand.ENTER
    await view.submit_draft()       # uses SUBMIT then EXIT
    await view.discard_draft()      # uses DISCARD then EXIT

#### `EXIT`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    async with view.draft():  # preferred
        await view.filter_rows(...)

    await view.enter_draft_mode()   # uses DraftCommand.ENTER
    await view.submit_draft()       # uses SUBMIT then EXIT
    await view.discard_draft()      # uses DISCARD then EXIT

#### `SUBMIT`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    async with view.draft():  # preferred
        await view.filter_rows(...)

    await view.enter_draft_mode()   # uses DraftCommand.ENTER
    await view.submit_draft()       # uses SUBMIT then EXIT
    await view.discard_draft()      # uses DISCARD then EXIT

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
    await view.set_values(new_column="Risk", values=values)

#### `__init__(self, value: 'Any', condition: 'Condition | CompoundCondition | NotCondition | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `CopySpec`

Specification for a single column copy in :meth:`View.copy_columns`.

Two mutually exclusive destination modes:

* **AS** (new column): set *as_name* (and optionally *type*) to create a
  brand-new column.  This is the default when neither field is set — the
  backend will auto-name the new column ``"<source> Copy"``.
* **DESTINATION** (existing column): set *destination* to the display name
  (or internal name) of an **existing** column whose values should be
  replaced.  When *destination* is set, *as_name* and *type* are ignored
  by the builder.

Providing **both** *as_name* and *destination* raises :exc:`ValueError`.

Examples::

    # Copy into a brand-new column
    await view.copy_columns(
        [CopySpec(source="Sales", as_name="Sales Copy", type=ColumnType.NUMERIC)]
    )

    # Overwrite an existing column's values
    await view.copy_columns([CopySpec(source="Sales", destination="Sales Backup")])

#### `__init__(self, source: 'str', as_name: 'str | None' = None, type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, condition: 'Condition | CompoundCondition | NotCondition | None' = None, destination: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `type`

Column data types for new columns and conversions.

### `ConversionSpec`

Specification for a column type conversion in :meth:`View.convert_type`.

Example::

    await view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])
    await view.convert_type([
        ConversionSpec(column="Date Col", to=ColumnType.DATE, format="MM/DD/YYYY")
    ])
    # "1.234,5" -> 1234.5 (the thousands separator defaults to the other one)
    await view.convert_type([
        ConversionSpec(column="Amount", to=ColumnType.NUMERIC, decimal_separator=",")
    ])

#### `__init__(self, column: 'str', to: 'ColumnType', format: 'str | None' = None, decimal_separator: 'str | None' = None, thousands_separator: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `SplitColumnSpec`

Specification for a new column in :meth:`View.split_column`.

Example::

    await view.split_column("Name", " ", [SplitColumnSpec("First"), SplitColumnSpec("Last")])

#### `__init__(self, name: 'str', type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `type`

Column data types for new columns and conversions.

### `BulkReplaceMapping`

Specification for a bulk replace mapping in :meth:`View.bulk_replace`.

Example::

    await view.bulk_replace(
        columns=["Item"],
        mapping=[BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE")],
    )

#### `__init__(self, search: 'list[str]', replace: 'str') -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `DateDelta`

Delta specification for :meth:`View.increment_date`.

Example::

    await view.increment_date("Order Date", DateDelta(days=30), new_column="Due Date")
    await view.increment_date("Start", DateDelta(years=1, months=-3), new_column="Adjusted")

#### `__init__(self, years: 'int' = 0, months: 'int' = 0, weeks: 'int' = 0, days: 'int' = 0, hours: 'int' = 0, minutes: 'int' = 0, seconds: 'int' = 0) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `days`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `hours`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `minutes`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `months`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `seconds`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `to_dict(self) -> 'dict[str, int]'`

Convert to backend DELTA format (uppercase keys, non-zero only).

#### `weeks`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

#### `years`

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x.__int__().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by '+' or '-' and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int('0b100', base=0)
4

### `AggregationSpec`

Specification for an aggregation in :meth:`View.pivot`.

Example::

    await view.pivot(
        group_by=["Region"],
        aggregations=[AggregationSpec(
            column="Sales", function=AggregateFunction.SUM, as_name="Total",
        )],
    )

#### `__init__(self, column: 'str', function: 'AggregateFunction', as_name: 'str | None' = None, delimiter: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `JoinKeySpec`

Specification for a join key pair in :meth:`View.join`.

Example::

    await view.join(..., on=[JoinKeySpec(left="Customer ID", right="Customer ID")])

#### `__init__(self, left: 'str', right: 'str') -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `JoinSelectSpec`

Specification for a column to bring in from a join in :meth:`View.join`.

Example::

    await view.join(..., select=[JoinSelectSpec(column="Category", alias="Cat")])

#### `__init__(self, column: 'str', alias: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `JsonExtractionSpec`

Specification for a JSON key extraction in :meth:`View.json_extract`.

Example::

    await view.json_extract("data", extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type="TEXT"),
        JsonExtractionSpec(key="age", as_name="Age", type="NUMERIC"),
    ])

#### `__init__(self, key: 'str', as_name: 'str | None' = None, type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `type`

Column data types for new columns and conversions.

### `CrosstabSpec`

Specification for the aggregation in :meth:`View.crosstab`.

Example::

    await view.crosstab(rows=["Region"], pivot_column="Gender",
                  select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"))

#### `__init__(self, function: 'AggregateFunction', column: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

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
    client = MammothClient(api_token="mm_...")
    client.set_project_id(10)
    view = await client.get_view(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
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

Base exception for all Mammoth SDK errors.

Attributes:
    message: Human-readable error description.
    details: Additional context dict (varies by subclass).

#### `__init__(self, message: 'str', details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothAPIError`

Exception raised when the Mammoth API returns an error response.

Attributes:
    message: Human-readable error description.
    status_code: HTTP status code (e.g. 400, 404, 500), or ``None``.
    response_body: Raw JSON response body dict from the API.

Example::

    try:
        await client.datasets.get(dataset_id=99999)
    except MammothAPIError as e:
        print(e.status_code)     # 404
        print(e.response_body)   # {"detail": "Not found"}

#### `__init__(self, message: 'str', status_code: 'int | None' = None, response_body: 'dict[str, Any] | None' = None, details: 'dict[str, Any] | None' = None, *, method: 'str | None' = None, request_id: 'str | None' = None, retry_after: 'str | None' = None, operation_state: 'str | None' = None, phase: 'str | None' = None, job_handle: 'object | None' = None, resource_handle: 'object | None' = None, endpoint: 'str | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothAuthError`

Exception raised when API credentials are invalid (HTTP 401).

Attributes:
    message: ``"Authentication failed"`` (default).
    status_code: Always ``401``.
    error_code: The server's own ``error_code``/``code`` for the refusal, if sent.
    hint: The server's own ``hint`` for the refusal, if sent.

#### `__init__(self, message: 'str' = 'Authentication failed', response_body: 'dict[str, Any] | None' = None, *, error_code: 'str | int | None' = None, hint: 'str | None' = None, **kwargs: 'Any') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothJobTimeoutError`

Exception raised when polling a job exceeds the timeout.

Attributes:
    message: Description including job ID and timeout.
    details: ``{"job_id": int, "timeout": int}``.

#### `__init__(self, job_id: 'int', timeout_seconds: 'int', *, observed_job: 'dict[str, Any] | None' = None, phase: 'str | None' = 'polling') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothJobFailedError`

Exception raised when a job completes with a failure status.

Attributes:
    message: Description including job ID and failure reason.
    details: ``{"job_id": int, "failure_reason": str | None}``.

#### `__init__(self, job_id: 'int', failure_reason: 'str | None' = None, *, observed_job: 'dict[str, Any] | None' = None, phase: 'str | None' = 'polling') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothTransformError`

Exception raised when a pipeline transformation task fails.

Attributes:
    message: Human-readable error description.
    task_key: The pipeline task key (e.g. ``"SET"``, ``"MATH"``).
    details: Additional context dict.

#### `__init__(self, message: 'str', task_key: 'str | None' = None, details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MammothColumnError`

Exception raised when a column display name cannot be resolved.

Attributes:
    message: Description including the missing column name and
        available columns.
    details: ``{"column_name": str, "available_columns": list[str] | None}``.

Example::

    try:
        await view.filter_rows(Condition("NonExistent", Operator.EQ, 1))
    except MammothColumnError as e:
        print(e.details["column_name"])        # "NonExistent"
        print(e.details["available_columns"])   # ["Sales", "Region", ...]

#### `__init__(self, column_name: 'str', available_columns: 'list[str] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## See also

- [Client](#client-api-reference) -- error handling in the client
- [Views](#views-reference) -- transformation methods that raise these exceptions


---


# Files API Reference

The `FilesAPI` manages file uploads, listing, and deletion.

**Access**: `client.files`

```python
# Upload a CSV file
result = await client.files.upload("data.csv")

# Upload an Excel file
result = await client.files.upload("report.xlsx")
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

### `create_datasets_from_multi_sheet(self, file_id: 'int', tables: '_list[dict[str, Any]]', delete_file_after_extract: 'bool' = True) -> 'dict[str, Any]'`

Create datasets from accepted sheet and table reads of a multi-sheet file.

Args:
    file_id: ID of the file.
    tables: Every accepted sheet/block read to create datasets from (1 to 100),
        each with ``sheet_name``, ``dataset_name`` and ``structure_map``.
    delete_file_after_extract: Delete the file once its datasets are created.

Returns:
    Dict with the finished ``job_id`` and ``status``, and ``resource_ids``: the
    resource ids of the files the job created, one per new dataset (not the
    dataset ids; each dataset starts processing and becomes ready on its own).

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

### `preview_multi_sheet(self, file_id: 'int', sheet_name: 'str', block_id: 'str | None' = None, user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`

Preview how one sheet of a multi-sheet file reads, before any dataset exists.

Args:
    file_id: ID of the file.
    sheet_name: The sheet to preview, exactly as it is named in the workbook.
    block_id: Which detected block to resolve, on a multi-table sheet.
    user_instruction: Plain-English description of how to read the sheet
        or block. Omitted: the detected header row and its data.
    structure_map: A structure map already known to be correct; skips the
        LLM call.

Returns:
    Dict with the sheet's read preview.

### `set_password(self, file_id: 'int', password: 'str') -> 'ObjectJobSchema'`

Set password for a password-protected file.

Args:
    file_id: ID of the file.
    password: Password to set.

Returns:
    ObjectJobSchema with job information.

### `update(self, file_id: 'int', patch_request: 'FilePatchRequest') -> 'ObjectJobSchema'`

Update file configuration (e.g., set password, extract sheets).

Waits for the job to complete before returning.

Args:
    file_id: ID of the file to update.
    patch_request: Configuration changes to apply.

Returns:
    ObjectJobSchema with job information.

### `upload(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | int | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`

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

Raises:
    MammothValidationError: The server refused files (``errors`` on the
        upload job, e.g. ``unsupported_files``) and no dataset was made.

### `upload_folder(self, folder_path: 'str | Path', folder_resource_id: 'str | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`

Upload all files in a folder to create datasets.

Args:
    folder_path: Path to the folder containing files.
    folder_resource_id: Resource ID of target folder in Mammoth.
    wait_for_completion: Wait for upload processing to complete.
    timeout: Timeout in seconds when waiting for completion.

Returns:
    List of dataset IDs (or single ID) if wait_for_completion=True.

### `upload_result(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | int | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> 'dict[str, Any]'`

Upload files and report the created datasets AND any server refusals.

Like :meth:`upload`, but returns ``{"job_id", "dataset_ids", "errors", "nested_job_ids"}``.
``errors`` is the upload job's own ``errors`` map (for example
``{"unsupported_files": ["X.pbix"]}``), empty when nothing was refused.

Each file becomes a separate dataset. Folder structure is preserved.

Args:
    files: File(s) to upload — file paths, Path objects, or file-like objects.
    folder_resource_id: Resource ID of target folder.
    append_to_ds_id: Dataset ID to append to (if appending).
    override_target_schema: Override target schema when appending.
    wait_for_completion: Wait for upload processing to complete.
    timeout: Timeout in seconds when waiting for completion.

Returns:
    ``job_id`` is the initial job; with wait_for_completion=False the
    other two are empty.


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

### `create_connection(self, connector_key: 'str', config: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new connection for a connector.

The ``config`` shape is per-connector and varies across the 25+ supported
connector types. The SDK forwards it verbatim — the backend validates per
connector_key. Common examples:

- **DB connectors** (postgres, mysql, mssql, mongodb):
  ``{hostname, port, database, username, password}``
- **Extended DB** (postgres, redshift):
  adds ``ssh_enabled``, ``proxy_*``, ``ssh_auth_type``, ``private_key``
- **OAuth connectors** (salesforce, hubspot, facebook, …):
  ``{code}``
- **Snowflake**: ``{url, username, password, database, warehouse, account, role}``
- **BigQuery**: ``{connection_data}`` (JSON string)
- **DataBricks**: ``{host, port, http_path, personal_access_token, catalog}``
- **SFTP**: ``{username, domain, port, password | private_key}``

Args:
    connector_key: Key identifying the connector type.
    config: Non-empty dict of connection credentials. Shape varies by
        connector_key — see above for common examples.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with created connection info.

Raises:
    MammothValidationError: If ``config`` is empty.

### `create_ds_config(self, connector_key: 'str', connection_key: 'str', *, query: 'str | None' = None, file_source: 'str | None' = None, table: 'str | None' = None, profile: 'str | None' = None, validate: 'bool' = True, data_sample: 'bool' = False, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a data source configuration.

Exactly one of ``query`` or ``file_source`` must be provided (mirrors the
backend ``ValidateAndSampleDataSpec`` validator). ``validate`` and
``data_sample`` are mutually exclusive.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    query: SQL query or table reference (required for DB connectors).
    file_source: File path or source identifier (required for file connectors
        such as SFTP or Google Drive).
    table: Optional table name hint.
    profile: Optional connector-specific profile (e.g. schema name for DB
        connectors, or ``"project_id.dataset_id"`` for BigQuery).
    validate: If ``True`` (default), the backend validates the config.
        Mutually exclusive with ``data_sample``.
    data_sample: If ``True``, the backend returns a data sample.
        Mutually exclusive with ``validate``.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with created data source config.

Raises:
    MammothValidationError: If neither ``query`` nor ``file_source`` is
        provided, or if both ``validate`` and ``data_sample`` are ``True``.

### `delete_connection(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

### `delete_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

### `ds_config_delete_all(self, connector_key: 'str', connection_key: 'str', config_ids: '_list[str] | str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk-delete data source configurations for a connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    config_ids: List of data source config keys (or comma-separated
        string) to delete.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

### `get(self, connector_key: 'str') -> 'dict[str, Any]'`

Get details of a specific connector.

Args:
    connector_key: Key identifying the connector type (e.g., "postgres", "mysql").

Returns:
    Dict with connector details.

### `get_connection(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get details of a specific connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with connection details.

### `get_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a specific data source configuration.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with data source config details.

### `list(self) -> '_list[dict[str, Any]]'`

List all available connectors.

Returns:
    List of connector dicts.

### `list_connections(self, connector_key: 'str', project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List connections for a connector type.

Args:
    connector_key: Key identifying the connector type.
    project_id: Project ID (uses client default if not provided).

Returns:
    List of connection dicts.

### `list_ds_configs(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List data source configurations for a connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    project_id: Project ID (uses client default if not provided).

Returns:
    List of data source config dicts.

### `query_connection(self, connector_key: 'str', connection_key: 'str', query: 'str', *, table: 'str | None' = None, profile: 'str | None' = None, project_id: 'int | None' = None, timeout: 'float' = 60.0) -> 'dict[str, Any]'`

Run a query on a connection and return a sample of its rows.

This is ``create_ds_config`` with ``data_sample=True``: Mammoth sends the
query to the connected database with a row limit and hands the rows back.
It saves no data source configuration and creates no dataset; the only
record Mammoth keeps is the short-lived job that carried the request.
Mammoth does not make the query read-only: the database account of the
connection is what stops a write.

Args:
    connector_key: Key identifying the connector type (e.g. ``"postgres"``).
    connection_key: Key identifying the connection.
    query: The SQL to run.
    table: Optional table name hint.
    profile: Optional connector-specific profile (e.g. schema name).
    project_id: Project ID (uses client default if not provided).
    timeout: Seconds to wait for the database to answer.

Returns:
    Dict with ``data_sample`` (``dataschema`` and ``rows``).

Raises:
    MammothJobFailedError: If the database refuses the query.
    MammothJobTimeoutError: If it does not answer within *timeout*.

### `update_connection(self, connector_key: 'str', connection_key: 'str', credentials: 'dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a connection's credentials.

The backend expects a JSON-patch envelope:
``{"patch": [{"op": "replace", "path": "connection", "value": <credentials>}]}``.
This method accepts the raw credentials dict and wraps it internally.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    credentials: Non-empty dict of updated connection credentials. Shape
        is the same as for ``create_connection`` (varies by connector_key).
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with updated connection info.

Raises:
    MammothValidationError: If ``credentials`` is empty.

### `update_ds_config(self, connector_key: 'str', connection_key: 'str', ds_config_key: 'str', patch: '_list[DsConfigPatchOp]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a data source configuration via JSON-patch operations.

The backend accepts a patch envelope:
``{"patch": [{"op": "replace", "path": "<path>", "value": <value>}]}``.

Note: only ``path='query'`` is currently implemented on the backend;
``profile``, ``on_refresh_action``, and ``unique_sequence_column`` are
accepted by the SDK but the server returns ``not_implemented_error``.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    ds_config_key: Key identifying the data source config.
    patch: Non-empty list of :class:`~mammoth.models.connectors.DsConfigPatchOp`
        instances.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with updated config.

Raises:
    MammothValidationError: If ``patch`` is empty, any op is not
        ``"replace"``, or any path is not a valid
        :class:`~mammoth.models.connectors.DsConfigPatchPath` value.


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
    api_token="mm_your-token",
)
client.set_project_id(10)

view = await client.views.get(1039)
```

---

## Filtering and labeling

### Filter to high-value rows

```python
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
```

### Filter with multiple conditions

```python
# Keep rows where Sales >= 1000 AND Region is "West"
await view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)

# Remove rows where Status is empty
await view.filter_rows(
    Condition("Status", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)
```

### Create a label column

```python
await view.set_values(
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
await view.set_values(
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
await view.math("Price * Quantity", new_column="Total")
await view.math("(Price + Tax) * 1.1", new_column="Grand Total")
```

### Update an existing column

```python
await view.math("Sales * 1.1", existing_column="Sales")
```

### Conditional math

```python
await view.math(
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
customers = await client.views.get(2050)

await view.join(
    foreign_view=customers,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Customer Name", "Email", "Segment"],
)
```

### Join with column prefix

```python
products = await client.views.get(2051)

await view.join(
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
await view.pivot(
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
await view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(column="Sales", function=AggregateFunction.SUM),
)
```

---

## Window functions

### Row number / ranking

```python
await view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

### Running total

```python
await view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### Lag / lead

```python
await view.window(
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
await view.copy_columns([CopySpec(source="old_name", as_name="new_name")])
await view.delete_columns(["old_name"])
```

### Combine columns

```python
await view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### Split a column

```python
await view.split_column(
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
await view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Order Date", to=ColumnType.DATE),
])
```

---

## Text operations

### Change text case

```python
await view.text_transform(columns=["Name"], case=TextCase.UPPER)
await view.text_transform(columns=["Description"], case=TextCase.TITLE)
```

### Trim whitespace

```python
await view.text_transform(columns=["Name", "Email"], trim=True)
```

### Find and replace

```python
await view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### Bulk replace

```python
await view.bulk_replace(
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
await view.substring("Product Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
await view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

---

## Date operations

### Extract date parts

```python
await view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
await view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
await view.extract_date("Order Date", DateComponent.QUARTER, new_column="Quarter")
```

### Date difference

```python
await view.date_diff(
    DateDiffUnit.DAY,
    start="Ship Date",
    end="Delivery Date",
    new_column="Delivery Days",
)
```

### Increment a date

```python
await view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended Due")
```

---

## Row operations

### Remove duplicates

```python
await view.discard_duplicates()

# Ignore specific columns when checking for duplicates
await view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### Limit rows

```python
# Top 100 by sales
await view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])

# Bottom 10
await view.limit_rows(10, bottom=True, order_by=[["Sales", SortDirection.ASC]])
```

### Fill missing values

```python
# FIRST_VALUE carries the previous row's value down (forward fill);
# LAST_VALUE takes the next row's value (back-fill).
await view.fill_missing(
    "Price",
    direction=FillDirection.FIRST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### Unnest (unpivot)

```python
await view.unnest(
    columns=["Q1", "Q2", "Q3", "Q4"],
    label_column="Quarter",
    value_column="Revenue",
)
```

---

## Advanced operations

### Lookup from another view

```python
await view.lookup(
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
await view.json_extract("data", keys=["name", "email", "age"])

# With type control
await view.json_extract(
    "data",
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT),
        JsonExtractionSpec(key="score", as_name="Score", type=ColumnType.NUMERIC),
    ],
)

# JSON list to rows
await view.json_extract("items", json_type=JsonType.LIST)
```

### AI-powered transformation

```python
await view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### SQL

```python
# Generate SQL from natural language
# Returns the query only; the view does not change until add_sql
sql = await view.generate_sql("count employees by department and sort by count descending")
print(sql)
await view.add_sql(sql)

# Add raw SQL
await view.add_sql('SELECT region, SUM(sales) AS total FROM "view:123" GROUP BY region')
```

---

## Draft mode (batch transformations)

By default each transformation runs the pipeline immediately. Use draft mode to queue multiple tasks and run the pipeline once -- much faster for large datasets.

### Context manager (recommended)

```python
async with view.draft():
    await view.text_transform(columns=["Name", "Email"], trim=True)
    await view.convert_type([
        ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
        ConversionSpec(column="Order Date", to=ColumnType.DATE),
    ])
    await view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))
    await view.math("Price * Quantity", new_column="Revenue")
# Pipeline runs once for all 4 tasks
```

### Explicit enter/submit

```python
await view.enter_draft_mode()
await view.add_column("Notes")
await view.set_values(
    new_column="Flag",
    column_type=ColumnType.TEXT,
    values=[SetValue("Yes", condition=Condition("Sales", Operator.GTE, 10000)), SetValue("No")],
)
await view.submit_draft()  # runs pipeline, refreshes metadata
```

### Discard on error

If an exception occurs inside `async with view.draft():`, queued tasks are automatically discarded. You can also discard explicitly:

```python
await view.enter_draft_mode()
await view.add_column("Temp")
await view.discard_draft()  # reverts, "Temp" is not added
```

### Toggle auto-run

```python
await view.set_auto_run(False)   # enters draft mode, tasks queue without running
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
await view.math("Sales * 1.1", new_column="Adjusted")
await view.set_auto_run(True)    # re-enables auto-run
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

client = MammothClient(api_token="mm_...")
client.set_project_id(10)

# 1. Get the view
view = await client.views.get(1039)
print(f"Starting with {len(view.display_names)} columns")

# 2. Clean: trim whitespace, convert types
await view.text_transform(columns=["Customer Name", "Region"], trim=True)
await view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Order Date", to=ColumnType.DATE),
])

# 3. Filter: remove empty sales
await view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))

# 4. Transform: add calculated columns
await view.math("Price * Quantity", new_column="Revenue")
await view.set_values(
    new_column="Segment",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)

# 5. Aggregate
await view.pivot(
    group_by=["Region", "Segment"],
    aggregations=[
        AggregationSpec(column="Revenue", function=AggregateFunction.SUM, as_name="Total Revenue"),
        AggregationSpec(column="Revenue", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)

# 6. Export
await view.export.to_csv("revenue_summary.csv")
await view.export.to_postgres(
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
path = await view.export.to_csv("output.csv")

# Export to S3
await view.export.to_s3(file_name="report.csv")

# A public live link to the view (needs a plan with live links)
link = await view.export.to_live_link()   # {"url": "<the live link>"}

# Export to PostgreSQL
await view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales",
    username="user", password="pass",
)

# Branch out to another dataset
await view.branch_out(dest_dataset_id=42)

# List and delete exports
exports = await view.export.list()
await view.export.delete(exports[0]["id"])
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

    await view.export.to_csv("output.csv")
    await view.export.to_postgres(host="...", database="...", table="...")
    await view.export.list()

#### `to_csv(self, output_path: 'str | None' = None, timeout: 'int' = 300) -> 'Path'`

Download dataview data as a local CSV file.

Args:
    output_path: Local path for the output file. Auto-generated
        if not provided.
    timeout: Timeout in seconds (default 300).

Returns:
    :class:`~pathlib.Path` to the downloaded CSV file.

Example::

    path = await view.export.to_csv("output.csv")
    print(f"Downloaded to {path}")

#### `to_s3(self, file_name: 'str | None' = None, file_type: 'ExportFileType' = <ExportFileType.CSV: 'csv'>, include_hidden: 'bool' = False, **kwargs: 'Any') -> 'ExportResult'`

Export to S3 (Mammoth-managed bucket).

Args:
    file_name: Output filename. Auto-generated with timestamp if
        not provided.
    file_type: File format (default ``ExportFileType.CSV``).
        Supported formats: CSV, JSON, PARQUET.
    include_hidden: Include hidden columns (default False).
    **kwargs: Additional export options.

Returns:
    Export result dict with download URL.

Example::

    result = await view.export.to_s3(file_name="report.csv")
    await view.export.to_s3(file_type=ExportFileType.PARQUET)

#### `to_live_link(self, file_name: 'str | None' = None, file_type: 'ExportFileType' = <ExportFileType.CSV: 'csv'>, include_hidden: 'bool' = False, timeout: 'int | None' = None, **kwargs: 'Any') -> 'dict[str, Any]'`

Create a live link: a public URL that serves this view's latest data.

An S3 export (see :meth:`to_s3`) flagged ``liveLink``. The workspace
plan must include live links; otherwise the API's error is raised.

Args:
    file_name: Output filename (``<prefix>_<token>.<ext>``; the server
        replaces the token). Auto-generated when omitted.
    file_type: File format (default CSV).
    include_hidden: Include hidden columns (default False).
    timeout: Seconds to wait for the link (default: client job timeout).
    **kwargs: Additional export options, as for :meth:`to_s3`.

Returns:
    Dict with ``url``, the live link.

Raises:
    MammothExportError: If the finished export carries no URL.

#### `to_postgres(self, host: 'str', port: 'int', database: 'str', table: 'str', username: 'str', password: 'str', **kwargs: 'Any') -> 'ExportResult'`

Export to a PostgreSQL database.

Requires a pre-configured PostgreSQL instance accessible from
the Mammoth platform.

Args:
    host: Database host.
    port: Database port.
    database: Database name.
    table: Target table name.
    username: Database username.
    password: Database password.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, etc.).

Returns:
    Export result dict.

Example::

    await view.export.to_postgres(
        host="db.example.com", port=5432,
        database="analytics", table="sales_export",
        username="user", password="pass",
    )

#### `to_mysql(self, host: 'str', port: 'int', database: 'str', table: 'str', username: 'str', password: 'str', **kwargs: 'Any') -> 'ExportResult'`

Export to MySQL database.

Args:
    host: Database host.
    port: Database port.
    database: Database name.
    table: Target table name.
    username: Database username.
    password: Database password.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    Export result dict.

#### `to_dataset(self, dataset_name: 'str | None' = None, *, target_ds_id: 'int | None' = None, save_as_mode: 'SaveAsDatasetMode' = <SaveAsDatasetMode.REPLACE: 'REPLACE_IN_DS'>, column_mapping: 'dict[str, str] | None' = None, label_ids: 'list[int] | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None, timeout: 'int | None' = None, target_project_id: 'int | None' = None) -> 'int'`

Save this view's data as an internal Mammoth dataset (branch out).

Runs through the ``internal_dataset`` export handler; the awaited call
returns only once the dataset is materialised.

Args:
    dataset_name: Name for the new dataset (display name when writing
        into an existing one); omit to use the product default 'Result Dataset'
        (what the app's Branch out form uses).
    target_ds_id: Existing dataset to write into; None creates a new one.
    save_as_mode: Replace or append when writing the output dataset.
    column_mapping: Source -> destination column-name map (empty = all).
        Renames only: when ``target_ds_id`` is None (a new dataset),
        any view column left out of this map is kept under its
        current name automatically, so a rename-only map (for
        example ``{"petal_width": "width_cm"}``) still copies every
        other column instead of silently dropping them. Writing into
        an EXISTING dataset (``target_ds_id`` set) maps exactly the
        listed columns, as before -- there the caller is matching a
        specific target schema.
        With ``save_as_mode=APPEND_TO_DS`` leave it empty to match every
        column by name: the backend appends only the mapped columns of
        a non-empty map and turns an unknown destination into a new
        column, so a partial map leaves the other target cells NULL.
    label_ids: Folder/label ids for the new dataset.
    condition: Optional row filter applied before copying.
    timeout: Max seconds to wait for the job.
    target_project_id: Project to create (or find ``target_ds_id``) the
        dataset in when it is not this view's project. The export stays
        a pipeline step of this view, so the copy is refreshed whenever
        the pipeline re-runs -- a "parallel send" into another project.

Returns:
    The id of the dataset written to (new when ``target_ds_id`` is None,
    otherwise ``target_ds_id``).

Example::

    new_id = await view.export.to_dataset("Sales snapshot")
    sent = await view.export.to_dataset("Sales feed", target_project_id=57)

#### `to_ftp(self, domain: 'str', directory: 'str', file: 'str', username: 'str', password: 'str', port: 'int' = 21, **kwargs: 'Any') -> 'ExportResult'`

Export to an FTP server.

Args:
    domain: FTP server hostname.
    directory: Remote directory to write into.
    file: Remote filename to write.
    username: FTP username.
    password: FTP password.
    port: FTP port (default 21).
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

Example::

    await view.export.to_ftp(
        domain="ftp.example.com", directory="/exports",
        file="sales.csv", username="user", password="pass",
    )

#### `to_sftp(self, host: 'str', username: 'str', password: 'str' = '', directory: 'str' = '', file_name: 'str' = '', port: 'int' = 22, randomize_file_name: 'bool' = False, ssh_key_authentication: 'bool' = False, private_key: 'str' = '', passphrase: 'str' = '', **kwargs: 'Any') -> 'ExportResult'`

Export to an SFTP server.

Supports both password and private-key authentication. For key auth,
set *ssh_key_authentication* and provide *private_key* (PEM string)
plus an optional *passphrase*.

Args:
    host: SFTP server hostname.
    username: SFTP username.
    password: SFTP password (omit when using key auth).
    directory: Remote directory; defaults server-side to the user home.
    file_name: Output filename; defaults server-side to
        ``{dataset}_{view}.csv``.
    port: SFTP port (default 22).
    randomize_file_name: Append a random suffix to the filename.
    ssh_key_authentication: Authenticate with a private key.
    private_key: PEM-format private key string (key auth).
    passphrase: Passphrase protecting *private_key*, if any.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

Raises:
    MammothValidationError: If key authentication is requested without a
        ``private_key``.

#### `to_email(self, emails: 'list[str]', subject: 'str' = '', message: 'str' = '', resource: 'str' = '', **kwargs: 'Any') -> 'ExportResult'`

Export by emailing a download link to recipients.

Args:
    emails: Recipient email addresses.
    subject: Email subject (defaults server-side).
    message: Body message appended to the email.
    resource: Display name of the exported resource in the email.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

Example::

    await view.export.to_email(emails=["analyst@example.com"], subject="Q1")

Raises:
    MammothValidationError: If *emails* is empty.

#### `to_bigquery(self, selected_profile: 'dict[str, Any]', selected_identity: 'dict[str, Any]', table: 'str', export_type: 'BigQueryExportType' = <BigQueryExportType.REPLACE: 'REPLACE'>, upsert_keys: 'list[dict[str, Any]] | None' = None, partition: 'dict[str, Any] | None' = None, **kwargs: 'Any') -> 'ExportResult'`

Export to Google BigQuery.

Uses an existing Mammoth BigQuery integration; *selected_profile*
and *selected_identity* are obtained from that integration rather
than passed as raw credentials here.

Args:
    selected_profile: Project/dataset selection, shaped as
        ``{"name": "<dataset>", "value": [[project_id, dataset_id]]}``.
    selected_identity: Service-account identity config, shaped as
        ``{"identity_config": {...}, "host": "<sa-email>"}``.
    table: Destination table name.
    export_type: Write mode (REPLACE, COMBINE, or UPSERT).
    upsert_keys: Required when *export_type* is UPSERT — a list of
        ``{"column": {"display_name": "<col>"}}`` dicts.
    partition: Optional partitioning spec. For datetime partitioning,
        ``{"FIELD": str, "GRANULARITY": "DAY"|"MONTH"|"YEAR"}``; for
        integer-range partitioning, ``{"FIELD": str, "START": int,
        "END": int, "INTERVAL": int}``.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

Raises:
    MammothValidationError: If *export_type* is UPSERT but no
        *upsert_keys* are given.

#### `to_redshift(self, host: 'str', port: 'int', database: 'str', table: 'str', username: 'str', password: 'str', **kwargs: 'Any') -> 'ExportResult'`

Export to an Amazon Redshift cluster.

Data is staged through a Mammoth-managed S3 bucket and then
``COPY``-ed into the target table.

Args:
    host: Cluster endpoint host.
    port: Cluster port (Redshift default is 5439).
    database: Database name.
    table: Target table name.
    username: Database username.
    password: Database password.
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

#### `to_elasticsearch(self, host: 'str', username: 'str', password: 'str', index: 'str', port: 'int' = 9243, connection: 'str' = 'https', chunksize: 'int' = 200, **kwargs: 'Any') -> 'ExportResult'`

Export to an Elasticsearch index.

Args:
    host: Elasticsearch host.
    username: Auth username.
    password: Auth password.
    index: Destination index name.
    port: Port (default 9243).
    connection: Protocol, ``"http"`` or ``"https"`` (default).
    chunksize: Bulk-insert batch size (default 200).
    **kwargs: Additional export options (``trigger_type``,
        ``run_immediately``, ``validate_only``,
        ``end_of_pipeline``, ``additional_properties``,
        ``condition``).

Returns:
    The created export trigger record or its tracking job.

#### `publish_to_db(self, table: 'str', odbc_type: 'OdbcType' = <OdbcType.POSTGRES: 'postgres'>) -> 'dict[str, Any]'`

Publish this view to a Mammoth-managed database for dashboards.

Unlike the other export helpers, publish-to-db uses
Mammoth-managed connection credentials (configured once per
workspace) — you only name the target *table* and connection type.
It posts to the dedicated ``publish-to-db`` endpoint, not the
pipeline-exports endpoint.

Args:
    table: Destination table name.
    odbc_type: Managed connection type (postgres or bigquery).

Returns:
    Dict with the tracking ``job_id`` for the publish job.

Example::

    await view.export.publish_to_db(table="sales_dashboard")

#### `list(self) -> '_list[dict[str, Any]]'`

List all exports configured for this dataview.

Returns:
    List of export dicts, each with ``id``, ``handler_type``,
    ``target_properties``, etc.

Example::

    exports = await view.export.list()
    for exp in exports:
        print(f"{exp['id']}: {exp['handler_type']}")

#### `delete(self, export_id: 'int') -> 'dict[str, Any]'`

Delete an export configuration.

Args:
    export_id: ID of the export to delete (from ``list()``).

Returns:
    Deletion confirmation dict.

Example::

    exports = await view.export.list()
    await view.export.delete(exports[0]["id"])

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

#### `delete(self, dataview_id: 'int', export_id: 'int', skip_validation: 'bool | None' = None, dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a pipeline export.

Args:
    dataview_id: ID of the dataview (must be > 0).
    export_id: ID of the export (must be > 0).
    skip_validation: Skip server-side validation of the deletion (optional).
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the deletion result, or an empty dict if the server
    returns no content.

Raises:
    MammothValidationError: If *dataview_id* or *export_id* ≤ 0.

#### `export_hosts(self) -> 'ExportHostPolicyRead'`

Get the hosts this workspace's custom export destinations may send to.

Returns:
    ExportHostPolicyRead: ``restricted`` (True: only ``hosts`` are allowed),
    ``hosts`` and ``in_use`` (hosts saved exports already send to).

#### `get(self, dataview_id: 'int', export_id: 'int', fields: 'str | None' = None, dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a single pipeline export.

Args:
    dataview_id: ID of the dataview (must be > 0).
    export_id: ID of the export (must be > 0).
    fields: Comma-separated fields to return, or one of the presets
        ``"__full"``, ``"__standard"``, ``"__min"`` (optional).
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with export details.

Raises:
    MammothValidationError: If *dataview_id* or *export_id* ≤ 0.

#### `list(self, dataview_id: 'int', fields: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'ExportStatus | None' = None, reordered: 'bool | None' = None, handler_type: 'HandlerType | None' = None, end_of_pipeline: 'bool | None' = None, runnable: 'bool | None' = None, dataset_id: 'int | None' = None) -> 'PipelineExportsPaginated'`

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
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    PipelineExportsPaginated with paginated list of exports.

#### `publish_db(self, dataview_id: 'int', odbc_type: 'OdbcType', target_properties: 'dict[str, Any]', dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a publish-to-database subscription for a dataview.

Args:
    dataview_id: ID of the dataview (must be > 0).
    odbc_type: Managed-connection type of the destination database.
    target_properties: Destination properties, e.g. ``{"table": "my_table"}``.
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the created publish-to-db job/result.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

#### `publish_db_update(self, dataview_id: 'int', patch: '_list[dict[str, Any]]', dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a dataview's publish-to-database subscription via patch operations.

Args:
    dataview_id: ID of the dataview (must be > 0).
    patch: List of patch operation dicts, e.g.
        ``[{"op": "replace", "path": "credentials",
        "value": {"odbc_type": "postgres"}}]``.
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the updated publish-to-db job/result.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

#### `rest_fill(self, dataview_id: 'int', docs_url: 'str', notes: 'str' = '', wait: 'bool' = True, timeout: 'float | None' = None, dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Propose REST API export settings from an API documentation page.

The server reads *docs_url* and proposes form values for a REST API export
(never credentials). Nothing is configured or sent: review the suggestion, then
create the export yourself. The server fetches *docs_url*, so pass only a
documentation page you are happy for Mammoth to read.

Args:
    dataview_id: ID of the dataview (must be > 0).
    docs_url: URL of the API documentation to read.
    notes: Extra guidance for the suggestion (at most 2000 characters).
    wait: Wait for the job to finish (default True). False returns the queued job.
    timeout: Seconds to wait (uses ``client.job_timeout`` if not provided).
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    The job dict. When finished, ``response["suggestion"]`` holds the proposal.

Raises:
    MammothValidationError: If *dataview_id* <= 0, *docs_url* is empty or *notes*
        is longer than 2000 characters.
    MammothJobFailedError: If the job fails (when *wait* is True).
    MammothJobTimeoutError: If the job does not finish in time (when *wait* is True).

#### `runs(self, dataview_id: 'int', export_id: 'int', limit: 'int' = 20, dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'ExportRuns'`

Get the run history of a saved export, newest first.

Each run says when it started, how long it took, how many rows it sent, where
they went, what triggered it and, if it failed, the error.

Args:
    dataview_id: ID of the dataview (must be > 0).
    export_id: ID of the export (must be > 0).
    limit: Number of most recent runs to return (1-50, default 20).
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    ExportRuns with ``export_id`` and ``runs``.

Raises:
    MammothValidationError: If *dataview_id* or *export_id* <= 0, or *limit*
        is outside 1-50.

#### `set_export_hosts(self, restricted: 'bool', hosts: '_list[str] | None' = None) -> 'ExportHostPolicy'`

Set the hosts this workspace's custom export destinations may send to.

Replaces the whole policy. Workspace admins only.

Args:
    restricted: True to allow only *hosts*; False to allow any host.
    hosts: Allowed hosts (at most 100, none empty).

Returns:
    ExportHostPolicy as saved.

Raises:
    MammothValidationError: If *hosts* holds more than 100 entries or an empty one.

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

#### `to_csv_url(self, dataview_id: 'int', timeout: 'int' = 300, dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a CSV export and return its signed download URL, undownloaded.

Creates a CSV export job and waits for completion, like :meth:`to_csv`,
but never writes a local file -- for a caller (for example a host
process running the CLI on a user's behalf) that hands the URL to
someone else instead.

Args:
    dataview_id: ID of the dataview to export.
    timeout: Timeout in seconds (default 300).
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with ``url`` (the signed download URL), ``trigger_id`` if the
    job reports one, and ``job_id`` of the completed export job.

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

#### `update(self, dataview_id: 'int', export_id: 'int', patches: '_list[dict[str, Any]]', skip_validation: 'bool | None' = None, dataset_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Edit a pipeline export via patch operations.

Args:
    dataview_id: ID of the dataview (must be > 0).
    export_id: ID of the export (must be > 0).
    patches: List of patch operation dicts, e.g.
        ``[{"op": "command", "path": "suspend", "value": None}]``.
    skip_validation: Skip server-side validation of the patch (optional).
    dataset_id: ID of the dataset (auto-detected if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the updated export, or an empty dict if the server
    returns no content.

Raises:
    MammothValidationError: If *dataview_id* or *export_id* ≤ 0.

## See also

- [Views](#views-reference) -- View object and transformation methods
- [Client](#client-api-reference) -- sub-client overview


---


# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

```python
# List projects (one page; the route caps limit at 100)
projects = await client.projects.list()
page_two = await client.projects.list(offset=100)

# Every project across pages
all_projects = await client.projects.list_all()

# Get a specific project
project = await client.projects.get(project_id=10)

# Create a new project
await client.projects.create(name="My Project", properties={"description": "..."})
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

### `add_agent_memory(self, project_id: 'int', text: 'str', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Save one agent preference for the caller in a project.

Args:
    project_id: ID of the project (must be a positive integer).
    text: The preference, in the user's words.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``items``: the saved preferences after the add.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `add_users(self, project_id: 'int', user_ids: '_list[int]', role: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Add users to a project.

The route takes ``{"users": [{"user_id", "role"}]}``; users are
addressed by numeric id (see ``workspace user list``), not by email.

Args:
    project_id: ID of the project.
    user_ids: Numeric user ids to add.
    role: ``project_admin`` or ``project_analyst`` (server default
        ``project_analyst``) applied to every listed user.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with result.

### `browse(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, name: 'str | None' = None, browse_type: 'str | None' = None, sort: 'str | None' = None, offset: 'int | None' = None, limit: 'int | None' = None) -> 'dict[str, Any]'`

Browse project contents (datasets, folders).

.. note::

    This endpoint may return HTTP 500 on some server versions.

Args:
    project_id: ID of the project.
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Comma-separated list of fields to return.
    name: Filter by name.
    browse_type: Filter by resource type.
    sort: Sort specification.
    offset: Number of results to skip.
    limit: Maximum number of results.

Returns:
    Dict with project contents.

### `bulk_delete(self, project_ids: '_list[int]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk delete multiple projects.

Args:
    project_ids: List of project IDs to delete.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with bulk deletion result.

### `bulk_delete_and_verify(self, project_ids: '_list[int]', workspace_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0) -> 'dict[str, Any]'`

Bulk delete projects and verify every id is gone from the project list.

Raises:
    MammothDeletionVerificationError: some ids still listed at timeout.

### `bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk update multiple projects.

Args:
    patch_data: Patch operations for multiple projects.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with bulk update result.

### `checkpoint_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`

List pipeline checkpoints across all dataviews in a project.

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Fields to return (e.g., "__standard", "__full", "__min").
    sort: Sort specification.
    dataview_id: Filter to checkpoints for a specific dataview.
    sequence: Filter by pipeline task sequence number.
    status: Filter by checkpoint status.

Returns:
    Dict with the checkpoints list.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `copy(self, project_id: 'int', name: 'str', dataset_ids: '_list[int] | None' = None, include_dashboards: 'bool' = False, exclude_data: 'bool' = False, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Copy a project's datasets, views and pipelines into a new project (a write).

Runs as one background job; wait for it with ``client.wait_if_job``. The job's
result is ``{project_id, dataset_map, view_map, skipped, dashboards}``.

Args:
    project_id: ID of the source project (must be > 0).
    name: Name of the new project (1 to 63 characters).
    dataset_ids: Datasets of the source project to copy; ``None`` copies them all.
    include_dashboards: Also copy the dashboards built on the copied datasets.
    exclude_data: Copy every dataset's pipeline without its rows.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``job_id``, the copy job to wait for.

Raises:
    MammothValidationError: If *project_id* is not positive, *name* is not 1 to 63
        characters, or *dataset_ids* is an empty list.

### `create(self, name: 'str', color: 'str | None' = None, project_access: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new project.

Args:
    name: Name for the new project.
    color: Color hex code (e.g., "#337FBD"). Defaults to server-assigned color.
    project_access: Access level — "only_me", "some_members_of_workspace",
        or "all_members_of_workspace". Defaults to "only_me".
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with created project info including id, name, properties, etc.

### `data_check_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`

List data checks across all dataviews in a project.

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Fields to return (e.g., "__standard", "__full", "__min").
    sort: Sort specification.
    dataview_id: Filter to data checks for a specific dataview.
    sequence: Filter by pipeline task sequence number.
    status: Filter by data check status.

Returns:
    Dict with the data checks list.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `delete(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a project.

Args:
    project_id: ID of the project to delete.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with deletion result.

### `delete_and_verify(self, project_id: 'int', workspace_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0) -> 'dict[str, Any]'`

Delete one project and verify it is gone from the project list.

The route acknowledges with 202 and an empty body, so this polls the
list until the project is absent (bounded by the client job timeout).

Raises:
    MammothDeletionVerificationError: still listed when the timeout ends.

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

### `list(self, workspace_id: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0, fields: 'str' = 'id,name', include_non_members: 'bool' = False) -> 'dict[str, Any]'`

List one page of projects in a workspace.

By default only projects the caller is a member of are returned, which
is what the Mammoth UI shows. A workspace owner or admin can read
every project, but cannot open the ones they are not a member of.

The backend caps ``limit`` at :data:`MAX_PAGE_SIZE` (100) and rejects
larger values with a validation error; use :meth:`list_all` to walk
every page.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    limit: Maximum number of results (default and maximum 100).
    offset: Number of leading projects to skip (server-side).
    fields: Comma-separated project fields to return (default ``id,name``).
    include_non_members: Also return projects the caller is not a member
        of; every row then carries ``member`` (true/false).

Returns:
    Dict containing projects list with the requested fields, plus ``limit``,
    ``offset`` and ``next`` (empty when this is the last page).

### `list_agent_memory(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

List the caller's saved agent preferences for a project.

Reads the project's ``properties.agent_memory`` (the caller's own list).

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``items``: the saved preferences, oldest first.

Raises:
    MammothValidationError: If project_id is not a positive integer.
    ValueError: If the project is not visible to the caller.

### `list_all(self, workspace_id: 'int | None' = None, fields: 'str' = 'id,name', include_non_members: 'bool' = False) -> '_list[dict[str, Any]]'`

Return every project the caller is a member of, following the 100-row pages.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Comma-separated project fields to return (default ``id,name``).
    include_non_members: Also return projects the caller is not a member
        of; every row then carries ``member`` (true/false).

Returns:
    List of project dicts with the requested fields across all pages.

### `needs_attention(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Return the rows of the Monitor modal's "Needs Attention" tab, with dataset ids.

Same sources and filters as the web app (mm-frontend
``resources.storePinia.js`` ``fetchPipelineChanges`` and
``monitor-needs-attention.vue``), for the view-bearing rows:

- ``pipeline_error``: ``pending_changes`` entries with ``is_pipeline_in_error``.
- ``pending_pipeline``: the remaining ``pending_changes`` entries (draft steps).
- ``pending_data``: ``pending_data_update_items`` with ``data_update_pending``
  (one row per dependency; the web app groups JOIN/LOOKUP sources by destination).
- ``checkpoint``: project checkpoints with status ``needs_approval`` and type ``approval``.
- ``data_check``: project data checks with status ``failed``.
- ``needs_input``: ``ds_action_needed_items`` -- files and datasets waiting for a
  person; ``action`` says which (``unstructured_rows``, ``ambiguous_date_format``,
  ``password_required``, ``sheet_selection_required``, ``schema_mismatch``).

The web app also lists pending retentions, which the v2 route does not return, so
they are not included. Each row carries ``view_id`` and the owning ``dataset_id``
(null when the view is not found in the project), so a caller can act on the
datasets.

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``items``, ``datasets`` (unique, each with its ``view_ids``),
    ``counts`` per kind and ``unresolved_view_ids``.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `pending_changes(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get pending (uncommitted) changes for a project.

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict describing the project's pending changes.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `publish_credentials(self, project_id: 'int', odbc_type: "Literal['postgres', 'bigquery']", workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get ODBC publish credentials for a project.

Args:
    project_id: ID of the project (must be a positive integer).
    odbc_type: ODBC connector type — "postgres" or "bigquery".
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with the publish credentials.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `remove_agent_memory(self, project_id: 'int', index: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Remove one of the caller's saved agent preferences in a project.

Args:
    project_id: ID of the project (must be a positive integer).
    index: Zero-based position of the preference in ``list_agent_memory``.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``items``: the saved preferences after the removal.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Remove users from a project.

Args:
    project_id: ID of the project.
    user_ids: List of user IDs to remove (one DELETE per user).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with the last removal's result.

Raises:
    MammothValidationError: If ``user_ids`` is empty.

### `resource_dependencies(self, project_id: 'int', resource_ids: '_list[str]', is_recursive: 'bool | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the dependency graph for a set of resources in a project.

Args:
    project_id: ID of the project (must be a positive integer).
    resource_ids: Resource IDs to look up dependencies for.
    is_recursive: Recursively traverse the dependency graph.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict keyed by resource_id with each resource's dependency graph.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `resource_dependencies_update(self, project_id: 'int', patches: '_list[DataSyncPatchItem]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Apply typed data-sync patches to resources in a project.

The release API accepts one or more ``data_sync`` replacements and
returns a job handle (HTTP 202). The CLI owns waiting and confirmation;
this SDK method only validates/serializes the public request and emits
the exact PATCH wire contract.

### `resource_status(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Get resource status summary for a project.

Args:
    project_id: ID of the project (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with the project's resource status summary.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `sample_flow(self, project_id: 'int', label_resource_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a sample flow: ingest a sample file into the project.

Args:
    project_id: ID of the project (must be a positive integer).
    label_resource_id: Parent folder resource ID to place the imported
        file under (optional; defaults to the project root).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with the created sample file's name and ingestion job_id.

Raises:
    MammothValidationError: If project_id is not a positive integer.

### `update(self, project_id: 'int', name: 'str | None' = None, color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a project.

.. note::

    Requires admin role — non-admin users receive HTTP 401.

Args:
    project_id: ID of the project to update.
    name: New name (optional).
    color: New color code (optional).
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated project info.

### `user_update(self, project_id: 'int', role: "Literal['project_admin', 'project_analyst']", user_id: 'int | None' = None, invite_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a project user's or pending invite's role.

Exactly one of *user_id* or *invite_id* must be given to identify the
target of the role change.

Args:
    project_id: ID of the project (must be a positive integer).
    role: New role — "project_admin" or "project_analyst".
    user_id: ID of the existing project user to update.
    invite_id: ID of the pending invite to update.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with the update result.

Raises:
    MammothValidationError: If project_id is not a positive integer, or
        if *user_id* and *invite_id* are not given exactly one at a time.


---


# Datasets API Reference

The `DatasetsAPI` manages datasets within a project. A dataset is a data table stored in Mammoth, created from file uploads, connectors, or cloning.

**Access**: `client.datasets`

```python
# List datasets in the current project
datasets = await client.datasets.list()

# Get a specific dataset
ds = await client.datasets.get(dataset_id=42)
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

### `add_definition(self, dataset_id: 'int', term: 'str', definition: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Save what *term* means for a dataset; a definition of the same term is replaced.

The term matches case-insensitively. A dataset holds at most 20 definitions;
over that the server answers ``4DSET076``.

Args:
    dataset_id: ID of the dataset.
    term: The term, 1-60 characters (for example ``late``).
    definition: What it means for this data, 1-300 characters.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``dataset_id`` and the dataset's ``definitions`` after the save.

### `bulk_delete(self, dataset_ids: '_list[int] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`

Delete several datasets by id (bulk operation).

Args:
    dataset_ids: Ids of the datasets to delete (sent as the ``ids``
        query parameter). Required: the route has no delete-all form
        and rejects an empty id list.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

### `bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update multiple datasets (bulk operation).

The plural route accepts one ``DatasetsPatchOperation``; to rename
several datasets at once pass
``{"op": "replace", "path": "name", "value": {"12": "a", "13": "b"}}``.

Args:
    patch_data: One patch operation object, sent as ``{"patch": patch_data}``.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with bulk update result.

### `column_stats(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Read every column's blank count, type and distinct count for the project's datasets.

One call for the whole project. The figures come from the stats the platform stored
at the last load or pipeline run, so nothing is profiled or run.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``datasets``, newest first: ``{id, name, rows, columns}``, each column
    ``{name, type, blank_count, blank_pct, distinct}`` (``blank_pct`` is 0-100).
    ``rows`` and ``distinct`` are ``None`` when the platform has not stored them.

### `confirm_interpretation(self, dataset_id: 'int', instruction: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Apply the reading last previewed for this instruction.

The plan itself is never sent: it carries SQL, which would then run
unchecked. An empty ``structure_map`` is what tells the route to re-read
the plan its own preview saved, rather than working the instruction out
again and possibly answering differently.

Args:
    dataset_id: ID of the dataset.
    instruction: The same instruction the preview was asked for.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

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

### `create_from_pdf(self, file_object_id: 'int', file_name: 'str', file_id: 'str | None' = None, table_list: '_list[int] | None' = None, delete_file_after_extract: 'bool' = False, is_preview_needed: 'bool | None' = None, user_instruction: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create one or more datasets from tables extracted out of a PDF file.

Args:
    file_object_id: Internal ID of the uploaded PDF file object (must be > 0).
    file_name: Original name of the uploaded PDF file.
    file_id: Unique identifier for the uploaded PDF file in pdf2csv (optional).
    table_list: Indices of the tables to extract and convert into datasets
        (optional; all tables are extracted if not provided).
    delete_file_after_extract: Delete the file from storage after
        extraction completes (default False).
    is_preview_needed: Whether a preview is required before dataset
        creation (optional).
    user_instruction: User-provided instruction for custom extraction
        logic (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with created dataset(s) information (may include a job ID for
    async extraction).

Raises:
    MammothValidationError: If *file_object_id* ≤ 0.

### `delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a dataset.

Args:
    dataset_id: ID of the dataset to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

### `delete_and_verify(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, *, timeout: 'int | None' = None, poll_interval: 'float' = 2.0, dependencies: 'Sequence[str] | None' = None) -> 'dict[str, Any]'`

Delete one dataset and verify its supported GET readback is absent.

``dependencies`` is an optional caller-supplied dependency record. It
is deliberately not inferred from arbitrary inventory differences. If
known dependents are supplied, the operation is blocked before DELETE;
callers must explicitly remove owned dependents first.

### `file_settings_undo(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Undo the last file data settings change for a dataset.

Args:
    dataset_id: ID of the dataset (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the restored file settings.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0.

### `file_settings_update(self, dataset_id: 'int', delimiter: 'str', has_header: 'bool', initial_skip_count: 'int', quotechar: 'str', date_format: 'str | None' = None, preview_mode: 'bool' = False, skip_auto_process_check: 'bool' = True, date_formats: 'dict[str, str] | None' = None, set_project_level_date_format: 'bool' = False, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update file data settings for a dataset (delimiter, header, dates, ...).

Args:
    dataset_id: ID of the dataset (must be > 0).
    delimiter: Delimiter used in the file (one of ``,``, ``\t``, ``|``, ``;``).
    has_header: Whether the file has a header row.
    initial_skip_count: Number of initial rows to skip in the file.
    quotechar: Quote character used in the file (one of ``'``, ``"``, ``""``).
    date_format: Default date format used in the source file, e.g. "US"
        or "UK" (optional).
    preview_mode: Whether to preview the changes before applying (default False).
    skip_auto_process_check: Whether to skip the automatic processing
        check (default True).
    date_formats: Per-column date format overrides, e.g.
        ``{"column_3": "UK"}`` (optional).
    set_project_level_date_format: Whether to set the date format at the
        project level (default False).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with updated file settings.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0.

### `get(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

Get dataset details by ID.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    fields: Comma-separated fields to return, or "__min" / "__standard" /
        "__full" (default: the standard set).

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

### `get_batch_data(self, dataset_id: 'int', batch_id: 'int', columns: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`

Get data for a batch; the API returns an asynchronous job.

### `get_data(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int' = 300, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`

Get the actual data from a dataset. Polls the job until completion.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    timeout: Maximum wait time in seconds (default 300).
    poll_interval: Seconds between job polls (default:
        client.job_poll_seconds).

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

### `get_unstructured_rows(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the lines of a file that did not fit the dataset built from it.

A file whose rows are ragged is read as far as it can be, and the lines
that did not fit are set aside. The dataset then holds data and still
waits, because nobody has said what to do about them.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``unstructured_rows`` (each with its line, line number and
    the reason it did not fit) and ``row_count``.

### `interpretation_confirm(self, dataset_id: 'int', user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None, destination_dataset_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, mode: 'str | None' = None) -> 'dict[str, Any]'`

Apply an interpretation to the whole file and finalise the dataset.

Moves the dataset out of the state where its file has more than one plausible
reading. Pass the ``structure_map`` a preview returned, or the same
``user_instruction``; or ``mode="original"`` to keep the file in the layout
it was uploaded in (later files for the dataset are then ingested the same
way, without review).

Args:
    dataset_id: ID of the dataset (must be > 0).
    user_instruction: Plain-English description of how to read the file.
    structure_map: The confirmed SheetStructureMap.
    destination_dataset_id: Replay the saved recipe of this destination dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    mode: ``"interpreted"`` (the default: apply the reviewed reshape) or
        ``"original"`` (keep the uploaded layout; takes no reshape inputs).

Returns:
    Dict, empty when the backend answers with no body.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0, *mode* is not one of the
        two, or ``mode="original"`` comes with a reshape input.

### `interpretation_preview(self, dataset_id: 'int', user_instruction: 'str | None' = None, structure_map: 'dict[str, Any] | None' = None, destination_dataset_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Preview how a file that could be read several ways would look once interpreted.

Applies a plain-English instruction (for example one of the dataset's stored
suggestions, "Skip preamble rows, row 5 is the header") or a ready structure
map to the cached sample rows. Nothing is finalised; the dataset stays as it is.

Args:
    dataset_id: ID of the dataset (must be > 0).
    user_instruction: Plain-English description of how to read the file.
    structure_map: A SheetStructureMap from an earlier preview; no model call.
    destination_dataset_id: Replay the saved recipe of this destination dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``preview_rows``, ``total_row_count``, ``structure_map`` and
    ``header_types``.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0.

### `list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0, sort: 'str' = '(created_at:desc)', fields: 'str' = 'id,name') -> 'dict[str, Any]'`

Get list of datasets in a project.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    limit: Maximum number of results (default 100).
    offset: Number of results to skip (default 0).
    sort: Sort order (default "(created_at:desc)").
    fields: Comma-separated dataset fields to return, or "__min" /
        "__standard" / "__full" (default "id,name"). ``stats`` carries
        the row/column counts, ``data_schema`` the column names and types,
        ``sources`` how the dataset was made, plus ``created_at`` and
        ``updated_at``.

Returns:
    Dict containing datasets list with the requested fields.

### `list_all(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)', max_pages: 'int' = 1000, fields: 'str' = 'id,name') -> 'dict[str, Any]'`

List all datasets with bounded, progress-checked pagination.

The server's supported ``offset``/``next`` contract is used directly.
Repeated pages, empty pages carrying ``next``, non-advancing hints and
unbounded continuation raise :class:`MammothPaginationError` instead
of silently claiming complete inventory coverage.

### `list_batches(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    List of batch dicts.

### `list_definitions(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

List what terms mean for a dataset, as saved by its users.

A definition is shared by every chat on the dataset; the in-app agent reads
the project's definitions in each turn.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``dataset_id`` and ``definitions``: ``{id, term, definition,
    created_by, created_at}`` each, oldest first.

### `preview_interpretation(self, dataset_id: 'int', instruction: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Show how a file would be read differently, without changing it.

A file that has more than one plausible reading — a title above the
header, say, or two rows of headers — is read one way and left waiting.
This asks for another reading in words and shows what it would give.

Args:
    dataset_id: ID of the dataset.
    instruction: How to read the file, in plain words.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict describing the reading: the columns it would give and a sample.

### `remove_definition(self, dataset_id: 'int', definition_id: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Remove one definition from a dataset by its id.

An id the dataset does not hold is answered with ``4DSET077``.

Args:
    dataset_id: ID of the dataset.
    definition_id: The definition's ``id`` from :meth:`list_definitions`.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``dataset_id`` and the dataset's remaining ``definitions``.

### `rename(self, dataset_id: 'int', name: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None, unique: 'bool' = False) -> 'dict[str, Any]'`

Rename a dataset.

Sends ``PATCH /datasets/{dataset_id}`` with the OpenAPI
``DatasetPatchOperation`` ``{"op": "replace", "path": "name",
"value": name}``.

Args:
    dataset_id: ID of the dataset to rename.
    name: New name for the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    unique: When true the server picks a free name (``name 2``, ``name 3``...)
        if ``name`` is taken, as dataset creation does. The result's ``name``
        is the name applied.

Returns:
    Dict with update result.

### `resolve_unstructured_rows(self, dataset_id: 'int', op: "Literal['add', 'remove']", batch_id: 'int', rows: 'list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Take corrected set-aside lines into the dataset, or discard them.

Runs as a job; once no set-aside line remains the dataset is finished.
Discarded lines do not come back: a line worth keeping has to be
corrected (``add``) or fixed in the source file and uploaded again.

Args:
    dataset_id: ID of the dataset.
    op: ``"add"`` to take the corrected lines in, ``"remove"`` to discard them.
    batch_id: Upload the lines came from (``batch_id`` of each row from
        :meth:`get_unstructured_rows`).
    rows: ``{"line_num": int, "line": str}`` entries. ``line`` is the
        corrected text for ``add`` and is ignored for ``remove``.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    The job record (``id``, ``status``, ...); wait on it before reading the dataset.

Raises:
    MammothValidationError: If *dataset_id* <= 0 or *rows* is empty.

### `restore(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Restore a trashed dataset.

Args:
    dataset_id: ID of the dataset (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with restore result.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0.

### `search(self, term: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Find the project's datasets whose name, column names or sampled values hold ``term``.

Sampled values are the per-column samples the profiler keeps, so a dataset that was
never profiled matches on its name and column names only.

Args:
    term: Text to look for (case-insensitive substring, at least 2 characters).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``datasets``: ``{id, name, matches}``, each match naming where it was
    found (``found_in`` is ``name``, ``column`` or ``value``) with its ``column`` and
    ``value``.

### `trash(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Move a dataset to trash.

Args:
    dataset_id: ID of the dataset (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with trash result.

Raises:
    MammothValidationError: If *dataset_id* ≤ 0.

### `update(self, patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Send raw patch operations to the plural ``/datasets`` endpoint.

This is a low-level passthrough; the payload is sent as
``{"patch": patch_data}`` without validation. The current OpenAPI
contract for this route (``DatasetsPatchOperation``) accepts a single
``{"op": "replace", "path": "name", "value": {"<dataset_id>": "<new
name>"}}`` object, so most callers want :meth:`rename` (one dataset)
or :meth:`bulk_update` (several datasets) instead.

Args:
    patch_data: Patch payload, passed through unchanged.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with update result.


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

### `aggregate(self, dataset_id: 'int', dataview_id: 'int', aggregations: '_list[dict[str, Any]] | None' = None, group_by: '_list[str | dict[str, Any]] | None' = None, metric: 'dict[str, Any] | None' = None, condition: 'dict[str, Any] | None' = None, sequence: 'int | None' = None, limit: 'int | None' = None, sort: '_list[_list[str]] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`

Run a read-only aggregation query against a dataview (POST .../data/query).

This is a volatile query: it computes and returns an aggregated result
(a PIVOT group-by, or a single METRIC value) without adding a task to
the view's pipeline or otherwise changing it — unlike :meth:`View.pivot`,
which adds a PIVOT task. Exactly one of *aggregations* or *metric* is
required.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    aggregations: One or more ``{"column": ..., "function": ...,
        "as_name": ...}`` dicts for a PIVOT query (mutually exclusive
        with *metric*). ``function`` is one of SUM, COUNT, AVG, MIN,
        MAX; ``column`` is required unless ``function`` is COUNT;
        ``as_name`` defaults to ``f"{function}_{column}"``.
    group_by: Columns to group the PIVOT by (optional; a PIVOT with no
        ``group_by`` aggregates the whole view into one row). Each
        entry is either a plain column name, or a ``{"column": ...,
        "truncate": ...}`` dict bucketing a DATE column by truncation
        level (one of SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER,
        YEAR, DECADE, CENTURY, MILLENNIUM, AUTO), or a ``{"column":
        ..., "resolution": ...}`` dict bucketing a NUMERIC column by
        resolution level.
    metric: A single ``{"column": ..., "function": ..., "as_name": ...}``
        dict for a METRIC query (mutually exclusive with
        *aggregations*/*group_by*), same shape as an *aggregations* entry.
    condition: Filter condition dict applied before aggregating (optional).
    sequence: Pipeline step to read data at (default: latest).
    limit: Maximum number of result rows to return (optional). Without
        *sort* the rows kept are arbitrary, not the top ones.
    sort: Up to three ``[result_column, "ASC"|"DESC"]`` pairs, applied by
        the backend before *limit*. ``result_column`` is the internal name
        of a result column: ``agg_<n>`` for the n-th aggregation, ``group_<n>``
        for the n-th group_by entry, ``metric`` for a METRIC.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    timeout: Max job wait time in seconds (default: client.job_timeout).
    poll_interval: Seconds between job polls (default: 2).

Returns:
    Dict with the aggregated result rows.

Raises:
    MammothValidationError: If neither or both of *aggregations*/
        *group_by* and *metric* are given, if a *function* is not one
        of SUM, COUNT, AVG, MIN, MAX, STDDEV, DISTINCT_COUNT, or if *column* is missing
        for a non-COUNT aggregation.

Example::

    await client.dataviews.aggregate(
        dataset_id=500, dataview_id=42,
        group_by=["Channel"],
        aggregations=[{"column": "Spend", "function": "SUM", "as_name": "Total Spend"}],
    )

### `analysis(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

List pipeline steps that can be dropped or moved without changing the result.

Read only. Each finding says whether the change provably preserves results.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``findings``: a list of ``{rule, seqs, detail, proposed_order, safe}``.

### `apply_exportable_config(self, dataset_id: 'int', dataview_id: 'int', *, items: '_list[dict[str, Any]] | None' = None, config: 'dict[str, Any] | None' = None, insert_after_sequence: 'int | None' = None, is_paste_mode: 'bool' = False, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Apply exactly one of items or full config.

### `bulk_delete(self, dataset_id: 'int', dataview_ids: '_list[int] | str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete multiple dataviews.

Args:
    dataset_id: ID of the dataset.
    dataview_ids: List of dataview IDs or comma-separated string.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with bulk deletion result.

### `compare(self, pairs: '_list[_list[int]]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Compare dataviews pairwise: row counts, column differences and checksums (read only).

Args:
    pairs: 1 to 20 ``[view_a, view_b]`` pairs of dataview ids.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with ``results``, one entry per pair in request order: ``view_a``,
    ``view_b``, ``status`` (``ok``, ``not_ready`` or ``not_comparable``),
    ``problem_views``, ``rows_a``, ``rows_b``, ``columns_only_in_a``,
    ``columns_only_in_b``, ``checksum_a``, ``checksum_b``, ``equal`` and
    ``mismatched_columns``.

Raises:
    MammothValidationError: If *pairs* is empty, has over 20 entries, or an entry
        is not two positive ids.

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

### `conditional_format_delete(self, dataset_id: 'int', dataview_id: 'int', rule_id: 'str | int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete one conditional formatting rule.

The route requires the ``rule_id`` query parameter (from
:meth:`conditional_format_list`); there is no delete-all form.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    rule_id: ID of the rule to delete.
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
    List of conditional format rule dicts. The release route returns
    the rules as a mapping keyed by rule id; each returned dict
    carries that key as ``rule_id`` (the value
    :meth:`conditional_format_delete` needs).

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
    Dict with ``"dataview_id"`` key containing the new dataview's ID.

### `delete(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Delete a dataview.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with deletion result.

### `delete_impact(self, dataset_id: 'int', dataview_id: 'int', scope: 'str', task_id: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

List what deleting a pipeline task or a whole view would affect (read only).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    scope: ``"task"`` for one pipeline task (then *task_id* is required) or
        ``"view"`` for the whole view.
    task_id: ID of the task, for ``scope="task"``.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the affected ``dashboards``, ``exports``, ``views`` (dependent
    dataviews) and ``automations``, plus ``dependencies`` when the scope is a task.

Raises:
    MammothValidationError: If *scope* is not ``task`` or ``view``, or a task
        scope has no *task_id*.

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

### `explore(self, dataset_id: 'int', dataview_id: 'int', column: 'str', column_type: 'str | None' = None, level: 'str | None' = None, metric: 'dict[str, Any] | None' = None, condition: 'dict[str, Any] | None' = None, sequence: 'int | None' = None, limit: 'int | None' = None, offset: 'int | None' = None, sort: 'str | None' = None, cumulative: 'bool' = False, percentage_of: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2) -> 'dict[str, Any]'`

Explore one column: trend/distribution/top values (a PIVOT convenience).

A read-only wrapper over :meth:`aggregate` that buckets *column* by its
type the way the web app's Explore card does: a DATE column by
``level`` truncation (default "AUTO"), a NUMERIC column by ``level``
resolution (default "AUTO"), and any other column (TEXT) by its own
distinct values. Every bucket carries a ``count`` and a ``percentage``
of the column's total (computed locally, against every bucket the
query returns, never just a page truncated by *limit*). An optional
*metric* adds a second aggregation over another column.

Buckets are ordered the way the Explore card orders them: a DATE or
NUMERIC bucket ascending (a trend or distribution reads left to
right); a TEXT top-values list by ``count`` descending, defaulting to
the top 20 when no *limit* is given. A DATE/NUMERIC result returns
every bucket unless *limit* is given.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    column: Column to explore (internal name).
    column_type: The column's type ("DATE", "NUMERIC", or "TEXT"/None);
        selects the bucketing and ordering strategy.
    level: Truncation level (DATE) or resolution level (NUMERIC);
        ignored for other column types. Defaults to "AUTO".
    metric: An optional ``{"column": ..., "function": ..., "as_name":
        ...}`` dict (SUM, COUNT, AVG, MIN, MAX, STDDEV or DISTINCT_COUNT) computed per
        bucket in addition to the COUNT.
    condition: Filter condition dict applied before exploring (optional).
    sequence: Pipeline step to read data at (default: latest).
    limit: Maximum number of buckets to return (default: 20 for TEXT,
        unlimited for DATE/NUMERIC).
    offset: Buckets to skip first ("load more"; default 0).
    sort: count_desc, count_asc, value_asc, value_desc, metric_desc or
        metric_asc (default: count_desc for TEXT, value_asc for
        DATE/NUMERIC). The ``metric_*`` orders rank by *metric*.
    percentage_of: ``"count"`` (default) or ``"metric"``: what each
        bucket's ``percentage`` is a share of. ``"metric"`` needs *metric*.
    cumulative: Add a ``cumulative`` running total per bucket (of the
        *metric* when given, else of the count), over every bucket in
        ascending bucket order, before any *sort*/*limit* is applied.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    timeout: Max job wait time in seconds (default: client.job_timeout).
    poll_interval: Seconds between job polls (default: 2).

Returns:
    Dict with one result row per bucket.

Raises:
    MammothValidationError: If *level* is not one of the backend's
        allowed date-truncation levels, or (from :meth:`aggregate`) if
        *metric*'s function is unsupported.

Example::

    await client.dataviews.explore(
        dataset_id=500, dataview_id=42,
        column="column_3", column_type="DATE", level="MONTH",
    )

### `explore_panel(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the Explore panel the caller saved on a dataview (their own, not shared).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    The saved panel, for example ``{"open": True, "items": [{"column": "column_1",
    "renderType": "chart", "selectedAggregation": {...}}]}``; ``{}`` when the caller
    saved none.

### `get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, sequence: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

Get dataview information.

Metadata is scoped to a pipeline task *sequence*. Omitting it leaves
the choice to the API, which reads the last task in the pipeline, so
the returned ``metadata`` reflects every pipeline-derived column (math,
add_column, etc.). Pass ``sequence=0`` for the original dataset columns.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    sequence: Pipeline step to read metadata at. Omit to let the
        API read the last task in the pipeline.
    fields: Field set to return (e.g. ``"__full"``); server default if omitted.

Returns:
    Dict with complete dataview information.

### `get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'float | None' = None, sequence: 'int | None' = None, raw: 'bool' = False) -> 'dict[str, Any]'`

Get dataview data (GET method).

Data is scoped to a pipeline task *sequence*. When ``sequence`` is
omitted it defaults to the latest task sequence, so rows include every
pipeline-derived column. Pass ``sequence=0`` for the original dataset.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    timeout: Max job wait time in seconds (default: client.job_timeout).
    poll_interval: Seconds between job polls (default:
        client.job_poll_seconds).
    sequence: Pipeline step to read data at (default: latest).
    raw: When true, DATE values carry their time (``2026-10-04 16:00:00``)
        instead of the date alone. Sent to the backend as ``raw``.

Returns:
    Dict with dataview data.

### `get_exportable_config(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the pipeline/export configuration for a dataview.

### `list(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)', offset: 'int' = 0) -> 'dict[str, Any]'`

Get list of dataviews in a dataset.

Args:
    dataset_id: ID of the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    limit: Maximum number of results (default 100).
    sort: Sort order (default "(created_at:desc)").
    offset: Number of dataviews to skip (default 0).

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

### `optimize(self, dataset_id: 'int', dataview_id: 'int', apply_rules: '_list[str] | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Apply the safe pipeline findings of :meth:`analysis` (a write; reruns the pipeline).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    apply_rules: Rules to apply (``drop_suspended``, ``drop_duplicate``,
        ``drop_noop_filter``, ``hoist_filter``); ``None`` applies every safe finding.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``applied``, ``skipped`` (``{rule, seqs, reason}``), ``before_steps``,
    ``after_steps`` and ``job_id`` (the rerun, when one was queued).

Raises:
    MammothValidationError: If a rule is not one of the four known rules.

### `parameter_context(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the parameter context available to a dataview's pipeline.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the available parameter context.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

### `preview(self, dataset_id: 'int', dataview_id: 'int', rows: 'int | None' = None, cols: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a lightweight preview of a dataview's data.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview (must be > 0).
    rows: Maximum number of rows to include in the preview (optional).
    cols: Maximum number of columns to include in the preview (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the preview data.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

### `query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int | None' = None, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, raw: 'bool' = False) -> 'dict[str, Any]'`

Get dataview data with filtering options (POST method).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    sequence: Pipeline step to fetch data at. Omit to let the API
        read the last task in the pipeline; pass ``0`` for the
        original dataset.
    offset: One-indexed starting row (default 1).
    limit: Number of rows to fetch (default 400).
    columns: List of column names to fetch (optional).
    condition: Filter condition dict (optional).
    sort: Sort specification string (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    raw: When true, DATE values carry their time (``2026-10-04 16:00:00``)
        instead of the date alone. Sent to the backend as ``raw``.

Returns:
    Dict with filtered dataview data.

### `restore(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Restore a trashed dataview.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with restore result.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

### `set_explore_panel(self, dataset_id: 'int', dataview_id: 'int', panel: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Replace the caller's saved Explore panel on a dataview.

The whole panel is replaced, so read it with :meth:`explore_panel` first, change
its ``items`` and write it back. It is a per-user preference: nobody else sees it.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    panel: The new panel (``open`` and ``items``), as :meth:`explore_panel` returns it.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with the patch result.

Raises:
    ValueError: If ``panel`` is not a dict.

### `summary(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Summarise what a view has had done to it and where it goes.

Read only, from the database alone (no model call): the Summary panel of a view.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with ``transformations``, ``actions``, ``data_out`` (exports and sends),
    ``dashboards`` (lists of dicts) and ``result`` (dict or None).

Raises:
    MammothValidationError: If *dataview_id* <= 0.

### `trash(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Move a dataview to trash.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview (must be > 0).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with trash result.

Raises:
    MammothValidationError: If *dataview_id* ≤ 0.

### `update(self, dataset_id: 'int', dataview_id: 'int', patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update dataview properties using JSON Patch operations.

Each operation in ``patch_data`` should have ``op``, ``path``, and
``value`` keys following JSON Patch conventions.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview to update.
    patch_data: List of patch operations.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with update result.

Example::

    await client.dataviews.update(
        dataset_id=123, dataview_id=456,
        patch_data=[{"op": "replace", "path": "name", "value": "Renamed"}],
    )


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

### `add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any] | list[dict[str, Any]]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Add a new transformation task, or a list of them, to the pipeline.

A list is sent as one request: the server adds every task with auto-run
paused and runs the pipeline once, after the last.

Args:
    dataview_id: ID of the dataview.
    task_spec: Task specification dict (varies by task type), or a list of them.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with created task info or job info.

### `command(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Execute a draft-mode command on a dataview's pipeline.

This wraps the OpenAPI ``ExecutePipelineDraftCommand`` operation, which
is the same ``.../draft-mode`` endpoint used by :meth:`draft_mode`.

Args:
    dataview_id: ID of the dataview.
    command: Draft mode command ("enter", "exit", "submit", "discard").
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Draft mode state dict.

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
    command: Draft mode command ("enter", "exit", "submit", "discard").
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Draft mode state dict.

### `edit_pipeline(self, dataview_id: 'int', patches: '_list[dict[str, Any]]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

PATCH pipeline with operations (auto_run, run, reset, etc.).

Args:
    dataview_id: ID of the dataview.
    patches: List of patch operation dicts.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Updated pipeline state dict.

### `find_dataset_for_dataview(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`

Public typed resolver: find the dataset that contains a dataview.

This is the supported public seam for dataview-to-dataset resolution.
Callers must not reach into the private ``_find_dataset_for_dataview``
helper across sub-clients.

Args:
    dataview_id: ID of the dataview to resolve.
    dataset_id: Known parent dataset ID. This is an identity hint,
        not a request to search: it is returned as-is so callers do
        not probe unrelated datasets.

Returns:
    The dataset_id that contains this dataview.

### `get_draft_status(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Read server-backed draft state for a dataview pipeline.

Draft state must be read from the server so it is consistent across
separate processes. This reads the current pipeline and reports whether
the dataview is in draft mode, using the server's own pipeline state
rather than any process-local flag.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    A dict with ``dataview_id``, ``is_draft``, and the raw pipeline
    ``draft`` section when the server provides one.

### `get_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get pipeline state for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Pipeline state dict.

### `get_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get a specific pipeline task.

Requests ``__full`` fields; see :meth:`list_tasks` for why.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Task details dict.

### `items(self, dataview_id: 'int', dataset_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`

Get pipeline items (tasks and exports, interleaved) for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).
    fields: Fields to return (e.g., "__standard", "__full", "__min").
    limit: Maximum number of results.
    offset: Number of results to skip.
    sort: Sort specification.
    sequence: Filter to a specific pipeline task sequence number.
    status: Filter by item status.

Returns:
    Dict with the pipeline items list.

### `items_all(self, dataview_id: 'int', dataset_id: 'int', fields: 'str | None' = None, limit: 'int' = 100, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'str | None' = None, max_pages: 'int' = 1000) -> 'dict[str, Any]'`

Read the complete bounded pipeline-item listing.

``items`` intentionally mirrors the CLI's single-page
``view.pipeline.items`` operation.  Use this method when a readback
needs completeness: every page is requested through :meth:`items`,
which re-resolves the same workspace/project/dataset/dataview parent,
while the shared paginator rejects repeated pages, non-advancing
offsets, empty pages with a continuation, and excessive page counts.
No mutation or server-provided URL is followed directly.

### `latest_task_sequence(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`

Return the highest active task sequence in the pipeline.

Deleted, suspended and suspending tasks are skipped: the server rejects
a ``sequence`` beyond the last active task (404 4DTVW005).

Data and metadata reads are scoped to a task *sequence*. Sequence 0 is
the original dataset; each task adds a sequence, and the columns a task
produces exist only from its sequence onward. Reading at the latest
sequence is therefore what surfaces every pipeline-derived column
(math, add_column, etc.).

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    The highest task sequence, or ``0`` when the view has no tasks.

### `list_tasks(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

List all pipeline tasks for a dataview.

Requests ``__full`` fields: the server's default (``__standard``)
omits ``transform_status`` and ``reference_errors``, so a task that
failed at run time (a GEN_AI step hitting a workspace AI quota, for
example) is otherwise invisible -- the pipeline still reads ready.

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with tasks list.

### `preview_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None, sample_size: 'int | None' = None) -> 'dict[str, Any]'`

Preview task results without adding to pipeline.

Args:
    dataview_id: ID of the dataview.
    task_spec: Task specification to preview.
    dataset_id: Dataset ID (auto-detected if not provided).
    sample_size: How many rows to sample; server default if omitted.

Returns:
    Preview result dict with sample data.

### `reconcile_draft_submission(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Read the server state after an interrupted draft submission.

This performs no mutation. A caller can safely invoke it from a fresh
process before deciding whether another SUBMIT is necessary.

### `rerun(self, dataview_id: 'int', from_sequence: 'int | None' = None, dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Rerun the pipeline starting from a specific task sequence.

Useful for rerunning a stale pipeline from the step where a parameter
is used, instead of rerunning the whole pipeline from scratch.

Args:
    dataview_id: ID of the dataview.
    from_sequence: Task sequence number to start the rerun from (>= 0).
        If not provided, the server reruns from step 0 (the full
        pipeline).
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Dict with the rerun job info.

Raises:
    MammothValidationError: If from_sequence is negative.

### `update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any] | None' = None, dataset_id: 'int | None' = None, patches: 'list[dict[str, Any]] | None' = None, skip_validation: 'bool | None' = None) -> 'dict[str, Any]'`

Update an existing pipeline task.

The route takes ``{"patches": [{"op", "path", "value"}]}`` with ``op``
``replace`` or ``command`` and ``path`` one of ``params``,
``display_info``, ``suspend``, ``restore``, ``discard``. ``task_spec``
is the shortcut for ``[{"op": "replace", "path": "params", "value":
task_spec}]``.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task to update.
    task_spec: New task params (replaces the ``params`` path).
    dataset_id: Exact parent dataset id.
    patches: Explicit patch operations, used instead of ``task_spec``.
    skip_validation: Forwarded as the ``skip_validation`` query flag.

Returns:
    Updated task dict.

### `wait_for_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None, timeout: 'float | None' = None, poll_interval: 'float' = 0.5) -> 'dict[str, Any]'`

Poll pipeline state until it reaches a terminal state.

After any pipeline mutation (add_task, delete_task, sql_generation),
the pipeline transitions through transient states before data is ready:
``modifying → modified → running → ready``.

The awaited call returns only once the pipeline reaches a terminal state
(``ready``, ``runtime_error``, ``ref_error``).

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).
    timeout: Max wait time in seconds (default: client.pipeline_timeout).
    poll_interval: Seconds before the second poll (default: 0.5); each wait
        is then 1.5 times the last, up to 15 seconds.

Returns:
    Final pipeline state dict.

Raises:
    MammothTransformError: If pipeline reaches ``runtime_error`` or ``ref_error``.
    MammothPipelineTimeoutError: If timeout is exceeded (a
        ``MammothJobTimeoutError`` subclass identifying the view, not a job).


---


# Jobs API Reference

The `JobsAPI` tracks asynchronous job status. Many Mammoth operations (data fetches, pipeline tasks, exports) create background jobs. The SDK polls these jobs automatically in most cases, but the Jobs API is available for manual control.

**Access**: `client.jobs`

---

## `JobsAPI`

Client for interacting with Mammoth Jobs API.

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `get_job(self, job_id: 'int', timeout: 'float | None' = None) -> 'dict[str, Any]'`

Get job status by ID.

Args:
    job_id: ID of the job to track
    timeout: Maximum time for this observation request.  Waiters pass
        their remaining polling budget so one request cannot exceed it.

Returns:
    Dict containing job information including status, response, timestamps

Raises:
    MammothAPIError: If the API request fails

### `get_jobs(self, job_ids: 'list[int] | str', timeout: 'float | None' = None) -> 'dict[str, Any]'`

Track multiple job IDs.

Args:
    job_ids: List of job IDs or comma-separated string of job IDs

Returns:
    Dict containing jobs list with status information

Raises:
    MammothAPIError: If the API request fails

### `wait_for_job(self, job_id: 'int', timeout: 'float | None' = None, poll_interval: 'float | None' = None, fetch: 'Callable[[int, float], Awaitable[dict[str, Any]]] | None' = None) -> 'dict[str, Any]'`

Wait for a job to complete and return the result.

Args:
    job_id: ID of the job to wait for
    timeout: Maximum time to wait in seconds (default: client.job_timeout)
    poll_interval: Upper bound on the time between polls in seconds (raised to 5 after
        60 seconds of waiting)
        (default: ``client.job_poll_seconds``). The first check is
        immediate and the gap then grows from ``_POLL_FIRST_DELAY`` up
        to this bound, so a sub-second job is not held for a full
        interval.
    fetch: Optional observer ``(job_id, remaining_timeout) -> job dict``
        used instead of ``GET /jobs/{id}``. Published-dashboard jobs
        are only readable through the URL-scoped job route, for
        example, and ``GET /jobs/{id}`` answers ``4PERM002`` for them.

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
    poll_interval: Upper bound on the time between polls in seconds (raised to 5 after
        60 seconds of waiting)
        (default: 2); gaps start short and grow to this bound.

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

Access via ``client.dashboards``::

    dashboards = await client.dashboards.list()
    dashboard = await client.dashboards.create_blank(
        CreateBlankParams(dataview_id=101, title="Revenue by region"),
    )
    await client.dashboards.share(
        dashboard_id=5,
        type_of_auth=DashboardAuthType.PUBLIC,
    )
    await client.dashboards.delete(dashboard_id=5)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `action(self, dashboard_id: 'int', action: 'DashboardActionType', params_enabled: 'bool | None' = None, params_view_id: 'int | None' = None, params_sequence: 'int | None' = None, params_filter_column: 'str | None' = None) -> 'dict[str, Any]'`

Perform an action on a dashboard.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    action: The action to execute.
    params_enabled: Required for ``auto-sync`` and ``auto-publish``;
        enables or disables the behaviour.
    params_view_id: Required (> 0) for ``delete-source``;
        optional for ``sync`` and ``auto-sync`` to scope to one source.
    params_sequence: The version to rewind to; required for ``restore``.
    params_filter_column: The column rows are filtered on; required
        when ``set-rls-config`` turns row-level security on.

Returns:
    Dict with action result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0, ``auto-sync`` /
        ``auto-publish`` are called without *params_enabled*, or
        ``delete-source`` is called without a positive *params_view_id*.

### `add_pages(self, dashboard_id: 'int', body: 'AddPagesSpec') -> 'AddPagesResponse'`

Append structural pages and start the asynchronous dashboard bake.

### `analytics(self: 'Any', dashboard_id: 'int') -> 'DashboardAnalyticsResponse'`

Get Dashboard Analytics.

### `append_figure(self, dashboard_id: 'int', dataview_id: 'int', figure: 'dict[str, Any]', banded: 'dict[str, Any] | None' = None, page_id: 'str | None' = None, page_new_title: 'str | None' = None) -> 'dict[str, Any]'`

Add one figure (an explore card) to a dashboard, with no LLM turn.

The server checks the figure against the board's source and profile before it
writes, appends it to the current draft and queues the bake.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    dataview_id: The figure's source; must be the board's own view (must be > 0).
    figure: The figure as the canvas stores it, without its ``id`` (the server
        mints it): ``kind`` plus its bindings, for example ``measure``, ``dim``,
        ``agg``, ``title``.
    banded: Optional banded dimension, without its id; ``figure["dim"]`` then
        points at it.
    page_id: Land on this existing content page.
    page_new_title: Land on a new page with this title. With neither, the board's
        first content page, else a new "From Explore" page.

Returns:
    Dict with ``sequence`` (the new draft head), ``bake_job_id`` (the async bake;
    wait with ``client.wait_if_job``), ``page_id``, ``figure_id`` and ``layout_key``.

Raises:
    MammothValidationError: If an id is not positive, ``figure`` is empty, or both
        a page id and a new page title are given.

### `archive(self, dashboard_id: 'int', archived: 'bool') -> 'Any'`

Set whether a dashboard is archived.

``archived=True`` archives the dashboard and ``archived=False``
restores it. The API declares no response body schema and the live
server answers with a non-object JSON value, so any 2xx JSON body is
accepted and returned unchanged instead of being rejected as a
response-contract violation on a write that already committed.

### `assess_pbix(self, file: 'str | Path') -> 'PbixAssessResponse'`

Assess a Power BI workbook without importing it.

### `assess_twb(self, file: 'str | Path') -> 'TwbAssessResponse'`

Assess a Tableau workbook without importing it.

### `attachment_assess(self, attachment_id: 'int') -> 'dict[str, Any]'`

Queue the assessment of an attached workbook (what it holds, no view needed).

Args:
    attachment_id: ID of the attachment (must be > 0).

Returns:
    Dict with ``future_id``, the job to wait for.

Raises:
    MammothValidationError: If *attachment_id* is not a positive integer.

### `attachment_create(self, file: 'str | Path') -> 'dict[str, Any]'`

Attach a local workbook to the chat so the agent can read it.

Args:
    file: Local workbook (``.pbix``, ``.twb`` or ``.twbx``).

Returns:
    The created attachment as the server answers it; its id names the attachment
    in :meth:`attachment_intent` and :meth:`attachment_assess`.

Raises:
    MammothValidationError: If *file* is not a readable local file.

### `attachment_intent(self, attachment_id: 'int', target_dataview_id: 'int') -> 'dict[str, Any]'`

Queue the read of an attached workbook against one of the caller's views.

The workbook is attached by the web app; this only reads it. Poll the returned
job (``client.wait_if_job``) for ``{intent, coverage, unmapped_visuals,
field_map, target_dataview_id}``, or ``{rejected, source}``.

Args:
    attachment_id: ID of the attachment (must be > 0).
    target_dataview_id: ID of the view to read the workbook against (must be > 0).

Returns:
    Dict with ``future_id``, the job to wait for.

Raises:
    MammothValidationError: If an id is not a positive integer.

### `audience(self, dashboard_id: 'int', days: 'int' = 7) -> 'dict[str, Any]'`

Get who read a board: totals, daily series, viewers, reach and actions.

Editors only. The route never returns an IP or a city and never counts the
editors' own visits.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    days: Window length: 7, 30 or 90.

Returns:
    Dict with totals against the window before, a 30-day daily series, named
    workspace viewers, anonymous counts, country / device / viewport coverage,
    people it was shared with who never opened it, page and tile reach, and
    outward actions.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *days* is not 7, 30 or 90.

### `audience_digest_get(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Get the caller's weekly audience email setting for one board.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with ``enabled`` (the effective answer), ``explicit`` (the stored
    choice, null when never chosen) and ``default_on``. Editors only.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `audience_digest_set(self, dashboard_id: 'int', enabled: 'bool | None') -> 'dict[str, Any]'`

Store the caller's choice for one board's weekly audience email.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    enabled: ``True`` or ``False`` to choose; ``None`` clears the choice, which
        returns to the default (on once the board has more than 5 viewers a week).

Returns:
    Dict with ``enabled``, ``explicit`` and ``default_on`` after the change.
    Editors only.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *enabled* is not a bool or None.

### `audience_get(self: 'Any', dashboard_id: 'int', days: 'int | None' = None) -> 'AudienceResponse'`

Dashboard audience.

### `audience_summary(self, dashboard_ids: '_list[int]') -> 'dict[str, Any]'`

Get views per board for the dashboard library: several boards in one call.

Args:
    dashboard_ids: Non-empty list of dashboard ids (each > 0, 200 at most are read).

Returns:
    Dict ``{"items": {dashboard_id: {...}}}`` with views and people over 7 days,
    views over 30 days, the last view and a 14-day daily series. A board never
    viewed is absent; boards outside the workspace or that the caller cannot
    edit are ignored.

Raises:
    MammothValidationError: If *dashboard_ids* is empty or holds an id ≤ 0.

### `bi_preflight(self: 'Any', dashboard_id: 'int') -> 'PowerBiPreflightResponse'`

What a Power BI export would carry.

### `cancel_generation(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Cancel an in-progress AI dashboard generation.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with cancellation result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `canvas_get(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None, rls_preview_value: 'str | None' = None) -> 'CanvasResponse'`

Get a dashboard's draft canvas, as the editor shows it.

### `canvas_restore(self: 'Any', dashboard_id: 'int', body: 'RestoreCanvasSpec') -> 'ObjectJobSchema | JobResponse'`

Undo, redo or revert the draft canvas to a target version.

### `canvas_save(self: 'Any', dashboard_id: 'int', body: 'SaveCanvasSpec') -> 'SaveCanvasResponse'`

Save the draft canvas as a new version.

### `chat_edit(self: 'Any', dashboard_id: 'int', body: 'ChatEditSpec') -> 'ObjectJobSchema | JobResponse'`

Send one chat message that edits the dashboard.

### `chat_history(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'mmai_dashboards_v3_schema_ChatHistoryResponse'`

Get a dashboard's editor chat transcript.

### `column_roster(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Get every column of a board's source dataset with its profile.

Served from the cached dataset profile: value samples, measure ranges and
aggregates, date spans and the profiler's identifier and protected-attribute
verdicts (the Data panel).

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with ``columns``, ``on_board_count``, ``row_count`` and ``signals``.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `columns(self: 'Any', dashboard_id: 'int') -> 'ColumnRoster'`

Source columns (Data panel).

### `context_apply(self, dashboard_id: 'int', review_id: 'str', keep: '_list[str] | None' = None, base_sequence: 'int | None' = None) -> 'ObjectJobSchema'`

Write the candidate a context review proposed, as a new canvas version.

The change lands like a chat edit, so undo, revert and the version timeline
reach it. The server rejects it when the candidate expired or was superseded,
and when the board's head moved since the review.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    review_id: ``review_id`` from the ``context_review`` job result (non-empty).
    keep: Roster keys whose hand-typed text to keep over the proposal.
    base_sequence: The head the review was computed against; 409 if it moved.

Returns:
    The job handle; its result holds ``sequence``, ``canvas``, ``version_before``
    and ``bake_ok``.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *review_id* is empty.

### `context_create(self: 'Any', body: 'ContextSpec') -> 'ContextResponse'`

Create a workspace context that dashboards can apply.

### `context_delete(self: 'Any', context_id: 'str') -> 'OkResponse'`

Delete a workspace context.

### `context_extract(self: 'Any', body: 'ContextExtractSpec') -> 'ContextExtractResponse'`

Read a context file into slot suggestions.

### `context_list(self: 'Any') -> 'ContextListResponse'`

List the workspace's contexts.

### `context_review(self, dashboard_id: 'int', scope: 'str | None' = None, note: 'str | None' = None, fresh: 'bool' = False) -> 'ObjectJobSchema'`

Dry-run what applying a board's current context would change.

Nothing is written: not the canvas, not the transcript, not the bake. The
planner runs under the grounding limit and the candidate is held server side.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    scope: How much prose to touch: ``summary`` (default), ``insights`` or ``all``.
    note: Free text to steer the review (1000 characters at most).
    fresh: Work the review out again instead of reusing a pending one.

Returns:
    The job handle; its result holds the item-level change set and a
    ``review_id`` (null when the context changes nothing).

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *note* is over 1000 characters.

### `context_update(self: 'Any', context_id: 'str', body: 'ContextSpec') -> 'ContextResponse'`

Update a workspace context.

### `create_blank(self, params: 'CreateBlankParams') -> 'dict[str, Any]'`

Create an empty v3 dashboard bound to a dataview.

The release endpoint returns the created dashboard ``id`` and seeded
canvas ``sequence``. Style is an unrestricted release string with a
default of ``dashboard``; the server owns any further style policy.

### `data_draft(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`

Get draft data from given SQL query.

### `data_published(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`

Get published data from given SQL query.

### `delete(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Delete a dashboard.

Args:
    dashboard_id: ID of the dashboard.

Returns:
    Dict with deletion result.

### `delete_tag(self, tag_id: 'int') -> 'dict[str, Any] | None'`

Delete a tag from the workspace vocabulary.

### `descriptor_data(self: 'Any', dashboard_id: 'int', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`

Start an asynchronous fetch of a dashboard's descriptor data.

### `duplicate(self, dashboard_id: 'int', project_id: 'int | None' = None, target_dataview_id: 'int | None' = None) -> 'DuplicateDashboardResponse'`

Duplicate a v3 dashboard, optionally onto another view.

With *target_dataview_id* the copy is made in that view's project and a data-swap
job is queued to re-point it; wait for ``swap_job_id`` with ``client.wait_if_job``.

Args:
    dashboard_id: ID of the dashboard to copy (must be > 0).
    project_id: Project to copy into when no target view is given.
    target_dataview_id: View to re-point the copy at (must be > 0 when given).

Returns:
    The new dashboard's ``id`` and ``swap_job_id`` (set only with a target view).

Raises:
    MammothValidationError: If an id is not a positive integer.

### `email_updates_get(self: 'Any', dashboard_id: 'int') -> 'EmailUpdatesOut'`

A dashboard's email updates.

### `email_updates_list(self: 'Any') -> 'EmailUpdateSummaryList'`

Email updates in this workspace.

### `email_updates_me_get(self: 'Any', dashboard_id: 'int') -> 'EmailUpdateSubscriptionOut'`

Whether I get this dashboard's email updates.

### `email_updates_me_set(self: 'Any', dashboard_id: 'int', body: 'EmailUpdateSubscriptionBody') -> 'EmailUpdateSubscriptionOut'`

Turn my email updates for this dashboard back on, or off.

### `email_updates_set(self: 'Any', dashboard_id: 'int', body: 'EmailUpdateSettingsBody') -> 'EmailUpdatesOut'`

Turn a dashboard's email updates on, off, or change them.

### `email_updates_test(self: 'Any', dashboard_id: 'int') -> 'EmailUpdateTestOut'`

Send me a test email update.

### `embed_config_get(self, dashboard_id: 'int') -> 'EmbedConfigResponse'`

Read a board's embed settings.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    The board's embed settings plus the URLs a snippet needs.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `embed_config_set(self, dashboard_id: 'int', mode: "Literal['key', 'signed']" = 'key', allow_any_origin: 'bool' = True, allowed_origins: '_list[str] | None' = None, appearance: 'dict[str, Any] | None' = None, snippet: 'dict[str, Any] | None' = None) -> 'EmbedConfigResponse'`

Save a board's embed settings (mode, origin allowlist, appearance).

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    mode: ``key`` (the board's embed key) or ``signed`` (a host-signed
        token). Ignored while the board is public.
    allow_any_origin: Any site may frame the board. Set false to
        restrict framing to *allowed_origins*.
    allowed_origins: Origin patterns allowed to frame the board while
        *allow_any_origin* is false. At most 20.
    appearance: The board's saved embed look (theme, filters, tile, ...).
    snippet: How the embed snippet is shaped (``height`` etc.).

Returns:
    The board's updated embed settings.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or the parameters
        fail validation (e.g. more than 20 *allowed_origins*).

### `embed_key_rotate(self, dashboard_id: 'int', keep_previous: 'bool' = True) -> 'EmbedKeyResponse'`

Create or rotate a board's embed key (Basic embeds).

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    keep_previous: Keep the replaced key usable for 24h (the default,
        for a planned rotation). Pass ``False`` to end it at once,
        for a leaked key.

Returns:
    The board's new embed key (shown once here; readable again via
    :meth:`embed_config_get`).

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `embed_lifetime_set(self, workspace_id: 'int', token_ttl: 'int') -> 'EmbedLifetimeResponse'`

Set how long an embed viewer session lives for a workspace.

Args:
    workspace_id: ID of the workspace (must be > 0).
    token_ttl: Session lifetime in seconds, 60 to 3600 inclusive.

Returns:
    The saved session lifetime.

Raises:
    MammothValidationError: If *workspace_id* ≤ 0 or *token_ttl* is
        outside [60, 3600].

### `embed_origin_revoke(self, dashboard_id: 'int', origin: 'str') -> 'EmbedConfigResponse'`

Remove one origin from a board's embed allowlist.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    origin: The origin to remove (non-empty).

Returns:
    The board's embed settings after the origin is removed.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *origin* is empty.

### `embed_preview_token_create(self, dashboard_id: 'int', claims: 'dict[str, Any] | None' = None) -> 'EmbedPreviewTokenResponse'`

Mint a preview token for the embed simulator (editor-only).

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    claims: Row-level-security claims, keyed by the board's RLS
        column name, exactly as a host's token would carry them.

Returns:
    A short-lived token, its expiry, and the embed URL to use it with.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `embed_secret_rotate(self, workspace_id: 'int') -> 'EmbedSecretResponse'`

Create or rotate the workspace's embed signing secret (owners/admins).

The plaintext secret is returned once, here, and never by a read route.
Rotating keeps the previous secret valid for 24 hours.

Args:
    workspace_id: ID of the workspace (must be > 0).

Returns:
    The new plaintext secret, its session token TTL, and rotation time.

Raises:
    MammothValidationError: If *workspace_id* ≤ 0.

### `embed_usage_get(self, dashboard_id: 'int') -> 'EmbedUsageResponse'`

Get one board's embed registry: origins, tiles and render counts.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Per-origin render/health counts and the active-origin total.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `embed_usage_summary(self, dashboard_ids: '_list[int]') -> 'dict[str, Any]'`

Count the active embed origins of several boards in one call.

The dashboard library's "embedded on N sites" figure. Boards outside
the workspace are ignored by the route.

Args:
    dashboard_ids: Non-empty list of dashboard ids (each > 0).

Returns:
    Dict with ``counts`` (origins that loaded each board in the last
    90 days) and ``refused`` (origins refused per board).

Raises:
    MammothValidationError: If *dashboard_ids* is empty or holds an id ≤ 0.

### `engagement(self, dashboard_id: 'int', days: 'int' = 30, viewers: 'str' = 'all') -> 'dict[str, Any]'`

Get the engagement report of a board: reach, depth per page and per person.

Editors only. Reach is counted against the people the board is shared with.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    days: Window length: 7, 30 or 90.
    viewers: ``all``, ``named`` or ``anonymous``; filters every block except
        reach and people, which are always named-only.

Returns:
    Dict with ``reach``, ``totals``, ``daily``, ``pages`` (with tile depth),
    ``people`` (with ``status`` and ``can_remind``), ``hours`` (UTC),
    ``surface``, ``devices``, ``actions`` and board ``events``.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0, *days* is not 7, 30 or 90, or
        *viewers* is not one of the three values.

### `engagement_get(self: 'Any', dashboard_id: 'int', days: 'int | None' = None, viewers: "Literal['all', 'named', 'anonymous'] | None" = None) -> 'EngagementResponse'`

Dashboard engagement report.

### `engagement_person(self, dashboard_id: 'int', user_id: 'int', days: 'int' = 30) -> 'dict[str, Any]'`

Get one person's visits to a board, newest first (at most 50).

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    user_id: ID of the person (must be > 0).
    days: Window length: 7, 30 or 90.

Returns:
    Dict with ``user_id``, ``name`` and ``visits``: each has ``started_at``,
    ``seconds``, ``pages`` (page id, name, seconds), ``device`` and ``surface``.

Raises:
    MammothValidationError: If an id is ≤ 0 or *days* is not 7, 30 or 90.

### `engagement_remind(self, dashboard_id: 'int', user_ids: '_list[int]') -> 'dict[str, Any]'`

Email the share link again to people who have not opened a board.

The server sends at most one reminder per person per board every 7 days.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    user_ids: 1 to 200 ids of people the board is shared with.

Returns:
    Dict with ``sent`` (user ids) and ``skipped`` (user id, ``reason`` and
    ``next_at``).

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *user_ids* is empty, over 200
        long or holds an id ≤ 0.

### `exemplar_extract(self: 'Any', body: 'ExemplarExtractSpec') -> 'ExemplarExtractResponse'`

Read an example report into an editable spec.

### `export_powerbi(self, dashboard_id: 'int', output_path: 'str | Path | None' = None) -> 'Path'`

Download this dashboard as a Power BI project (.zip) to a local file.

The zip holds the PBIP project, a CSV snapshot of the data, and a
readme written for someone who has never seen the Mammoth original.
See :meth:`powerbi_preflight` for what will convert before committing
to the download.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    output_path: Path for the .zip file (auto-generated if not provided).

Returns:
    Path to the downloaded file.

### `export_tableau(self, dashboard_id: 'int', output_path: 'str | Path | None' = None) -> 'Path'`

Download this dashboard as a Tableau workbook (.twbx) to a local file.

One file, no refresh step and no gateway -- a .twbx carries its own
data. See :meth:`tableau_preflight` for what will convert before
committing to the download.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    output_path: Path for the .twbx file (auto-generated if not provided).

Returns:
    Path to the downloaded file.

### `extract_context(self, body: 'ContextExtractSpec') -> 'dict[str, Any]'`

Extract a context file into slot suggestions (release route).

### `extract_exemplar(self, body: 'ExemplarExtractSpec') -> 'dict[str, Any]'`

Extract an example report into an editable dashboard spec.

### `figure_add(self: 'Any', dashboard_id: 'int', body: 'AppendFigureSpec') -> 'AppendFigureResponse'`

Append one authored figure (no LLM turn, no canvas round trip).

### `figure_intent(self: 'Any', dashboard_id: 'int', body: 'FigureIntentSpec') -> 'FigureIntentResponse'`

Resolve an AI-add figure from an intent.

### `format_preview(self, dashboard_id: 'int', style: 'str') -> 'dict[str, Any]'`

Dry-run a format switch: what carries over, what is added, what is lost.

Computed by the server on a copy of the canvas; nothing is persisted.

Args:
    dashboard_id: ID of the v3 dashboard (must be > 0).
    style: Target format/style name (non-empty), as ``dashboard style
        preset list`` names them.

Returns:
    Dict with the carried and added counts and the ``not_shown`` ledger.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *style* is empty.

### `gallery_get(self, slug: 'str') -> 'dict[str, Any]'`

Get one template card from the public gallery.

Args:
    slug: Template slug (non-empty).

Returns:
    Dict ``{"template": {...}}``. The route answers 404 for an unknown
    slug, a user-saved template, or a curated one that is not live.

Raises:
    MammothValidationError: If *slug* is empty.

### `gallery_list(self, function: 'str | None' = None, industry: 'str | None' = None) -> 'dict[str, Any]'`

List the public template gallery: curated, live templates only.

The anonymous catalog (no internal ids). Each card carries its copy,
taxonomy labels, ``thumbnail_ref`` and ``viewer_url``.

Args:
    function: Keep only templates for this business function.
    industry: Keep only templates for this industry.

Returns:
    Dict with the template cards and the facet lists with counts. The
    route answers 404 for an unknown facet or one with nothing under it.

### `generate_v3(self, params: 'GenerateV3Params | dict[str, Any]') -> 'dict[str, Any]'`

Have Mammoth build a v3 dashboard on a dataview from a brief.

The route answers with the id of the job that builds it.

Args:
    params: What to build, as
        :class:`~mammoth.models.dashboards.GenerateV3Params` or the
        same fields as a dict. ``format="qa"`` opens a
        question-and-answer notebook, which needs no ``intent``.

Returns:
    Dict carrying the build job.

Raises:
    MammothValidationError: If the brief is not one the route takes.

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

### `get_draft_data(self, dashboard_id: 'int', widget_id: 'str', global_filters: 'dict[str, Any] | None' = None, drilldown_filters: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`

Get one widget's rows from a dashboard's draft (unpublished) state.

The route is historically named ``GetDraftDataFromSql`` but the API
contract takes a ``WidgetDataSpec``: ``{"params": {"widget_id", ...}}``.
A top-level ``sql`` body is rejected with HTTP 400 ``params: Field
required``.

Args:
    dashboard_id: ID of the dashboard.
    widget_id: UUID of the widget whose data to fetch.
    global_filters: Sidebar filters, ``{column: value}``.
    drilldown_filters: Chart-click filters, ``{column: value}``
        (always exact match).

Returns:
    Dict with a ``data`` list of row dicts.

### `get_publish_data(self, dashboard_id: 'int', widget_id: 'str', global_filters: 'dict[str, Any] | None' = None, drilldown_filters: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`

Get one widget's rows from a dashboard's published state.

Same ``WidgetDataSpec`` contract as :meth:`get_draft_data`.

Args:
    dashboard_id: ID of the dashboard.
    widget_id: UUID of the widget whose data to fetch.
    global_filters: Sidebar filters, ``{column: value}``.
    drilldown_filters: Chart-click filters, ``{column: value}``.

Returns:
    Dict with a ``data`` list of row dicts.

### `get_sources(self) -> '_list[dict[str, Any]]'`

Get available dashboard data sources.

.. note::

    This endpoint may return HTTP 500 on some server configurations.

Returns:
    List of source dicts.

### `import_workbook(self, file: 'str | Path', project_id: 'int | None' = None) -> 'ImportDatasetResponse'`

Import a workbook into a project-scoped dataset.

### `job_by_url(self, url: 'str', job_id: 'int') -> 'dict[str, Any]'`

Get the status/result of an async dashboard job, addressed by URL slug.

Args:
    url: Dashboard URL slug.
    job_id: ID of the job (must be > 0).

Returns:
    Dict with job status/result.

Raises:
    MammothValidationError: If *job_id* ≤ 0.

### `list(self, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List all dashboards.

Returns:
    List of dashboard dicts.

### `list_tags(self) -> 'dict[str, Any]'`

List the workspace dashboard-tag vocabulary.

### `live_chart_audience(self: 'Any', dashboard_id: 'int', body: 'ChangeAudienceSpec') -> 'LiveChartResponse'`

Change who can see a live chart.

### `live_chart_create(self: 'Any', body: 'CreateLiveChartSpec', project_id: 'int | None' = None) -> 'CreateLiveChartResponse'`

Make a chat chart live.

### `live_chart_get(self: 'Any', dashboard_id: 'int') -> 'LiveChartResponse'`

Read a live chart.

### `live_chart_list(self: 'Any', session_id: 'str') -> 'LiveChartListResponse'`

The charts one chat made live.

### `live_chart_placement(self: 'Any', dashboard_id: 'int', body: 'RecordPlacementSpec') -> 'dict[str, Any]'`

Record a dashboard the chart was added to.

### `live_chart_usage(self: 'Any', dashboard_id: 'int') -> 'LiveChartUsageResponse'`

Where a live chart is used.

### `merge_tag(self, tag_id: 'int', target_id: 'int') -> 'dict[str, Any]'`

Merge one workspace tag into another using the release request shape.

### `oembed(self: 'Any', url: 'str | None' = None, maxwidth: 'str | None' = None, maxheight: 'str | None' = None, format: 'str | None' = None) -> 'dict[str, Any]'`

oEmbed provider — a pasted board link, as a live embed.

### `og_card(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`

Dashboard card thumbnail (draft or published PNG).

### `own_data_accept(self, dashboard_id: 'int', choice: 'str' = 'proposal', exclude: '_list[str] | None' = None) -> 'ObjectJobSchema'`

Apply the proposed version of the board. This changes the board.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    choice: ``proposal``, ``partial`` or ``reshape``.
    exclude: Change ids of added items to leave out (at most 20).

Returns:
    The applying job; wait with ``client.wait_if_job``.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0, *choice* is not one of the
        three or *exclude* is not a list of at most 20 strings.

### `own_data_dismiss(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Drop the pending "use my data" run. The board is not changed.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    The server's acknowledgement.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `own_data_preview(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Preview the board on the user's data, as proposed (baked, not saved).

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with the adapted board, in the shape of a template preview.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `own_data_start(self, dashboard_id: 'int', ingest_job_id: 'int | None' = None, dataset_id: 'int | None' = None, dataview_id: 'int | None' = None, file_name: 'str | None' = None) -> 'dict[str, Any]'`

Fit a template board to the user's own data. The board is not changed.

Replaces any pending run. The server leaves a proposal to review with
``own_data_preview`` and ``own_data_accept``.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    ingest_job_id: Job of a file just uploaded; the server waits for it.
    dataset_id: A dataset already in the workspace.
    dataview_id: A view already in the workspace.
    file_name: Name shown in the progress strip and the notification (≤ 255).
        Not a source.

Returns:
    Dict with ``job_id`` (the preparing job; wait with ``client.wait_if_job``)
    and the run's state.

Raises:
    MammothValidationError: If not exactly one of the three sources is given, an
        id is ≤ 0 or *dashboard_id* ≤ 0.

### `own_data_status(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Get the pending "use my data" run of a template board.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with the run's ``status`` and ``stage``, and once fitted the proposal
    (fit grade and what changed). ``{"status": None}`` when nothing is pending.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `page_plan(self: 'Any', dashboard_id: 'int', body: 'PlanPageSpec') -> 'PlanPageResponse'`

Compose a new page from an intent.

### `pages_add(self: 'Any', dashboard_id: 'int', body: 'AddPagesSpec') -> 'AddPagesResponse'`

Add pages structurally (no LLM turn).

### `pbix_assess(self: 'Any', attachment_id: 'int') -> 'AttachmentJob'`

Read an attached workbook before importing it.

### `pbix_intent(self: 'Any', attachment_id: 'int', body: 'AttachmentIntentForm') -> 'AttachmentJob'`

Read an attached workbook against one of your views.

### `pdf_artifact(self: 'Any', dashboard_id: 'int', job_id: 'int') -> 'dict[str, Any]'`

Download a completed draft PDF export.

### `pdf_export(self: 'Any', dashboard_id: 'int', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`

Kick a draft-dashboard PDF export.

### `powerbi_export_artifact(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Fetch the raw Power BI export artifact (release route).

SDK-only: :meth:`export_powerbi` decodes ``content_base64`` and writes
the result to disk; that is the reviewed CLI command.

### `powerbi_preflight(self, dashboard_id: 'int') -> 'PowerBiPreflightResponse'`

What a Power BI export of this dashboard would carry (release route).

### `published_canvas(self: 'Any', url: 'str') -> 'CanvasResponse'`

Get a published dashboard's viewer canvas.

### `published_data(self: 'Any', url: 'str', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`

Descriptor data for a published dashboard.

### `published_data_by_url(self, url: 'str', body: 'dict[str, Any]') -> 'dict[str, Any]'`

Get published dashboard widget data via SQL, addressed by URL slug.

Args:
    url: Dashboard URL slug.
    body: Widget data request payload (``WidgetDataSpec``), e.g.
        ``{"params": {"widget_id": ..., "global_filters": {...},
        "drilldown_filters": {...}}}``.

Returns:
    Dict with query results (may include a job ID for async execution).

### `published_og_card(self: 'Any', url: 'str') -> 'dict[str, Any]'`

Published dashboard's link-unfurl OG card (baked PNG).

### `published_pdf_artifact(self: 'Any', url: 'str', job_id: 'int') -> 'dict[str, Any]'`

Download a completed published PDF export.

### `published_pdf_export(self: 'Any', url: 'str', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`

Kick a published-dashboard PDF export.

### `published_share_page(self: 'Any', url: 'str') -> 'dict[str, Any]'`

Published dashboard's link-unfurl share page (crawler-facing HTML).

### `published_video_artifact(self: 'Any', url: 'str') -> 'dict[str, Any]'`

Stream a published motion-story video (Range-enabled).

### `published_video_export(self: 'Any', url: 'str') -> 'ObjectJobSchema | JobResponse'`

Kick a motion-story video export (published view).

### `qa_ask(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'AskSpec') -> 'ObjectJobSchema | JobResponse'`

Ask one question in a Q&A session; the answer arrives asynchronously.

### `qa_comment_create(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'CommentSpec') -> 'SessionResponse'`

Comment on a shared Q&A session.

### `qa_comment_delete(self: 'Any', dashboard_id: 'int', session_id: 'int', comment_id: 'int') -> 'SessionResponse'`

Delete a comment (author or session owner).

### `qa_feedback(self: 'Any', dashboard_id: 'int', session_id: 'int', message_id: 'int', body: 'FeedbackSpec') -> 'SessionResponse'`

Rate an assistant answer (up/down; null clears).

### `qa_insights(self, dashboard_id: 'int', days: 'int' = 7) -> 'dict[str, Any]'`

Get the questions viewers asked on a board, grouped by their text.

Editors only. Nobody is named: no user, session or name is returned, and the
editors' own questions are left out.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    days: Window length: 7, 30 or 90.

Returns:
    Dict with ``groups`` (feedback and unanswered counts, the measure and
    dimension each answer was about), ``feedback``, ``questions_total`` and
    ``range_days``.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or *days* is not 7, 30 or 90.

### `qa_session_create(self: 'Any', dashboard_id: 'int', body: 'CreateSessionSpec') -> 'SessionResponse'`

Create a Q&A session.

### `qa_session_delete(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'dict[str, Any]'`

Delete a Q&A session (owner only).

### `qa_session_fork(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'SessionResponse'`

Fork a shared Q&A session into a private copy.

### `qa_session_get(self: 'Any', dashboard_id: 'int', session_id: 'int') -> 'SessionResponse'`

Read a Q&A session (replayable — carries baked answers).

### `qa_session_list(self: 'Any', dashboard_id: 'int') -> 'SessionListResponse'`

List Q&A sessions.

### `qa_session_rename(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'RenameSessionSpec') -> 'SessionResponse'`

Rename a Q&A session (owner only).

### `qa_session_set_visibility(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'VisibilitySpec') -> 'SessionResponse'`

Share/unshare a Q&A session (owner only).

### `qa_settings_get(self: 'Any', dashboard_id: 'int') -> 'QaSettingsResponse'`

Get this dashboard's Q&A settings.

### `qa_settings_set(self: 'Any', dashboard_id: 'int', body: 'QaSettingsSpec') -> 'QaSettingsResponse'`

Update this dashboard's Q&A settings (editors only).

### `query(self: 'Any', dashboard_id: 'int', body: 'AdhocQuerySpec') -> 'AdhocQueryResponse'`

Run an ad-hoc descriptor query from the editor.

### `rename_tag(self, tag_id: 'int', name: 'str') -> 'dict[str, Any]'`

Rename one workspace dashboard tag using the release request shape.

### `render_figure_svg(self, spec: 'dict[str, Any]', style_id: 'str | None' = None) -> 'str'`

Render one figure to an SVG document, with no board and no write.

Args:
    spec: The engine figure spec: ``chart`` ("bar" or "table"), ``title`` and
        the data (``data`` of ``label``/``value`` for a bar, ``columns`` and
        ``rows`` of ``cells`` for a table).
    style_id: Optional saved style to render with.

Returns:
    The SVG document as text.

Raises:
    MammothValidationError: If ``spec`` is not a dict, or the response holds no SVG.

### `restore(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Restore a trashed dashboard.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with restore result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `rls_assignment_list(self: 'Any', dashboard_id: 'int') -> 'RlsAssignmentsResponse'`

List RLS viewer assignments.

### `rls_assignment_set(self: 'Any', dashboard_id: 'int', body: 'RlsAssignmentsSpec') -> 'dict[str, Any]'`

Replace RLS viewer assignments.

### `rls_column_list(self: 'Any', dashboard_id: 'int') -> 'RlsColumnsResponse'`

Candidate columns for the RLS filter.

### `rls_value_list(self: 'Any', dashboard_id: 'int', column: 'str', search: 'str | None' = None) -> 'RlsDistinctValuesResponse'`

Distinct values for an RLS filter column.

### `set_tags(self, dashboard_id: 'int', tags: 'builtins.list[str]') -> 'dict[str, Any]'`

Replace a dashboard's complete tag set using the release request shape.

### `share(self, dashboard_id: 'int', type_of_auth: 'DashboardAuthType', users: '_list[DashboardShareUser] | None' = None) -> 'dict[str, Any]'`

Share a dashboard.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    type_of_auth: Authentication model for the shared link.
    users: Optional list of :class:`~mammoth.models.dashboards.DashboardShareUser`
        granting per-user access.  Only used when *type_of_auth* is
        :attr:`~mammoth.models.dashboards.DashboardAuthType.MAMMOTH`;
        ignored for ``public`` / ``password``.  Each user must have a
        non-empty ``email``.

Returns:
    Dict with sharing result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0 or any user has an
        empty ``email``.

### `signature_create(self: 'Any', body: 'SignatureSpec') -> 'SignatureResponse'`

Create a workspace signature.

### `signature_delete(self: 'Any', signature_id: 'str') -> 'OkResponse'`

Delete a signature.

### `signature_list(self: 'Any') -> 'SignatureListResponse'`

List the workspace's signatures.

### `signature_update(self: 'Any', signature_id: 'str', body: 'SignatureSpec') -> 'SignatureResponse'`

Update a signature.

### `source_list(self: 'Any') -> 'DashboardSourcesType'`

Get Dashboard Sources.

### `style_custom_create(self: 'Any', body: 'CustomStyleSpec') -> 'StyleResponse'`

Create a workspace custom style.

### `style_custom_delete(self: 'Any', style_id: 'str') -> 'OkResponse'`

Delete a custom style.

### `style_custom_list(self: 'Any') -> 'StyleListResponse'`

List the workspace's custom styles.

### `style_custom_update(self: 'Any', style_id: 'str', body: 'CustomStyleSpec') -> 'StyleResponse'`

Update a custom style.

### `style_default_get(self: 'Any') -> 'DefaultStyleResponse'`

Get the workspace's default style id.

### `style_default_set(self: 'Any', body: 'DefaultStyleSpec') -> 'DefaultStyleResponse'`

Set the workspace default style id.

### `style_derive(self: 'Any', body: 'DeriveStyleSpec') -> 'dict[str, Any] | DeriveStyleResponse'`

Derive a full Style bundle from signals.

### `style_extract_brand(self: 'Any', body: 'ExtractBrandSpec') -> 'ObjectJobSchema | JobResponse'`

Kick a brand extraction from a URL.

### `style_preset_list(self: 'Any') -> 'StylePresetsResponse'`

Style presets (stock + custom).

### `style_token_list(self: 'Any', id: 'str') -> 'StyleTokensResponse'`

Get a full style bundle by id (stock or custom).

### `suggestion_list(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`

Data-grounded starting points for the create screen.

### `swap_data(self, dashboard_id: 'int', body: 'SwapDataSpec') -> 'ObjectJobSchema'`

Re-point a v3 dashboard at a different dataset.

### `swap_fit(self, source_dashboard_id: 'int', target_dataview_ids: '_list[int]', include_over_budget: 'bool' = False, seconds_budget: 'float | None' = None) -> 'dict[str, Any]'`

Score one board against candidate datasets before ``swap_data`` (no writes).

Pure computation over dataset profiles: no model call, nothing persisted.

Args:
    source_dashboard_id: The v3 board that would be re-pointed (must be > 0).
    target_dataview_ids: Candidate dataview ids, 1 to 60, returned in this order.
    include_over_budget: Score even datasets past the cost budget (an explicit
        per-dataset check).
    seconds_budget: Seconds of cold profile building the request may spend
        (0 to 30); the server default when omitted. 0 scores cached datasets only.

Returns:
    Dict with ``fits`` (one entry per dataview: a grade with matched, total and
    reasons, or a ``skipped`` reason), ``cell_budget``, ``sample_dataview_ids``,
    ``seconds_spent`` and ``seconds_budget``.

Raises:
    MammothValidationError: If an id is ≤ 0, the list is empty or over 60, or
        *seconds_budget* is outside 0 to 30.

### `tableau_export_artifact(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Fetch the raw Tableau export artifact (release route).

SDK-only: :meth:`export_tableau` decodes ``content_base64`` and writes
the result to disk; that is the reviewed CLI command.

### `tableau_preflight(self, dashboard_id: 'int') -> 'TableauPreflightResponse'`

What a Tableau export of this dashboard would carry (release route).

### `tags_delete(self: 'Any', tag_id: 'int') -> 'dict[str, Any]'`

Delete a tag from the workspace vocabulary.

### `tags_list(self: 'Any') -> 'dict[str, Any]'`

List the workspace tag vocabulary.

### `tags_merge(self: 'Any', tag_id: 'int', body: 'TagMergeParams') -> 'dict[str, Any]'`

Merge one tag into another.

### `tags_rename(self: 'Any', tag_id: 'int', body: 'TagRenameParams') -> 'dict[str, Any]'`

Rename a tag.

### `tags_set(self: 'Any', dashboard_id: 'int', body: 'DashboardTagsParams') -> 'dict[str, Any]'`

Set a dashboard's tags.

### `take_pending_template(self) -> 'dict[str, Any]'`

Claim the pending dashboard template for the workspace.

### `template_apply(self: 'Any', body: 'ApplyTemplateSpec', project_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`

Apply a template to a target dataset.

### `template_create(self: 'Any', body: 'SaveTemplateSpec') -> 'TemplateDetailResponse'`

Save a dashboard as a workspace template.

### `template_delete(self: 'Any', template_id: 'str') -> 'OkResponse'`

Delete a saved workspace template.

### `template_fit(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'TemplateFitResponse'`

Fit-score the whole catalog against one dataset.

### `template_get(self: 'Any', template_id: 'str') -> 'TemplateDetailResponse'`

One template's metadata + self-fit recipe.

### `template_list(self: 'Any') -> 'TemplateListResponse'`

Curated template catalog.

### `template_preview(self: 'Any', body: 'PreviewTemplateSpec') -> 'PreviewTemplateResponse'`

Preview a template mapping applied to a target dataset.

### `template_rename(self: 'Any', template_id: 'str', body: 'RenameTemplateSpec') -> 'TemplateDetailResponse'`

Rename a saved workspace template.

### `template_resolve_mapping(self: 'Any', body: 'ResolveTemplateMappingSpec') -> 'ResolveTemplateMappingResponse'`

Propose a template mapping onto a target dataset.

### `template_thumbnail_clear(self, template_id: 'str') -> 'dict[str, Any]'`

Remove a saved template's picture; its card falls back to the og-card.

Owner or workspace admin only.

Args:
    template_id: Template slug (non-empty).

Returns:
    Dict ``{"ok": bool}``: ``False`` when the template had no picture.

Raises:
    MammothValidationError: If *template_id* is empty.

### `template_thumbnail_get(self, template_id: 'str') -> 'dict[str, Any]'`

Download the picture a template's card shows.

Args:
    template_id: Template slug (non-empty).

Returns:
    Dict with ``content_type``, ``size_bytes``, ``sha256`` and
    ``content_base64``. The route answers 404 when the template has no
    picture; the card then falls back to its og-card.

Raises:
    MammothValidationError: If *template_id* is empty.

### `template_thumbnail_set(self, template_id: 'str', file: 'str | Path') -> 'dict[str, Any]'`

Replace the picture of a saved workspace template.

Owner or workspace admin only; curated templates are not writable.
The server accepts PNG, JPEG or WebP (by content) up to 1 MB.

Args:
    template_id: Template slug (non-empty).
    file: Path to a local image file.

Returns:
    Dict ``{"ok": True}``.

Raises:
    MammothValidationError: If *template_id* is empty or *file* is not
        a readable local file.

### `templates_pending(self: 'Any') -> 'PendingTemplateResponse'`

Take the template this workspace signed up for.

### `templates_use(self: 'Any', slug: 'str', body: 'UseTemplateSpec') -> 'ObjectJobSchema | JobResponse'`

Take a template on its own sample data.

### `trash(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Move a dashboard to trash.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with trash result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `update(self, dashboard_id: 'int', patch: '_list[DashboardPatchItem]') -> 'dict[str, Any]'`

Update a dashboard with patch operations.

The patch items look like RFC 6902 JSON Patch but ``path`` is a bare
field name from :class:`~mammoth.models.dashboards.DashboardPatchPath`
(``"title"``, ``"intent"``, ``"theme"``, ``"pages"``, ``"filters"``),
not a JSON pointer: ``"/title"`` is rejected.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    patch: Non-empty list of :class:`~mammoth.models.dashboards.DashboardPatchItem`
        describing the operations to apply.

        Supported combos:

        * ``op=add, path=intent`` — trigger AI edit; value must be str ≥ 10 chars.
        * ``op=replace, path=title`` — rename dashboard; value must be str.
        * ``op=replace, path=theme`` — change theme; value must be str.

Returns:
    Dict with updated dashboard info.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0, *patch* is empty, or
        an ``intent`` value is too short / a ``title``/``theme`` value is
        not a string.

### `use_template(self, slug: 'str', body: 'UseTemplateSpec') -> 'ObjectJobSchema | JobResponse'`

Instantiate a dashboard template on its sample data.

### `v3_generate(self: 'Any', body: 'GenerateDashboardV3Spec', project_id: 'int | None' = None) -> 'ObjectJobSchema | JobResponse'`

Generate a v3 dashboard.

### `video_export(self: 'Any', dashboard_id: 'int') -> 'ObjectJobSchema | JobResponse'`

Kick a motion-story video export.

### `video_state(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`

Motion-story video export state (never kicks a render).

### `wait_for_job_by_url(self, url: 'str', job_id: 'int', timeout: 'float | None' = None, poll_interval: 'float | None' = None) -> 'dict[str, Any]'`

Wait for a published-dashboard job through the URL-scoped job route.

Jobs dispatched by the ``/dashboards/url/{url}/...`` routes are not
readable through ``GET /jobs/{id}`` (the server answers ``4PERM002``),
so poll :meth:`job_by_url` with the same timeout and failure semantics
as :meth:`~mammoth.api.jobs.JobsAPI.wait_for_job`.

### `widget_data(self, dashboard_id: 'int', body: 'dict[str, Any]') -> 'dict[str, Any]'`

Get data for multiple dashboard widgets in bulk.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    body: Bulk widget data request payload (``BulkWidgetDataSpec``).

Returns:
    Dict with per-widget data results.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `widget_data_by_url(self, url: 'str', body: 'dict[str, Any]') -> 'dict[str, Any]'`

Get data for multiple dashboard widgets in bulk, addressed by URL slug.

Args:
    url: Dashboard URL slug.
    body: Bulk widget data request payload (``BulkWidgetDataSpec``).

Returns:
    Dict with per-widget data results.


---


# Webhooks API Reference

The `WebhooksAPI` manages webhook datasets -- HTTP endpoints that receive data into the Mammoth platform. Webhooks allow external systems to push data directly into Mammoth.

**Access**: `client.webhooks`

---

## `WebhooksAPI`

Client for managing webhook datasets.

Access via client.webhooks:
    webhooks = client.webhooks.list()
    webhook = client.webhooks.create(name="My Webhook", mode=WebhookMode.REPLACE)
    client.webhooks.update(webhook_id, mode=WebhookMode.COMBINE)
    client.webhooks.delete(webhook_id)
    client.webhooks.send_data(webhook_uri, {"col1": "val1"})

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `create(self, name: 'str' = 'Generic Webhook', mode: 'str | WebhookMode' = 'replace', folder_resource_id: 'str | None' = None, origins: 'str' = '*', is_secure: 'bool' = False) -> 'dict[str, Any]'`

Create a webhook dataset.

Args:
    name: Name of the webhook.
    mode: Data ingestion mode — "replace" or "combine".
    folder_resource_id: Optional folder to place the webhook in.
    origins: Allowed CORS origins (default "*").
    is_secure: Whether to generate a secret for authentication.

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

### `list(self, limit: 'int' = 50, offset: 'int' = 0) -> '_list[dict[str, Any]]'`

List webhook datasets.

Args:
    limit: Maximum number of results to return.
    offset: Number of results to skip.

Returns:
    List of webhook dicts.

### `send_data(self, webhook_uri: 'str', data: 'dict[str, Any]') -> 'dict[str, Any]'`

Send data to a webhook via POST.

Args:
    webhook_uri: The webhook URI path (e.g. "nHC1zIl97JzgDMopgcfpOgLV").
    data: Data payload to send.

Returns:
    Dict with the API response.

### `send_data_get(self, webhook_uri: 'str', params: 'dict[str, Any] | None' = None) -> 'dict[str, Any]'`

Send data to a webhook via GET query parameters.

Args:
    webhook_uri: The webhook URI path (e.g. "nHC1zIl97JzgDMopgcfpOgLV").
    params: Data as query parameters.

Returns:
    Dict with the API response.

### `update(self, webhook_id: 'int', mode: 'str | WebhookMode | None' = None, origins: 'str | None' = None, is_secure: 'bool | None' = None) -> 'dict[str, Any]'`

Update a webhook using JSON Patch format.

Args:
    webhook_id: ID of the webhook.
    mode: New data ingestion mode.
    origins: New allowed CORS origins.
    is_secure: Whether the webhook requires a secret.

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

Access via ``client.automations``::

    automations = await client.automations.list()
    automation = await client.automations.create(
        name="Nightly refresh",
        description="Pulls cloud data every night",
        tasks=[AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
        )],
    )
    schedules = await client.automations.list_schedules()

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `capabilities(self) -> 'dict[str, Any]'`

List everything an automation can be created with.

The server derives this from the same schemas it validates a create
with, so it cannot go stale.

Returns:
    Dict with ``tasks`` (each: ``task_type``, ``summary``,
    ``required_fields``, ``optional_fields``, ``options`` (accepted
    values per field), ``formats_in`` and ``formats_out`` (file formats
    the task reads or writes)) and ``conditions`` (each:
    ``condition_type``, ``summary``, ``fields``, ``options``).

#### `create(self, name: 'str', description: 'str', tasks: '_list[AutomationTaskSpec]', conditions: '_list[AutomationConditionSpec] | None' = None, condition_mode: 'AutomationConditionMode' = <AutomationConditionMode.AND: 'and'>) -> 'dict[str, Any]'`

Create a new automation.

Args:
    name: Automation name (non-empty).
    description: Human-readable description (may be empty string).
    tasks: Non-empty list of :class:`~mammoth.models.automations.AutomationTaskSpec`.
        Each task must supply the fields required by its ``task_type``.
    conditions: Optional list of
        :class:`~mammoth.models.automations.AutomationConditionSpec`.
    condition_mode: How multiple conditions are combined
        (``"and"`` or ``"or"``; default ``"and"``).

Returns:
    Dict with created automation info.

Raises:
    MammothValidationError: If *name* is empty, *tasks* is empty,
        a task is missing required fields for its type, or a condition
        is missing required fields for its type.

#### `create_schedule(self, spec: 'ScheduleCreateSpec') -> 'dict[str, Any]'`

Create a new schedule.

Args:
    spec: :class:`~mammoth.models.automations.ScheduleCreateSpec` describing
        the recurrence rule and optional work items.

Returns:
    Dict with created schedule info.

Raises:
    MammothValidationError: If ``rrule.interval`` ≤ 0.

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

#### `restore(self, automation_id: 'int') -> 'dict[str, Any]'`

Restore a trashed automation.

Args:
    automation_id: ID of the automation.

Returns:
    Dict with the restored automation info.

#### `trash(self, automation_id: 'int') -> 'dict[str, Any]'`

Move an automation to trash.

Args:
    automation_id: ID of the automation.

Returns:
    Dict with the trashed automation info.

#### `update(self, automation_id: 'int', patch: '_list[AutomationPatchItem]') -> 'dict[str, Any]'`

Update an automation via JSON-patch operations.

Args:
    automation_id: ID of the automation (must be > 0).
    patch: Non-empty list of :class:`~mammoth.models.automations.AutomationPatchItem`.

        Supported combos:

        * ``op=command, path=run`` — trigger the automation immediately.
        * ``op=replace, path=status`` — suspend or resume; ``value``
          must be ``"suspend"`` or ``"resume"``. ``"resume"`` is sent
          to the backend as ``"restore"`` (its actual wire value).
        * ``op=replace, path=details`` — update fields; ``value`` must
          be a :class:`~mammoth.models.automations.PatchAutomationDetails`
          with at least one of name/description/tasks/conditions set.

Returns:
    Dict with updated automation info.

Raises:
    MammothValidationError: If *automation_id* ≤ 0, *patch* is empty,
        or an op+path+value combination is invalid.

#### `update_schedule(self, schedule_id: 'int', patch: '_list[SchedulePatchItem]') -> 'dict[str, Any]'`

Update a schedule via JSON-patch operations.

Args:
    schedule_id: ID of the schedule (must be > 0).
    patch: Non-empty list of :class:`SchedulePatchItem`.

        Supported combos:

        * ``op=replace, path=rrule`` — update recurrence rule + work items;
          ``value`` must be a
          :class:`~mammoth.models.automations.SchedulePatchValue`.
        * ``op=replace, path=status`` — pause or resume; ``value`` must
          be ``"pause"`` or ``"resume"``.

Returns:
    Dict with updated schedule info.

Raises:
    MammothValidationError: If *schedule_id* ≤ 0, *patch* is empty,
        or an op+path+value combination is invalid.

---

## SchedulesAPI

### `SchedulesAPI`

Client for managing schedules under projects.

Access via ``client.schedules``::

    schedules = await client.schedules.list()
    schedule = await client.schedules.create(
        spec=ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=datetime(2025, 1, 1)),
        )
    )
    await client.schedules.delete(schedule_id)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, spec: 'ScheduleCreateSpec', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a new schedule.

Args:
    spec: :class:`~mammoth.models.automations.ScheduleCreateSpec` describing
        the recurrence rule and optional work items.
    project_id: Project ID (uses client default if not provided; must
        be > 0 if given).

Returns:
    Dict with created schedule info.

Raises:
    MammothValidationError: If *project_id* ≤ 0 or ``rrule.interval`` ≤ 0.

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

.. note::

    The server may not support listing all schedules (HTTP 405).
    Use :meth:`get` to retrieve individual schedules by ID.

Args:
    project_id: Project ID (uses client default if not provided).
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).

Returns:
    Dict with schedules list and pagination info.

#### `update(self, schedule_id: 'int', patch: '_list[SchedulePatchItem]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a schedule via JSON-patch operations.

Args:
    schedule_id: ID of the schedule (must be > 0).
    patch: Non-empty list of :class:`~mammoth.api.automations.SchedulePatchItem`.

        Supported combos:

        * ``op=replace, path=rrule`` — update recurrence rule + work items;
          ``value`` must be a
          :class:`~mammoth.models.automations.SchedulePatchValue`.
        * ``op=replace, path=status`` — pause or resume; ``value`` must
          be ``"pause"`` or ``"resume"``.

    project_id: Project ID (uses client default if not provided; must
        be > 0 if given).

Returns:
    Dict with updated schedule info.

Raises:
    MammothValidationError: If *schedule_id* ≤ 0, *project_id* ≤ 0,
        *patch* is empty, or an op+path+value combination is invalid.


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

#### `current(self) -> 'CurrentWorkspace'`

Ask which workspace this client's token acts in.

Returns:
    The workspace's ``id``, and the ``resource`` (RFC 8707) an OAuth
    token was issued for: the URI of the one server the user let it
    reach. ``resource`` is None for a token made by hand, and for a
    token issued for no server. ``read_only`` is True when the user
    granted the connection read-only access.

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

Get one workspace user, with roles and status.

The API has no GET for a single workspace user, so this reads the
member list (``__full`` fields) and returns the matching entry.

Args:
    user_id: ID of the user.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with user details.

Raises:
    MammothAPIError: 404 when the user is not in the workspace.

#### `list(self, limit: 'int' = 100) -> 'dict[str, Any]'`

List all accessible workspaces.

Args:
    limit: Maximum number of results (default 100).

Returns:
    Dict containing workspaces list with id and name.

#### `list_users(self, workspace_id: 'int | None' = None, fields: 'str | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`

List all users in a workspace (or the members of one project).

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    fields: Field set to return (e.g. ``"__full"`` adds ``user_roles`` and
        ``status``); server default if omitted.
    project_id: Keep only members of this project.

Returns:
    List of user dicts. Pending invites are not included; see
    ``WorkspacesAPI.invite_list``.

#### `reactivate(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Reactivate a deactivated workspace.

Args:
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with reactivation result.

#### `update(self, patches: '_list[WorkspacePatchOp]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update workspace settings via JSON-patch operations.

The backend expects ``{"patches": [<ops>]}``.  Each op has:

- ``op``: ``"replace"`` (only supported op).
- ``path``: one of ``name``, ``metadata``, ``plan_id``, ``billing_cycle``.
- ``value``: type depends on path:

  - ``name`` → ``str`` 1–50 chars
  - ``metadata`` → ``dict``
  - ``plan_id`` → ``int``
  - ``billing_cycle`` → ``"monthly"``, ``"yearly"``, or ``"annual"``

Args:
    patches: Non-empty list of
        :class:`~mammoth.models.workspaces.WorkspacePatchOp` instances.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated workspace info.

Raises:
    MammothValidationError: If ``patches`` is empty.

#### `update_user(self, user_id: 'str', patches: '_list[UserRolePatchOp]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Update a user's role in the workspace via JSON-patch operations.

The backend expects ``{"patches": [{"op": "replace", "path": "role",
"value": "<role>"}]}``.

Allowed role values (:class:`~mammoth.models.workspaces.WorkspaceRoleType`):
``workspace_member``, ``workspace_admin``, ``workspace_owner``,
``workspace_guest``.

Args:
    user_id: Non-empty ID of the user to update.
    patches: Non-empty list of
        :class:`~mammoth.models.workspaces.UserRolePatchOp` instances.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with updated user info.

Raises:
    MammothValidationError: If ``user_id`` is empty or ``patches`` is empty.

---

## UserProfileAPI

### `UserProfileAPI`

Client for managing user profile and settings.

Access via client.user_profile::

    profile = await client.user_profile.get()
    await client.user_profile.update(first_name="New Name")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `change_password(self, current_password: 'str', new_password: 'str') -> 'dict[str, Any]'`

Change user password.

Retired: the server no longer serves ``POST /user/change_password``, so this
call answers 404. The web app changes it under Profile settings > Reset Password.

Args:
    current_password: Current password.
    new_password: New password.

Returns:
    Dict with result.

#### `connected_apps(self) -> 'dict[str, Any]'`

List the apps the signed-in user has authorised.

Returns:
    Dict ``{"result": [...]}``; each entry has ``id`` (the grant id that
    :meth:`revoke_connected_app` takes), ``client_name``, ``workspace_id``,
    ``project_id`` (None means all projects) and ``created_at``.

#### `get(self) -> 'dict[str, Any]'`

Get current user profile.

Returns:
    Dict with user profile information.

#### `get_preferences(self) -> 'dict[str, Any]'`

Get user preferences.

Returns:
    Dict with user preferences.

#### `revoke_connected_app(self, oauth_grant_id: 'int') -> 'dict[str, Any]'`

Disconnect one authorised app, so its tokens stop working.

Args:
    oauth_grant_id: ID of the grant, as listed by :meth:`connected_apps`.

Returns:
    Empty dict on success (the server answers 204).

#### `update(self, *, first_name: 'str | None' = None, last_name: 'str | None' = None) -> 'dict[str, Any]'`

Update the current user's own display name.

The endpoint (``PATCH /self``) takes a JSON-Patch-shaped body
(``{"patch": [{"op": "replace", "path": ..., "value": ...}]}``), not a
flat field dict, so this builds that envelope from the given name
parts. There is no ``email`` path on this endpoint's accepted
``path`` values (``first_name``, ``last_name``, ``password``,
``mfa``) -- an email change is out of scope here.

Args:
    first_name: New first name.
    last_name: New last name.

Returns:
    Dict with the updated profile.

Raises:
    MammothValidationError: Neither ``first_name`` nor ``last_name``
        was given.

#### `update_preferences(self, patch: 'list[dict[str, Any]] | None' = None, **prefs: 'Any') -> 'dict[str, Any]'`

Update user preferences.

The route takes ``{"patch": [{"op": "replace", "path": ..., "value": ...}]}``
where ``path`` is a dot-separated preference path rooted at ``GLOBAL``
or ``WORKSPACE_PREFERENCES`` (for example
``GLOBAL.PREFERENCES.TOP_TABS``). Keyword arguments are turned into
``replace`` operations on the given path.

Args:
    patch: Explicit patch operations.
    **prefs: ``path=value`` shortcuts, each becoming a ``replace``.

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

#### `bulk_delete(self, folder_ids: '_list[int] | None' = None, check_dependency: 'bool | None' = None, remove_contents: 'bool | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`

Bulk delete folders, matching the ``DeleteFolders`` operation directly.

Unlike :meth:`delete`, every query parameter here is optional — omitting
``folder_ids`` lets the server apply its own default deletion scope.

Args:
    folder_ids: Folder IDs to delete (optional).
    check_dependency: Whether to check for dependencies before deleting.
    remove_contents: Whether to remove folder contents before deleting.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    None.

#### `create(self, name: 'str', parent_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'FolderSchema'`

Create a new folder.

Args:
    name: Name for the new folder.
    parent_resource_id: Parent folder resource ID (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    FolderSchema with created folder info (id, name, resource_id, etc.).

#### `delete(self, folder_ids: '_list[int]', workspace_id: 'int | None' = None, project_id: 'int | None' = None, check_dependency: 'bool' = True, remove_contents: 'bool' = True) -> 'None'`

Delete multiple folders.

Args:
    folder_ids: List of folder IDs to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    check_dependency: Check for dependency before deleting.
    remove_contents: Remove folder contents before deleting.

#### `get(self, folder_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, fields: 'str | None' = None) -> 'FolderSchema'`

Get a single folder by ID.

Args:
    folder_id: ID of the folder (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    fields: Fields to return (e.g., "__standard", "__full", "__min").

Returns:
    FolderSchema with the folder's details.

Raises:
    MammothValidationError: If folder_id is not a positive integer.

#### `get_project_root(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'FolderSchema'`

Get a FolderSchema representing the project root folder.

In Mammoth, the project root is not a physical folder entity — it is the
implicit top-level container.  The returned object has
``resource_id=None``.  When passed to ``files.upload(folder_resource_id=...)``,
a ``None`` resource_id causes files to be placed at the project root (the
same as omitting the parameter entirely).

Args:
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    FolderSchema with ``name="Project Root"`` and ``resource_id=None``.

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

#### `move(self, resource_ids: '_list[str] | None' = None, target_folder_resource_id: 'str | None' = None, source_folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None, *, dataset_ids: '_list[int] | None' = None, view_ids: '_list[int] | None' = None) -> 'ObjectJobSchema'`

Move resources between folders.

Args:
    resource_ids: Raw resource ids to move. This is NOT a dataset's or
        view's own id — it is the ``resource_id`` field returned by
        the resources lookup the SDK uses internally for
        ``dataset_ids``/``view_ids`` below. Prefer those two params
        unless you already have a resource id from elsewhere.
    target_folder_resource_id: The target folder's id — the ``id``
        field ``folder list``/``folder get``/``folder create``
        return (despite this parameter's name, NOT the folder's
        ``resource_id`` field). ``None``/``""``/``"root"`` moves to
        the project root.
    source_folder_resource_id: Same id kind as
        ``target_folder_resource_id``. Accepted for compatibility;
        the route infers the source itself.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    dataset_ids: Dataset ids, as returned by ``dataset get``/``dataset
        list`` (their ``id`` field). Resolved to resource ids
        automatically — use this instead of ``resource_ids`` when all
        you have is the dataset's own id.
    view_ids: View ids, as returned by ``view get``/``view list``
        (their ``id`` field). Resolved to resource ids automatically —
        use this instead of ``resource_ids`` when all you have is the
        view's own id.

Returns:
    ObjectJobSchema with job information for the move.

Raises:
    MammothValidationError: If no ids are given in any of
        ``resource_ids``/``dataset_ids``/``view_ids``, or if a
        dataset/view id in ``dataset_ids``/``view_ids`` can't be
        resolved to a resource id.

#### `trash(self, folder_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'JobResponse'`

Trash a folder's contents and hard-delete the now-empty folder.

Args:
    folder_id: ID of the folder to trash (must be a positive integer).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    JobResponse with job information for the trash operation.

Raises:
    MammothValidationError: If folder_id is not a positive integer.

#### `update(self, folder_id: 'int', name: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'FolderSchema'`

Update folder details (currently supports renaming only).

Args:
    folder_id: ID of the folder to update (must be a positive integer).
    name: New name for the folder.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    FolderSchema with the updated folder details.

Raises:
    MammothValidationError: If folder_id is not a positive integer.

---

## BatchesAPI

**Access**: `client.batches`

Client for managing dataset batch operations.

Access via client.batches::

    batches = await client.batches.list(dataset_id=123)
    batch = await client.batches.get(dataset_id=123, batch_id=1)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `bulk_delete(self, dataset_id: 'int', ids: '_list[int] | str | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk-delete batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    ids: Batch IDs (list or comma-separated string) to delete. The
        backend requires them; omitting ``ids`` is rejected, it does
        not delete every batch.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

#### `create(self, dataset_id: 'int', source_id: 'int', mapping: 'dict[str, str] | _list[dict[str, Any]]', project_id: 'int | None' = None, new_ds_params: 'dict[str, Any] | None' = None, is_validation_required: 'bool | None' = None, change_map: 'dict[str, Any] | None' = None, delete_source_ds: 'bool' = False, expected_destination_c_type: 'str' = 'TEXT') -> 'dict[str, Any]'`

Create a new batch for a dataset.


Args:
    dataset_id: ID of the destination dataset.
    source_id: ID of the source dataset (must be a positive integer).
    mapping: Non-empty ``{"src_col": "dst_col"}`` dict (expanded to
        ``ColumnNameMapping`` items, each stamped with
        ``expected_destination_c_type``) or an explicit list of
        ``ColumnNameMapping`` / ``ColumnIdMapping`` objects, every
        item carrying its own ``expected_destination_c_type``
        (``TEXT``, ``NUMERIC`` or ``DATE``; the route requires it).
    project_id: Project ID (uses client default if not provided).
    new_ds_params: Optional params for creating a new dataset.
    is_validation_required: Whether to validate the batch.
    change_map: Optional change-tracking column map.
    delete_source_ds: Whether to delete the source dataset after batch
        (default ``False``).
    expected_destination_c_type: Type stamped on every item of a
        ``{src: dst}`` mapping dict (default ``"TEXT"``); ignored for
        list mappings, which carry their own.

Returns:
    Dict with created batch info.

Raises:
    MammothValidationError: If ``source_id`` is not positive or ``mapping``
        is empty.

#### `create_spec(self, dataset_id: 'int', spec: 'BatchesPostRequest | dict[str, Any]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Create a batch using the release ``BatchesPostRequest`` shape.

This additive method preserves the older ``create`` contract while
supporting either ``source_id`` plus array ``mapping`` or ``file_id``
alone.  The CLI owns confirmation policy for destructive calls.

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

#### `list(self, dataset_id: 'int', project_id: 'int | None' = None, limit: 'int' = 50, offset: 'int' = 0) -> 'dict[str, Any]'`

List batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    project_id: Project ID (uses client default if not provided).
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).

Returns:
    Dict with batches list and pagination info.

#### `update(self, dataset_id: 'int', patch: 'dict[str, Any] | _list[dict[str, Any]]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update batches for a dataset via a patch operation.

The backend expects ``{"patch": <op>}`` with exactly one operation:

- ``op``: ``"replace"`` or ``"remove"``
- ``path``: ``"batches"`` (filled in when left out)
- ``value``: ``{"suspend": [batch ids], "restore": [batch ids]}``

Args:
    dataset_id: ID of the dataset.
    patch: The operation dict, or a list holding that one dict.  It must
        include ``"op"`` (``"replace"`` or ``"remove"``) and ``"value"``.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with updated batch info.

Raises:
    MammothValidationError: If ``patch`` is empty or any op has an
        invalid ``op`` value.

---

## BrowseAPI

**Access**: `client.browse`

Client for browsing and discovering resources.

Access via client.browse::

    resources = await client.browse.workspaces()
    resources = await client.browse.projects()
    resources = await client.browse.datasets(project_id=10)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `datasets(self, project_id: 'int | None' = None, workspace_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None) -> 'dict[str, Any]'`

Browse datasets in a project.

Args:
    project_id: Project ID (uses client default if not provided).
    workspace_id: Workspace ID (uses client default if not provided).
    fields: Field set to return, e.g. ``"__min"``; server default if
        omitted.
    limit: Maximum number of results.
    offset: Number of results to skip.

Returns:
    Dict with dataset resources.

#### `dataviews(self, dataset_id: 'int', project_id: 'int | None' = None, workspace_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None) -> 'dict[str, Any]'`

Browse dataviews in a dataset.

Args:
    dataset_id: ID of the dataset.
    project_id: Project ID (uses client default if not provided).
    workspace_id: Workspace ID (uses client default if not provided).
    fields: Field set to return, e.g. ``"__min"``; server default if
        omitted.
    limit: Maximum number of results.
    offset: Number of results to skip.

Returns:
    Dict with dataview resources.

#### `folder_resources(self, folder_id: 'int', project_id: 'int | None' = None, workspace_id: 'int | None' = None, level: 'int' = 2, fields: 'str' = '__min') -> 'dict[str, Any]'`

Browse resources inside a folder.

Args:
    folder_id: ID of the folder (label).
    project_id: Project ID (uses client default if not provided).
    workspace_id: Workspace ID (uses client default if not provided).
    level: Depth of children to include (1 or 2, default 2).
    fields: Fields to return (default "__min").

Returns:
    Dict with folder's child resources.

#### `projects(self, workspace_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None) -> 'dict[str, Any]'`

Browse projects in a workspace.

Args:
    workspace_id: Workspace ID (uses client default if not provided).
    fields: Field set to return, e.g. ``"__min"``; server default if
        omitted.
    limit: Maximum number of results.
    offset: Number of results to skip.

Returns:
    Dict with project resources.

#### `resource_ancestors(self, resource_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the folder path of a folder: the chain from the project root down to it.

The breadcrumb for a deep link that knows only the folder's id.

Args:
    resource_id: The folder's ``resource_id`` as resources v2 returns it
        (not its object id). A value of 0 or less means the project root.
    project_id: Project ID (uses the client default if not provided).

Returns:
    Dict ``{"resources": [...]}``, root first and ending with the folder
    itself; empty for the project root. The route answers 404 when the
    id is not a live folder in the project.

#### `resource_get(self, resource_type: 'str', object_id: 'int', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get one resource with its full properties (resources v2).

Args:
    resource_type: Resource type, e.g. ``dataset`` or ``dataview``.
    object_id: ID of the resource within that type.
    project_id: Project ID (uses the client default if not provided).

Returns:
    Dict ``{"resource": {...}}``.

#### `resources_bulk(self, items: 'list[tuple[str, int]]', project_id: 'int | None' = None) -> 'list[dict[str, Any]]'`

Get many resources of one project by ``(type, object id)`` pair (resources v2).

One request per 100 pairs, the route's cap. A dataview row carries its
parent in ``dataset`` (``{id, name}``). Pairs that do not exist in the
project, or that the caller cannot read, are left out of the result.

Args:
    items: ``(resource_type, object_id)`` pairs, e.g. ``("dataview", 42)``.
    project_id: Project ID (uses the client default if not provided).

Returns:
    The resources found, each as ``resource_get`` returns them.

#### `resources_list(self, project_id: 'int | None' = None, parent_type: 'str | None' = None, parent_id: 'int | None' = None, resource_type: 'str | None' = None, search: 'str | None' = None, cursor: 'str | None' = None, limit: 'int | None' = None, sort: 'str | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

List one project's resources, a cursor page at a time (resources v2).

Args:
    project_id: Project ID (uses the client default if not provided).
    parent_type: Type of the folder-like parent to list inside.
    parent_id: ID of that parent; omit for the project root.
    resource_type: Keep only this resource type.
    search: Keep only resources whose name matches.
    cursor: ``next_cursor`` of the previous page.
    limit: Page size; the route defaults to 50.
    sort: Sort specification.
    fields: Field set to return; the route defaults to ``standard``.

Returns:
    Dict with ``resources``, ``next_cursor`` and ``has_more``.

#### `resources_search(self, search: 'str | None' = None, resource_type: 'str | None' = None, cursor: 'str | None' = None, limit: 'int | None' = None, sort: 'str | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

Search resources across every project the user can open in the workspace.

Args:
    search: Keep only resources whose name matches.
    resource_type: Keep only these types (comma-separated).
    cursor: ``next_cursor`` of the previous page.
    limit: Page size; the route defaults to 50.
    sort: Sort specification.
    fields: Field set to return; the route defaults to ``standard``.

Returns:
    Dict with ``resources``, ``next_cursor`` and ``has_more``.

#### `root(self, fields: 'str | None' = None, name: 'str | None' = None, browse_type: 'str | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, sort: 'str | None' = None, offset: 'int | None' = None, limit: 'int | None' = None, ids: 'str | None' = None, include_hidden: 'bool | None' = None, level: 'int | None' = None, permissions: 'str | None' = None) -> 'dict[str, Any]'`

Browse resources across all workspaces the caller has access to.

This is the top-level, non-workspace-scoped browse endpoint (``/browse``).

Args:
    fields: Comma-separated list of fields to include in the response.
    name: Filter by resource name.
    browse_type: Filter by resource type (e.g. "workspace", "project").
    created_at: Filter by creation date.
    updated_at: Filter by last-updated date.
    sort: Sort order for results.
    offset: Number of results to skip.
    limit: Maximum number of results.
    ids: Comma-separated list of resource IDs to filter by.
    include_hidden: Whether to include hidden resources.
    level: Depth of children to include.
    permissions: Filter by permission level.

Returns:
    Dict with browse resources.

#### `workspace_resources(self, workspace_id: 'int | None' = None, level: 'int' = 2, fields: 'str' = '__min', limit: 'int' = 100) -> 'dict[str, Any]'`

Browse all resources in a workspace (projects, datasets, folders).

Args:
    workspace_id: Workspace ID (uses client default if not provided).
    level: Depth of children to include (1 or 2, default 2).
    fields: Fields to return (default "__min").
    limit: Max resources to return (default 100).

Returns:
    Dict with hierarchical resource list.

#### `workspaces(self, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None) -> 'dict[str, Any]'`

Browse available workspaces.

Args:
    fields: Field set to return, e.g. ``"__min"``; server default if
        omitted.
    limit: Maximum number of results.
    offset: Number of results to skip.

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

.. note::

    Requires admin role — non-admin users receive HTTP 401.

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

    keys = await client.external_keys.list()
    key = await client.external_keys.create(name="My Key")
    await client.external_keys.delete(key_id)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `create(self, key_type: 'ExternalKeyType', key_name: 'str', secure_key: 'str', description: 'str | None' = None, model_id: 'str | None' = None, model_settings: 'ModelConfigSpec | None' = None) -> 'dict[str, Any]'`

Create a new external (LLM provider) API key.

Args:
    key_type: Provider the key authenticates against.
    key_name: Human-readable name for the key.
    secure_key: The secret key value (>= 3 characters).
    description: Optional description of the key's purpose.
    model_id: Optional specific model to use (defaults to the
        provider's recommended model server-side).
    model_settings: Optional per-key model configuration overrides;
        requires *model_id* to be set.

Returns:
    Dict with created key info.

Raises:
    MammothValidationError: If *key_name* is empty, *secure_key* is too
        short, or *model_settings* is given without *model_id*.

Example::

    await client.external_keys.create(
        key_type=ExternalKeyType.ANTHROPIC,
        key_name="My Claude key",
        secure_key="sk-ant-...",
    )

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

    logs = await client.activity_logs.list()
    export = await client.activity_logs.export(format="csv")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `export(self, format: 'str' = 'csv', **filters: 'Any') -> 'dict[str, Any]'`

Export activity logs.

Args:
    format: Export format (default "csv").
    **filters: Filter parameters for the export.

Returns:
    Dict with export result (may include download URL or job ID).

#### `list(self, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None, project_id: 'int | None' = None, categories: 'list[Any] | None' = None, activities: 'list[Any] | None' = None, resource_id: 'str | None' = None, result: 'str | None' = None, start_time: 'str | None' = None, end_time: 'str | None' = None, origin: 'str | None' = None, user_ids: 'list[Any] | None' = None, parent_id: 'int | None' = None, search_text: 'str | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

List activity logs.

Args:
    limit: Maximum number of results (default 50).
    offset: Number of results to skip (default 0).
    sort: Sort specification.
    project_id: Filter to one project's activity.
    categories: Filter by activity categories (e.g. "Project", "Dataview").
    activities: Filter by activity names (e.g. "create_project").
    resource_id: Filter to one resource's activity.
    result: Filter by outcome (e.g. "success").
    start_time: Filter to activity at or after this time.
    end_time: Filter to activity at or before this time.
    origin: Filter by request origin (e.g. "user").
    user_ids: Filter by the ids of the users who performed the activity.
    parent_id: Filter by the parent resource id.
    search_text: Free-text search across activity log entries.
    fields: Entry fields to return (comma list or a mode such as "__min");
        the route's default carries each entry's full details.

Returns:
    Dict with activity logs and pagination info.

---

## AddonsAPI

**Access**: `client.addons`

Client for managing workspace addons (connectors, storage, users).

Access via client.addons::

    await client.addons.add_connector(connector_id=42)
    await client.addons.add_connector(connector_ids=[42, 43])
    await client.addons.add_storage(additional_storage_gb=50)
    await client.addons.add_users(user_count=5)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_connector(self, connector_id: 'int | None' = None, connector_ids: '_list[int] | None' = None) -> 'dict[str, Any]'`

Add one or more connector addons to the workspace.

Provide exactly one of *connector_id* (single) or *connector_ids* (bulk).

Args:
    connector_id: A single connector id to add.
    connector_ids: A non-empty list of connector ids to add.

Returns:
    Dict with addon result.

Raises:
    MammothValidationError: If neither or both arguments are given, or
        any id is not a positive integer.

#### `add_storage(self, additional_storage_gb: 'int') -> 'dict[str, Any]'`

Add storage capacity to the workspace.

Args:
    additional_storage_gb: GB of storage to add (positive integer).

Returns:
    Dict with addon result.

Raises:
    MammothValidationError: If *additional_storage_gb* is not positive.

#### `add_users(self, user_count: 'int' = 1) -> 'dict[str, Any]'`

Add user seats to the workspace.

Args:
    user_count: Number of seats to add (positive integer, default 1).

Returns:
    Dict with addon result.

Raises:
    MammothValidationError: If *user_count* is not positive.

#### `list(self) -> 'dict[str, Any]'`

List active addons for the workspace.

Retired: the server no longer serves ``GET /workspaces/{id}/addons``, so this
call answers 404. The web app lists add-ons under Settings > Plan.

Returns:
    Dict with addon information.

#### `remove_connector(self, connector_id: 'int | None' = None, connector_ids: '_list[int] | None' = None) -> 'dict[str, Any]'`

Remove one or more connector addons from the workspace.

Provide exactly one of *connector_id* (single) or *connector_ids* (bulk).

Args:
    connector_id: A single connector id to remove.
    connector_ids: A non-empty list of connector ids to remove.

Returns:
    Dict with removal result.

Raises:
    MammothValidationError: If neither or both arguments are given, or
        any id is not a positive integer.

#### `remove_storage(self, removal_storage_gb: 'int') -> 'dict[str, Any]'`

Remove storage capacity from the workspace.

Args:
    removal_storage_gb: GB of storage to remove (positive integer).

Returns:
    Dict with removal result.

Raises:
    MammothValidationError: If *removal_storage_gb* is not positive.

#### `remove_users(self, user_count: 'int') -> 'dict[str, Any]'`

Remove user seats from the workspace.

Args:
    user_count: Number of seats to remove (positive integer).

Returns:
    Dict with removal result.

Raises:
    MammothValidationError: If *user_count* is not positive.

---

## ReportsAPI

**Access**: `client.reports`

Client for listing workspace reports.

Access via client.reports::

    reports = await client.reports.list()

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
    client.ai.generate_sql(intent="total sales by region")
    suggestions = client.ai.get_suggestions()

#### `PROFILE_ACTIONS`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

#### `SUGGESTION_TYPES`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `condition_generate(self, intent: 'str', dataset_id: 'int', dataview_id: 'int | None' = None, sequence_number: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate a filter condition from a natural language intent.

Corresponds to the backend ``ConditionGenerationSpec``:
``{params: {intent, sequence_number}}``.

Args:
    intent: Natural language description of the desired condition.
    dataset_id: ID of the dataset to generate the condition against.
    dataview_id: Optional ID of the dataview for column context.
    sequence_number: Optional sequence order in the pipeline.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with the generated condition.

#### `expression_generate(self, intent: 'str', mode: 'str', dataset_id: 'int', dataview_id: 'int | None' = None, sequence_number: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate a math/metric expression from a natural language intent.

Corresponds to the backend ``ExpressionGenerationSpec``:
``{params: {intent, mode, sequence_number}}``.

Args:
    intent: Natural language description of the desired expression.
    mode: ``"math"`` for a row-level numeric expression, or ``"metric"``
        for an aggregate 1-row-1-column expression.
    dataset_id: ID of the dataset to generate the expression against.
    dataview_id: Optional ID of the dataview for column context.
    sequence_number: Optional sequence order in the pipeline.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with the generated expression.

Raises:
    MammothValidationError: If ``mode`` is not ``"math"`` or ``"metric"``.

#### `generate_data(self, dataview_id: 'int', prompt: 'str', no_of_rows: 'int' = 10, columns: 'list[str] | None' = None, dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate synthetic data for a dataview.

Corresponds to the backend ``GenAISpec``:
``{prompt, no_of_rows (1–100), columns}``.

Args:
    dataview_id: ID of the dataview.
    prompt: Non-empty string describing what data to generate.
    no_of_rows: Number of rows to generate (1–100, default 10).
    columns: Optional list of column names to fill.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with generation result or job info.

Raises:
    MammothValidationError: If ``prompt`` is empty or ``no_of_rows``
        is outside the 1–100 range.

#### `generate_profile(self, dataview_id: 'int', dataset_id: 'int | None' = None, action: 'str' = 'insights') -> 'dict[str, Any]'`

Generate an AI profile/summary of the dataview data.

Corresponds to the backend ``ProfileGenerationSpec``:
``{"params": {"action": <action>}}``.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).
    action: One of ``"stats"``, ``"insights"`` (default),
        ``"data_quality"`` or ``"join_recommendation"``.

Returns:
    Dict with profile information.

Raises:
    MammothValidationError: If ``action`` is not a supported value.

#### `generate_sql(self, intent: 'str', sequence_number: 'int' = 0, dataset_id: 'int | None' = None, dataview_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate SQL from natural language intent.

Uses the project-level sql_generation endpoint, which requires the
``dataset_id`` query parameter (``dataview_id`` optional).

Args:
    intent: Natural language description of the query.
    sequence_number: Sequence number for the SQL generation request.
    dataset_id: Dataset the SQL is generated against (required).
    dataview_id: Optional dataview within that dataset.

Returns:
    Dict with generated SQL and metadata.

#### `get_data_gen_info(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get data generation information for a dataview.

The route answers only a validation request, so ``validate_only=true`` is sent.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with data generation info.

#### `get_suggestions(self, suggestion_type: 'str | None' = None, params: 'dict[str, Any] | None' = None, dataset_id: 'int | None' = None, dataview_id: 'int | None' = None) -> 'dict[str, Any]'`

Get AI-powered suggestions for the current project.

Corresponds to the backend ``UnifiedPromptSpec``:
``{"suggestion_type": <type>, "params": {...}}`` where the ``params``
shape depends on the type (e.g. ``generate_task`` takes ``{"prompt"}``,
``add_condition`` takes ``{"prompt", "sequence_number"}``,
``extract_text`` takes ``{"column_name", "sequence_number", "prompt"}``).

Args:
    suggestion_type: One of ``extract_text``, ``add_condition``,
        ``generate_task``, ``apply_ai_template``, ``dashboards`` or
        ``derivative_fuzzy_bucket`` (required).
    params: Type-specific parameters (required).
    dataset_id: Optional dataset to scope the suggestions to
        (query parameter).
    dataview_id: Optional dataview to scope the suggestions to
        (query parameter).

Returns:
    Dict with suggestions.

Raises:
    MammothValidationError: If ``suggestion_type`` or ``params`` is
        missing or the type is unknown.

#### `query_gen(self, connector_key: 'str', connection_key: 'str', query: 'str', project_id: 'int | None' = None, profile: 'str | None' = None) -> 'dict[str, Any]'`

Generate a query for a connector using AI.

Corresponds to the backend ``Intent`` body: ``{"query": <intent>,
"profile": <optional profile>}``.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    query: Natural language intent describing the query.
    project_id: Project ID (uses client default if not provided).
    profile: Optional connector profile name.

Returns:
    Dict with generated query.

#### `retention_condition(self, dataset_id: 'int', mode: 'str', intent: 'str | None' = None, condition_sql: 'str | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate or test a retention-policy WHERE clause.

``mode='generate'`` requires a natural-language ``intent`` and may
return an asynchronous job. ``mode='test'`` requires ``condition_sql``
and returns per-batch row counts (the API's union response may still
be a job envelope). The request is always explicitly scoped to the
client's workspace and selected project.

#### `status(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the status of an AI chat session for a connector connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with chat status information.


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
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
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
dataset_id = await client.files.upload("sales_data.csv")
print(f"Created dataset: {dataset_id}")

# Get the default View for the uploaded dataset
views = await client.views.list(dataset_id=dataset_id)
view = views[0]
```

Other upload options:

```python
# Multiple files at once
dataset_ids = await client.files.upload(["sales.csv", "customers.xlsx"])

# Upload an entire folder
dataset_ids = await client.files.upload_folder("./data/")

# Append to an existing dataset
await client.files.upload("new_rows.csv", append_to_ds_id=dataset_id)
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
result = await view.data(limit=5)
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
> await view.convert_type([ConversionSpec(column="Order Date", to=ColumnType.DATE, format="MM/DD/YYYY")])
> ```
>

## 5. Apply transformations

### Filter rows

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
await view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Negate a condition with ~
await view.filter_rows(~Condition("Status", Operator.EQ, "Cancelled"))
```

### Add computed columns

```python
from mammoth import ColumnType, SetValue

# Conditional labeling
await view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),
    ],
)

# Math expression
await view.math("Price * Quantity", new_column="Revenue")
```

### Aggregate with pivot

```python
from mammoth import AggregateFunction, AggregationSpec

await view.pivot(
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
await view.text_transform(["Customer"], case=TextCase.UPPER)

# Date: extract year
await view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")

# Window: rank within groups
await view.window(
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
path = await view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

### Export to S3

```python
result = await view.export.to_s3(file_name="monthly_report.csv")
```

### Export to a database

```python
# PostgreSQL
await view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_summary",
    username="user",
    password="pass",
)

# MySQL
await view.export.to_mysql(
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
await view.export.to_bigquery(...)
await view.export.to_redshift(...)
await view.export.to_sftp(host="sftp.example.com", path="/exports/data.csv", username="user", password="pass")
await view.export.to_email(recipients=["team@example.com"])
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
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
)
client.set_project_id(42)

try:
    # 2. Upload data
    dataset_id = await client.files.upload("sales_data.csv")
    views = await client.views.list(dataset_id=dataset_id)
    view = views[0]
    print(f"Uploaded: {view.name} ({len(view.display_names)} columns)")

    # 3. Clean data
    await view.filter_rows(
        Condition("Region", Operator.IS_EMPTY),
        filter_type=FilterType.REMOVE,
    )
    await view.filter_rows(Condition("Sales", Operator.GTE, 0))

    # 4. Transform
    await view.set_values(
        new_column="Tier",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
            SetValue("Basic"),
        ],
    )
    await view.math("Price * Quantity", new_column="Revenue")

    # 5. Export
    path = await view.export.to_csv("output.csv")
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
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
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
dataset_id = await client.files.upload("sales_data.csv")

# Upload multiple files at once
dataset_ids = await client.files.upload(["sales.csv", "customers.xlsx"])

# Upload all files in a folder
dataset_ids = await client.files.upload_folder("./data/")

# After upload, get the view for the new dataset
views = await client.views.list(dataset_id=dataset_id)
view = views[0]
print(view.display_names)
```

## List resources

```python
# List projects — returns envelope dict, unwrap "projects" key
resp = await client.projects.list()
projects = resp["projects"]                 # list of plain dicts
for p in projects:
    print(p["id"], p["name"])               # dict access, NOT p.id / p.name

# List datasets
datasets = await client.datasets.list()

# List all views in a dataset (returns list of View objects)
views = await client.views.list(dataset_id=42)
for v in views:
    print(f"{v.id}: {v.name} ({len(v.display_names)} columns)")
```

## Get a View and inspect it

```python
view = await client.views.get(1039)

print(f"Name: {view.name}")
print(f"Columns: {view.display_names}")
print(f"Types: {view.column_types}")
print(f"Column mapping: {view.columns}")
```

## Fetch data

```python
# First 100 rows
result = await view.data(limit=100)

# Specific columns
result = await view.data(columns=["Sales", "Region"], limit=50)

# With a condition
from mammoth import Condition, Operator
result = await view.data(
    condition=Condition("Sales", Operator.GTE, 1000),
    limit=200,
)
```

## Apply a transformation

```python
from mammoth import Condition, Operator

await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
print(f"Columns after filter: {view.display_names}")
```

## Export to CSV

```python
path = await view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

## Context manager

```python
async with MammothClient(
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
) as client:
    client.set_project_id(10)
    view = await client.views.get(1039)
    await view.export.to_csv("output.csv")
# Session closed automatically
```

## Pipeline management

```python
# List tasks on a view
tasks = await view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key', 'unknown')}")

# Delete a task
await view.delete_task(task_id=42)

# Preview a task before applying
preview = await view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

## Create and clone views

```python
# Create a new empty view
new_view = await client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
clone = await client.views.create(dataset_id=42, name="Copy of Analysis", clone_from=1039)

# Delete a view
await client.views.delete(view_id=new_view.id)
```

## Complete workflow

```python
import asyncio
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

async def main():
    client = MammothClient(
        api_token=os.getenv("MAMMOTH_API_TOKEN"),
    )
    client.set_project_id(10)

    try:
        view = await client.views.get(1039)
        print(f"View: {view.name} ({len(view.display_names)} columns)")

        # Filter
        await view.filter_rows(Condition("Sales", Operator.GTE, 1000))

        # Add a label
        await view.set_values(
            new_column="Tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
                SetValue("Standard"),
            ],
        )

        # Export
        path = await view.export.to_csv("output.csv")
        print(f"Exported to {path}")

    except MammothAPIError as e:
        print(f"Error: {e.message} (HTTP {e.status_code})")

if __name__ == "__main__":
    asyncio.run(main())
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
    client = MammothClient(api_token="mm_bad")
    client.set_project_id(1)
    await client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API token")
```

### API errors

```python
from mammoth import MammothAPIError

try:
    datasets = await client.datasets.list()
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
    await view.filter_rows(Condition("Nonexistent Column", Operator.GTE, 100))
except MammothColumnError as e:
    print(e.message)
    # "Column 'Nonexistent Column' not found. Available columns: ['Sales', 'Region', ...]"
    print(f"Available columns: {e.details['available_columns']}")
```

### Job timeout

```python
from mammoth import MammothJobTimeoutError

try:
    await view.pivot(
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
    await view.convert_type([{"column": "Sales", "to": "NUMERIC"}])
except MammothJobFailedError as e:
    print(f"Job {e.details['job_id']} failed")
    print(f"Reason: {e.details.get('failure_reason', 'Unknown')}")
```

### Transform errors

```python
from mammoth import MammothTransformError

try:
    await view.math("InvalidExpr @@@ 2", new_column="Result")
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
    view = await client.views.get(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.export.to_csv("output.csv")

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
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
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
    api_token="mm_...",
    job_timeout=300,  # 5 minutes instead of default 60s
)
```

Or increase the timeout for CSV exports:

```python
await view.export.to_csv("output.csv", timeout=600)  # 10 minutes
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
    api_token="mm_your-token",
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
    api_token="mm_...",
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
await view.export.to_csv("output.csv", timeout=600)  # 10 minutes
```

## No automatic retries

The SDK does not implement retries. If an API call fails due to a transient error, the exception is raised immediately. Implement retry logic at the application level if needed:

```python
import asyncio
from mammoth import MammothAPIError

async def with_retry(fn, max_retries=3, backoff=2):
    """Await ``fn()`` — a function returning a coroutine — retrying server errors."""
    for attempt in range(max_retries):
        try:
            return await fn()
        except MammothAPIError as e:
            if e.status_code and 400 <= e.status_code < 500:
                raise  # Do not retry client errors
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(backoff ** attempt)

view = await with_retry(lambda: client.views.get(1039))
```

## Environment-based configuration

```python
import os

config = {
    "api_token": os.environ["MAMMOTH_API_TOKEN"],
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

Every SDK call that reaches the API is a **coroutine**: `await` it. An awaited transformation returns once the operation completes and the view metadata is refreshed. The backend runs tasks as background jobs; the SDK polls them for you while you wait.

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
    await view.pivot(
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
tasks = await view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key')} (seq {task.get('sequence')})")

# Delete a task (re-runs the pipeline without it)
await view.delete_task(task_id=42)

# Preview a task before applying
preview = await view.preview_task(task_spec)
```

## Draft mode

By default, each transformation triggers an immediate pipeline run. For batch operations on large datasets, use **draft mode** to queue tasks and run the pipeline once:

```python
from mammoth import Condition, Operator, SetValue, ColumnType

# Context manager approach (recommended)
async with view.draft():
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.math("Price * 2", new_column="Double")
# Pipeline runs once for both tasks

# Explicit approach
await view.enter_draft_mode()
await view.add_column("Notes")
await view.set_values(new_column="Flag", column_type=ColumnType.TEXT, values=[SetValue("x")])
await view.submit_draft()  # runs pipeline, refreshes metadata, exits draft mode
```

If an exception occurs inside the `async with view.draft():` block, all queued tasks are discarded automatically. You can also discard explicitly with `view.discard_draft()`.

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
await view.export.to_postgres(
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
await view.export.to_mysql(
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
result = await view.export.to_s3(file_name="report.csv")
```

## Export to BigQuery

```python
await view.export.to_bigquery(
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

client = MammothClient(api_token="mm_...")
client.set_project_id(10)

# 1. Export from your source database to CSV
df = pd.read_sql("SELECT * FROM customers WHERE status = 'active'", connection)
df.to_csv("customers.csv", index=False)

# 2. Upload to Mammoth
await client.files.upload("customers.csv")
```

## Branch out to another dataset

Send processed data from one view to another Mammoth dataset:

```python
await view.branch_out(dest_dataset_id=42)

# With column mapping
await view.branch_out(
    dest_dataset_id=42,
    column_mapping={"Sales": "revenue", "Region": "area"},
)
```

## Webhook integration

Set up webhooks to receive notifications on pipeline events:

```python
webhooks = await client.webhooks.list()
```

## Scheduled automation

Use automations and schedules for recurring workflows:

```python
schedules = await client.schedules.list()
automations = await client.automations.list()
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

- Verify your API token is correct (it starts with `mm_`)
- Confirm the `workspace_id` matches your account
- Check that the `base_url` points to the correct Mammoth instance
- Ensure your API credentials have not been revoked or rotated

```python
# Verify your credentials
try:
    client = MammothClient(api_token="mm_...")
    if await client.test_connection():
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
await view.export.to_csv("output.csv", timeout=600)
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

    await view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])
except MammothJobFailedError as e:
    print(f"Reason: {e.details['failure_reason']}")
```

## project_id not set

**Symptom**: `ValueError: project_id must be set on the client using client.set_project_id()`

**Solution**: Call `client.set_project_id(id)` before performing operations:

```python
client = MammothClient(api_token="mm_...")
client.set_project_id(10)  # Required before most operations
```

## Date columns not working

**Symptom**: Date operations fail on columns uploaded from CSV.

**Cause**: CSV date columns are uploaded as TEXT type by default.

**Solution**: Convert to DATE type first:

```python
await view.convert_type([{"column": "Order Date", "to": "DATE"}])
# Now date operations work
await view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
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

## v0.8.0

### Changed — breaking

- The SDK is async. Every method that calls the API is a coroutine and must be
  awaited: `await client.views.get(1039)`, `await view.filter_rows(...)`,
  `await client.datasets.list()`. `View.is_draft_mode` is an async property:
  `await view.is_draft_mode`. Pure builders and setters stay sync
  (`client.set_project_id`, `Condition`, the spec models).
- The transport is `httpx` instead of `requests`, which is no longer a
  dependency. API calls still raise `MammothAPIError` for transport failures;
  only code that uses `client.session` or `client.download_session` directly
  sees the change — both are `httpx.AsyncClient`s now.
- `MammothClient` is an async context manager: `async with MammothClient(...)
  as client:`. `close()` is a coroutine. The sync `with` form is gone.
- One client belongs to one event loop: its connection pool lives on the loop
  that first used it.

Migrating from 0.7.x:

1. Run SDK calls inside a coroutine, e.g. `asyncio.run(main())`.
2. Put `await` in front of every call that reaches the API.
3. Replace `with MammothClient(...)` with `async with MammothClient(...)`, or
   call `await client.close()`.

Code that must stay sync should pin `mammoth-io<0.8`.

### Added

- `MammothClient(api_root=...)` addresses the API server directly, for a
  caller inside the network. The default stays `"/api/v2"`.
- `MammothClient(job_poll_seconds=...)` and a `poll_interval=` argument on the
  job waits (`JobsAPI.wait_for_job`, `JobsAPI.wait_for_jobs`,
  `MammothClient.wait_if_job`, `PipelineAPI.wait_for_pipeline` and the data
  reads that wait) set how often a running job is asked. Default:
  `DEFAULT_JOB_POLL_SECONDS`.
- `fields=`, `limit=` and `offset=` on `BrowseAPI.workspaces` and `projects`
  ask for one page of smaller records.
- `PipelineAPI.preview_task(sample_size=...)`.
- `DashboardsAPI.generate_v3` builds a v3 dashboard. `DashboardsAPI.action`
  takes `params_sequence` (restore a version) and `params_filter_column`
  (row-level security).
- `DatasetsAPI.preview_interpretation`, `confirm_interpretation` and
  `discard_unstructured_rows`, for a file whose dataset stopped for a decision.

### Fixed

- `DataviewsAPI.get` and `query_data` no longer resolve and send a pipeline
  `sequence` when the caller gave none. The resolved value could be a staged
  draft step that never ran, so a read in draft mode failed with "Job failed".
  The API now picks the step, and one request fewer is made.
- `ExportsAPI.to_csv` (and `view.export.to_csv`) failed on every call under
  the async client: the download still used the `requests` streaming API. It
  now streams through `httpx`, with the same atomic write and error handling.
- `MammothClient.branch_out` returned an un-awaited coroutine instead of the
  dataset id.
- `DatasetsAPI.get_unstructured_rows` reads `.../unstructured_data`, the same
  route `discard_unstructured_rows` deletes from (it read
  `.../unstructured_rows` in 0.7.40).
- Automations accept the task types, statuses and commands the routes accept
  today; `"restore"` is accepted as well as `"resume"`.
- Export specs default the properties the route defaults.
- An API error keeps the reason the API gave instead of a bare status code.

## v0.7.18

### Fixed

- `View.fill_missing` and `FillDirection` documented the directions the wrong
  way round. `FIRST_VALUE` is the forward fill (a blank takes the previous
  row's value in the `order_by` order); `LAST_VALUE` is the back-fill (the
  next row's value). Verified on release; behaviour is unchanged.

## v0.7.17

### Added

- `View.rename_columns({"old": "new"})` and `View.sort_rows([["Col", "DESC"]])`:
  the web grid's column rename and sort, set as view display properties
  (`COLUMN_NAMES`, `SORT`). They add no pipeline task.

### Fixed

- A column renamed in the web app resolves by its new name: `View` applies
  the view's `COLUMN_NAMES` display property when it reads column metadata.

## v0.7.16

### Added

- `MammothClient(api_token="mm_...")`: API-token (Bearer) authentication. The
  `api_key` + `api_secret` pair is deprecated but still accepted.

## v0.7.15

### Added

- Math expressions accept a quoted display name (`"Unit Price"` or
  `` `Unit Price` ``) as well as the bare form; an unknown quoted name is
  named in the error.

## v0.7.14

### Fixed

- Transform methods returned the server's submit record (`status:
  "processing"`) after the pipeline had already finished. Outside draft mode
  the result now says `status: "done"` with `pipeline_state` (`"ready"`);
  in draft mode it is unchanged, since the task is only queued.

## v0.7.13

- Added `target_project_id` to `View.to_dataset()` and `View.branch_out()`:
  send a view into another project as a pipeline step that re-materialises
  on every run. The SDK fills the backend's `USER_ID` / `export_project` /
  `project_id` / `source_project_id` target properties from `/self`.

## v0.7.12

### Fixed

- Every transform method read the server's draft flag *after* submitting the
  task. The backend flips that flag when the new task carries a reference
  error (missing column, wrong column type), so the SDK skipped the pipeline
  wait and returned `{"has_error": true, "status": "done"}` as success while
  the view sat in `ref_error`. Draft state is now read before the submit and
  a `has_error` result raises `MammothTransformError`.

## v0.7.11

### Added

- `ProjectsAPI.list` takes a server-side `offset`; `list_all` walks the
  route's 100-row pages; `get(project="name")` searches every page.

## v0.7.10

### Added

- Structured logging on the `mammoth.http` and `mammoth.jobs` loggers. Every
  request emits one `http` record (method, path, status, duration,
  backend request id, outcome) and every job poll one `job.poll` record, as
  `extra={"mammoth": {...}}` on a standard `logging` record. No headers,
  bodies or credentials are logged. Nothing is emitted unless the
  application attaches a handler; the CLI's run log does.

## v0.7.9

### Fixed

- `view.set_values(condition=...)` applied the condition to no row: the
  payload carried it at task level, which the backend's VERSION 2 `VALUES`
  form ignores, so every row was overwritten. The condition is now folded
  into each value item (AND-ed with a value's own condition). Filling blanks
  with a constant now touches only the blank rows.
- `dataviews.conditional_format_list()` returned `[]` for a view with rules:
  the release route answers `{rule_id: rule}`, which was discarded. Rules are
  returned as a list with `rule_id` on each item.
- `view.add_sql()` documentation: the view is referenced as the quoted table
  `"view:<dataview_id>"` (or its quoted display name); `__TABLE__` and other
  placeholders are rejected by the backend.

## v0.7.8

### Changed

- `batches.create()` stamps `expected_destination_c_type` (default
  `"TEXT"`, or the new keyword) on every item expanded from a `{src: dst}`
  mapping and rejects list items that lack it; the route requires the field.
- `support.workspace_list()` wraps the bare JSON array the release backend
  returns as `{"workspaces": [...]}`.

## v0.7.7

### Changed

- Request bodies now match the release API contracts: `projects.update()`
  sends `{"patches": [...]}`, `projects.add_users()` takes numeric user ids
  and sends `{"users": [{"user_id", "role"}]}`, `folders.move()` sends a
  `{"patch": [{"op": "move", ...}]}` list, `user_profile.update_preferences()`
  takes a `patch` list, `pipeline.update_task()` sends `{"patches": [...]}`
  (with optional `skip_validation`), `batches.create()` sends the
  `BatchesPostRequest` shape (list `mapping`, `new_ds_details`,
  `validate_only`), `ai.generate_sql()` requires `dataset_id`,
  `ai.get_suggestions()` takes `suggestion_type` + `params`,
  `ai.generate_profile()` sends `{"params": {"action"}}`, `ai.query_gen()`
  takes `query` (was `prompt`), `dataviews.conditional_format_delete()`
  requires `rule_id`, and `datasets.bulk_delete()` requires `dataset_ids`.
- `jobs.wait_for_job()` and `wait_if_job()` accept a `fetch` callable so a job
  can be polled through a scoped route; `dashboards.wait_for_job_by_url()`
  uses it for published-dashboard jobs, whose `/jobs/{id}` reads return
  4PERM002.

### Fixed

- A 2xx response whose body is not an object (for example `202 Accepted`
  with a bare status) is returned as `{"status_code", "response"}` instead
  of raising an outcome-unknown error for a write that committed.

## v0.7.6

### Changed

- `dashboards.get_draft_data()` / `get_publish_data()` take `widget_id` (plus
  optional `global_filters` / `drilldown_filters`) and send the
  `WidgetDataSpec` envelope the routes require; the former `sql` body was
  rejected with HTTP 400.

### Fixed

- `dashboards.archive()` and `share()` accept any 2xx JSON body on their
  undeclared-schema routes instead of raising a response-contract violation
  for a write that committed.
- Generated dashboard wrappers return a 2xx body unchanged when it matches no
  snapshot model instead of raising `ValidationError`.
- `dashboards.update()` documents that `path` is a bare field name, not a
  JSON pointer.

## v0.7.5

### Fixed

- `templates.list()` and `connector_ai.session_list()` accept the bare-array
  responses those routes return.
- Dashboard artifact reads (og-card, PDF, video, share page) return a
  described body (`content_type`, `size_bytes`, `sha256`, and `text` or
  `content_base64`) instead of failing to parse JSON.

## v0.7.4

### Fixed

- `client.datasets.rename()` uses the singular dataset PATCH route with the
  documented `replace`/`name` operation; the previous payload returned HTTP 400.

## v0.7.3

### Security

- API client base URLs must use HTTPS by default. Development HTTP is available
  only for an explicit loopback opt-in.
- Live integration tests read required credentials from the environment and
  skip when that configuration is absent.

## v0.7.2

The 0.7.2 release requires Python 3.12, 3.13, or 3.14 and improves
response outcome classification, effectful webhook GET metadata, and bounded
job waiting behavior.

## v0.7.1

The 0.7.1 release includes transformation and pipeline
reliability fixes and requires Python 3.12, 3.13, or 3.14.

## v0.7.0

The 0.7.0 release requires Python 3.12, 3.13, or 3.14. Transformation
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
