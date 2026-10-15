# SPDX-License-Identifier: AGPL-3.0-only
"""Several mailboxes: settings, routing, modes, per-app choices, encrypted storage, the scheduler."""
import datetime as dt
import email
import json
import re
from email.message import EmailMessage
from email.policy import default as POLICY

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from conftest import FakeIMAP, FakeSMTP, FOLDERS
from selfhost_remote_mail_mcp import server

LATER = dt.datetime.now(dt.timezone.utc).replace(microsecond=0) + dt.timedelta(hours=3)


@pytest.fixture
def three(monkeypatch):
    """me@ (full, from MAIL_*), work@ (draft only), old@ (read only)."""
    monkeypatch.setenv("MAIL_2_ADDRESS", "work@example.org")
    monkeypatch.setenv("MAIL_2_PASSWORD", "w")
    monkeypatch.setenv("MAIL_2_MODE", "draft")
    monkeypatch.setenv("MAIL_3_ADDRESS", "old@example.net")
    monkeypatch.setenv("MAIL_3_PASSWORD", "o")
    monkeypatch.setenv("MAIL_3_IMAP_HOST", "imap.example.net")
    monkeypatch.setenv("MAIL_3_MODE", "read")
    for a in ("me@example.com", "work@example.org", "old@example.net"):
        FakeIMAP.stores.setdefault(a, {f: {} for f in FOLDERS})
    return FakeIMAP.stores


def put(store, folder, sender, subject, to="me@example.com"):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to, subject
    msg["Message-ID"] = f"<{subject.replace(' ', '')}@test>"
    msg["Date"] = "Mon, 12 Oct 2026 10:00:00 +0000"
    msg.set_content("Hello")
    uid = FakeIMAP.next_uid
    FakeIMAP.next_uid += 1
    store[folder][uid] = msg.as_bytes()
    return uid


def new_id(text):
    return re.search(r"ID: (\S+)", text)[1].rstrip(".")


# ---- settings

def test_settings_parse_modes_defaults_and_cap(three, monkeypatch):
    boxes = server.all_accounts()
    assert [(a.address, a.mode) for a in boxes] == [("me@example.com", "full"), ("work@example.org", "draft"),
                                                  ("old@example.net", "read")]
    work, old = boxes[1], boxes[2]
    assert work.imap_host == "imap.test" and work.smtp_host == "smtp.test" and work.name == "Me"   # from mailbox 1
    assert old.imap_host == "imap.example.net"
    monkeypatch.setenv("MAX_MAILBOXES", "2")
    assert len(server.all_accounts()) == 2
    monkeypatch.setenv("MAIL_2_MODE", "sometimes")
    with pytest.raises(ToolError, match="Unknown mailbox mode"):
        server.all_accounts()


def test_same_address_twice_first_wins(three, monkeypatch):
    monkeypatch.setenv("MAIL_4_ADDRESS", "ME@example.com")
    monkeypatch.setenv("MAIL_4_PASSWORD", "z")
    monkeypatch.setenv("MAIL_4_MODE", "read")
    assert [a.mode for a in server.all_accounts() if a.address == "me@example.com"] == ["full"]


# ---- routing and modes

def test_new_drafts_go_where_asked(three):
    d1 = new_id(server.draft(to=["x@y.test"], subject="A", body="a"))
    assert d1.startswith("Drafts#")
    d2 = new_id(server.draft(to=["x@y.test"], subject="B", body="b", account="work@example.org"))
    assert d2.startswith("work@example.org:Drafts#")
    assert len(three["work@example.org"]["Drafts"]) == 1 and len(three["me@example.com"]["Drafts"]) == 1
    sent_from = email.message_from_bytes(next(iter(three["work@example.org"]["Drafts"].values())), policy=POLICY)["From"]
    assert "work@example.org" in sent_from
    with pytest.raises(ToolError, match="read-only"):
        server.draft(to=["x@y.test"], subject="C", body="c", account="old@example.net")
    with pytest.raises(ToolError, match="isn't one of the mailboxes"):
        server.draft(to=["x@y.test"], subject="D", body="d", account="stranger@nowhere.test")


