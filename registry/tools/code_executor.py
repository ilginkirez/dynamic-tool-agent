"""Code Executor — evaluates simple Python math expressions safely."""

from __future__ import annotations

import math

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="code_executor",
    display_name="Code Executor",
    description=(
        "Executes simple Python mathematical expressions and returns the computed "
        "result. Supports arithmetic operators, power, modulo, and common math "
        "functions like sqrt, sin, cos, log. Ideal for quick calculations, unit "
        "conversions, and formula evaluations without needing a full runtime."
    ),
    category="computation",
    tags=["math", "hesaplama", "calculator", "python", "eval", "computation"],
    parameters=[
        ToolParameter(name="expression", type="string", description="Python math expression to evaluate, e.g. '2**10 + math.sqrt(49)'"),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "Calculate 2 to the power of 16.",
        "math.sqrt(144) + 3 * 7 işlemini hesapla.",
        "What is sin(pi/4) rounded to 4 decimal places?",
    ],
    callable_template="result = code_executor(expression='{expression}')",
)

_SAFE_NAMES = {
    "math": math,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "pi": math.pi,
    "e": math.e,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
}


def execute(params: dict) -> dict:
    """Evaluate a math expression using a restricted set of builtins."""
    expression = params.get("expression", "0")

    try:
        result = eval(expression, {"__builtins__": {}}, _SAFE_NAMES)  # noqa: S307
        return {"expression": expression, "result": result, "success": True}
    except Exception as exc:
        return {"expression": expression, "error": str(exc), "success": False}
