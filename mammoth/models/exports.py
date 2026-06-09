"""
Export-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from mammoth.models.jobs import JobResponse


class HandlerType(str, Enum):
    """Handler types for export operations."""

    POSTGRES = "postgres"
    CSV_FILE = "csv_file"
    S3 = "s3"
    MYSQL = "mysql"
    MSSQL = "mssql"
    FTP = "ftp"
    SFTP = "sftp"
    EMAIL = "email"
    ELASTICSEARCH = "elasticsearch"
    POWERBI = "powerbi"
    REDSHIFT = "redshift"
    BIGQUERY = "bigquery"
    INTERNAL_DATASET = "internal_dataset"
    PUBLISHDB = "publishdb"
    AZURE_BLOB = "azure_blob"
    SHAREPOINT = "sharepoint"
    ONEDRIVE = "onedrive"
    TABLEAU_SERVER = "tableau_server"
    GENERIC_REST_API_EXPORT = "generic_rest_api_export"


class TriggerType(str, Enum):
    """Trigger types for export operations."""

    NONE = "none"
    PIPELINE = "pipeline"
    SCHEDULE = "schedule"


class OdbcType(str, Enum):
    """Managed-connection types supported by publish-to-db."""

    POSTGRES = "postgres"
    BIGQUERY = "bigquery"


class BigQueryExportType(str, Enum):
    """How rows are written into the BigQuery destination table."""

    REPLACE = "REPLACE"
    COMBINE = "COMBINE"
    UPSERT = "UPSERT"


class HttpMethod(str, Enum):
    """HTTP verbs accepted by the generic REST API export."""

    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


class RestAuthType(str, Enum):
    """Authentication schemes accepted by the generic REST API export."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2_AUTHORIZATION_CODE = "oauth2_authorization_code"


class ExportStatus(str, Enum):
    """Status values for exports."""

    DELETED = "deleted"
    EXECUTED = "executed"
    EXECUTING = "executing"
    EDITED = "edited"
    ADDED = "added"
    SUSPENDED = "suspended"
    SUSPENDING = "suspending"


class S3TargetProperties(BaseModel):
    """Configuration properties for S3 export destinations."""

    file: str = Field(..., description="Output filename")
    file_type: str = Field(..., description="File format type e.g. csv")
    include_hidden: bool = Field(..., description="Include hidden columns")
    is_format_set: bool = Field(..., description="Format explicitly set")
    use_format: bool = Field(..., description="Apply formatting")


class AddExportSpec(BaseModel):
    """Specification for adding export tasks to dataview pipeline."""

    DATAVIEW_ID: int = Field(
        ..., description="The ID of the View (dataview) from which data will be exported"
    )
    sequence: int | None = Field(
        description="Pipeline execution order position.",
        default=None,
    )
    TRIGGER_ID: int | None = Field(
        description="Trigger ID. Non-None means editing.",
        default=None,
    )
    end_of_pipeline: bool = Field(
        description="Execute at end of pipeline after transforms.",
        default=True,
    )
    handler_type: HandlerType = Field(..., description="Export handler (destination type)")
    trigger_type: TriggerType = Field(..., description="Trigger that controls when export executes")
    target_properties: S3TargetProperties | dict[str, Any] = Field(
        ..., description="Destination configuration properties"
    )
    additional_properties: dict[str, Any] = Field(
        ..., description="Additional export configuration"
    )
    condition: dict[str, Any] = Field(
        description="Export conditions. Empty dict means none.",
        default_factory=dict,
    )
    run_immediately: bool = Field(..., description="Execute immediately upon creation")
    validate_only: bool = Field(
        description="Validate config without executing.",
        default=False,
    )


class ItemExportInfo(BaseModel):
    """Information about an individual export in the pipeline."""

    id: int | None = Field(None, description="Unique identifier for the export")
    dataview_id: int | None = Field(None, description="ID of the dataview this export belongs to")
    sequence: int | None = Field(None, description="Position in the pipeline execution order")
    sub_sequence: int | None = Field(None, description="Sub-position within the same sequence")
    handler_type: HandlerType | None = Field(None, description="Type of export handler")
    trigger_type: TriggerType | None = Field(None, description="Type of trigger for this export")
    end_of_pipeline: bool | None = Field(
        None, description="Whether this export executes at the end of the pipeline"
    )
    status: ExportStatus | None = Field(None, description="Current status of the export")
    target_properties: dict[str, Any] | None = Field(
        None, description="Export destination configuration"
    )
    runnable: bool | None = Field(None, description="Whether the export can be executed")
    reordered: bool | None = Field(None, description="Whether the export has been reordered")
    data_pass_through: bool | None = Field(
        None, description="Whether data passes through this export"
    )
    additional_properties: dict[str, Any] | None = Field(
        None, description="Additional export configuration"
    )
    condition: dict[str, Any] | None = Field(None, description="Conditional logic for the export")
    last_modified_time: datetime | None = Field(
        None, description="When the export was last modified"
    )
    execution_start_time: datetime | None = Field(
        None, description="When the export execution started"
    )
    execution_end_time: datetime | None = Field(None, description="When the export execution ended")
    last_run_result: dict[str, Any] | None = Field(None, description="Result of the last execution")
    error_info: dict[str, Any] | None = Field(
        None, description="Error information if execution failed"
    )