def test_replies_stay_in_their_mailbox(three):
    uid = put(three["work@example.org"], "INBOX", "Client <client@x.test>", "Brief", to="work@example.org")
    d = new_id(server.draft(reply_to=f"work@example.org:INBOX#{uid}", body="Thanks"))
    assert d.startswith("work@example.org:Drafts#")
    reply = email.message_from_bytes(three["work@example.org"]["Drafts"][int(d.split("#")[1])], policy=POLICY)
    assert reply["To"] == "Client <client@x.test>" and "work@example.org" in reply["From"]
    # a reply to the read-only mailbox is drafted in the first mailbox that may draft
    uid = put(three["old@example.net"], "INBOX", "Old friend <f@x.test>", "Hi", to="old@example.net")
    d = new_id(server.draft(reply_to=f"old@example.net:INBOX#{uid}", body="Hey"))
    assert d.startswith("Drafts#")


def test_sending_respects_each_mailbox_mode(three):
    d = new_id(server.draft(to=["x@y.test"], subject="From work", body="b", account="work@example.org"))
    with pytest.raises(ToolError, match="never sends"):
        server.send_email(d)
    with pytest.raises(ToolError, match="never sends"):
        server.schedule_send(d, LATER.isoformat())
    assert not FakeSMTP.sent
    d = new_id(server.draft(to=["x@y.test"], subject="From me", body="b"))
    server.send_email(d)
    assert FakeSMTP.sent[0].sent_from == "me@example.com"
    assert len(three["me@example.com"]["Sent"]) == 1 and not three["work@example.org"]["Sent"]


def test_moves_never_cross_mailboxes(three):
    uid = put(three["work@example.org"], "INBOX", "a@x.test", "Move me", to="work@example.org")
    server.action("archive", [f"work@example.org:INBOX#{uid}"])
    assert uid in three["work@example.org"]["Archive"] and not three["me@example.com"]["Archive"]
    uid2 = put(three["work@example.org"], "INBOX", "a@x.test", "Stay", to="work@example.org")
    with pytest.raises(ToolError, match="between two mailboxes"):
        server.action("moveToFolder", [f"work@example.org:INBOX#{uid2}"], folder="me@example.com:Archive")
    with pytest.raises(ToolError, match="read-only"):
        server.action("pin", [f"old@example.net:INBOX#{put(three['old@example.net'], 'INBOX', 'a@x.test', 'P')}"])


def test_accounts_lists_every_mailbox_with_its_mode(three):
    out = server.accounts()
    assert "Mailbox 1: me@example.com  (default)" in out
    assert "work@example.org" in out and "never send" in out and "read and search only" in out


def test_scheduler_sends_from_every_full_mailbox(three, monkeypatch):
    monkeypatch.setenv("MAIL_2_MODE", "full")
    d1 = new_id(server.draft(to=["x@y.test"], subject="One", body="b"))
    d2 = new_id(server.draft(to=["x@y.test"], subject="Two", body="b", account="work@example.org"))
    server.schedule_send(d1, LATER.isoformat())
    server.schedule_send(d2, LATER.isoformat())
    listed = server.scheduled()
    assert "One" in listed and "Two" in listed and "work@example.org:Drafts#" in listed
    server.run_scheduled_once(now=LATER + dt.timedelta(seconds=30))
    assert sorted(m.sent_from for m in FakeSMTP.sent) == ["me@example.com", "work@example.org"]


# ---- what each app may use

class FakeProvider:
    def __init__(self, grants, senders=()):
        self.grants = grants
        self.senders = set(senders)


def as_app(monkeypatch, client_id, grants, senders=()):
    from mcp.server.auth.middleware import auth_context
    token = server.AccessToken(token="t", client_id=client_id, scopes=["mail"])
    monkeypatch.setattr(server, "PROVIDER", FakeProvider(grants, senders))
    monkeypatch.setattr(auth_context, "get_access_token", lambda: token)


