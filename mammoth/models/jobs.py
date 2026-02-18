"""
Job-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"
    PROCESSING = "processing"
    ERROR = "error"


class JobSchema(BaseModel):
    """Job schema model."""

    id: int = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status can be success, failure or processing")
    response: dict[str, Any] = Field(..., description="Result of async task is stored in response")
    last_updated_at: datetime = Field(
        ..., description="Job last updated at is the time when Job status was last updated"
    )
    created_at: datetime = Field(..., description="Create at is time when async task was created")
    path: str = Field(..., description="API request path of the Job operation")
    operation: str = Field(..., description="Operation is async task name which Job is tracking")


class JobResponse(BaseModel):
    """Job response model."""

    job: JobSchema = Field(..., description="Job information")


class JobsGetResponse(BaseModel):
    """Multiple jobs response model."""

    jobs: list[JobSchema] = Field(..., description="List of jobs")


class ObjectJobSchema(BaseModel):
    """Object job schema model."""

    status_code: int | None = Field(None, description="Status code")
    job_id: int | None = Field(None, description="Created job id")
    failure_reason: str | None = Field(None, description="Failure reason if status is failure")
