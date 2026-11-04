"""Server-side i18n for bot messages, notifications and transactional emails.

Usage:
    from app.i18n import t
    t(user.language, "bot.start.greeting", name=user.first_name)

`t(lang, key, **params)` resolves a dotted key in the chosen language catalog,
falling back to English, then to the raw key (so a missing key is visible, never
a crash). Catalogs live in i18n/ru.py and i18n/en.py as nested dicts.
"""
from app.i18n import en as _en
from app.i18n import ru as _ru

DEFAULT_LANG = "en"
SUPPORTED = ("ru", "en")

_CATALOGS = {"ru": _ru.MESSAGES, "en": _en.MESSAGES}


def _lookup(catalog: dict, key: str):
    node = catalog
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def normalize_lang(lang: str | None) -> str:
    """Map an arbitrary language_code/value to a supported language (en fallback)."""
    if lang and lang.lower().startswith("ru"):
        return "ru"
    if lang in SUPPORTED:
        return lang
    return DEFAULT_LANG


def t(lang: str | None, key: str, **params) -> str:
    """Translate `key` into `lang` (en fallback, then the raw key)."""
    lang = lang if lang in _CATALOGS else DEFAULT_LANG
    msg = _lookup(_CATALOGS[lang], key)
    if msg is None and lang != DEFAULT_LANG:
        msg = _lookup(_CATALOGS[DEFAULT_LANG], key)
    if msg is None:
        return key
    if not params:
        return msg
    try:
        return msg.format(**params)
    except (KeyError, IndexError, ValueError):
        return msg
