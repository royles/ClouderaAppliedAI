"""UI locale hints for assistant responses."""

from __future__ import annotations

HEBREW_UI_INSTRUCTION = """
Language (required): The user's application UI is set to Hebrew (he-IL).
Write the JSON "answer" field entirely in Modern Hebrew with a professional Israeli insurance tone.
Keep JSON property names, action_ids, segment keys, and API/tool identifiers in English as required.
Do not answer in English except for untranslatable proper nouns, codes, or numbers from live data.
If the user writes in Hebrew, match their language. If they write in English but UI is Hebrew, still respond in Hebrew.
"""

ENGLISH_UI_INSTRUCTION = """
Language: The user's application UI is set to English. Write the JSON "answer" field in English unless the user clearly asks for another language.
"""


def normalize_ui_locale(locale: str | None) -> str:
    raw = (locale or "").strip().lower()
    if raw.startswith("he"):
        return "he"
    return "en"


def bedrock_language_instruction(locale: str | None) -> str:
    return HEBREW_UI_INSTRUCTION if normalize_ui_locale(locale) == "he" else ENGLISH_UI_INSTRUCTION
