"""Weather Service — retrieves current and forecast weather data for a location."""

from __future__ import annotations

import random

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="weather_service",
    display_name="Weather Service",
    description=(
        "Retrieves real-time weather information including temperature, humidity, "
        "wind speed, and general conditions for any city or geographic coordinate. "
        "Supports both current observations and multi-day forecasts so users can "
        "plan ahead for travel, events, or daily activities."
    ),
    category="data",
    tags=["weather", "hava durumu", "forecast", "temperature", "sıcaklık", "meteorology"],
    parameters=[
        ToolParameter(name="location", type="string", description="City name or coordinates (lat,lon)"),
        ToolParameter(name="units", type="string", description="Temperature unit: 'celsius' or 'fahrenheit'", required=False),
        ToolParameter(name="days", type="number", description="Forecast days (1-7)", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "İstanbul'da yarın hava nasıl olacak?",
        "Show me the 5-day forecast for Tokyo in Celsius.",
        "Ankara'nın şu anki sıcaklığını öğren.",
    ],
    callable_template="result = weather_service(location='{location}')",
)

_CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Snowy", "Windy", "Foggy"]


def execute(params: dict) -> dict:
    """Return mock weather data that varies by parameters."""
    location = params.get("location", "Istanbul")
    units = params.get("units", "celsius")
    days = int(params.get("days", 1))

    unit_symbol = "°C" if units == "celsius" else "°F"
    base_temp = random.randint(5, 35) if units == "celsius" else random.randint(40, 95)

    forecast = []
    for day in range(days):
        temp = base_temp + random.randint(-3, 3)
        forecast.append(
            {
                "day": day + 1,
                "temperature": f"{temp}{unit_symbol}",
                "humidity": f"{random.randint(30, 90)}%",
                "wind_speed": f"{random.randint(5, 40)} km/h",
                "condition": random.choice(_CONDITIONS),
            }
        )

    return {
        "location": location,
        "units": units,
        "forecast": forecast,
    }
