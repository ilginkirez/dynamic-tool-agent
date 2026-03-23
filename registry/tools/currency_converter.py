"""Currency Converter — converts between fiat currencies and cryptocurrencies."""

from __future__ import annotations

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="currency_converter",
    display_name="Currency Converter",
    description=(
        "Converts monetary amounts between fiat currencies (USD, EUR, TRY, GBP, JPY) "
        "and popular cryptocurrencies (BTC, ETH). Uses simulated exchange rates to "
        "provide quick conversions for financial planning, travel budgets, and "
        "cryptocurrency portfolio tracking."
    ),
    category="data",
    tags=["currency", "döviz", "exchange", "crypto", "finance", "money", "para"],
    parameters=[
        ToolParameter(name="amount", type="number", description="Amount to convert"),
        ToolParameter(name="from_currency", type="string", description="Source currency code (e.g. USD, BTC)"),
        ToolParameter(name="to_currency", type="string", description="Target currency code (e.g. TRY, ETH)"),
    ],
    version=ToolVersion(major=1, minor=1, patch=0),
    examples=[
        "100 USD kaç TRY yapar?",
        "Convert 0.5 BTC to EUR.",
        "1500 Euro'yu Japon Yeni'ne çevir.",
    ],
    callable_template="result = currency_converter(amount={amount}, from_currency='{from_currency}', to_currency='{to_currency}')",
)

# Simulated rates against USD
_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "TRY": 38.45,
    "GBP": 0.79,
    "JPY": 149.50,
    "BTC": 0.0000115,
    "ETH": 0.000285,
}


def execute(params: dict) -> dict:
    """Convert amount between two currencies using mock rates."""
    amount = float(params.get("amount", 1))
    from_cur = params.get("from_currency", "USD").upper()
    to_cur = params.get("to_currency", "TRY").upper()

    from_rate = _RATES_TO_USD.get(from_cur)
    to_rate = _RATES_TO_USD.get(to_cur)

    if from_rate is None or to_rate is None:
        unknown = from_cur if from_rate is None else to_cur
        return {"error": f"Unknown currency: {unknown}", "success": False}

    usd_amount = amount / from_rate if from_cur != "USD" else amount
    converted = usd_amount * to_rate if to_cur != "USD" else usd_amount

    return {
        "from_currency": from_cur,
        "to_currency": to_cur,
        "original_amount": amount,
        "converted_amount": round(converted, 6),
        "rate": round(to_rate / from_rate, 6),
        "success": True,
    }
