# SPDX-License-Identifier: AGPL-3.0-only
"""Languages for the web pages: picking one, falling back to English, the translate command and its checks."""
import json
import re

import pytest
from starlette.testclient import TestClient

from selfhost_remote_mail_mcp import i18n, pages, server

PASS = "web test passphrase"


@pytest.fixture
def locales(tmp_path, monkeypatch):
    """A private locales folder holding a small test language, 'xx'."""
    monkeypatch.setenv("MAIL_LOCALES_DIR", str(tmp_path))
    monkeypatch.setattr(i18n, "PACKAGE_LOCALES", tmp_path / "none")
    i18n._catalogs.clear()
    (tmp_path / "xx.json").write_text(json.dumps({
        "Passphrase": "Wachtwoordzin-xx",
        "Settings": "Instellingen-xx",
        "Wrong passphrase.": "Verkeerd-xx.",
        "{app} wants your <span class=\"hl\">mailbox</span>": "{app} wil je <span class=\"hl\">postvak</span>-xx",
        "Remember this device for 90 days": "",
    }), encoding="utf-8")
    yield tmp_path
    i18n._catalogs.clear()
    i18n.LANG.set("en")


def test_pick_follows_the_browser_and_the_setting(locales):
    assert i18n.pick("xx;q=0.9, en;q=0.5") == "xx"
    assert i18n.pick("de-DE, de;q=0.9") == "en"                  # no German file here: English
    assert i18n.pick("xx-YY") == "xx"                             # a regional variant finds the base language
    assert i18n.pick("xx", forced="en") == "en"                   # LANGUAGE wins over the browser
    assert i18n.pick("") == "en"


def test_shipped_language_codes_match_variants():
    i18n._catalogs.clear()
    codes = set(i18n.available())
    if {"zh-CN", "zh-TW", "pt-BR"} <= codes:
        assert i18n.pick("zh-HK") == "zh-TW" and i18n.pick("zh-Hans-CN") == "zh-CN" and i18n.pick("pt-PT") == "pt-BR"


def test_missing_texts_fall_back_to_english(locales):
    i18n.LANG.set("xx")
    assert i18n._("Passphrase") == "Wachtwoordzin-xx"
    assert i18n._("Remember this device for 90 days") == "Remember this device for 90 days"   # empty: English
    assert i18n._("Open settings") == "Open settings"


