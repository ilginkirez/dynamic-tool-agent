"""Database Query — simulates running SQL queries against a relational database."""

from __future__ import annotations

import random

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="database_query",
    display_name="Database Query",
    description=(
        "Executes simulated SQL queries against a mock relational database and "
        "returns structured result sets. Supports SELECT, INSERT, UPDATE, and "
        "DELETE operations. Useful for data retrieval, reporting, analytics, and "
        "ad-hoc data exploration without direct database access."
    ),
    category="data",
    tags=["database", "veritabanı", "sql", "query", "data", "sorgu", "analytics"],
    parameters=[
        ToolParameter(name="query", type="string", description="SQL query to execute"),
        ToolParameter(name="database", type="string", description="Target database name", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "SELECT * FROM users WHERE country = 'TR' LIMIT 10",
        "Veritabanından son 30 günün satış toplamını getir.",
        "Count the number of active subscriptions grouped by plan type.",
    ],
    callable_template="result = database_query(query='{query}')",
)

_MOCK_USERS = [
    {"id": 1, "name": "Ahmet Yılmaz", "email": "ahmet@example.com", "country": "TR"},
    {"id": 2, "name": "Emily Chen", "email": "emily@example.com", "country": "US"},
    {"id": 3, "name": "Carlos López", "email": "carlos@example.com", "country": "ES"},
    {"id": 4, "name": "Ayşe Kaya", "email": "ayse@example.com", "country": "TR"},
    {"id": 5, "name": "Takeshi Tanaka", "email": "takeshi@example.com", "country": "JP"},
]

_MOCK_SALES = [
    {"product": "Widget A", "amount": 129.99, "quantity": 42},
    {"product": "Widget B", "amount": 249.50, "quantity": 18},
    {"product": "Service Plan", "amount": 999.00, "quantity": 7},
]


def execute(params: dict) -> dict:
    """Return mock query results based on query content."""
    query = params.get("query", "").strip().upper()
    database = params.get("database", "main_db")

    if query.startswith("SELECT"):
        if "USER" in query:
            rows = _MOCK_USERS
        elif "SALE" in query or "ORDER" in query:
            rows = _MOCK_SALES
        else:
            rows = [{"column1": f"value_{i}", "column2": random.randint(1, 100)} for i in range(5)]

        return {
            "database": database,
            "query": params.get("query", ""),
            "rows_returned": len(rows),
            "rows": rows,
            "success": True,
        }

    if query.startswith(("INSERT", "UPDATE", "DELETE")):
        affected = random.randint(1, 10)
        return {
            "database": database,
            "query": params.get("query", ""),
            "rows_affected": affected,
            "success": True,
        }

    return {"error": "Unsupported query type", "success": False}