class PipelineExportsPaginated(BaseModel):
    """Paginated response for pipeline exports."""

    limit: int = Field(10, description="Setting limit would limit the items received in the page")
    offset: int = Field(0, description="First position to return from the results")
    next: str = Field(..., description="Url of the next page")
    exports: list[ItemExportInfo] = Field(..., description="List of export items")


class PipelineExportsModificationResp(BaseModel):
    """Response for export modification operations."""

    trigger_id: int = Field(..., description="Id of the export")
    status: ExportStatus | None = Field(None, description="New status of the export")
    future_id: int | None = Field(
        None, description="Id of the trackable job running in the background"
    )


# What an export-creation call returns: either the saved trigger record
# (synchronous handlers) or a tracking job (asynchronous handlers).
ExportResult = PipelineExportsModificationResp | JobResponse


class ExportTargetKey:
    """Wire keys for export ``target_properties`` (the dict each handler reads).

    Named constants so the per-handler contracts and builders never carry raw
    string literals. Values are the exact backend keys — some are camelCase by
    backend convention (BigQuery export type / upsert keys).
    """

    HOST = "host"
    PORT = "port"
    USERNAME = "username"
    PASSWORD = "password"
    DATABASE = "database"
    TABLE = "table"
    # s3 / file output
    FILE = "file"
    FILE_TYPE = "file_type"
    INCLUDE_HIDDEN = "include_hidden"
    IS_FORMAT_SET = "is_format_set"
    USE_FORMAT = "use_format"
    # email
    EMAILS = "emails"
    MESSAGE = "message"
    RESOURCE = "resource"
    SUBJECT = "subject"
    # ftp
    DOMAIN = "domain"
    DIRECTORY = "directory"
    # sftp
    FILE_NAME = "file_name"
    SSH_KEY_AUTHENTICATION = "ssh_key_authentication"
    PRIVATE_KEY = "private_key"
    PASSPHRASE = "passphrase"
    RANDOMIZE_FILE_NAME = "randomize_file_name"
    # elasticsearch
    INDEX = "index"
    CONNECTION = "connection"
    CHUNKSIZE = "chunksize"
    # azure blob / sharepoint / onedrive (MS Graph)
    STORAGE_ACCOUNT_NAME = "storage_account_name"
    TENANT_ID = "tenant_id"
    CLIENT_ID = "client_id"
    CLIENT_ID_CAMEL = "clientId"  # power bi backend reads camelCase (powerbi.py:82,140)
    CLIENT_SECRET = "client_secret"
    CONTAINER_NAME = "container_name"
    FOLDER_PATH = "folder_path"
    SITE_URL = "site_url"
    DOCUMENT_LIBRARY = "document_library"
    USER_ID = "user_id"
    # bigquery
    SELECTED_PROFILE = "selected_profile"
    SELECTED_IDENTITY = "selected_identity"
    EXPORT_TYPE = "exportType"
    UPSERT_KEYS = "upsertKeys"
    PARTITION = "partition"
    # generic rest api
    BASE_URL = "base_url"
    ENDPOINT_PATH = "endpoint_path"
    AUTH_TYPE = "auth_type"
    HTTP_METHOD = "http_method"
    WRAP_PATH = "wrap_path"
    BATCH_SIZE = "batch_size"
    TIMEOUT_SECONDS = "timeout_seconds"
    RATE_LIMIT_RPS = "rate_limit_requests_per_second"
    SSL_VERIFY = "ssl_verify"
    DEFAULT_HEADERS = "default_headers"
    REQUEST_HEADERS = "request_headers"
    QUERY_PARAMS = "query_params"
    EXTRA_BODY_FIELDS = "extra_body_fields"
    # publishdb
    ODBC_TYPE = "odbc_type"
    PROJECT_ID = "project_id"
    DATASET = "dataset"
    # tableau server
    SERVER_URL = "server_url"
    TOKEN_NAME = "token_name"
    TOKEN_SECRET = "token_secret"
    SITE_NAME = "site_name"
    PROJECT_NAME = "project_name"
    DATASOURCE_NAME = "datasource_name"
    CA_BUNDLE_PATH = "ca_bundle_path"


class DashboardSpecKey:
    """Wire keys for the AI dashboard-generation spec (``POST /dashboards`` body)."""

    PARAMS = "params"
    INTENT = "intent"
    SOURCE = "source"
    ENABLE_FILTERS = "enable_filters"
    ENABLE_PAGES = "enable_pages"
