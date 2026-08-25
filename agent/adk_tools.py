"""
agent/adk_tools.py — Exposes Liya's existing action modules to Google ADK
as FunctionTools.

Every action in actions/ shares the same legacy call shape:
    action(parameters: dict, response=None, player=None, session_memory=None) -> str

ADK's FunctionTool instead derives its function-calling schema from a
Python function's own type-annotated parameters and docstring. Rather than
rewrite every action module's internals, each wrapper below re-packs its
explicit, typed arguments into that legacy `parameters` dict and calls
straight into the existing, already-tested action function. This means
ADK and the legacy planner/executor both execute the exact same code path
— no logic is duplicated or forked.
"""
from __future__ import annotations

from google.adk.tools import FunctionTool

from agent.tool_result import is_tool_result
from actions.web_search import web_search as _web_search
from actions.file_controller import file_controller as _file_controller
from actions.open_app import open_app as _open_app
from actions.reminder import reminder as _reminder
from actions.weather_report import weather_action as _weather_action


def _text(r) -> str:
    """Unwrap a structured ToolResult dict into plain text for ADK, which
    expects each FunctionTool to return a string. Legacy string returns
    pass through unchanged."""
    return r["message"] if is_tool_result(r) else r


def web_search_tool(query: str, mode: str = "search") -> str:
    """Search the web for current information, or compare items.

    Args:
        query: A clear, focused search query. Required unless using
            compare mode with `items` handled elsewhere.
        mode: Either "search" for a normal web lookup or "compare".

    Returns:
        A text summary of the search results.
    """
    return _text(_web_search({"query": query, "mode": mode}))


def file_controller_tool(action: str, path: str = "desktop", name: str = "",
                          content: str = "") -> str:
    """Read, write, list, or manage files on the local filesystem.

    Args:
        action: One of "list", "create_file", "create_folder", "delete",
            "move", "copy", "rename", "read", "write", "find",
            "largest", "disk_usage".
        path: Target directory. Use "desktop" for the Desktop folder.
        name: Target filename (for create_file/read/write/delete/etc).
        content: File content to write (for create_file/write actions).

    Returns:
        A text description of the result.
    """
    return _text(_file_controller({
        "action": action, "path": path, "name": name, "content": content,
    }))


def open_app_tool(app_name: str) -> str:
    """Launch a desktop application by name.

    Args:
        app_name: Name of the application to open, e.g. "notepad", "chrome".

    Returns:
        A text confirmation or error message.
    """
    return _text(_open_app({"app_name": app_name}))


def reminder_tool(date: str, time: str, message: str = "Reminder") -> str:
    """Schedule a one-time reminder notification.

    Args:
        date: Date in YYYY-MM-DD format.
        time: Time in 24-hour HH:MM format.
        message: The reminder text to show.

    Returns:
        A text confirmation that the reminder was scheduled.
    """
    return _reminder({"date": date, "time": time, "message": message})


def weather_report_tool(city: str, time: str = "today") -> str:
    """Get a weather report for a city.

    Args:
        city: City name to look up.
        time: "today" or a relative day description.

    Returns:
        A text weather summary.
    """
    return _weather_action({"city": city, "time": time})


def get_liya_adk_tools() -> list[FunctionTool]:
    """Returns the set of Liya actions currently exposed to ADK agents."""
    return [
        FunctionTool(web_search_tool),
        FunctionTool(file_controller_tool),
        FunctionTool(open_app_tool),
        FunctionTool(reminder_tool),
        FunctionTool(weather_report_tool),
    ]
