"""Timer & Alarm — manages countdown timers and alarms."""

from __future__ import annotations

from datetime import datetime, timedelta

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="timer_alarm",
    display_name="Timer & Alarm",
    description=(
        "Creates and manages countdown timers and alarms. Supports setting timers "
        "for a specific duration (minutes/seconds) or alarms for an exact time. "
        "Can list active timers, cancel them, and provides estimated completion "
        "times. Perfect for productivity tracking, cooking, meetings, and reminders."
    ),
    category="utility",
    tags=["timer", "zamanlayıcı", "alarm", "countdown", "reminder", "pomodoro", "süre"],
    parameters=[
        ToolParameter(name="action", type="string", description="Action: 'set', 'list', or 'cancel'"),
        ToolParameter(name="label", type="string", description="Timer label", required=False),
        ToolParameter(name="duration_seconds", type="number", description="Duration in seconds", required=False),
        ToolParameter(name="alarm_time", type="string", description="Alarm time in HH:MM format", required=False),
        ToolParameter(name="timer_id", type="string", description="Timer ID for cancellation", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "25 dakikalık bir Pomodoro zamanlayıcısı kur.",
        "Set an alarm for 17:30 labeled 'End of Work'.",
        "Aktif zamanlayıcıları listele.",
    ],
    callable_template="result = timer_alarm(action='{action}', label='{label}', duration_seconds={duration_seconds})",
)

_ACTIVE_TIMERS: list[dict] = [
    {"id": "tmr_001", "label": "Tea Brewing", "remaining_seconds": 180, "status": "active"},
    {"id": "tmr_002", "label": "Pomodoro Session", "remaining_seconds": 1200, "status": "active"},
]


def execute(params: dict) -> dict:
    """Manage mock timers and alarms."""
    action = params.get("action", "list")

    if action == "set":
        label = params.get("label", "Timer")
        duration = int(params.get("duration_seconds", 300))
        alarm_time = params.get("alarm_time")

        now = datetime.now()
        if alarm_time:
            hour, minute = map(int, alarm_time.split(":"))
            target = now.replace(hour=hour, minute=minute, second=0)
            if target < now:
                target += timedelta(days=1)
            duration = int((target - now).total_seconds())

        timer_id = f"tmr_{len(_ACTIVE_TIMERS) + 1:03d}"
        new_timer = {
            "id": timer_id,
            "label": label,
            "duration_seconds": duration,
            "fires_at": (now + timedelta(seconds=duration)).isoformat(),
            "status": "active",
        }
        return {"action": "set", "timer": new_timer, "success": True}

    if action == "cancel":
        timer_id = params.get("timer_id", "")
        found = any(t["id"] == timer_id for t in _ACTIVE_TIMERS)
        return {"action": "cancel", "timer_id": timer_id, "found": found, "success": found}

    # default: list
    return {"action": "list", "timers": _ACTIVE_TIMERS, "total": len(_ACTIVE_TIMERS)}
