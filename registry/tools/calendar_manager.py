"""Calendar Manager — manages events, reminders, and scheduling."""

from __future__ import annotations

from datetime import datetime, timedelta

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="calendar_manager",
    display_name="Calendar Manager",
    description=(
        "Manages calendar events including creation, listing, and conflict detection. "
        "Supports scheduling meetings, setting reminders, and checking availability "
        "for a given date range. Useful for personal productivity, team coordination, "
        "and automated scheduling workflows."
    ),
    category="utility",
    tags=["calendar", "takvim", "schedule", "event", "reminder", "hatırlatıcı", "meeting"],
    parameters=[
        ToolParameter(name="action", type="string", description="Action: 'create', 'list', or 'check_availability'"),
        ToolParameter(name="title", type="string", description="Event title", required=False),
        ToolParameter(name="date", type="string", description="Date in YYYY-MM-DD format", required=False),
        ToolParameter(name="time", type="string", description="Time in HH:MM format", required=False),
        ToolParameter(name="duration_minutes", type="number", description="Duration in minutes", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "Yarın saat 14:00'te 'Takım Toplantısı' etkinliği oluştur.",
        "List all events for next Monday.",
        "Check if I'm free on 2026-03-25 between 10:00 and 12:00.",
    ],
    callable_template="result = calendar_manager(action='{action}', title='{title}', date='{date}', time='{time}')",
)

_MOCK_EVENTS = [
    {"title": "Standup Meeting", "date": "2026-03-24", "time": "09:00", "duration_minutes": 15},
    {"title": "Sprint Planning", "date": "2026-03-24", "time": "14:00", "duration_minutes": 60},
    {"title": "Lunch with Client", "date": "2026-03-25", "time": "12:30", "duration_minutes": 90},
]


def execute(params: dict) -> dict:
    """Perform a calendar action with mock data."""
    action = params.get("action", "list")

    if action == "create":
        title = params.get("title", "Untitled Event")
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        time_ = params.get("time", "09:00")
        duration = int(params.get("duration_minutes", 30))
        new_event = {"title": title, "date": date, "time": time_, "duration_minutes": duration}
        return {"action": "created", "event": new_event, "success": True}

    if action == "check_availability":
        date = params.get("date", "")
        time_ = params.get("time", "09:00")
        conflicts = [e for e in _MOCK_EVENTS if e["date"] == date and e["time"] == time_]
        return {
            "date": date,
            "time": time_,
            "available": len(conflicts) == 0,
            "conflicts": conflicts,
        }

    # default: list
    target_date = params.get("date")
    events = _MOCK_EVENTS if not target_date else [e for e in _MOCK_EVENTS if e["date"] == target_date]
    return {"action": "list", "events": events, "total": len(events)}
