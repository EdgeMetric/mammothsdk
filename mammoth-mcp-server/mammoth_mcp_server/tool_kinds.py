"""What each tool does to the user's data, as MCP annotations a client reads.

A client treats a tool with no annotations as one that may do anything, so each
tool says which kind it is. A client may run a read-only tool freely and ask
the user before a destructive one.
"""

from mcp.types import ToolAnnotations

# Reads, and changes nothing.
READS = ToolAnnotations(read_only_hint=True)
# Adds or changes something that can be put back.
CHANGES = ToolAnnotations(read_only_hint=False, destructive_hint=False)
# Deletes, sends rows out, publishes, sets something to run, or throws data away.
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True)
