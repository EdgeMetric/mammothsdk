"""Names, limits and field names the MCP server uses."""

from .config import APP_URL, DASHBOARD_DOMAIN

MCP_SERVER_NAME = "Mammoth Analytics"
MCP_INSTRUCTIONS = (
    "Mammoth Analytics lets you explore, clean, transform and export data. "
    "Data is organised as workspace > project > dataset > view; a view is a "
    "pipeline of transformation tasks over a dataset. Every tool acts as the "
    "signed-in user, with that user's permissions."
)

# The same upload, drawn in the chat by a client that speaks MCP Apps. The host
# lets the page's frame fetch only from the origins its resource names.
UPLOAD_APP_URI = "ui://mammoth/upload.html"
# Where the user settles, in the web app, what an upload waits on and no tool can.
MAMMOTH_PROJECT_URL = f"{APP_URL}/#/workspaces/{{workspace_id}}/projects/{{project_id}}"
# A dashboard's two links, built as the share emails build them
# (`api.email.transactional`). The one to give the user is the viewer link: it
# opens the published board, on the host that serves it. The editor link is the
# owner's, and the viewer host bounces it back to the viewer. Each pair has a
# route per engine, and a board drawn on the other engine's route is blank.
DASHBOARD_VIEWER_URL = f"{DASHBOARD_DOMAIN}/#/{{route}}/{{url}}"
DASHBOARD_EDITOR_URL = f"{APP_URL}/#/workspaces/{{workspace_id}}/{{route}}/{{id}}"
# The engine the current dashboards are drawn on, as the API names it.
ENGINE_V3 = "v3"
VIEWER_ROUTE = {ENGINE_V3: "dashboard-v3"}
EDITOR_ROUTE = {ENGINE_V3: "publish"}
OLDER_ENGINE_ROUTE = "dashboard"
# How long an upload link is good for: long enough to leave the conversation,
# find the file and come back, and no longer.
UPLOAD_SECONDS = 30 * 60
# How long `check_upload` holds the call while the user is still picking their
# file. Answering at once ends the model's turn, and a turn that has ended
# needs the user to start another one just to say the file is in. Short enough
# to leave `TOOL_CALL_SECONDS` room for the job wait that follows.
UPLOAD_WAIT_SECONDS = 30.0
UPLOAD_POLL_SECONDS = 1.0
# Listing tools page by default, so one call cannot fill the model's context.
LIST_LIMIT_DEFAULT = 50

# Rows one `get_data` call returns. A model reads a sample to decide what to do
# next; it does not read the table. The cap is the API's page limit.
DATA_LIMIT_DEFAULT = 50
DATA_LIMIT_MAX = 400

# Async API routes answer with a job, so a tool polls until the job finishes.
# A tool call has to return inside the client's own request timeout.
JOB_POLL_SECONDS = 0.2
# A wait between checks doubles from `JOB_POLL_SECONDS` up to this: a short job is
# seen at once, and a long build is not checked several times a second.
JOB_POLL_MAX_SECONDS = 2.0
JOB_TIMEOUT_SECONDS = 60.0
# How long one tool call may wait in all, over every job it waits on. A client
# gives up on a call after about a minute, so the answer must come before then.
TOOL_CALL_SECONDS = 45.0
# How long to wait on an AI dashboard build before answering "still building".
# Shorter than the rest: a build outlasts any wait worth making, and a client
# that gives up first never sees the answer at all — so the model is told
# nothing, assumes nothing was built, and starts a second, paid-for build.
BUILD_WAIT_SECONDS = 25.0

# How long one API route may take before a tool gives up on it. A route that
# never answers would hold this worker until gunicorn kills it, which drops every
# other caller's connection too.
ROUTE_TIMEOUT_SECONDS = 90.0


# Rows a step preview runs on. A preview is for checking a step's shape, not
# for reading the table.
PREVIEW_ROWS_DEFAULT = 10
PREVIEW_ROWS_MAX = 100

# How many times to read set-aside lines while discarding them. One read returns
# the first 100, so this covers 5,000 lines and still ends.
DISCARD_READS = 50

# The multipart field the API's upload route reads the file from.
UPLOAD_FIELD = "data"
# What a model can hand over as text and Mammoth can read. Anything else has to
# go through the web app, because a tool argument carries no binary.
UPLOAD_MEDIA_TYPES = {
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".json": "application/json",
    ".txt": "text/plain",
}


