"""What each tool does to the user's data, as MCP annotations a client reads.

A client treats a tool with no annotations as one that may do anything, so each
tool says which kind it is. A client may run a read-only tool freely and ask
the user before a destructive one.

Every hint is set, not left to a client's default. "Outside" means the tool can
reach a system beyond the user's Mammoth workspace: a database, a destination an
export or automation sends to, or anyone a published dashboard is open to. A
view's exports run when the view runs, so a tool that runs a view counts.
"""

from mcp.types import ToolAnnotations

# Reads, and changes nothing.
READS = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
READS_OUTSIDE = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=True)
# Adds or changes something that can be put back.
CHANGES = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
CHANGES_OUTSIDE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, open_world_hint=True
)
# Deletes, sends rows out, publishes, sets something to run, or throws data away.
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False)
DESTRUCTIVE_OUTSIDE = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, open_world_hint=True
)
