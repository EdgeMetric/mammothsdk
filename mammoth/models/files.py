"""
File-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SheetInfo(BaseModel):
    """Information about a sheet in an Excel file."""

    sheet_name: str = Field(..., min_length=1, description="Name of the sheet")
    num_rows: int = Field(..., description="Number of rows in the sheet")
    num_cols: int = Field(..., description="Number of columns in the sheet")


class AdditionalInfo(BaseModel):
    """Additional information about a file."""

    append_to_ds_id: int | None = Field(None, description="Dataset ID to append to")
    parent_id: str | None = Field(None, description="Parent folder ID")
    delete_existing_after_append: bool = Field(
        False, description="Whether to delete existing data after append"
    )
    password_protected: bool = Field(False, description="Whether the file is password protected")
    sheets_info: list[SheetInfo] | None = Field(
        None, description="Information about sheets in Excel files"
    )
    final_ds_id: int | None = Field(None, description="Final dataset ID after processing")
    url: str | None = Field(None, description="URL of the file")


class StatusInfo(BaseModel):
    """Status information for a file."""

    extracting: str | None = Field(None, description="Extracting status information")
    extracted: str | None = Field(None, description="Extracted status information")
    action_needed: str | None = Field(None, description="Action needed information")
    processing: str | None = Field(None, description="Processing status information")
    processed: str | None = Field(None, description="Processed status information")
    error: str | None = Field(None, description="Error status information")
    is_hidden: bool = Field(False, description="Whether the file is hidden")
    is_empty: bool = Field(False, description="Whether the file is empty")


class FileSchema(BaseModel):
    """Schema for a file object."""

    id: int | None = Field(None, description="Unique identifier for the file")
    name: str | None = Field(None, min_length=1, description="Name of the file")
    status: str | None = Field(None, min_length=1, description="Current status of the file")
    created_at: datetime | None = Field(None, description="Timestamp when the file was created")
    last_updated_at: datetime | None = Field(
        None, description="Timestamp when the file was last updated"
    )
    status_info: StatusInfo | None = Field(None, description="Detailed status information")
    additional_info: AdditionalInfo | None = Field(None, description="Additional file information")


class FileDetails(BaseModel):
    """Response model for file details."""

    file: FileSchema


class FilesList(BaseModel):
    """Response model for listing files."""

    files: list[FileSchema] = Field(..., description="List of files")
    limit: int = Field(10, description="Maximum number of results returned")
    offset: int = Field(0, description="Offset from the beginning of results")
    next: str = Field(..., description="URL for the next page of results")


class ExtractSheetsPatch(BaseModel):
    """Configuration for extracting sheets from Excel files."""

    sheets: list[str] = Field(..., description="Names of sheets to extract")
    delete_file_after_extract: bool = Field(
        True, description="Whether to delete main file after extraction"
    )
    combine_after_extract: bool = Field(
        False, description="Whether to combine sheets after extraction"
    )


class PdfUserInstruction(BaseModel):
    """A plain-English instruction for how to read a PDF."""

    instruction: str = Field(..., description="What to extract, in plain English")
    instruction_type: Literal["initial", "edited", "final"] = Field(
        "initial",
        description="'initial'/'edited' preview a page; 'final' applies to the whole document",
    )


class ExtractPdfTablesPatch(BaseModel):
    """Configuration for extracting tables or content from a PDF file.

    This is the extraction setting a destination dataset's saved recipe replays for
    PDFs that later arrive through an automation. The server checks the combination
    (for example ``extract_full_document`` is required with a ``final`` instruction
    and not allowed with an ``initial`` or ``edited`` one).
    """

    filename: str = Field(..., description="Name of the PDF file to extract from")
    extraction_method: Literal["tables_only", "all_content", "custom"] = Field(
        ..., description="What to extract from the document"
    )
    user_instruction: PdfUserInstruction | None = Field(
        None, description="Instruction for a custom extraction"
    )
    preview_page: int | None = Field(None, description="Page number to preview")
    extract_full_document: bool = Field(False, description="Whether to extract the entire document")
    delete_file_after_extract: bool = Field(
        False, description="Whether to delete the PDF after extraction"
    )


class FilePatchOperation(str, Enum):
    """Valid operations for file patching."""

    REPLACE = "replace"


class FilePatchPath(str, Enum):
    """Valid paths for file patching."""

    EXTRACT_SHEETS = "extract_sheets"
    PASSWORD = "password"
    EXTRACT_PDF_TABLES = "extract_pdf_tables"


class FilePatchData(BaseModel):
    """Data for a single patch operation."""

    op: FilePatchOperation = Field(..., description="Operation to perform")
    path: FilePatchPath = Field(..., description="Path to patch")
    value: str | ExtractSheetsPatch | ExtractPdfTablesPatch = Field(..., description="Value to set")


class FilePatchRequest(BaseModel):
    """Request model for patching file configuration."""

    patch: list[FilePatchData] = Field(..., description="List of patch operations")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"patch": [{"op": "replace", "path": "password", "value": "test"}]},
                {
                    "patch": [
                        {
                            "op": "replace",
                            "path": "extract_sheets",
                            "value": {
                                "sheets": ["Sheet1", "Sheet2"],
                                "delete_file_after_extract": True,
                            },
                        }
                    ]
                },
            ]
        }
    )