class UploadFields:
    """The upload handoff: its record, its link, and what `check_upload` reports."""

    # The kind the ticket is stored under, and the query the page is opened with.
    TICKET = "upload"
    UPLOAD_ID = "upload_id"
    UPLOAD_URL = "upload_url"
    # What the record holds while the user is away.
    WORKSPACE_ID = "workspace_id"
    PROJECT_ID = "project_id"
    CALLER = "caller"
    JOB_ID = "job_id"
    FILE_NAMES = "file_names"
    # When the files were sent: what the upload made is what was created since.
    UPLOADED_AT = "uploaded_at"
    # Where the upload has got to. `waiting` until the user picks a file,
    # `processing` while Mammoth reads it, then `done`.
    STATUS = "status"
    WAITING = "waiting"
    PROCESSING = "processing"
    DONE = "done"
    FILES = "files"
    REJECTED = "rejected"
    # Where the upload job lists the files Mammoth refused.
    ERRORS = "errors"


class UploadReportFields:
    """One file or dataset in what `check_upload` reports, and what it waits on."""

    KIND = "kind"
    FILE_ID = "file_id"
    DATASET_ID = "dataset_id"
    # The view a finished dataset is read through: a dashboard, a read or a
    # transformation takes the view, not the dataset.
    VIEW_ID = "view_id"
    NAME = "name"
    NEEDS = "needs"
    ACTION = "action"
    NEXT_STEP = "next_step"
    MAMMOTH_URL = "mammoth_url"
    SHEETS = "sheets"
    # What Mammoth could not decide about a file's layout, and the ways of
    # answering it that Mammoth itself suggests.
    SUMMARY = "summary"
    SUGGESTIONS = "suggested_instructions"
    # The core-list property Mammoth keeps what an item waits on in.
    USER_ACTION_REQUIRED = "user_action_required"


class InterpretationFields:
    """Telling Mammoth how to read a file it found more than one way to read.

    The dataset carries what it could not decide under its own
    `interpretation`, which the resources API reports with everything else it
    holds. The preview route turns a plain-English instruction into rows, and
    the confirm route reads the whole file that way.
    """

    # Where the dataset keeps it, as the resources API nests it.
    ADDITIONAL_INFO = "additional_info"
    INTERPRETATION = "interpretation"
    # Set on a batch that is about to be read the way its dataset was read
    # before. It carries the same status as a file nobody can read, and this
    # is what tells the two apart.
    REPLAYING = "recipe_replay_pending"
    SUMMARY = "interpretation_summary"
    SUGGESTIONS = "instruction_suggestions"
    # The rows the web app's modal draws its own preview from. A model reads
    # the rows an instruction makes instead, so it never asks for these.
    SAMPLE_ROWS = "sample_rows"
    # What the two routes take, and what the preview answers with.
    INSTRUCTION = "user_instruction"
    STRUCTURE_MAP = "structure_map"
    ROWS = "preview_rows"
    TOTAL_ROWS = "total_row_count"
    APPLIED = "applied"
    # How a refusal arrives: the plan is replaced by the verdict, and the
    # answer is otherwise an ordinary empty preview. A first reading is judged
    # on whether the instruction reshapes the file at all; a batch added to an
    # existing dataset, on whether it still fits that dataset's columns.
    IN_SCOPE = "is_in_scope"
    COMPATIBLE = "schema_compatible"
    REFUSED = "out_of_scope_reason"
    # What says "read the whole file the way you just previewed it". The route
    # never trusts a map sent back to it — `transform_sql` would be arbitrary
    # SQL — so it re-reads the one the preview saved, and only this field's
    # presence chooses that over deriving a fresh one.
    REUSE_THE_PREVIEW: dict[str, str] = {}


class UnstructuredFields:
    """The lines of a file that did not fit the dataset Mammoth built from it.

    A file whose rows are ragged is read as far as it can be, and the lines
    that did not fit are set aside. The dataset then holds data and still
    waits, because nobody has said what to do about them.
    """

    ROWS = "unstructured_rows"
    ROW_COUNT = "row_count"
    LINE = "line"
    LINE_NUMBER = "line_num"
    REASON = "reason"
    BATCH_ID = "batch_id"
    DELETED = "rows_deleted"
    DISCARDED = "discarded"


class FilePatchFields:
    """The body `PATCH /files/{id}` accepts: which sheets of a workbook to bring
    in, and the password that opens a locked one."""

    PATCH = "patch"
    OP = "op"
    REPLACE = "replace"
    PATH = "path"
    EXTRACT_SHEETS = "extract_sheets"
    PASSWORD = "password"
    VALUE = "value"
    SHEETS = "sheets"


