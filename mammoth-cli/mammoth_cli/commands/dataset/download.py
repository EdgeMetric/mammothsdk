"""Download several datasets, views and folders of the project as one file."""

from __future__ import annotations

from mammoth_cli.commands.dataset._common import _meta, _symbol
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.local_files import refuse_existing_file

_URL_SYMBOL = "mammoth.api.exports.ExportsAPI.bulk_download_url"


def dataset_download(invocation: Invocation) -> HandlerResult:
    """Download several datasets, views and folders as one csv, zip of csvs or xlsx file.

    ``--input '{"resource_ids": [12, 13], "name": "sales"}'`` writes ``sales.csv`` (``.zip``
    for several CSVs) to the current directory; ``file_type`` ``xlsx`` makes one workbook,
    ``stack`` puts same-column datasets in one file, ``numbered`` numbers the files in order
    and ``output_path`` names the file. An existing file is not replaced unless
    ``--overwrite``. Embedded, no file is written: the signed download URL is returned.
    """
    project_id = require_project(invocation)
    kwargs = bind_command_inputs(invocation.command_id, invocation.load_input() or {})
    if embedded.active():
        if "output_path" in kwargs:
            raise CliError(
                code=CODE_UNSUPPORTED_CONTRACT,
                message="output_path is not supported here; embedded calls write no file.",
                exit_status=EXIT_USAGE,
                hint="Drop output_path -- an embedded call returns a download_url instead.",
            )
        with open_service(invocation) as (service, auth):
            data = service.call(_URL_SYMBOL, **kwargs)
        return {"download_url": data["url"]}, _meta(invocation, auth.workspace_id, project_id)
    if kwargs.get("output_path") is not None:
        refuse_existing_file(invocation, kwargs["output_path"])
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id, project_id)
