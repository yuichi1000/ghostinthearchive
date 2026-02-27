"""ISO 639-1 → 英語言語名マッピング。

Aggregator, Scholar, Polymath, Publisher から共通利用される。
外部ライブラリ不要、主要50言語をカバー。
"""

# 主要50言語の ISO 639-1 → 英語名マッピング
_LANGUAGE_NAMES: dict[str, str] = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "ga": "Irish",
    "gl": "Galician",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "ko": "Korean",
    "la": "Latin",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "zh": "Chinese",
}


def get_language_name(lang_code: str) -> str:
    """ISO 639-1 コードから英語言語名を返す。

    未知のコードは lang_code.upper() にフォールバック。

    Args:
        lang_code: ISO 639-1 言語コード（例: "en", "de", "ja"）

    Returns:
        英語の言語名（例: "English", "German", "Japanese"）
    """
    return _LANGUAGE_NAMES.get(lang_code.lower(), lang_code.upper())