def test_an_app_only_sees_its_ticked_mailboxes(three, monkeypatch):
    as_app(monkeypatch, "phone", {"phone": ["work@example.org"]})
    out = server.accounts()
    assert "work@example.org" in out and "me@example.com" not in out
    assert server.emails().startswith("INBOX:")                    # its default is now work@
    with pytest.raises(ToolError, match="isn't one of the mailboxes"):
        server.emails("me@example.com:INBOX")
    with pytest.raises(ToolError, match="isn't one of the mailboxes"):
        server.folders("old@example.net")


def test_an_app_with_no_mailbox_left_gets_a_clear_error(three, monkeypatch):
    as_app(monkeypatch, "phone", {"phone": []})
    with pytest.raises(ToolError, match="may not use any mailbox"):
        server.accounts()


def test_older_apps_without_a_choice_see_everything(three, monkeypatch):
    as_app(monkeypatch, "old-app", {})
    assert "old@example.net" in server.accounts()


# ---- mailboxes added on the settings page

def web_account(address="web@example.com", password="secret-pw-123"):
    return server.Account(address=address, password=password, imap_host="imap.test", smtp_host="smtp.test", mode="draft")


def test_web_mailboxes_are_stored_encrypted():
    server.save_web_accounts([web_account()])
    raw = server.STORE_FILE.read_text()
    assert "secret-pw-123" not in raw and "web@example.com" in raw
    assert oct(server.STORE_FILE.stat().st_mode & 0o777) == "0o600"
    assert oct(server.KEY_FILE.stat().st_mode & 0o777) == "0o600"
    loaded = server.web_accounts()
    assert loaded[0].password == "secret-pw-123" and loaded[0].source == "web"
    assert [a.address for a in server.all_accounts()] == ["me@example.com", "web@example.com"]


def test_secret_key_setting_and_a_wrong_key(monkeypatch, capsys):
    monkeypatch.setenv("MAIL_SECRET_KEY", "first key")
    server.save_web_accounts([web_account()])
    assert not server.KEY_FILE.exists()                       # the setting is used, no key file
    monkeypatch.setenv("MAIL_SECRET_KEY", "another key")
    assert server.web_accounts() == []                        # can't unlock: skipped, not crashed
    assert "can't unlock" in capsys.readouterr().err


def test_settings_actions_add_update_delete(monkeypatch):
    p = FakeProvider({"app1": ["me@example.com", "new@example.com"]})
    p.clients = {"app1": None}
    p.lock = __import__("threading").Lock()
    p.save = lambda: None
    form = {"action": "add", "address": "new@example.com", "password": "pw", "mode": "read",
            "imap_host": "imap.test", "smtp_host": "smtp.test"}
    assert server.settings_action(p, "mailbox", form)[0] == "ok"
    assert [(a.address, a.mode) for a in server.all_accounts()][-1] == ("new@example.com", "read")
    assert server.settings_action(p, "mailbox", form)[1].endswith("already set up.")
    upd = {"action": "update", "address": "new@example.com", "mode": "full", "name": "New"}
    assert server.settings_action(p, "mailbox", upd)[0] == "ok"
    acc = server.web_accounts()[0]
    assert acc.mode == "full" and acc.password == "pw"         # empty password field keeps the old one
    assert server.settings_action(p, "mailbox", {"action": "update", "address": "me@example.com"})[0] == "error"
    assert server.settings_action(p, "mailbox", {"action": "delete", "address": "new@example.com"})[0] == "error"
    assert server.settings_action(p, "mailbox", {"action": "delete", "address": "new@example.com", "confirm": "yes"})[0] == "ok"
    assert server.web_accounts() == [] and p.grants["app1"] == ["me@example.com"]


def test_adding_a_mailbox_that_cant_log_in_is_refused(monkeypatch):
    p = FakeProvider({})

    def refuse(account):
        raise server.ToolError("The mail server refused the login")
    monkeypatch.setattr(server, "connect", refuse)
    kind, text = server.settings_action(p, "mailbox", {"action": "add", "address": "bad@example.com", "password": "x",
                                                        "imap_host": "i", "smtp_host": "s", "mode": "full"})
    assert kind == "error" and "Not added" in text and not server.STORE_FILE.exists()


