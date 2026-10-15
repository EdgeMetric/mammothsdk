"""The one MCP Apps extension every page drawn in the chat registers on.

A server takes each extension once, so the uploader and the connect button
share it.
"""

from mcp.server.apps import Apps

chat_apps = Apps()
