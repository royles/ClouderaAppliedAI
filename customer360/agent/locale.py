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


INSIGHT_HEBREW = """
Language (required): The application UI is Hebrew (he-IL).
Write every JSON string value (preamble, summary, guidance, each suggested_actions entry,
experience_note) in Modern Hebrew with a professional Israeli insurance tone.
Keep JSON keys and primary_focus values ("upsell" / "retention") in English.
If live data is in English, you may keep proper nouns and codes as-is inside Hebrew prose.
"""

INSIGHT_ENGLISH = """
Language: The application UI is English. Write all JSON string values in English unless the
user data clearly requires another language for customer-facing phrases.
"""

DRAFT_HEBREW = """
Language (required): The application UI is Hebrew (he-IL).
Write subject and body in Modern Hebrew (professional Customer Care tone). Keep JSON keys and
channel value in English. SMS may include the portal URL as given in the rules.
"""

DRAFT_ENGLISH = """
Language: The application UI is English. Write subject and body in English unless the customer
context clearly requires another language.
"""


def insight_language_instruction(locale: str | None) -> str:
    return INSIGHT_HEBREW if normalize_ui_locale(locale) == "he" else INSIGHT_ENGLISH


def draft_language_instruction(locale: str | None) -> str:
    return DRAFT_HEBREW if normalize_ui_locale(locale) == "he" else DRAFT_ENGLISH
