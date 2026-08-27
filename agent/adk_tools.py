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

Governance parity: the legacy path enforces agent/governance.py's
allow/confirm/deny policy inside agent/executor.py before every tool call.
Earlier versions of this file called actions directly and skipped that
check entirely, so a `confirm`-tier tool (e.g. send_message) could run
through the ADK agent with no gate at all — a real hole, not a cosmetic
one, since POST /task/adk is the flagship "we used Google's framework"
path. _governed() below closes that gap: every wrapper runs through the
same check_tool_permission() the legacy executor uses, so `deny`d tools
raise, and `confirm`-tier tools (send_message, computer control, etc.)
are blocked under headless/cloud unless auto_approve was set on the
request — same rule, same policy table, both execution paths.
"""
from __future__ import annotations

import os

from google.adk.tools import FunctionTool

from agent.tool_result import is_tool_result
from agent.governance import check_tool_permission, SecurityException
from actions.web_search import web_search as _web_search
from actions.file_controller import file_controller as _file_controller
from actions.open_app import open_app as _open_app
from actions.reminder import reminder as _reminder
from actions.weather_report import weather_action as _weather_action
from actions.flight_finder import flight_finder as _flight_finder
from actions.file_processor import file_processor as _file_processor
from actions.send_message import send_message as _send_message
from memory.memory_manager import remember as _remember, forget as _forget

# Set on the request path (agent/adk_runner.py) so governance can honor the
# same `auto_approve` flag the legacy /task endpoint already respects,
# without threading an extra parameter through every FunctionTool's
# ADK-derived call signature.
_AUTO_APPROVE = False


def set_auto_approve(value: bool) -> None:
    """Called once per run by agent/adk_runner.py before invoking the agent."""
    global _AUTO_APPROVE
    _AUTO_APPROVE = value


def _text(r) -> str:
    """Unwrap a structured ToolResult dict into plain text for ADK, which
    expects each FunctionTool to return a string. Legacy string returns
    pass through unchanged."""
    return r["message"] if is_tool_result(r) else r


def _governed(tool_name: str, params: dict, call):
    """Runs the same allow/confirm/deny check the legacy executor runs,
    then calls through to the real action. Mirrors agent/executor.py's
    governance block so both execution paths enforce one policy table."""
    is_headless = os.environ.get("LIYA_HEADLESS", "false").lower() == "true"
    try:
        check_tool_permission(
            tool=tool_name,
            parameters=params,
            has_ui_consent=_AUTO_APPROVE,
            is_headless=is_headless,
        )
    except SecurityException as exc:
        # Surfaced back through ADK as the tool's return value (a string),
        # not an unhandled exception — the agent sees the denial as a
        # normal tool result and can report it to the user, same as any
        # other tool failure.
        return f"[blocked by governance] {exc}"
    return _text(call())


def web_search_tool(query: str, mode: str = "search") -> str:
    """Search the web for current information, or compare items.

    Args:
        query: A clear, focused search query. Required unless using
            compare mode with `items` handled elsewhere.
        mode: Either "search" for a normal web lookup or "compare".

    Returns:
        A text summary of the search results.
    """
    params = {"query": query, "mode": mode}
    return _governed("web_search", params, lambda: _web_search(params))


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
    params = {"action": action, "path": path, "name": name, "content": content}
    return _governed("file_controller", params, lambda: _file_controller(params))


def open_app_tool(app_name: str) -> str:
    """Launch a desktop application by name.

    Args:
        app_name: Name of the application to open, e.g. "notepad", "chrome".

    Returns:
        A text confirmation or error message.
    """
    params = {"app_name": app_name}
    return _governed("open_app", params, lambda: _open_app(params))


def reminder_tool(date: str, time: str, message: str = "Reminder") -> str:
    """Schedule a one-time reminder notification.

    Args:
        date: Date in YYYY-MM-DD format.
        time: Time in 24-hour HH:MM format.
        message: The reminder text to show.

    Returns:
        A text confirmation that the reminder was scheduled.
    """
    params = {"date": date, "time": time, "message": message}
    return _governed("reminder", params, lambda: _reminder(params))


def weather_report_tool(city: str, time: str = "today") -> str:
    """Get a weather report for a city.

    Args:
        city: City name to look up.
        time: "today" or a relative day description.

    Returns:
        A text weather summary.
    """
    params = {"city": city, "time": time}
    return _governed("weather_report", params, lambda: _weather_action(params))


def flight_finder_tool(origin: str, destination: str, date: str) -> str:
    """Search for flights between two cities on a given date.

    Args:
        origin: Departure city or airport.
        destination: Arrival city or airport.
        date: Travel date, e.g. "2026-09-14" or "tomorrow".

    Returns:
        A text summary of matching flights.
    """
    params = {"origin": origin, "destination": destination, "date": date}
    return _governed("flight_finder", params, lambda: _flight_finder(params))


def file_processor_tool(path: str, instruction: str = "summarize") -> str:
    """Analyze or process an existing file (document, image, video, etc).

    Args:
        path: Full path to the file to process.
        instruction: What to do with it, e.g. "summarize", "describe".

    Returns:
        A text result of the analysis.
    """
    params = {"path": path, "instruction": instruction}
    return _governed("file_processor", params, lambda: _file_processor(params))


def send_message_tool(receiver: str, message_text: str, platform: str = "whatsapp") -> str:
    """Send a message to someone via a messaging platform.

    This is a `confirm`-tier tool under agent/governance.py: in headless
    or cloud contexts it is blocked unless the request set
    auto_approve=true, exactly like the legacy /task path. Included
    specifically to make governance enforcement visible on the ADK path
    too, not just the legacy planner path.

    Args:
        receiver: Name or handle of the message recipient.
        message_text: The message to send.
        platform: One of "whatsapp", "telegram", "signal", "discord",
            "instagram", "messenger". Defaults to "whatsapp".

    Returns:
        A text confirmation, or a governance-block message if denied.
    """
    params = {"receiver": receiver, "message_text": message_text, "platform": platform}
    return _governed("send_message", params, lambda: _send_message(params))


def memory_tool(action: str, key: str, value: str = "", category: str = "notes") -> str:
    """Remember or forget a durable fact about the user, persisted across
    sessions (memory/memory_manager.py — Firestore, or local JSON fallback).

    Unlike the other tools here, this isn't governed by
    agent/governance.py's allow/confirm/deny table: it only ever touches
    the agent's own memory store, never an external system, app, or
    person, so there's nothing for that policy to gate.

    Args:
        action: Either "remember" (store `value` under `key`) or "forget"
            (delete `key`).
        key: Short identifier for the fact, e.g. "favorite_editor".
        value: The fact to store. Required when action is "remember",
            ignored for "forget".
        category: One of "identity", "preferences", "projects",
            "relationships", "wishes", "notes". Defaults to "notes".

    Returns:
        A text confirmation of what was remembered or forgotten.
    """
    if action == "forget":
        return _forget(key, category)
    return _remember(key, value, category)


def get_liya_adk_tools() -> list[FunctionTool]:
    """Returns the set of Liya actions currently exposed to ADK agents.

    9 of the repo's 16 actions are wrapped here today. memory_tool is new:
    it's the one addition that isn't a re-wrap of an existing actions/*.py
    module — it gives the ADK path the same durable, cross-session memory
    the legacy planner path already had via _load_memory_context() in
    agent/executor.py, so the agent can persist a user preference or fact
    mid-conversation instead of only reading memory in at plan time.

    The remaining 7 (browser_control, computer_settings, computer_control,
    desktop_control, screen_processor, youtube_video, code_helper,
    dev_agent) follow the identical wrapper pattern above and are the
    natural next additions — left out of this pass because they carry real
    desktop/UI dependencies (Playwright, pyautogui) that don't belong in a
    headless Cloud Run container, unlike the ones below, which all run
    cleanly server-side.
    """
    return [
        FunctionTool(web_search_tool),
        FunctionTool(file_controller_tool),
        FunctionTool(open_app_tool),
        FunctionTool(reminder_tool),
        FunctionTool(weather_report_tool),
        FunctionTool(flight_finder_tool),
        FunctionTool(file_processor_tool),
        FunctionTool(send_message_tool),
        FunctionTool(memory_tool),
    ]