class FileSettingsFields:
    """How Mammoth read a dataset's file, as its `file_settings` route has it.

    Re-reading the file with a date format sends back the settings it was read
    with, so nothing else changes. That includes the choices already made about
    single columns: the route takes the whole set every time, so one left out
    is one undone.
    """

    INFO = "info"
    DATE_FORMAT = "date_format"
    # A format for one named column, which beats the whole file's. A file put
    # together from two systems can hold a column of each.
    DATE_FORMATS = "date_formats"
    PROJECT_DEFAULT = "set_project_level_date_format"
    # The date columns the user may set, which is the ambiguous ones and the
    # ones already set by hand.
    DATE_COLUMNS = "editable_date_columns"
    AMBIGUOUS_COLUMNS = "date_columns"
    APPLIED = "applied"
    KEPT = ("delimiter", "has_header", "initial_skip_count", "quotechar")


class ApiPaths:
    """The routes a tool calls that the SDK has no method for yet."""

    WORKSPACES = "/workspaces"
    FILES = "/workspaces/{workspace_id}/projects/{project_id}/files"
    FILE = FILES + "/{file_id}"
    FILE_SETTINGS = (
        "/workspaces/{workspace_id}/projects/{project_id}" "/datasets/{dataset_id}/file_settings"
    )
    RESOURCES = "/workspaces/{workspace_id}/projects/{project_id}/resources"
    BROWSE = "/workspaces/{workspace_id}/browse"


class ResourceTypes:
    """The kinds of item a project lists that an upload makes."""

    FILE = "file_object"
    DATASET = "datasource"


class FileStatus:
    """The states an uploaded file moves through."""

    PROCESSING = "processing"
    EXTRACTING = "extracting"
    PROCESSED = "processed"
    EXTRACTED = "extracted"
    ERROR = "error"
    ACTION_NEEDED = "action_needed"


class DatasetStatus:
    """The states a dataset moves through while Mammoth reads its file."""

    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    DUPLICATING = "duplicating"
    APPENDING = "appending"
    MERGING = "merging"
    READY = "ready"
    PROCESSED = "processed"
    EMPTY = "empty"
    ACTION_NEEDED = "need_action"
    HAS_UNSTRUCTURED_DATA = "has_unstructured_data"


class UserActions:
    """What Mammoth says a file or dataset waits on the user for."""

    TYPE = "type"
    SHEET_INFO = "sheet_info"
    SHEET_SELECTION_REQUIRED = "sheet_selection_required"
    AMBIGUOUS_DATE_FORMAT = "ambiguous_date_format"
    PASSWORD_REQUIRED = "password_required"
    UNSTRUCTURED_ROWS = "unstructured_rows"


class ErrorFields:
    """Where an API error body, or a failed job, puts its reason."""

    NAME = "name"
    MESSAGE = "message"


class ListFields:
    """Keys the API's list answers put their rows under, and a row's own fields."""

    PROJECTS = "projects"
    DATASETS = "datasets"
    VIEWS = "dataviews"
    ID = "id"
    NAME = "name"


class BrowseFields:
    """The browse route's query parameters and the key its rows come under.

    Browse is the one route that answers for a named resource id, which is how
    a pinned connection reads its own project without paging for it.
    """

    RESOURCES = "resources"
    TYPE = "browse_type"
    PROJECT = "project"
    IDS = "ids"
    LEVEL = "level"
    # Level 1 is the resources themselves, with none of their children.
    ITSELF = 1


class JobFields:
    """The job an async API route returns, and the statuses it moves through."""

    JOB = "job"
    JOB_ID = "job_id"
    ID = "id"
    STATUS = "status"
    RESPONSE = "response"
    PROCESSING = "processing"
    SUCCESS = "success"
    # What a tool that answers before its job finished tells the model to do.
    NOTE = "note"


class ViewFields:
    """What `delete_views` reports. The SDK names the fields it sends itself."""

    VIEW_ID = "view_id"
    ERROR = "error"
    DELETED = "deleted"
    FAILED = "failed"


class TaskFields:
    """A pipeline change, and the pipeline run it may start.

    The add-task route answers with the change itself when it rejects it up
    front, and otherwise with a job whose result is the change. A change that
    started a run is still processing and names the run's job in `future_id`.
    """

    STATUS = "status"
    DONE = "done"
    PROCESSING = "processing"
    HAS_ERROR = "has_error"
    ERROR_INFO = "error_info"
    RUN_ID = "future_id"
    TASK_RESULTS = "taskwise_execution_result"
    ERROR_DETAILS = "error_details"
    # The view a task param is for, as the task routes name it.
    DATAVIEW_ID = "DATAVIEW_ID"


