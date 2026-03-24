"""Execution Logger for tracking tool usage, latency, and results."""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Assumes this will only be imported where AgentState is available, 
# but to avoid circular imports, we just use typing.Any for state.


class ToolExecutionLog(BaseModel):
    """Log record for a single tool execution attempt."""

    trace_id: str
    timestamp: str
    user_input: str
    search_query: str
    found_tool_names: list[str]
    selected_tool: str | None
    tool_params: dict
    tool_result: Any | None
    success: bool
    error: str | None
    latency_ms: float


class ExecutionLogger:
    """Manages appending execution logs to JSONL and printing Rich summaries."""

    def __init__(self, log_path: str = "logs/executions.jsonl") -> None:
        self.log_file = Path(log_path)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        self._active_traces: dict[str, float] = {}  # trace_id -> start_time_perf_counter

    def log(self, data: ToolExecutionLog) -> None:
        """Append a JSON line to the log file."""
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(data.model_dump_json() + "\n")

    def start_trace(self, user_input: str) -> str:
        """Create a new trace, record start time, and return the trace_id."""
        trace_id = str(uuid.uuid4())
        self._active_traces[trace_id] = time.perf_counter()
        return trace_id

    def finish_trace(self, trace_id: str, state: dict, tool_manager: Any = None) -> None:
        """
        Finalize a trace, compute latency, construct ToolExecutionLog,
        print a rich summary, and write to disk. Optionally updates ToolManager stats.
        """
        start_time = self._active_traces.pop(trace_id, time.perf_counter())
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        success = state.get("error") is None

        # Extract names from found tools list
        found_tools = state.get("found_tools", [])
        found_tool_names = [getattr(t, "name", str(t)) for t in found_tools]

        selected_tool_obj = state.get("selected_tool")
        selected_tool_name = getattr(selected_tool_obj, "name", None) if selected_tool_obj else None

        log_record = ToolExecutionLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_input=state.get("user_input", ""),
            search_query=state.get("search_query", ""),
            found_tool_names=found_tool_names,
            selected_tool=selected_tool_name,
            tool_params=state.get("tool_params", {}),
            tool_result=state.get("tool_result"),
            success=success,
            error=state.get("error"),
            latency_ms=latency_ms,
        )

        # 1. Write to JSONL
        self.log(log_record)

        # 2. Update ToolManager stats if provided
        if tool_manager and selected_tool_name:
            tool_manager.update_stats(
                tool_name=selected_tool_name,
                success=success
            )

        # 3. Print Rich terminal output
        icon = "[bold green]✅[/bold green]" if success else "[bold red]❌[/bold red]"
        tool_display = selected_tool_name or "NO_TOOL"
        
        status_text = Text.from_markup(
            f"{icon} [bold cyan]Tool:[/bold cyan] {tool_display}  "
            f"[bold magenta]Latency:[/bold magenta] {latency_ms:.2f}ms"
        )
        
        if not success:
            error_msg = str(state.get("error", "Unknown Error"))
            status_text.append(f"\n[bold red]Error:[/bold red] {error_msg}")

        panel = Panel(
            status_text,
            title=f"Execution Trace: [dim]{trace_id[:8]}[/dim]",
            border_style="green" if success else "red",
            expand=False,
        )
        self.console.print(panel)
