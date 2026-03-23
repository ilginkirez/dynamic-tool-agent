"""Translation Service — translates text between languages."""

from __future__ import annotations

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="translation_service",
    display_name="Translation Service",
    description=(
        "Translates given text from one language to another. Supports major world "
        "languages including English, Turkish, German, French, Spanish, Japanese, "
        "and Chinese. Detects the source language automatically when not specified. "
        "Ideal for multilingual communication, content localization, and language learning."
    ),
    category="utility",
    tags=["translate", "çeviri", "language", "dil", "localization", "multilingual"],
    parameters=[
        ToolParameter(name="text", type="string", description="Text to translate"),
        ToolParameter(name="source_language", type="string", description="Source language code (e.g. 'en', 'tr')", required=False),
        ToolParameter(name="target_language", type="string", description="Target language code (e.g. 'tr', 'de')"),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "'Hello, how are you?' cümlesini Türkçe'ye çevir.",
        "Translate 'Günaydın dünya' to German.",
        "Convert this Japanese text to English.",
    ],
    callable_template="result = translation_service(text='{text}', target_language='{target_language}')",
)

_MOCK_TRANSLATIONS: dict[tuple[str, str], dict[str, str]] = {
    ("en", "tr"): {
        "hello": "merhaba",
        "goodbye": "hoşça kal",
        "thank you": "teşekkür ederim",
    },
    ("tr", "en"): {
        "merhaba": "hello",
        "hoşça kal": "goodbye",
        "teşekkür ederim": "thank you",
    },
    ("en", "de"): {
        "hello": "hallo",
        "goodbye": "auf wiedersehen",
        "thank you": "danke schön",
    },
}


def execute(params: dict) -> dict:
    """Return a mock translation result."""
    text = params.get("text", "")
    source = params.get("source_language", "auto")
    target = params.get("target_language", "en")

    # Attempt to find a mock translation
    text_lower = text.lower().strip()
    translated = None

    if source == "auto":
        for (src, tgt), mappings in _MOCK_TRANSLATIONS.items():
            if tgt == target and text_lower in mappings:
                translated = mappings[text_lower]
                source = src
                break
    else:
        pair = _MOCK_TRANSLATIONS.get((source, target), {})
        translated = pair.get(text_lower)

    if translated is None:
        translated = f"[{target.upper()}] {text}"

    return {
        "original_text": text,
        "translated_text": translated,
        "source_language": source,
        "target_language": target,
        "confidence": 0.95,
        "success": True,
    }