class ColumnFields:
    """One column of a view or of a file, as the API lists it."""

    DISPLAY_NAME = "display_name"
    INTERNAL_NAME = "internal_name"
    TYPE = "type"
    FORMAT = "format"
    DATE_FORMAT_TYPE = "date_format_type"


class SqlGenerationFields:
    """What the SQL generation job answers with, under `response`."""

    RESPONSE = "response"
    STATUS_CODE = "status_code"
    DETAIL = "detail"
    RESULT = "result"
    SUCCESS = "SQ01"


class AutomationFields:
    """The body `POST automations` accepts, and the patches that change one."""

    ID = "id"
    NAME = "name"
    DESCRIPTION = "description"
    TASKS = "tasks"
    TASK_TYPE = "task_type"
    # What `get_automation_schema` answers: one task type, and every condition.
    TASK = "task"
    CONDITIONS = "conditions"
    AUTOMATIONS = "automations"
    # The status patch names the ACTION, not the status it leaves behind:
    # "suspend" sets the status "suspended".
    SUSPEND = "suspend"
    RESTORE = "restore"
    AUTOMATION = "automation"


class DashboardFields:
    """The bodies the dashboard routes accept, and what a dashboard reports."""

    ID = "id"
    DASHBOARDS = "dashboards"
    TITLE = "title"
    TAGS = "tags"
    BOARD = "dashboard"
    MAMMOTH = "mammoth"
    MESSAGE = "message"
    URL = "url"
    STATUS = "status"
    READY = "ready"
    BUILDING = "building"
    ENGINE = "engine"
    # Whether a published version exists, as the route names it and as this
    # server reports it. The route's name reads as a past tense and is not one.
    WAS_PUBLISHED = "was_published"
    PUBLISHED = "published"
    # The two links a dashboard has: the one its audience opens, and the one
    # its owner builds it in.
    SHARE_URL = "share_url"
    EDITOR_URL = "editor_url"
    # What a finished AI build reports that a model can use. The rest is its
    # whole canvas and internal version numbers. `url` is the share link's last
    # segment on its own, so the links are built from it rather than reported.
    GENERATED = (ID, TITLE, MESSAGE, TAGS)
    # A dashboard built on the older engine answers with its whole rendered page
    # and the messages that built it. A model can act on neither, and together
    # they dwarf every other field.
    TOO_LARGE_TO_READ = frozenset({"html", "messages"})


class ApiFields:
    """the API's `fields` query parameter and its presets."""

    FIELDS = "fields"
    MINIMAL = "__min"
    STANDARD = "__standard"
    FULL = "__full"


# Whoever the token was issued to: Mammoth does not say, and nothing here asks.
TOKEN_CLIENT = "mammoth"


class TokenClaims:
    """What a caller's access token carries, so a tool call can act as them."""

    # The one workspace the caller's token belongs to.
    WORKSPACE_ID = "workspace_id"
    # The one project the user picked when they connected, or None when they
    # picked "All projects". Mammoth refuses the token on any other project.
    PROJECT_ID = "project_id"


class PipelineFields:
    """A view's pipeline and the requests that change it."""

    PIPELINE = "pipeline"
    STEPS = "steps"
    TASKS = "tasks"
    DRAFT_MODE = "draft_mode"
    NOT_DRAFTING = "off"
    DRAFT_OPERATION = "draft_operation"
    DRAFT_ON = "enter"
    DRAFT_OFF = "exit"
    DRAFT_SUBMIT = "submit"
    DRAFT_DISCARD = "discard"
    PATCHES = "patches"
    RUN = {"op": "command", "path": "run", "value": None}


class PageFields:
    """A page of rows, as the API answers it and as a tool hands it on."""

    NEXT = "next"
    LIMIT = "limit"
    DATA = "data"
    PAGING = "paging"
    OFFSET = "offset"
    COUNT = "count"
    TOTAL = "total"
    NEXT_OFFSET = "next_offset"


class ViewShape:
    """The fields of a view that a model reads; the API sends many more."""

    KEPT = ("id", "name", "ds_id", "status", "row_count", "column_count", "updated_at")
    METADATA = "metadata"
    COLUMN_KEPT = ("display_name", "internal_name", "type", "format", "min", "max")
    NUMERIC = "NUMERIC"
