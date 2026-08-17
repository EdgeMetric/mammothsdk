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
    - [`delete(self, file_id: 'int') -> 'None'`](#deleteself-file_id-int---none)
    - [`extract_sheets(self, file_id: 'int', sheets: '_list[str]', delete_file_after_extract: 'bool' = True, combine_after_extract: 'bool' = False) -> 'ObjectJobSchema'`](#extract_sheetsself-file_id-int-sheets-_liststr-delete_file_after_extract-bool-true-combine_after_extract-bool-false---objectjobschema)
    - [`get(self, file_id: 'int', fields: 'str | None' = None) -> 'FileSchema'`](#getself-file_id-int-fields-str-none-none---fileschema)
    - [`list(self, fields: 'str | None' = None, file_ids: '_list[int] | None' = None, names: '_list[str] | None' = None, statuses: '_list[str] | None' = None, created_at: 'str | None' = None, updated_at: 'str | None' = None, limit: 'int' = 50, offset: 'int' = 0, sort: 'str | None' = None) -> 'FilesList'`](#listself-fields-str-none-none-file_ids-_listint-none-none-names-_liststr-none-none-statuses-_liststr-none-none-created_at-str-none-none-updated_at-str-none-none-limit-int-50-offset-int-0-sort-str-none-none---fileslist)
    - [`set_password(self, file_id: 'int', password: 'str') -> 'ObjectJobSchema'`](#set_passwordself-file_id-int-password-str---objectjobschema)
    - [`update(self, file_id: 'int', patch_request: 'FilePatchRequest') -> 'ObjectJobSchema'`](#updateself-file_id-int-patch_request-filepatchrequest---objectjobschema)
    - [`upload(self, files: '_list[str | Path | BinaryIO] | str | Path | BinaryIO | None' = None, folder_resource_id: 'str | int | None' = None, append_to_ds_id: 'int | None' = None, override_target_schema: 'bool | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#uploadself-files-_liststr-path-binaryio-str-path-binaryio-none-none-folder_resource_id-str-int-none-none-append_to_ds_id-int-none-none-override_target_schema-bool-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
    - [`upload_folder(self, folder_path: 'str | Path', folder_resource_id: 'str | None' = None, wait_for_completion: 'bool' = True, timeout: 'int' = 300) -> '_list[int] | int | None'`](#upload_folderself-folder_path-str-path-folder_resource_id-str-none-none-wait_for_completion-bool-true-timeout-int-300---_listint-int-none)
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
    - [`add_users(self, project_id: 'int', user_ids: '_list[str]', role: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_usersself-project_id-int-user_ids-_liststr-role-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`browse(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, name: 'str | None' = None, browse_type: 'str | None' = None, sort: 'str | None' = None, offset: 'int | None' = None, limit: 'int | None' = None) -> 'dict[str, Any]'`](#browseself-project_id-int-workspace_id-int-none-none-fields-str-none-none-name-str-none-none-browse_type-str-none-none-sort-str-none-none-offset-int-none-none-limit-int-none-none---dictstr-any)
    - [`bulk_delete(self, project_ids: '_list[int]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_deleteself-project_ids-_listint-workspace_id-int-none-none---dictstr-any)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none---dictstr-any)
    - [`checkpoint_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#checkpoint_listself-project_id-int-workspace_id-int-none-none-fields-str-none-none-sort-str-none-none-dataview_id-int-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`create(self, name: 'str', color: 'str | None' = None, project_access: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-name-str-color-str-none-none-project_access-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`data_check_list(self, project_id: 'int', workspace_id: 'int | None' = None, fields: 'str | None' = None, sort: 'str | None' = None, dataview_id: 'int | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#data_check_listself-project_id-int-workspace_id-int-none-none-fields-str-none-none-sort-str-none-none-dataview_id-int-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`delete(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#deleteself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`get(self, project: 'int | str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-project-int-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, limit: 'int' = 100) -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-limit-int-100---dictstr-any)
    - [`pending_changes(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#pending_changesself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`publish_credentials(self, project_id: 'int', odbc_type: "Literal['postgres', 'bigquery']", workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#publish_credentialsself-project_id-int-odbc_type-literalpostgres-bigquery-workspace_id-int-none-none---dictstr-any)
    - [`remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#remove_usersself-project_id-int-user_ids-_liststr-workspace_id-int-none-none---dictstr-any)
    - [`resource_dependencies(self, project_id: 'int', resource_ids: '_list[str]', is_recursive: 'bool | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#resource_dependenciesself-project_id-int-resource_ids-_liststr-is_recursive-bool-none-none-workspace_id-int-none-none---dictstr-any)
    - [`resource_status(self, project_id: 'int', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#resource_statusself-project_id-int-workspace_id-int-none-none---dictstr-any)
    - [`sample_flow(self, project_id: 'int', label_resource_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#sample_flowself-project_id-int-label_resource_id-int-none-none-workspace_id-int-none-none---dictstr-any)
    - [`update(self, project_id: 'int', name: 'str | None' = None, color: 'str | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-project_id-int-name-str-none-none-color-str-none-none-workspace_id-int-none-none---dictstr-any)
    - [`user_update(self, project_id: 'int', role: "Literal['project_admin', 'project_analyst']", user_id: 'int | None' = None, invite_id: 'int | None' = None, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`](#user_updateself-project_id-int-role-literalproject_admin-project_analyst-user_id-int-none-none-invite_id-int-none-none-workspace_id-int-none-none---dictstr-any)
- [Datasets](#datasets)
  - [`DatasetsAPI`](#datasetsapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`bulk_delete(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`](#bulk_deleteself-workspace_id-int-none-none-project_id-int-none-none---none)
    - [`bulk_update(self, patch_data: 'dict[str, Any]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#bulk_updateself-patch_data-dictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create(self, dataset_spec: 'dict[str, Any]', ds_creation_type: 'str', folder_resource_id: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#createself-dataset_spec-dictstr-any-ds_creation_type-str-folder_resource_id-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`create_from_pdf(self, file_object_id: 'int', file_name: 'str', file_id: 'str | None' = None, table_list: '_list[int] | None' = None, delete_file_after_extract: 'bool' = False, is_preview_needed: 'bool | None' = None, user_instruction: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#create_from_pdfself-file_object_id-int-file_name-str-file_id-str-none-none-table_list-_listint-none-none-delete_file_after_extract-bool-false-is_preview_needed-bool-none-none-user_instruction-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`](#deleteself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---none)
    - [`file_settings_undo(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#file_settings_undoself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`file_settings_update(self, dataset_id: 'int', delimiter: 'str', has_header: 'bool', initial_skip_count: 'int', quotechar: 'str', date_format: 'str | None' = None, preview_mode: 'bool' = False, skip_auto_process_check: 'bool' = True, date_formats: 'dict[str, str] | None' = None, set_project_level_date_format: 'bool' = False, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#file_settings_updateself-dataset_id-int-delimiter-str-has_header-bool-initial_skip_count-int-quotechar-str-date_format-str-none-none-preview_mode-bool-false-skip_auto_process_check-bool-true-date_formats-dictstr-str-none-none-set_project_level_date_format-bool-false-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_batch(self, dataset_id: 'int', batch_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_batchself-dataset_id-int-batch_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int' = 300, poll_interval: 'int' = 2) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-300-poll_interval-int-2---dictstr-any)
    - [`get_file_settings(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_file_settingsself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`list(self, workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`](#listself-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc---dictstr-any)
    - [`list_batches(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#list_batchesself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---_listdictstr-any)
    - [`rename(self, dataset_id: 'int', name: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#renameself-dataset_id-int-name-str-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`restore(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#restoreself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`trash(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#trashself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`update(self, patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-patch_data-_listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
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
    - [`get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, sequence: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`](#getself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none-sequence-int-none-none-fields-str-none-none---dictstr-any)
    - [`get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2, sequence: 'int | None' = None) -> 'dict[str, Any]'`](#get_dataself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none-timeout-int-none-none-poll_interval-int-2-sequence-int-none-none---dictstr-any)
    - [`list(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, limit: 'int' = 100, sort: 'str' = '(created_at:desc)') -> 'dict[str, Any]'`](#listself-dataset_id-int-workspace_id-int-none-none-project_id-int-none-none-limit-int-100-sort-str-created_atdesc---dictstr-any)
    - [`mark_active(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#mark_activeself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`parameter_context(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#parameter_contextself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`preview(self, dataset_id: 'int', dataview_id: 'int', rows: 'int | None' = None, cols: 'int | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#previewself-dataset_id-int-dataview_id-int-rows-int-none-none-cols-int-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int | None' = None, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#query_dataself-dataset_id-int-dataview_id-int-sequence-int-none-none-offset-int-1-limit-int-400-columns-_liststr-none-none-condition-dictstr-any-none-none-sort-str-none-none-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`restore(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#restoreself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`trash(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#trashself-dataset_id-int-dataview_id-int-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
    - [`update(self, dataset_id: 'int', dataview_id: 'int', patch_data: '_list[dict[str, Any]]', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`](#updateself-dataset_id-int-dataview_id-int-patch_data-_listdictstr-any-workspace_id-int-none-none-project_id-int-none-none---dictstr-any)
- [Pipeline](#pipeline)
  - [`PipelineAPI`](#pipelineapi)
    - [`__init__(self, client: 'MammothClient') -> 'None'`](#__init__self-client-mammothclient---none)
    - [`add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#add_taskself-dataview_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`command(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#commandself-dataview_id-int-command-str-dataset_id-int-none-none---dictstr-any)
    - [`delete_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#delete_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`draft_mode(self, dataview_id: 'int', command: 'str', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#draft_modeself-dataview_id-int-command-str-dataset_id-int-none-none---dictstr-any)
    - [`edit_pipeline(self, dataview_id: 'int', patches: '_list[dict[str, Any]]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#edit_pipelineself-dataview_id-int-patches-_listdictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`find_dataset_for_dataview(self, dataview_id: 'int') -> 'int'`](#find_dataset_for_dataviewself-dataview_id-int---int)
    - [`get_draft_status(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_draft_statusself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`get_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_pipelineself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`get_task(self, dataview_id: 'int', task_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#get_taskself-dataview_id-int-task_id-int-dataset_id-int-none-none---dictstr-any)
    - [`items(self, dataview_id: 'int', dataset_id: 'int | None' = None, fields: 'str | None' = None, limit: 'int | None' = None, offset: 'int | None' = None, sort: 'str | None' = None, sequence: 'int | None' = None, status: 'str | None' = None) -> 'dict[str, Any]'`](#itemsself-dataview_id-int-dataset_id-int-none-none-fields-str-none-none-limit-int-none-none-offset-int-none-none-sort-str-none-none-sequence-int-none-none-status-str-none-none---dictstr-any)
    - [`latest_task_sequence(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`](#latest_task_sequenceself-dataview_id-int-dataset_id-int-none-none---int)
    - [`list_tasks(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#list_tasksself-dataview_id-int-dataset_id-int-none-none---dictstr-any)
    - [`preview_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#preview_taskself-dataview_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`rerun(self, dataview_id: 'int', from_sequence: 'int | None' = None, dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#rerunself-dataview_id-int-from_sequence-int-none-none-dataset_id-int-none-none---dictstr-any)
    - [`update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`](#update_taskself-dataview_id-int-task_id-int-task_spec-dictstr-any-dataset_id-int-none-none---dictstr-any)
    - [`wait_for_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 3) -> 'dict[str, Any]'`](#wait_for_pipelineself-dataview_id-int-dataset_id-int-none-none-timeout-int-none-none-poll_interval-int-3---dictstr-any)
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
    - [`action(self, dashboard_id: 'int', action: 'DashboardActionType', params_enabled: 'bool | None' = None, params_view_id: 'int | None' = None) -> 'dict[str, Any]'`](#actionself-dashboard_id-int-action-dashboardactiontype-params_enabled-bool-none-none-params_view_id-int-none-none---dictstr-any)
    - [`analytics(self: 'Any', dashboard_id: 'int') -> 'DashboardAnalyticsResponse'`](#analyticsself-any-dashboard_id-int---dashboardanalyticsresponse)
    - [`cancel_generation(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#cancel_generationself-dashboard_id-int---dictstr-any)
    - [`canvas_get(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'CanvasResponse'`](#canvas_getself-any-dashboard_id-int-sequence-int-none-none---canvasresponse)
    - [`canvas_restore(self: 'Any', dashboard_id: 'int', body: 'RestoreCanvasSpec') -> 'ObjectJobSchema | JobResponse'`](#canvas_restoreself-any-dashboard_id-int-body-restorecanvasspec---objectjobschema-jobresponse)
    - [`canvas_save(self: 'Any', dashboard_id: 'int', body: 'SaveCanvasSpec') -> 'SaveCanvasResponse'`](#canvas_saveself-any-dashboard_id-int-body-savecanvasspec---savecanvasresponse)
    - [`chat_edit(self: 'Any', dashboard_id: 'int', body: 'ChatEditSpec') -> 'ObjectJobSchema | JobResponse'`](#chat_editself-any-dashboard_id-int-body-chateditspec---objectjobschema-jobresponse)
    - [`chat_history(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'mmai_dashboards_v3_schema_ChatHistoryResponse'`](#chat_historyself-any-dashboard_id-int-sequence-int-none-none---mmai_dashboards_v3_schema_chathistoryresponse)
    - [`context_create(self: 'Any', body: 'ContextSpec') -> 'ContextResponse'`](#context_createself-any-body-contextspec---contextresponse)
    - [`context_delete(self: 'Any', context_id: 'str') -> 'OkResponse'`](#context_deleteself-any-context_id-str---okresponse)
    - [`context_list(self: 'Any') -> 'ContextListResponse'`](#context_listself-any---contextlistresponse)
    - [`context_update(self: 'Any', context_id: 'str', body: 'ContextSpec') -> 'ContextResponse'`](#context_updateself-any-context_id-str-body-contextspec---contextresponse)
    - [`create(self, intent: 'str', source: '_list[int]', enable_filters: 'bool' = True, enable_pages: 'bool' = False) -> 'dict[str, Any]'`](#createself-intent-str-source-_listint-enable_filters-bool-true-enable_pages-bool-false---dictstr-any)
    - [`data_draft(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`](#data_draftself-any-dashboard_id-int-body-widgetdataspec---widgetdataresponse-objectjobschema-jobresponse)
    - [`data_published(self: 'Any', dashboard_id: 'int', body: 'WidgetDataSpec') -> 'WidgetDataResponse | ObjectJobSchema | JobResponse'`](#data_publishedself-any-dashboard_id-int-body-widgetdataspec---widgetdataresponse-objectjobschema-jobresponse)
    - [`delete(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#deleteself-dashboard_id-int---dictstr-any)
    - [`descriptor_data(self: 'Any', dashboard_id: 'int', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`](#descriptor_dataself-any-dashboard_id-int-body-descriptordataspec---objectjobschema-jobresponse)
    - [`duplicate(self: 'Any', dashboard_id: 'int') -> 'DuplicateDashboardResponse'`](#duplicateself-any-dashboard_id-int---duplicatedashboardresponse)
    - [`figure_intent(self: 'Any', dashboard_id: 'int', body: 'FigureIntentSpec') -> 'FigureIntentResponse'`](#figure_intentself-any-dashboard_id-int-body-figureintentspec---figureintentresponse)
    - [`get(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#getself-dashboard_id-int---dictstr-any)
    - [`get_analytics(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#get_analyticsself-dashboard_id-int---dictstr-any)
    - [`get_by_url(self, url: 'str') -> 'dict[str, Any]'`](#get_by_urlself-url-str---dictstr-any)
    - [`get_draft_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`](#get_draft_dataself-dashboard_id-int-sql-str---dictstr-any)
    - [`get_publish_data(self, dashboard_id: 'int', sql: 'str') -> 'dict[str, Any]'`](#get_publish_dataself-dashboard_id-int-sql-str---dictstr-any)
    - [`get_sources(self) -> '_list[dict[str, Any]]'`](#get_sourcesself---_listdictstr-any)
    - [`job_by_url(self, url: 'str', job_id: 'int') -> 'dict[str, Any]'`](#job_by_urlself-url-str-job_id-int---dictstr-any)
    - [`list(self, project_id: 'int | None' = None) -> '_list[dict[str, Any]]'`](#listself-project_id-int-none-none---_listdictstr-any)
    - [`og_card(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`](#og_cardself-any-dashboard_id-int---dictstr-any)
    - [`page_plan(self: 'Any', dashboard_id: 'int', body: 'PlanPageSpec') -> 'PlanPageResponse'`](#page_planself-any-dashboard_id-int-body-planpagespec---planpageresponse)
    - [`pdf_artifact(self: 'Any', dashboard_id: 'int', job_id: 'int') -> 'dict[str, Any]'`](#pdf_artifactself-any-dashboard_id-int-job_id-int---dictstr-any)
    - [`pdf_export(self: 'Any', dashboard_id: 'int', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`](#pdf_exportself-any-dashboard_id-int-body-pdfexportspec---objectjobschema-jobresponse)
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
    - [`restore(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#restoreself-dashboard_id-int---dictstr-any)
    - [`rls_assignment_list(self: 'Any', dashboard_id: 'int') -> 'RlsAssignmentsResponse'`](#rls_assignment_listself-any-dashboard_id-int---rlsassignmentsresponse)
    - [`rls_assignment_set(self: 'Any', dashboard_id: 'int', body: 'RlsAssignmentsSpec') -> 'dict[str, Any]'`](#rls_assignment_setself-any-dashboard_id-int-body-rlsassignmentsspec---dictstr-any)
    - [`rls_column_list(self: 'Any', dashboard_id: 'int') -> 'RlsColumnsResponse'`](#rls_column_listself-any-dashboard_id-int---rlscolumnsresponse)
    - [`rls_value_list(self: 'Any', dashboard_id: 'int', column: 'str', search: 'str | None' = None) -> 'RlsDistinctValuesResponse'`](#rls_value_listself-any-dashboard_id-int-column-str-search-str-none-none---rlsdistinctvaluesresponse)
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
    - [`suggestion_list(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'DashboardSuggestionsResponse'`](#suggestion_listself-any-dataview_id-int-table_item_id-int-none-none---dashboardsuggestionsresponse)
    - [`template_apply(self: 'Any', body: 'ApplyTemplateSpec') -> 'ObjectJobSchema | JobResponse'`](#template_applyself-any-body-applytemplatespec---objectjobschema-jobresponse)
    - [`template_create(self: 'Any', body: 'SaveTemplateSpec') -> 'TemplateDetailResponse'`](#template_createself-any-body-savetemplatespec---templatedetailresponse)
    - [`template_delete(self: 'Any', template_id: 'str') -> 'OkResponse'`](#template_deleteself-any-template_id-str---okresponse)
    - [`template_fit(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'TemplateFitResponse'`](#template_fitself-any-dataview_id-int-table_item_id-int-none-none---templatefitresponse)
    - [`template_get(self: 'Any', template_id: 'str') -> 'TemplateDetailResponse'`](#template_getself-any-template_id-str---templatedetailresponse)
    - [`template_list(self: 'Any') -> 'TemplateListResponse'`](#template_listself-any---templatelistresponse)
    - [`template_preview(self: 'Any', body: 'PreviewTemplateSpec') -> 'PreviewTemplateResponse'`](#template_previewself-any-body-previewtemplatespec---previewtemplateresponse)
    - [`template_rename(self: 'Any', template_id: 'str', body: 'RenameTemplateSpec') -> 'TemplateDetailResponse'`](#template_renameself-any-template_id-str-body-renametemplatespec---templatedetailresponse)
    - [`template_resolve_mapping(self: 'Any', body: 'ResolveTemplateMappingSpec') -> 'ResolveTemplateMappingResponse'`](#template_resolve_mappingself-any-body-resolvetemplatemappingspec---resolvetemplatemappingresponse)
    - [`trash(self, dashboard_id: 'int') -> 'dict[str, Any]'`](#trashself-dashboard_id-int---dictstr-any)
    - [`update(self, dashboard_id: 'int', patch: '_list[DashboardPatchItem]') -> 'dict[str, Any]'`](#updateself-dashboard_id-int-patch-_listdashboardpatchitem---dictstr-any)
    - [`v3_generate(self: 'Any', body: 'GenerateDashboardV3Spec') -> 'ObjectJobSchema | JobResponse'`](#v3_generateself-any-body-generatedashboardv3spec---objectjobschema-jobresponse)
    - [`video_export(self: 'Any', dashboard_id: 'int') -> 'ObjectJobSchema | JobResponse'`](#video_exportself-any-dashboard_id-int---objectjobschema-jobresponse)
    - [`video_state(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`](#video_stateself-any-dashboard_id-int---dictstr-any)
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

Python 3.12-3.14 | [PyPI](https://pypi.org/project/mammoth-io/) | [GitHub](https://github.com/EdgeMetric/mammothsdk)

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
- **Issues**: [GitHub Issues](https://github.com/EdgeMetric/mammothsdk/issues)
- **Email**: support@mammoth.io


---


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

- [Quick Start Guide](#quick-start-guide) -- create your first client and apply transformations
- [Authentication](#authentication) -- set up API credentials


---


# Quick Start Guide

Get up and running with the Mammoth Python SDK in five minutes.

## 1. Install the SDK

```bash
pip install mammoth-io==0.3.6
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

#### `__init__(self, api_key: 'str', api_secret: 'str', workspace_id: 'int', base_url: 'str' = 'https://app.mammoth.io/api/v2', timeout: 'int' = 30, job_timeout: 'int' = 60, pipeline_timeout: 'int' = 3600) -> 'None'`

Initialize the Mammoth client.

Args:
    api_key: Your Mammoth API key.
    api_secret: Your Mammoth API secret.
    workspace_id: Your Mammoth workspace ID.
    base_url: Base URL for the Mammoth API.
    timeout: Request timeout in seconds.
    job_timeout: Job polling timeout in seconds.
    pipeline_timeout: Pipeline readiness polling timeout in seconds.

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

    view = client.get_view(1039)
    print(view.display_names)

#### `find_dataset_for_dataview(self, dataview_id: 'int') -> 'int'`

Find the parent dataset ID for a given dataview.

Searches all datasets in the current project to locate which
dataset contains the specified dataview.

Args:
    dataview_id: ID of the dataview.

Returns:
    Dataset ID that contains the dataview.

Raises:
    MammothAPIError: If the dataview cannot be found in any dataset.

Example::

    dataset_id = client.find_dataset_for_dataview(1039)

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

    if client.test_connection():
        print("Connected!")

### ViewsResource

### `ViewsResource`

Resource that returns rich View objects.

Access via client.views::

    view = client.views.get(view_id)           # returns View object
    views = client.views.list()                 # returns list of View objects
    view = client.views.create(dataset_id)      # returns View object

#### `get(self, view_id: 'int') -> 'View'`

Get a rich View object for a dataview.

Args:
    view_id: ID of the dataview.

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

#### `delete(self, view_id: 'int') -> 'dict[str, Any]'`

Delete a dataview.

Args:
    view_id: ID of the dataview.

Returns:
    Dict with deletion result.

#### `bulk_delete(self, view_ids: '_list[int]') -> 'dict[str, Any]'`

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

    rows = view.data(limit=10)
    rows = view.data(columns=["Name", "Sales"], limit=50)
    rows = view.data(
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
    If a column is missing after refresh, call ``view.data(limit=1)``
    to verify the column exists in the output, or re-get the view
    with ``client.views.get(view.id)``.

Returns:
    self (for chaining).

Example::

    view.refresh()
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

    tasks = view.list_tasks()
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

    tasks = view.list_tasks()
    view.delete_task(tasks[-1]["id"])  # remove last task

#### `preview_task(self, task_spec: 'dict[str, Any]') -> 'dict[str, Any]'`

Preview the result of a task without applying it to the pipeline.

Args:
    task_spec: Task specification dict (same format as ``_add_task``
        payloads).

Returns:
    Preview data dict showing what the data would look like.

Example::

    preview = view.preview_task({"DELETE": ["column_abc123"]})

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

Enters draft mode on ``__enter__``, submits on clean exit,
discards on exception::

    with view.draft():
        view.filter_rows(Condition("Sales", Operator.GTE, 1000))
        view.math("Price * 2", new_column="Double")
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

Whether this view is currently in draft mode.

#### `branch_out(self, dataset_name: 'str', *, target_ds_id: 'int | None' = None, save_as_mode: 'SaveAsDatasetMode' = <SaveAsDatasetMode.REPLACE: 'REPLACE_IN_DS'>, column_mapping: 'dict[str, str] | None' = None, label_ids: 'list[int] | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None, timeout: 'int | None' = None) -> 'int'`

Branch out — save this view's data as a Mammoth dataset.

Shortcut for :meth:`ViewExport.to_dataset`. ``target_ds_id`` None
creates a new dataset named *dataset_name*; an int replaces/appends
into that existing dataset (per *save_as_mode*).

Args:
    dataset_name: Name for the new dataset (display name when writing
        into an existing one).
    target_ds_id: Existing dataset to write into; None creates a new one.
    save_as_mode: Replace or append when writing the output dataset.
    column_mapping: Source -> destination column-name map (empty = all).
    label_ids: Folder/label ids for the new dataset.
    condition: Optional row filter applied before copying.
    timeout: Max seconds to wait for the job.

Returns:
    The id of the dataset written to (new when ``target_ds_id`` is None,
    otherwise ``target_ds_id``).

Example::

    new_id = view.branch_out(dataset_name="Q1 snapshot")

#### `filter_rows(self, condition: 'Condition | CompoundCondition | NotCondition', filter_type: 'FilterType' = <FilterType.SHOW: 'SHOW'>, prompt: 'str' = '') -> 'dict[str, Any]'`

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

    view.set_values(
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

    view.math("Price * Quantity", new_column="Total")
    view.math("(Price + Tax) * 1.1", new_column="Grand Total")

#### `join(self, foreign_view: 'int | View', join_type: 'JoinType', on: 'list[JoinKeySpec]', select: 'list[str | JoinSelectSpec]', column_prefix: 'str | None' = None) -> 'dict[str, Any]'`

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

Returns:
    API response dict.

Examples::

    # Join with View object (display names everywhere)
    other = client.views.get(2050)
    view.join(
        foreign_view=other,
        join_type=JoinType.LEFT,
        on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
        select=["Category", "Name"],
    )

    # Join with view ID (internal names for foreign view)
    view.join(
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

    view.pivot(
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

    view.window(
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
async job. This method blocks until the dataset is materialised.

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

    view.crosstab(
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

    view.add_column("Notes")
    view.add_column("Score", column_type=ColumnType.NUMERIC)
    view.add_column("Created", column_type=ColumnType.DATE)

#### `delete_columns(self, columns: 'list[str]') -> 'dict[str, Any]'`

Remove one or more columns (DELETE task).

Args:
    columns: List of display names to delete.

Returns:
    API response dict.

Examples::

    view.delete_columns(["Temp"])
    view.delete_columns(["Notes", "Internal ID", "Debug"])

#### `copy_columns(self, copies: 'list[CopySpec]') -> 'dict[str, Any]'`

Duplicate columns (COPY task).

Args:
    copies: List of :class:`CopySpec` objects::

            [CopySpec(source="Sales", as_name="Sales Copy")]

Returns:
    API response dict.

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
    view.combine_columns(
        ["First Name", "Last Name"],
        new_column="Full Name", separator=" ",
    )

    # Combine with custom separator, overwrite existing column
    view.combine_columns(
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
    view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])

    # Text to date (specify the source format)
    view.convert_type([
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

    view.text_transform(["Name"], case=TextCase.UPPER)
    view.text_transform(["City", "State"], case=TextCase.TITLE)
    view.text_transform(["Notes"], trim=True)
    view.text_transform(
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

    view.replace_values(["City"], find="NYC", replace="New York")
    view.replace_values(
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

    view.bulk_replace(
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

    view.split_column(
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
    view.substring("Code", direction=SubstringDirection.START,
                   num_char=3, new_column="Prefix")

    # Last 4 characters
    view.substring("Phone", direction=SubstringDirection.END,
                   num_char=4, new_column="Last4")

    # Characters before position 5
    view.substring("SKU", direction=SubstringDirection.LEFT,
                   char_position=5, new_column="Category")

    # Regex extraction
    view.substring("Email", regex_pattern=r"@(.+)",
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
    view.increment_date("Order Date", DateDelta(days=30),
                        new_column="Due Date")

    # Subtract 1 year, add 6 months
    view.increment_date("Start Date", DateDelta(years=-1, months=6),
                        new_column="Adjusted Date")

    # Conditional increment
    view.increment_date(
        "Ship Date", DateDelta(days=7),
        existing_column="Ship Date",
        condition=Condition("Priority", Operator.EQ, "Low"),
    )

#### `fill_missing(self, column: 'str', direction: 'FillDirection', partition_by: 'str | None' = None, order_by: 'list[list[str | SortDirection]] | None' = None) -> 'dict[str, Any]'`

Fill missing (null/empty) values using adjacent rows (FILL task).

Args:
    column: Display name of column to fill.
    direction: Fill direction — ``FillDirection.LAST_VALUE``
        fills downward (forward-fill), ``FillDirection.FIRST_VALUE``
        fills upward (back-fill).
    partition_by: Display name of column to partition by (optional).
        Fill restarts at each partition boundary.
    order_by: Sort order applied before filling (optional)::

            [["Date", SortDirection.ASC]]

Returns:
    API response dict.

Examples::

    from mammoth import FillDirection, SortDirection

    # Forward-fill missing values
    view.fill_missing("Price", FillDirection.LAST_VALUE)

    # Fill within partitions, ordered by date
    view.fill_missing(
        "Metric", FillDirection.LAST_VALUE,
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

    view.limit_rows(100)
    view.limit_rows(10, order_by=[["Sales", SortDirection.DESC]])
    view.limit_rows(5, bottom=True)

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

Unpivot (melt) columns to rows (UNNEST task).

Converts multiple columns into rows. Each original column becomes a
label/value pair, multiplying the row count accordingly.

Args:
    columns: Display names of columns to unnest.
    label_column: Name for the new label column that holds the
        original column names (default ``"Label"``).
    value_column: Name for the new value column that holds the
        original cell values (default ``"Value"``).

Returns:
    API response dict.

Example::

    # Columns "Q1", "Q2", "Q3", "Q4" → rows with Label/Value
    view.unnest(["Q1", "Q2", "Q3", "Q4"],
                label_column="Quarter", value_column="Revenue")

#### `lookup(self, source: 'str', lookup_view_id: 'int', key: 'str', value: 'str', new_column: 'str | None' = None, existing_column: 'str | None' = None) -> 'dict[str, Any]'`

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
    existing_column: Display name of existing column to overwrite.

Returns:
    API response dict.

Example::

    view.lookup(
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
    view.json_extract("data", keys=["name", "email", "age"])

    # Advanced with custom types
    view.json_extract(
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

    view.gen_ai(
        prompt="Classify the sentiment of the review",
        context_columns=["Review Text"],
        new_column="Sentiment",
    )

#### `generate_sql(self, intent: 'str') -> 'str'`

Generate SQL from natural language using the Mammoth LLM.

Calls the ``/sql_generation`` endpoint which converts the intent
into SQL, adds the resulting task to the pipeline, waits for
completion, and returns the generated query.

Args:
    intent: Natural language description of the desired query
        (e.g. ``"count employees by department"``).

Returns:
    The generated SQL query string.

Example::

    sql = view.generate_sql("show total sales by region")
    print(sql)  # "SELECT region, SUM(sales) FROM ... GROUP BY region"

#### `add_sql(self, query: 'str') -> 'dict[str, Any]'`

Add a raw SQL query as a pipeline task (SQL task).

The query runs against the dataview's underlying data. Column
references should use internal names (e.g. ``column_abc123``).

.. note::

    Requires the SQL addon to be enabled on the workspace.

Args:
    query: SQL query string.

Returns:
    API response dict.

Example::

    view.add_sql("SELECT *, column_abc * 2 AS doubled FROM __TABLE__")

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `ColumnType`

Column data types for new columns and conversions.

#### `DATE`

Column data types for new columns and conversions.

#### `NUMERIC`

Column data types for new columns and conversions.

#### `TEXT`

Column data types for new columns and conversions.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `TextCase`

Text case transformations.

#### `LOWER`

Text case transformations.

#### `TITLE`

Text case transformations.

#### `UPPER`

Text case transformations.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `YEAR_MONTH_NUMBER`

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `WindowRange`

Window range types.

#### `RUNNING`

Window range types.

#### `UNBOUNDED`

Window range types.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `FillDirection`

Fill directions for missing value imputation.

#### `FIRST_VALUE`

Fill directions for missing value imputation.

#### `LAST_VALUE`

Fill directions for missing value imputation.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `SortDirection`

Sort direction for order_by clauses.

#### `ASC`

Sort direction for order_by clauses.

#### `DESC`

Sort direction for order_by clauses.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `JsonType`

JSON structure types for json_extract.

#### `LIST`

JSON structure types for json_extract.

#### `OBJECT`

JSON structure types for json_extract.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `JsonOpType`

JSON operation types for json_extract.

#### `JSON_LIST_TO_ROWS`

JSON operation types for json_extract.

#### `JSON_OBJECT_TO_COLUMNS`

JSON operation types for json_extract.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `ExportFileType`

File types for S3 and file-based exports.

#### `CSV`

File types for S3 and file-based exports.

#### `JSON`

File types for S3 and file-based exports.

#### `PARQUET`

File types for S3 and file-based exports.

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

### `DraftCommand`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    with view.draft():  # preferred
        view.filter_rows(...)

    view.enter_draft_mode()   # uses DraftCommand.ENTER
    view.submit_draft()       # uses SUBMIT then EXIT
    view.discard_draft()      # uses DISCARD then EXIT

#### `DISCARD`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    with view.draft():  # preferred
        view.filter_rows(...)

    view.enter_draft_mode()   # uses DraftCommand.ENTER
    view.submit_draft()       # uses SUBMIT then EXIT
    view.discard_draft()      # uses DISCARD then EXIT

#### `ENTER`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    with view.draft():  # preferred
        view.filter_rows(...)

    view.enter_draft_mode()   # uses DraftCommand.ENTER
    view.submit_draft()       # uses SUBMIT then EXIT
    view.discard_draft()      # uses DISCARD then EXIT

#### `EXIT`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    with view.draft():  # preferred
        view.filter_rows(...)

    view.enter_draft_mode()   # uses DraftCommand.ENTER
    view.submit_draft()       # uses SUBMIT then EXIT
    view.discard_draft()      # uses DISCARD then EXIT

#### `SUBMIT`

Draft mode commands for pipeline task batching.

Use via ``view.draft()`` context manager or explicit methods::

    with view.draft():  # preferred
        view.filter_rows(...)

    view.enter_draft_mode()   # uses DraftCommand.ENTER
    view.submit_draft()       # uses SUBMIT then EXIT
    view.discard_draft()      # uses DISCARD then EXIT

#### `__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

#### `capitalize(self, /)`

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

#### `casefold(self, /)`

Return a version of the string suitable for caseless comparisons.

#### `center(self, width, fillchar=' ', /)`

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

#### `count`

Return the number of non-overlapping occurrences of substring sub in string S[start:end].

Optional arguments start and end are interpreted as in slice notation.

#### `encode(self, /, encoding='utf-8', errors='strict')`

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

#### `endswith`

Return True if the string ends with the specified suffix, False otherwise.

suffix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `expandtabs(self, /, tabsize=8)`

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

#### `find`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `format(self, /, *args, **kwargs)`

Return a formatted version of the string, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

#### `format_map(self, mapping, /)`

Return a formatted version of the string, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

#### `index`

Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `isalnum(self, /)`

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

#### `isalpha(self, /)`

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

#### `isascii(self, /)`

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

#### `isdecimal(self, /)`

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

#### `isdigit(self, /)`

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

#### `isidentifier(self, /)`

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

#### `islower(self, /)`

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

#### `isnumeric(self, /)`

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

#### `isprintable(self, /)`

Return True if all characters in the string are printable, False otherwise.

A character is printable if repr() may use it in its output.

#### `isspace(self, /)`

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

#### `istitle(self, /)`

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

#### `isupper(self, /)`

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

#### `join(self, iterable, /)`

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

#### `ljust(self, width, fillchar=' ', /)`

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `lower(self, /)`

Return a copy of the string converted to lowercase.

#### `lstrip(self, chars=None, /)`

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `maketrans`

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### `partition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

#### `removeprefix(self, prefix, /)`

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

#### `removesuffix(self, suffix, /)`

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

#### `replace(self, old, new, /, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

  count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

#### `rfind`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Return -1 on failure.

#### `rindex`

Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].

Optional arguments start and end are interpreted as in slice notation.
Raises ValueError when the substring is not found.

#### `rjust(self, width, fillchar=' ', /)`

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

#### `rpartition(self, sep, /)`

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

#### `rsplit(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

#### `rstrip(self, chars=None, /)`

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `split(self, /, sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

  sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \n \r \t \f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits.
    -1 (the default value) means no limit.

Splitting starts at the front of the string and works to the end.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

#### `splitlines(self, /, keepends=False)`

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

#### `startswith`

Return True if the string starts with the specified prefix, False otherwise.

prefix
  A string or a tuple of strings to try.
start
  Optional start position. Default: start of the string.
end
  Optional stop position. Default: end of the string.

#### `strip(self, chars=None, /)`

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

#### `swapcase(self, /)`

Convert uppercase characters to lowercase and lowercase characters to uppercase.

#### `title(self, /)`

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

#### `translate(self, table, /)`

Replace each character in the string using the given translation table.

  table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

#### `upper(self, /)`

Return a copy of the string converted to uppercase.

#### `zfill(self, width, /)`

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.

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
    view.copy_columns([CopySpec(source="Sales", as_name="Sales Copy", type=ColumnType.NUMERIC)])

    # Overwrite an existing column's values
    view.copy_columns([CopySpec(source="Sales", destination="Sales Backup")])

#### `__init__(self, source: 'str', as_name: 'str | None' = None, type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>, condition: 'Condition | CompoundCondition | NotCondition | None' = None, destination: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `type`

Column data types for new columns and conversions.

### `ConversionSpec`

Specification for a column type conversion in :meth:`View.convert_type`.

Example::

    view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])
    view.convert_type([
        ConversionSpec(column="Date Col", to=ColumnType.DATE, format="MM/DD/YYYY")
    ])

#### `__init__(self, column: 'str', to: 'ColumnType', format: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `SplitColumnSpec`

Specification for a new column in :meth:`View.split_column`.

Example::

    view.split_column("Name", " ", [SplitColumnSpec("First"), SplitColumnSpec("Last")])

#### `__init__(self, name: 'str', type: 'ColumnType' = <ColumnType.TEXT: 'TEXT'>) -> None`

Initialize self.  See help(type(self)) for accurate signature.

#### `type`

Column data types for new columns and conversions.

### `BulkReplaceMapping`

Specification for a bulk replace mapping in :meth:`View.bulk_replace`.

Example::

    view.bulk_replace(
        columns=["Item"],
        mapping=[BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE")],
    )

#### `__init__(self, search: 'list[str]', replace: 'str') -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `DateDelta`

Delta specification for :meth:`View.increment_date`.

Example::

    view.increment_date("Order Date", DateDelta(days=30), new_column="Due Date")
    view.increment_date("Start", DateDelta(years=1, months=-3), new_column="Adjusted")

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

    view.pivot(
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

    view.join(..., on=[JoinKeySpec(left="Customer ID", right="Customer ID")])

#### `__init__(self, left: 'str', right: 'str') -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `JoinSelectSpec`

Specification for a column to bring in from a join in :meth:`View.join`.

Example::

    view.join(..., select=[JoinSelectSpec(column="Category", alias="Cat")])

#### `__init__(self, column: 'str', alias: 'str | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `JsonExtractionSpec`

Specification for a JSON key extraction in :meth:`View.json_extract`.

Example::

    view.json_extract("data", extractions=[
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

    view.crosstab(rows=["Region"], pivot_column="Gender",
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

Base exception for all Mammoth SDK errors.

Attributes:
    message: Human-readable error description.
    details: Additional context dict (varies by subclass).

#### `__init__(self, message: 'str', details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothAPIError`

Exception raised when the Mammoth API returns an error response.

Attributes:
    message: Human-readable error description.
    status_code: HTTP status code (e.g. 400, 404, 500), or ``None``.
    response_body: Raw JSON response body dict from the API.

Example::

    try:
        client.datasets.get(dataset_id=99999)
    except MammothAPIError as e:
        print(e.status_code)     # 404
        print(e.response_body)   # {"detail": "Not found"}

#### `__init__(self, message: 'str', status_code: 'int | None' = None, response_body: 'dict[str, Any] | None' = None, details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothAuthError`

Exception raised when API credentials are invalid (HTTP 401).

Attributes:
    message: ``"Authentication failed"`` (default).
    status_code: Always ``401``.

#### `__init__(self, message: 'str' = 'Authentication failed') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothJobTimeoutError`

Exception raised when polling a job exceeds the timeout.

Attributes:
    message: Description including job ID and timeout.
    details: ``{"job_id": int, "timeout": int}``.

#### `__init__(self, job_id: 'int', timeout_seconds: 'int') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothJobFailedError`

Exception raised when a job completes with a failure status.

Attributes:
    message: Description including job ID and failure reason.
    details: ``{"job_id": int, "failure_reason": str | None}``.

#### `__init__(self, job_id: 'int', failure_reason: 'str | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothTransformError`

Exception raised when a pipeline transformation task fails.

Attributes:
    message: Human-readable error description.
    task_key: The pipeline task key (e.g. ``"SET"``, ``"MATH"``).
    details: Additional context dict.

#### `__init__(self, message: 'str', task_key: 'str | None' = None, details: 'dict[str, Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

### `MammothColumnError`

Exception raised when a column display name cannot be resolved.

Attributes:
    message: Description including the missing column name and
        available columns.
    details: ``{"column_name": str, "available_columns": list[str] | None}``.

Example::

    try:
        view.filter_rows(Condition("NonExistent", Operator.EQ, 1))
    except MammothColumnError as e:
        print(e.details["column_name"])        # "NonExistent"
        print(e.details["available_columns"])   # ["Sales", "Region", ...]

#### `__init__(self, column_name: 'str', available_columns: 'list[str] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `add_note(self, note, /)`

Add a note to the exception

#### `with_traceback(self, tb, /)`

Set self.__traceback__ to tb and return self.

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

Download dataview data as a local CSV file.

Args:
    output_path: Local path for the output file. Auto-generated
        if not provided.
    timeout: Timeout in seconds (default 300).

Returns:
    :class:`~pathlib.Path` to the downloaded CSV file.

Example::

    path = view.export.to_csv("output.csv")
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

    result = view.export.to_s3(file_name="report.csv")
    view.export.to_s3(file_type=ExportFileType.PARQUET)

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

    view.export.to_postgres(
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

#### `to_dataset(self, dataset_name: 'str', *, target_ds_id: 'int | None' = None, save_as_mode: 'SaveAsDatasetMode' = <SaveAsDatasetMode.REPLACE: 'REPLACE_IN_DS'>, column_mapping: 'dict[str, str] | None' = None, label_ids: 'list[int] | None' = None, condition: 'Condition | CompoundCondition | NotCondition | None' = None, timeout: 'int | None' = None) -> 'int'`

Save this view's data as an internal Mammoth dataset (branch out).

Runs through the ``internal_dataset`` export handler and blocks until
the dataset is materialised.

Args:
    dataset_name: Name for the new dataset (display name when writing
        into an existing one).
    target_ds_id: Existing dataset to write into; None creates a new one.
    save_as_mode: Replace or append when writing the output dataset.
    column_mapping: Source -> destination column-name map (empty = all).
    label_ids: Folder/label ids for the new dataset.
    condition: Optional row filter applied before copying.
    timeout: Max seconds to wait for the job.

Returns:
    The id of the dataset written to (new when ``target_ds_id`` is None,
    otherwise ``target_ds_id``).

Example::

    new_id = view.export.to_dataset("Sales snapshot")

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

    view.export.to_ftp(
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

    view.export.to_email(emails=["analyst@example.com"], subject="Q1")

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

    view.export.publish_to_db(table="sales_dashboard")

#### `list(self) -> '_list[dict[str, Any]]'`

List all exports configured for this dataview.

Returns:
    List of export dicts, each with ``id``, ``handler_type``,
    ``target_properties``, etc.

Example::

    exports = view.export.list()
    for exp in exports:
        print(f"{exp['id']}: {exp['handler_type']}")

#### `delete(self, export_id: 'int') -> 'dict[str, Any]'`

Delete an export configuration.

Args:
    export_id: ID of the export to delete (from ``list()``).

Returns:
    Deletion confirmation dict.

Example::

    exports = view.export.list()
    view.export.delete(exports[0]["id"])

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

### `remove_users(self, project_id: 'int', user_ids: '_list[str]', workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Remove users from a project.

Args:
    project_id: ID of the project.
    user_ids: List of user IDs to remove.
    workspace_id: ID of the workspace (uses client default if not provided).

Returns:
    Dict with result.

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

### `delete(self, dataset_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'None'`

Delete a dataset.

Args:
    dataset_id: ID of the dataset to delete.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

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

### `rename(self, dataset_id: 'int', name: 'str', workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Rename a dataset.

Convenience method wrapping :meth:`update` with a ``rename_dataset``
patch operation.

Args:
    dataset_id: ID of the dataset to rename.
    name: New name for the dataset.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with update result.

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

Update datasets using JSON Patch operations.

The server expects patch operations sent to the plural ``/datasets``
endpoint. Each operation must include ``op``, ``path``, and ``value``.

Supported operations (mapped via ``OP_PATCH_TO_FUNCTION_MAP`` on the
backend): ``rename_dataset``, ``update_datasets``, ``delete_datasets``,
``change_ds_column_type``, ``add_columns``, ``remove_columns``,
``rename_column``, ``refresh_data``, ``reattach_connection``.

Args:
    patch_data: List of patch operations.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

Returns:
    Dict with update result.

Example::

    # Rename a dataset
    client.datasets.update([
        {"op": "rename_dataset", "path": "/123", "value": {"name": "New Name"}}
    ])


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

### `get(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, sequence: 'int | None' = None, fields: 'str | None' = None) -> 'dict[str, Any]'`

Get dataview information.

Metadata is scoped to a pipeline task *sequence*. When ``sequence`` is
omitted it defaults to the latest task sequence, so the returned
``metadata`` reflects every pipeline-derived column (math, add_column,
etc.). Pass ``sequence=0`` for the original dataset columns.

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).
    sequence: Pipeline step to read metadata at (default: latest).
    fields: Field set to return (e.g. ``"__full"``); server default if omitted.

Returns:
    Dict with complete dataview information.

### `get_data(self, dataset_id: 'int', dataview_id: 'int', workspace_id: 'int | None' = None, project_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 2, sequence: 'int | None' = None) -> 'dict[str, Any]'`

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
    poll_interval: Seconds between job polls (default: 2).
    sequence: Pipeline step to read data at (default: latest).

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

### `query_data(self, dataset_id: 'int', dataview_id: 'int', sequence: 'int | None' = None, offset: 'int' = 1, limit: 'int' = 400, columns: '_list[str] | None' = None, condition: 'dict[str, Any] | None' = None, sort: 'str | None' = None, workspace_id: 'int | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get dataview data with filtering options (POST method).

Args:
    dataset_id: ID of the dataset.
    dataview_id: ID of the dataview.
    sequence: Pipeline step to fetch data at (default: latest task
        sequence, so rows include every pipeline-derived column; pass
        ``0`` for the original dataset).
    offset: One-indexed starting row (default 1).
    limit: Number of rows to fetch (default 400).
    columns: List of column names to fetch (optional).
    condition: Filter condition dict (optional).
    sort: Sort specification string (optional).
    workspace_id: ID of the workspace (uses client default if not provided).
    project_id: ID of the project (uses client default if not provided).

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

    client.dataviews.update(
        dataset_id=123, dataview_id=456,
        patch_data=[{"op": "replace", "path": "/name", "value": "Renamed"}],
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

### `add_task(self, dataview_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Add a new transformation task to the pipeline.

Args:
    dataview_id: ID of the dataview.
    task_spec: Task specification dict (varies by task type).
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
    command: Draft mode command ("enter", "commit", "discard").
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

### `find_dataset_for_dataview(self, dataview_id: 'int') -> 'int'`

Public typed resolver: find the dataset that contains a dataview.

This is the supported public seam for dataview-to-dataset resolution.
Callers must not reach into the private ``_find_dataset_for_dataview``
helper across sub-clients.

Args:
    dataview_id: ID of the dataview to resolve.

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

### `latest_task_sequence(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'int'`

Return the highest non-deleted task sequence in the pipeline.

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

### `update_task(self, dataview_id: 'int', task_id: 'int', task_spec: 'dict[str, Any]', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Update an existing pipeline task.

Args:
    dataview_id: ID of the dataview.
    task_id: ID of the task to update.
    task_spec: Updated task specification.
    dataset_id: Dataset ID (auto-detected if not provided).

Returns:
    Updated task dict.

### `wait_for_pipeline(self, dataview_id: 'int', dataset_id: 'int | None' = None, timeout: 'int | None' = None, poll_interval: 'int' = 3) -> 'dict[str, Any]'`

Poll pipeline state until it reaches a terminal state.

After any pipeline mutation (add_task, delete_task, sql_generation),
the pipeline transitions through transient states before data is ready:
``modifying → modified → running → ready``.

This method blocks until the pipeline reaches a terminal state
(``ready``, ``runtime_error``, ``ref_error``).

Args:
    dataview_id: ID of the dataview.
    dataset_id: Dataset ID (auto-detected if not provided).
    timeout: Max wait time in seconds (default: client.pipeline_timeout).
    poll_interval: Seconds between polls (default: 3).

Returns:
    Final pipeline state dict.

Raises:
    MammothTransformError: If pipeline reaches ``runtime_error`` or ``ref_error``.
    MammothJobTimeoutError: If timeout is exceeded.


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

Access via ``client.dashboards``::

    dashboards = client.dashboards.list()
    dashboard = client.dashboards.create(
        intent="Show quarterly revenue by region",
        source=[101, 102],
    )
    client.dashboards.share(
        dashboard_id=5,
        type_of_auth=DashboardAuthType.PUBLIC,
    )
    client.dashboards.delete(dashboard_id=5)

### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `action(self, dashboard_id: 'int', action: 'DashboardActionType', params_enabled: 'bool | None' = None, params_view_id: 'int | None' = None) -> 'dict[str, Any]'`

Perform an action on a dashboard.

Args:
    dashboard_id: ID of the dashboard (must be > 0).
    action: The action to execute.
    params_enabled: Required for ``auto-sync`` and ``auto-publish``;
        enables or disables the behaviour.
    params_view_id: Required (> 0) for ``delete-source``;
        optional for ``sync`` and ``auto-sync`` to scope to one source.

Returns:
    Dict with action result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0, ``auto-sync`` /
        ``auto-publish`` are called without *params_enabled*, or
        ``delete-source`` is called without a positive *params_view_id*.

### `analytics(self: 'Any', dashboard_id: 'int') -> 'DashboardAnalyticsResponse'`

Get Dashboard Analytics.

### `cancel_generation(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Cancel an in-progress AI dashboard generation.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with cancellation result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `canvas_get(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'CanvasResponse'`

Editor canvas (draft).

### `canvas_restore(self: 'Any', dashboard_id: 'int', body: 'RestoreCanvasSpec') -> 'ObjectJobSchema | JobResponse'`

Undo / redo / revert the canvas to a target version.

### `canvas_save(self: 'Any', dashboard_id: 'int', body: 'SaveCanvasSpec') -> 'SaveCanvasResponse'`

Save the canvas (append a draft version).

### `chat_edit(self: 'Any', dashboard_id: 'int', body: 'ChatEditSpec') -> 'ObjectJobSchema | JobResponse'`

One chat-edit turn.

### `chat_history(self: 'Any', dashboard_id: 'int', sequence: 'int | None' = None) -> 'mmai_dashboards_v3_schema_ChatHistoryResponse'`

Editor chat transcript.

### `context_create(self: 'Any', body: 'ContextSpec') -> 'ContextResponse'`

Create a context.

### `context_delete(self: 'Any', context_id: 'str') -> 'OkResponse'`

Delete a context.

### `context_list(self: 'Any') -> 'ContextListResponse'`

The workspace's contexts.

### `context_update(self: 'Any', context_id: 'str', body: 'ContextSpec') -> 'ContextResponse'`

Update a context.

### `create(self, intent: 'str', source: '_list[int]', enable_filters: 'bool' = True, enable_pages: 'bool' = False) -> 'dict[str, Any]'`

Create a new AI-generated dashboard.

Args:
    intent: Natural-language description of what the dashboard should
        show (minimum 10 characters).
    source: Non-empty list of dataview IDs to use as the data source.
        All IDs must be positive integers; existence is validated
        server-side.
    enable_filters: Whether to include filter widgets (default ``True``).
    enable_pages: Whether to generate multiple pages (default ``False``).

Returns:
    Dict with created dashboard info (may include a job ID for async
    creation).

Raises:
    MammothValidationError: If *intent* is shorter than 10 characters,
        *source* is empty, or any source ID is not a positive integer.

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

### `descriptor_data(self: 'Any', dashboard_id: 'int', body: 'DescriptorDataSpec') -> 'ObjectJobSchema | JobResponse'`

Descriptor data — future-request.

### `duplicate(self: 'Any', dashboard_id: 'int') -> 'DuplicateDashboardResponse'`

Duplicate a v3 dashboard.

### `figure_intent(self: 'Any', dashboard_id: 'int', body: 'FigureIntentSpec') -> 'FigureIntentResponse'`

Resolve an AI-add figure from an intent.

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

.. note::

    This endpoint may return HTTP 500 on some server configurations.

Returns:
    List of source dicts.

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

### `og_card(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`

Dashboard card thumbnail (draft or published PNG).

### `page_plan(self: 'Any', dashboard_id: 'int', body: 'PlanPageSpec') -> 'PlanPageResponse'`

Compose a new page from an intent.

### `pdf_artifact(self: 'Any', dashboard_id: 'int', job_id: 'int') -> 'dict[str, Any]'`

Download a completed draft PDF export.

### `pdf_export(self: 'Any', dashboard_id: 'int', body: 'PdfExportSpec') -> 'ObjectJobSchema | JobResponse'`

Kick a draft-dashboard PDF export.

### `published_canvas(self: 'Any', url: 'str') -> 'CanvasResponse'`

Published viewer canvas.

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

One Q&A ask turn (async).

### `qa_comment_create(self: 'Any', dashboard_id: 'int', session_id: 'int', body: 'CommentSpec') -> 'SessionResponse'`

Comment on a shared Q&A session.

### `qa_comment_delete(self: 'Any', dashboard_id: 'int', session_id: 'int', comment_id: 'int') -> 'SessionResponse'`

Delete a comment (author or session owner).

### `qa_feedback(self: 'Any', dashboard_id: 'int', session_id: 'int', message_id: 'int', body: 'FeedbackSpec') -> 'SessionResponse'`

Rate an assistant answer (up/down; null clears).

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

This dashboard's Q&A settings.

### `qa_settings_set(self: 'Any', dashboard_id: 'int', body: 'QaSettingsSpec') -> 'QaSettingsResponse'`

Update this dashboard's Q&A settings (editors only).

### `query(self: 'Any', dashboard_id: 'int', body: 'AdhocQuerySpec') -> 'AdhocQueryResponse'`

Editor ad-hoc descriptor query.

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

Create a signature.

### `signature_delete(self: 'Any', signature_id: 'str') -> 'OkResponse'`

Delete a signature.

### `signature_list(self: 'Any') -> 'SignatureListResponse'`

The workspace's signatures.

### `signature_update(self: 'Any', signature_id: 'str', body: 'SignatureSpec') -> 'SignatureResponse'`

Update a signature.

### `source_list(self: 'Any') -> 'DashboardSourcesType'`

Get Dashboard Sources.

### `style_custom_create(self: 'Any', body: 'CustomStyleSpec') -> 'StyleResponse'`

Create a custom style.

### `style_custom_delete(self: 'Any', style_id: 'str') -> 'OkResponse'`

Delete a custom style.

### `style_custom_list(self: 'Any') -> 'StyleListResponse'`

The workspace's custom styles.

### `style_custom_update(self: 'Any', style_id: 'str', body: 'CustomStyleSpec') -> 'StyleResponse'`

Update a custom style.

### `style_default_get(self: 'Any') -> 'DefaultStyleResponse'`

The workspace default style id.

### `style_default_set(self: 'Any', body: 'DefaultStyleSpec') -> 'DefaultStyleResponse'`

Set the workspace default style id.

### `style_derive(self: 'Any', body: 'DeriveStyleSpec') -> 'dict[str, Any] | DeriveStyleResponse'`

Derive a full Style bundle from signals.

### `style_extract_brand(self: 'Any', body: 'ExtractBrandSpec') -> 'ObjectJobSchema | JobResponse'`

Kick a brand extraction from a URL.

### `style_preset_list(self: 'Any') -> 'StylePresetsResponse'`

Style presets (stock + custom).

### `style_token_list(self: 'Any', id: 'str') -> 'StyleTokensResponse'`

Full Style bundle by id (stock or custom).

### `suggestion_list(self: 'Any', dataview_id: 'int', table_item_id: 'int | None' = None) -> 'DashboardSuggestionsResponse'`

Data-grounded starting points for the create screen.

### `template_apply(self: 'Any', body: 'ApplyTemplateSpec') -> 'ObjectJobSchema | JobResponse'`

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

### `trash(self, dashboard_id: 'int') -> 'dict[str, Any]'`

Move a dashboard to trash.

Args:
    dashboard_id: ID of the dashboard (must be > 0).

Returns:
    Dict with trash result.

Raises:
    MammothValidationError: If *dashboard_id* ≤ 0.

### `update(self, dashboard_id: 'int', patch: '_list[DashboardPatchItem]') -> 'dict[str, Any]'`

Update a dashboard via JSON-patch operations.

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

### `v3_generate(self: 'Any', body: 'GenerateDashboardV3Spec') -> 'ObjectJobSchema | JobResponse'`

Generate a v3 dashboard.

### `video_export(self: 'Any', dashboard_id: 'int') -> 'ObjectJobSchema | JobResponse'`

Kick a motion-story video export.

### `video_state(self: 'Any', dashboard_id: 'int') -> 'dict[str, Any]'`

Motion-story video export state (never kicks a render).

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

    automations = client.automations.list()
    automation = client.automations.create(
        name="Nightly refresh",
        description="Pulls cloud data every night",
        tasks=[AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
        )],
    )
    schedules = client.automations.list_schedules()

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

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
          must be ``"suspend"`` or ``"resume"``.
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

    schedules = client.schedules.list()
    schedule = client.schedules.create(
        spec=ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=datetime(2025, 1, 1)),
        )
    )
    client.schedules.delete(schedule_id)

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

.. note::

    Requires workspace admin permissions. Non-admin users may
    receive HTTP 405.

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

    profile = client.user_profile.get()
    client.user_profile.update(name="New Name")

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `change_password(self, current_password: 'str', new_password: 'str') -> 'dict[str, Any]'`

Change user password.

Note: This endpoint is not documented in the public OpenAPI spec.

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

    batches = client.batches.list(dataset_id=123)
    batch = client.batches.get(dataset_id=123, batch_id=1)

#### `__init__(self, client: 'MammothClient') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

#### `bulk_delete(self, dataset_id: 'int', ids: '_list[int] | str | None' = None, project_id: 'int | None' = None) -> 'dict[str, Any]'`

Bulk-delete batches for a dataset.

Args:
    dataset_id: ID of the dataset.
    ids: Optional list of batch IDs (or comma-separated string) to
        delete. If omitted, all batches for the dataset are deleted.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with deletion result.

#### `create(self, dataset_id: 'int', source_id: 'int', mapping: 'dict[str, str]', project_id: 'int | None' = None, new_ds_params: 'dict[str, Any] | None' = None, is_validation_required: 'bool | None' = None, change_map: 'dict[str, Any] | None' = None, delete_source_ds: 'bool' = False) -> 'dict[str, Any]'`

Create a new batch for a dataset.

The ``source`` field is hardcoded to ``"datasource"`` — the only
supported source type.

Args:
    dataset_id: ID of the destination dataset.
    source_id: ID of the source dataset (must be a positive integer).
    mapping: Non-empty dict mapping source column names to destination
        column names, e.g. ``{"src_col": "dst_col"}``.
    project_id: Project ID (uses client default if not provided).
    new_ds_params: Optional params for creating a new dataset.
    is_validation_required: Whether to validate the batch.
    change_map: Optional change-tracking column map.
    delete_source_ds: Whether to delete the source dataset after batch
        (default ``False``).

Returns:
    Dict with created batch info.

Raises:
    MammothValidationError: If ``source_id`` is not positive or ``mapping``
        is empty.

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

#### `update(self, dataset_id: 'int', patch: '_list[dict[str, Any]]', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Update batches for a dataset via patch operations.

The backend expects ``{"patch": [<ops>]}``. Each op has:

- ``op``: ``"replace"`` or ``"remove"``
- ``value``: for ``replace`` — a dict mapping operation name to list of
  batch IDs; for ``remove`` — a list of batch IDs.

Args:
    dataset_id: ID of the dataset.
    patch: Non-empty list of patch operation dicts.  Each dict must
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

#### `projects(self, workspace_id: 'int | None' = None) -> 'dict[str, Any]'`

Browse projects in a workspace.

Args:
    workspace_id: Workspace ID (uses client default if not provided).

Returns:
    Dict with project resources.

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

    keys = client.external_keys.list()
    key = client.external_keys.create(name="My Key")
    client.external_keys.delete(key_id)

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

    client.external_keys.create(
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

    client.addons.add_connector(connector_id=42)
    client.addons.add_connector(connector_ids=[42, 43])
    client.addons.add_storage(additional_storage_gb=50)
    client.addons.add_users(user_count=5)

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
    client.ai.generate_sql(intent="total sales by region")
    suggestions = client.ai.get_suggestions()

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

#### `generate_profile(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate an AI profile/summary of the dataview data.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with profile information.

#### `generate_sql(self, intent: 'str', sequence_number: 'int' = 0) -> 'dict[str, Any]'`

Generate SQL from natural language intent.

Uses the project-level sql_generation endpoint.

Args:
    intent: Natural language description of the query.
    sequence_number: Sequence number for the SQL generation request.

Returns:
    Dict with generated SQL and metadata.

#### `get_data_gen_info(self, dataview_id: 'int', dataset_id: 'int | None' = None) -> 'dict[str, Any]'`

Get data generation information for a dataview.

Args:
    dataview_id: ID of the dataview.
    dataset_id: ID of the dataset (auto-detected if not provided).

Returns:
    Dict with data generation info.

#### `get_suggestions(self) -> 'dict[str, Any]'`

Get AI-powered transformation suggestions for the current project.

Returns:
    Dict with suggested transformations.

#### `query_gen(self, connector_key: 'str', connection_key: 'str', prompt: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Generate a query for a connector using AI.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    prompt: Natural language prompt describing the query.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with generated query.

#### `status(self, connector_key: 'str', connection_key: 'str', project_id: 'int | None' = None) -> 'dict[str, Any]'`

Get the status of an AI chat session for a connector connection.

Args:
    connector_key: Key identifying the connector type.
    connection_key: Key identifying the connection.
    project_id: Project ID (uses client default if not provided).

Returns:
    Dict with chat status information.


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
- Verify Python 3.12-3.14: `python --version`
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