def test_pages_speak_the_browsers_language(locales, monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    page = client.get("/settings", headers={"accept-language": "xx"}).text
    assert 'lang="xx"' in page and "Instellingen-xx" in page and "Wachtwoordzin-xx" in page
    r = client.post("/settings/login", data={"passphrase": "wrong one!"},
                    headers={"origin": "http://localhost", "accept-language": "xx"})
    assert "Verkeerd-xx." in r.text
    assert 'lang="en"' in client.get("/settings").text
    monkeypatch.setenv("LANGUAGE", "xx")
    assert "Instellingen-xx" in client.get("/settings", headers={"accept-language": "en"}).text
    monkeypatch.setattr(server, "PROVIDER", None)


def test_values_in_translations_are_escaped(locales):
    i18n.LANG.set("xx")
    html = pages.login("<script>x</script>", "claude.ai", "req", [("me@example.com", "full", "")])
    assert "<script>x</script>" not in html and "&lt;script&gt;" in html
    assert 'postvak</span>-xx' in html


def test_problems_catch_broken_translations():
    assert i18n.problems("Hello {name}", "Hallo {naam}")
    assert i18n.problems("<b>Not ticked:</b> {app}", "Nicht {app}")
    assert i18n.problems("Save", "<script>alert(1)</script>")
    assert i18n.problems("Size {size}", "Größe {size")
    assert not i18n.problems("<b>Ticked:</b> {app} can send", "<b>Angehakt:</b> {app} kann senden")


def test_a_broken_translation_never_breaks_a_page(locales):
    (locales / "xx.json").write_text(json.dumps({"Update available: {version}": "Update {versie"}), encoding="utf-8")
    i18n._catalogs.clear()
    i18n.LANG.set("xx")
    assert i18n._("Update available: {version}", version="v1") == "Update available: v1"


def test_the_translate_command(locales, capsys):
    server.run_translate(["ko"])
    data = json.loads((locales / "ko.json").read_text(encoding="utf-8"))
    assert "Passphrase" in data and "Allow {app} to send email" in data and len(data) > 150
    assert all(v == "" for v in data.values())
    data["Passphrase"] = "암호문"
    data["Allow {app} to send email"] = "{app}이 메일을 보내도록 허용"
    (locales / "ko.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    server.run_translate(["ko"])                                          # running again keeps what's filled in
    again = json.loads((locales / "ko.json").read_text(encoding="utf-8"))
    assert again["Passphrase"] == "암호문"
    with pytest.raises(SystemExit, match="still to translate"):
        server.run_translate(["--check", "ko"])
    assert "2 of" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="Usage"):
        server.run_translate(["../evil"])


def test_every_page_text_is_marked_for_translation():
    """Catches a new English sentence added to a page without _(): every text between tags on a fully drawn page
    must be translatable (or be a name, address, number or code)."""
    texts = set(i18n.source_texts([server.HERE / "pages.py", server.HERE / "server.py",
                                   *sorted(server.LIBRARY.glob("*/addon.py"))]))
    assert len(texts) > 150
    import html as htmllib
    pieces = [f.strip(" .") for t in texts for f in re.split(r"<[^>]+>", t) if f.strip(" .")]
    patterns = [re.compile("^" + re.sub(r"\\\{\w+\\\}", ".+", re.escape(f)) + "$") for f in pieces]
    box = {"address": "a@example.com", "mode": "full", "source": "web", "name": "A", "label": "Work",
           "imap_host": "i", "imap_port": 993, "smtp_host": "s", "smtp_port": 465, "username": "", "smtp_username": ""}
    full = pages.settings("t", [box], [{"client_id": "c", "name": "Claude", "host": "claude.ai", "grant": None,
                                        "may_send": True}], None, 5, True,
                          {"version": "1", "update": None, "changelog": "", "addons": ["decks"]}, True,
                          {"on": True, "forced_off": False, "signins": [{"ok": False, "where": "Settings page",
                           "time": "1 Oct", "device": "Mac", "ip": "1.2.3.4"}],
                           "list": [{"id": "x", "device": "", "ip": "1.2.3.4", "since": "1 Oct", "seen": "2 Oct",
                                     "remember": True, "current": False}]},
                          [{"name": "upload_links", "label": "Upload links for AI apps", "on": True, "forced_off": False}],
                          [], [{"name": "pdf_maker", "about": "", "on": True, "library": True},
                               {"name": "invoices", "about": "", "on": False, "library": True},
                               {"name": "decks", "about": "", "on": True, "library": False}])
    files = pages.uploads("t", [{"code": "F-AAAAAA", "name": "a.pdf", "size_text": "1 MB", "level": "suspect",
                                 "why": "x", "used": True, "minutes_left": 30}], None, "25 MB", ".pdf")
    setup_fields = [{**f, "full": "INVOICES_" + f["key"], "value": "", "where": w, "has_value": w == "server"}
                    for f, w in zip(server.addon_fields("invoices"), ["", "server"] + [""] * 20)]
    setup_fields.append({"key": "K", "label": "Your name or business name", "help": "", "required": False,
                         "lines": 1, "secret": True, "full": "X_K", "value": "", "where": "page", "has_value": True})
    html = (pages.addon_setup("t", {"name": "invoices", "about": "", "on": True, "library": True, "in_settings": False},
                              setup_fields, ("ok", "x"))
            + pages.addon_setup("t", {"name": "pdf_maker", "about": "", "on": True, "library": True,
                                      "in_settings": True}, [], None)
            + pages.uploads("t", [], None, "25 MB", ".pdf") + pages.settings_login() + pages.upload_link() + full + files
            + pages.login("Claude", "claude.ai", "r", [("a@example.com", "full", ""), ("b@example.com", "read", "")])
            + pages.login(None, None, "r", []) + pages.upload_link(done={"name": "a", "level": "safe", "why": ""}))
    for chunk in re.findall(r">([^<>{}]*[a-z]{3,}[^<>{}]*)<", html):
        chunk = chunk.strip().removesuffix(" · Selfhost Mail")
        if not chunk or chunk.startswith(("Selfhost", "Selfhost-Remote")) or "@" in chunk:
            continue
        chunk = htmllib.unescape(chunk).strip(" .·,")
        plain = [re.sub(r"<[^>]+>", "", t) for t in texts]
        assert (any(chunk in t for t in plain) or any(p.search(chunk) for p in patterns)
                or chunk in ("Self-hosted MCP", "Claude", "Work", "Mac", "decks", "a.pdf", "1 MB")), chunk
