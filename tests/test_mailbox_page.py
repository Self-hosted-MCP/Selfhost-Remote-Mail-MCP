# SPDX-License-Identifier: AGPL-3.0-only
"""The settings page's mailbox controls: make default, mode, a signature per mailbox, remove (with its clean-up),
and the AI asking which mailbox a signature is for."""
import threading

import pytest

from selfhost_remote_mail_mcp import server
from selfhost_remote_mail_mcp.server import ToolError
from test_multi import FakeProvider, as_app, web_account
from test_web import sign_in, web  # noqa: F401  (the fixture)


class Provider(FakeProvider):
    """The parts of the login system that removing a mailbox touches."""
    def __init__(self, grants):
        super().__init__(grants)
        self.lock, self.clients = threading.Lock(), {}

    def save(self):
        pass


@pytest.fixture
def two():
    """me@example.com from the settings file, web@example.com added on the page."""
    server.save_web_accounts([web_account()])
    yield Provider({"c1": ["me@example.com", "web@example.com"]})
    server.PREFS_FILE.unlink(missing_ok=True)


def act(p, **form):
    return server.settings_action(p, "mailbox", form)


def test_make_default_reorders_and_the_setting_wins(two, monkeypatch):
    assert [a.address for a in server.all_accounts()] == ["me@example.com", "web@example.com"]
    kind, text = act(two, action="default", address="web@example.com")
    assert kind == "ok" and "Start a new chat" in text
    assert [a.address for a in server.all_accounts()] == ["web@example.com", "me@example.com"]
    assert "Mailbox 1: web@example.com  (default)" in server.accounts()
    monkeypatch.setenv("MAIL_DEFAULT", "me@example.com")
    assert server.all_accounts()[0].address == "me@example.com"
    assert act(two, action="default", address="web@example.com")[0] == "error"
    assert act(two, action="default", address="nobody@example.com")[0] == "error"


def test_mode_is_changed_alone_and_only_for_page_mailboxes(two):
    server.save_label("web@example.com", "Web")
    kind, _ = act(two, action="mode", address="web@example.com", mode="read")
    web = next(a for a in server.all_accounts() if a.address == "web@example.com")
    assert kind == "ok" and web.mode == "read" and web.password == "secret-pw-123" and web.label == "Web"
    assert act(two, action="mode", address="me@example.com", mode="read")[0] == "error"   # from the settings file


def test_a_new_mailbox_needs_a_chosen_mode(two):
    with pytest.raises(ToolError, match="full, draft only or read only"):   # the page shows it as an error
        act(two, action="add", address="new@example.com", password="x", imap_host="i", smtp_host="s")


def test_signature_per_mailbox_on_the_page(two):
    assert act(two, action="signature", address="me@example.com", signature="Me\nStudio")[0] == "ok"
    assert act(two, action="signature", address="web@example.com", signature="<b>Web</b>")[0] == "ok"
    assert server.signature("me@example.com")[0] == "-- \nMe\nStudio"
    assert server.signature("web@example.com") == ("Web", "<b>Web</b>")
    out = server.draft(to=["you@example.org"], subject="Hi", body="Hello")
    assert "Studio" in out and "Web" not in out   # each mailbox its own
    assert act(two, action="signature", address="web@example.com", signature="")[0] == "ok"
    assert server.signature("web@example.com") == ("", "")


def test_remove_cleans_up_after_itself(two):
    act(two, action="signature", address="web@example.com", signature="Web sig")
    act(two, action="default", address="web@example.com")
    assert act(two, action="delete", address="web@example.com")[0] == "error"   # the box isn't ticked
    kind, text = act(two, action="delete", address="web@example.com", confirm="yes")
    assert kind == "ok" and "untouched" in text
    assert [a.address for a in server.all_accounts()] == ["me@example.com"]
    assert "web@example.com" not in server.read_signatures() and "default_mailbox" not in server.read_prefs()
    assert two.grants["c1"] == ["me@example.com"]   # apps lost it too
    assert act(two, action="delete", address="me@example.com", confirm="yes")[0] == "error"   # settings file


def test_the_ai_asks_which_mailbox_for_a_signature(two):
    server.save_label("web@example.com", "Web")
    with pytest.raises(ToolError, match=r'Which mailbox\? Ask the user: me@example.com, Web \(web@example.com\), or mailbox="all"'):
        server.change_setting("signature", "Me")
    assert "Signature for Web (web@example.com) changed" in server.change_setting("signature", "Web team", mailbox="web")
    assert "every mailbox" in server.change_setting("signature", "Everyone", mailbox="all")
    assert "Everyone" in server.signature("me@example.com")[0] and "Everyone" in server.signature("web@example.com")[0]
    assert "removed from me@example.com" in server.change_setting("signature", "off", mailbox="me@example.com")
    with pytest.raises(ToolError, match="No mailbox called"):
        server.change_setting("signature", "x", mailbox="nope")


def test_an_app_only_changes_signatures_of_its_mailboxes(two, monkeypatch):
    as_app(monkeypatch, "c1", {"c1": ["web@example.com"]})
    monkeypatch.setattr(server.PROVIDER, "clients", {}, raising=False)
    assert "every mailbox" not in server.change_setting("signature", "Only web", mailbox="all")
    assert server.signature("me@example.com") == ("", "") and "Only web" in server.signature("web@example.com")[0]


def test_the_page_shows_the_new_controls(web, two):
    client, _provider = web
    server.set_signature(["web@example.com"], "</textarea><script>x()</script>")
    _csrf, page = sign_in(client)
    assert page.count(">Make default</button>") == 1 and "Choose a mode" in page and "Save signature" in page
    assert "Remove for good" in page and page.count("Remove web@example.com from this server?") == 1
    assert "<script>x()" not in page and "&lt;/textarea&gt;&lt;script&gt;" in page   # escaped in the box
    assert "Save mode" in page and page.count("Save mode") == 1   # only the page-added mailbox
