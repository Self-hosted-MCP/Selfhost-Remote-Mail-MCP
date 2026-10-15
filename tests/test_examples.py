# SPDX-License-Identifier: AGPL-3.0-only
"""The starter files in examples/ load and fill in without leftovers."""
from pathlib import Path

from selfhost_remote_mail_mcp import server

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_every_example_template_fills_in(monkeypatch, mailbox):
    monkeypatch.setattr(server, "TEMPLATES", EXAMPLES / "templates")
    templates = server.load_templates()
    assert len(templates) == 5
    for t in templates:
        manual = [p for p in server.placeholders(t) if p not in server.AUTO_PLACEHOLDERS]
        out = server.draft(to=["Sam Lee <sam@example.org>"], template=t["name"],
                           placeholder=[f"{p}=X{p}" for p in manual])
        assert "{{" not in out and "Hi Sam," in out, t["name"]
        assert all(f"X{p}" in out for p in manual), t["name"]


def test_plain_signatures(monkeypatch):
    monkeypatch.setattr(server, "SIGNATURE_HTML", EXAMPLES / "missing.html")
    for f in (EXAMPLES / "signatures").glob("plain-*.md"):
        monkeypatch.setattr(server, "SIGNATURE", f)
        assert server.signature()[0].startswith("-- \nAlex Rivera"), f.name


def test_signature_designs_have_clean_text_copies(monkeypatch):
    designs = sorted((EXAMPLES / "signatures").glob("*.html"))
    assert len(designs) == 5
    for f in designs:
        monkeypatch.setattr(server, "SIGNATURE_HTML", f)
        plain, html = server.signature()
        lines = plain.splitlines()
        assert lines[0] in ("Alex Rivera", "AR"), f.name
        assert all(line == line.strip() and line for line in lines), f.name
        assert "<" not in plain and "\xa0" not in plain and "<!--" not in html, f.name


def test_signature_links_keep_their_address():
    text = server.signature_text('<a href="https://example.com/shop">Shop</a> <a href="https://example.com">example.com</a>'
                                 ' <a href="mailto:a@b.test">a@b.test</a>')
    assert text == "Shop (https://example.com/shop) example.com a@b.test"
