"""Login passphrase, hosting addresses, the read-only mailbox and the signature."""
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server


def test_plain_passphrase(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", "correct horse battery")
    assert server.passphrase_ok("correct horse battery")
    assert not server.passphrase_ok("wrong")
    assert not server.passphrase_ok("")


def test_hash_wins_over_plain(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", "plain passphrase here")
    monkeypatch.setenv("LOGIN_HASH", server.hash_passphrase("hashed passphrase", rounds=1000))
    assert server.passphrase_ok("hashed passphrase")
    assert not server.passphrase_ok("plain passphrase here")


def test_no_passphrase_means_no_login():
    assert not server.passphrase_ok("anything")


@pytest.mark.parametrize("env, url", [
    ({}, "http://localhost:8765"),
    ({"PORT": "9000"}, "http://localhost:9000"),
    ({"RAILWAY_PUBLIC_DOMAIN": "mail-x.up.railway.app"}, "https://mail-x.up.railway.app"),
    ({"RENDER_EXTERNAL_URL": "https://mail-x.onrender.com/"}, "https://mail-x.onrender.com"),
    ({"PUBLIC_URL": "https://mail.example.com", "RENDER_EXTERNAL_URL": "https://x.onrender.com"},
     "https://mail.example.com"),
])
def test_public_url(env, url):
    assert server.public_url(env) == url


def test_read_only_mailbox_refuses_every_change(monkeypatch, mailbox):
    monkeypatch.setenv("READ_ONLY_ADDRESS", "other@example.com")   # the older setting still works
    monkeypatch.setenv("READ_ONLY_PASSWORD", "y")
    assert "other@example.com" in server.accounts() and "read and search only" in server.accounts()
    with server.imap() as c:
        with pytest.raises(ToolError, match="read-only"):
            c.select_folder("other@example.com:INBOX")             # write access
        with pytest.raises(ToolError, match="read-only"):
            c.append("other@example.com:Drafts", b"x")
        c.select_folder("other@example.com:INBOX", readonly=True)  # reading is fine
        with pytest.raises(ToolError, match="read-only"):
            c.add_flags([1], [b"\\Seen"])
    with pytest.raises(ToolError, match="read-only"):
        server.action("archive", ["other@example.com:INBOX#1"])


def test_main_mailbox_is_never_the_read_only_one(monkeypatch):
    monkeypatch.setenv("READ_ONLY_ADDRESS", "ME@example.com")
    monkeypatch.setenv("READ_ONLY_PASSWORD", "y")
    boxes = server.all_accounts()
    assert [(a.address, a.mode) for a in boxes] == [("me@example.com", "full")]


def test_signature_added_when_present(mailbox):
    assert "Signature: none" in server.accounts()
    server.SIGNATURE.write_text("Me\nsig-line-123")
    try:
        assert "Signature: set up" in server.accounts()
        out = server.draft(to=["you@example.org"], subject="Hi", body="Hello.\n\nBest,")
        assert "sig-line-123" in out
        assert "sig-line-123" not in server.draft(to=["you@example.org"], subject="Hi", body="x", no_signature=True)
    finally:
        server.SIGNATURE.unlink()


def test_signature_from_setting(monkeypatch):
    monkeypatch.setenv("MAIL_SIGNATURE", "Me\\nexample-sig")
    plain, html = server.signature()
    assert plain == "-- \nMe\nexample-sig" and "example-sig" in html


def test_smtp_login_name():
    acc = lambda **k: server.Account(address="a@icloud.com", password="x", imap_host="i", smtp_host="s", **k)
    assert acc().smtp_login == "a@icloud.com"
    assert acc(username="a").smtp_login == "a"
    assert acc(username="a", smtp_username="a@icloud.com").smtp_login == "a@icloud.com"