def test_add_form_fills_known_providers():
    acc = server.account_from_form({"address": "Someone@Gmail.com", "password": "x", "mode": "full"})
    assert (acc.address, acc.imap_host, acc.smtp_host) == ("someone@gmail.com", "imap.gmail.com", "smtp.gmail.com")
    with pytest.raises(ToolError, match="isn't known"):
        server.account_from_form({"address": "a@unknown-provider.test", "password": "x"})


# ---- mailbox names

def test_mailbox_names_from_settings_and_renaming(three, monkeypatch):
    monkeypatch.setenv("MAIL_2_LABEL", "Work")
    assert "Mailbox 2: Work (work@example.org)" in server.accounts()
    d = new_id(server.draft(to=["x@y.test"], subject="By name", body="b", account="work"))
    assert d.startswith("work@example.org:Drafts#")
    assert server.folders("WORK").startswith("work@example.org")
    assert "By name" in server.search(query="By", scope="Work")
    server.save_label("old@example.net", "Archive 2019")              # a rename on the settings page wins
    assert "Archive 2019 (old@example.net)" in server.accounts()
    with pytest.raises(ToolError, match="Keep the name short"):
        server.clean_label("a:b")
    server.save_label("old@example.net", "")
    assert "Mailbox 3: old@example.net" in server.accounts()


def test_rename_and_add_with_a_name_on_the_settings_page(three):
    p = FakeProvider({})
    assert server.settings_action(p, "mailbox", {"action": "rename", "address": "me@example.com", "label": "Personal"})[0] == "ok"
    assert server.all_accounts()[0].label == "Personal"
    form = {"action": "add", "address": "new@example.com", "password": "pw", "label": "Studio", "mode": "draft",
            "imap_host": "imap.test", "smtp_host": "smtp.test"}
    assert server.settings_action(p, "mailbox", form)[0] == "ok"
    assert [a.label for a in server.all_accounts()][-1] == "Studio"
    page = server.pages.login("Claude", "claude.ai", "r", [(a.address, a.mode, a.label) for a in server.all_accounts()])
    assert "<b>Personal</b>" in page and "<b>Studio</b>" in page


def test_an_unreachable_mailbox_is_listed_with_a_note(three, monkeypatch):
    real = server.connect

    def flaky(account):
        if account.address == "old@example.net":
            raise server.ToolError("Can't reach imap.example.net:993 for old@example.net")
        return real(account)
    monkeypatch.setattr(server, "connect", flaky)
    out = server.accounts()
    assert "Mailbox 3: old@example.net" in out and "Can't log in right now" in out and "Mailbox 1" in out



# ---- sending permission per app

def test_an_app_without_send_permission_can_only_draft(three, monkeypatch):
    as_app(monkeypatch, "chat", {"chat": ["me@example.com"]})
    assert "this app wasn't allowed to send" in server.accounts()
    d = new_id(server.draft(to=["x@y.test"], subject="Drafted", body="b"))
    with pytest.raises(ToolError, match="may not send"):
        server.send_email(d)
    with pytest.raises(ToolError, match="may not send"):
        server.schedule_send(d, LATER.isoformat())
    assert not FakeSMTP.sent


def test_an_app_with_send_permission_sends(three, monkeypatch):
    as_app(monkeypatch, "claude", {"claude": ["me@example.com"]}, senders=["claude"])
    server.send_email(new_id(server.draft(to=["x@y.test"], subject="Go", body="b")))
    assert len(FakeSMTP.sent) == 1


def test_apps_from_before_the_choice_keep_sending(three, monkeypatch):
    as_app(monkeypatch, "old-app", {})
    server.send_email(new_id(server.draft(to=["x@y.test"], subject="Old", body="b")))
    assert len(FakeSMTP.sent) == 1


def test_line_breaks_cant_sneak_in_extra_headers(mailbox):
    with pytest.raises(ToolError, match="Line breaks"):
        server.draft(to=["x@y.test"], subject="Hi\r\nBcc: everyone@x.test", body="b")
    with pytest.raises(ToolError, match="Line breaks"):
        server.draft(to=["x@y.test\nBcc: everyone@x.test"], subject="Hi", body="b")
    assert not mailbox["Drafts"]
