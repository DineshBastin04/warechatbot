import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatContext:
    """
    Who is asking, and in which workspace. This replaces the Flask-session
    reads the chat pipeline used to do. Web requests pass None and keep using
    the session; Teams (and any other channel with no HTTP session) passes one
    of these instead.

    workspace_name is the ChromaDB collection identifier the retrieval layer
    uses. workspace_id is the workspace UUID that config, writes and billing
    are keyed on. They are two identifiers for the same workspace.
    """
    workspace_id: str
    workspace_name: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: str = "user"
    channel: str = "web"                 # "web" | "teams"
    teams_aad_id: Optional[str] = None
    email: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "superadmin")


def friendly_sql_error(error_message: str) -> str:
    """Turns a pyodbc/SQL Server error into a message an end user can act on,
    surfacing the real database error rather than a generic failure."""
    column_match = re.findall(r"Invalid column name '([^']+)'", error_message)
    table_match = re.findall(r"Invalid object name '([^']+)'", error_message)
    if column_match:
        return f"The query could not be executed because the column '{column_match[0]}' does not exist. Please check your database schema."
    if table_match:
        return f"The query could not be executed because the table '{table_match[0]}' does not exist. Please verify the table name."
    # pyodbc wraps SQL Server errors as "[SQL Server]<message> (<code>) (SQLExecDirectW)"
    sql_server_match = re.search(r"\[SQL Server\](.+?)(?:\s*\(\d+\)\s*\(SQL\w*\)|$)", error_message)
    detail = sql_server_match.group(1).strip() if sql_server_match else error_message[:300]
    return f"The query could not be executed: {detail}"
