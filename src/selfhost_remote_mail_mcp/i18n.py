# SPDX-License-Identifier: AGPL-3.0-only
"""Languages for the web pages (login, settings, upload). Tool answers stay in English: the AI app reads them and
talks to the user in the user's own language.

Every text a person sees on a page is written in English inside _("...") (or N_("...") where it's stored first and
translated later). A language is a JSON file, locales/<code>.json, mapping each English text to its translation.
Texts may hold {placeholders} and a few HTML tags; a translation keeps both exactly. Missing texts fall back to
English, so a half-done language still works. `selfhost-remote-mail-mcp translate <code>` makes or updates a file
for an AI agent (or a person) to fill in, and `translate --check <code>` checks it.
"""

from __future__ import annotations

import ast
import contextvars
import json
import os
import re
from pathlib import Path

PACKAGE_LOCALES = Path(__file__).resolve().parent / "locales"

# The languages that ship with the server, by their own name. Others can be added with the translate command.
LANGUAGES = {
    "en": "English", "es": "Español", "pt-BR": "Português (Brasil)", "fr": "Français", "de": "Deutsch",
    "it": "Italiano", "nl": "Nederlands", "pl": "Polski", "sv": "Svenska", "tr": "Türkçe", "ru": "Русский",
    "uk": "Українська", "ja": "日本語", "zh-CN": "简体中文", "zh-TW": "繁體中文", "ko": "한국어", "hi": "हिन्दी",
    "id": "Bahasa Indonesia", "vi": "Tiếng Việt", "el": "Ελληνικά",
}

LANG: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default="en")
_catalogs: dict[str, dict[str, str]] = {}
PLACEHOLDER = re.compile(r"\{(\w+)\}")
TAG = re.compile(r"</?[a-z][^>]*>")


def user_locales() -> Path:
    """Where the translate command saves, and where the server looks first: <config folder>/locales, or
    MAIL_LOCALES_DIR."""
    config = Path(os.environ.get("MAIL_CONFIG_DIR") or Path.home() / ".config" / "selfhost-remote-mail-mcp")
    return Path(os.environ.get("MAIL_LOCALES_DIR") or config / "locales").expanduser()


def catalog(code: str) -> dict[str, str]:
    if code == "en":
        return {}
    if code not in _catalogs:
        found = {}
        for folder in (PACKAGE_LOCALES, user_locales()):   # a user's own file wins
            path = folder / f"{code}.json"
            if path.is_file():
                try:
                    found.update({k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items()
                                  if isinstance(v, str) and v.strip()})
                except (OSError, ValueError):
                    pass
        _catalogs[code] = found
    return _catalogs[code]


def available() -> list[str]:
    codes = {"en"}
    for folder in (PACKAGE_LOCALES, user_locales()):
        if folder.is_dir():
            codes |= {p.stem for p in folder.glob("*.json")}
    return sorted(codes)


def _(text: str, **values) -> str:
    """The text in the page's language, with {placeholders} filled in. A broken translation falls back to English."""
    translated = catalog(LANG.get()).get(text, text)
    if not values:
        return translated
    try:
        return translated.format(**values)
    except (KeyError, IndexError, ValueError):
        return text.format(**values)


def N_(text: str) -> str:
    """Marks a text for translation without translating it yet (for lists defined before a page is drawn)."""
    return text


def pick(accept_language: str = "", forced: str = "") -> str:
    """The best language for a request: LANGUAGE setting if set, else the browser's preferences, else English."""
    codes = available()
    lower = {c.lower(): c for c in codes}

    def match(tag: str) -> str | None:
        tag = tag.strip().lower().replace("_", "-")
        if not tag:
            return None
        if tag in lower:
            return lower[tag]
        if tag.startswith("zh"):   # Chinese: traditional for Taiwan, Hong Kong, Macau and "Hant"
            return lower.get("zh-tw" if any(x in tag for x in ("tw", "hk", "mo", "hant")) else "zh-cn")
        base = tag.split("-")[0]
        if base in lower:
            return lower[base]
        return next((c for low, c in lower.items() if low.split("-")[0] == base), None)

    if forced and match(forced):
        return match(forced)
    wanted = []
    for i, part in enumerate(accept_language.split(",")):
        tag, _sep, q = part.strip().partition(";q=")
        try:
            wanted.append((float(q or 1), -i, tag))
        except ValueError:
            continue
    for _q, _i, tag in sorted(wanted, reverse=True):
        found = match(tag)
        if found:
            return found
    return "en"


# ---------------------------------------------------------------- for the translate command

def source_texts(files: list[Path]) -> list[str]:
    """Every English text inside _("...") or N_("...") in the given source files, in order of appearance."""
    texts = []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "N_", "T_")
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                if node.args[0].value not in texts:
                    texts.append(node.args[0].value)
    return texts


def problems(english: str, translated: str) -> list[str]:
    """What's wrong with one translation: placeholders or HTML tags that don't match the English text."""
    issues = []
    if sorted(PLACEHOLDER.findall(english)) != sorted(PLACEHOLDER.findall(translated)):
        issues.append("the {placeholders} must be exactly the same as in English")
    if sorted(TAG.findall(english)) != sorted(TAG.findall(translated)):
        issues.append("the HTML tags must be exactly the same as in English")
    if "<script" in translated.lower() or "javascript:" in translated.lower():
        issues.append("scripts aren't allowed")
    try:
        translated.format(**{name: "x" for name in PLACEHOLDER.findall(english)})
    except (KeyError, IndexError, ValueError):
        issues.append("unmatched { or } (write {{ or }} for a literal brace)")
    return issues
