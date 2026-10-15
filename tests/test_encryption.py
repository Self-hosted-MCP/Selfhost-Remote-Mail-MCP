# SPDX-License-Identifier: AGPL-3.0-only
"""What is encrypted or private by default: connections, the send log, the keychain, HTTPS-only pages."""
import ssl

from starlette.testclient import TestClient

from selfhost_remote_mail_mcp import server

REAL_CONNECT = server.connect   # saved before the test fixture swaps in the fake mail server


def test_connections_check_certificates_and_need_tls_1_2():
    ctx = server.tls_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname
    assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_imap_is_given_the_strict_context(monkeypatch):
    seen = {}

    class Spy:
        def __init__(self, host, port=None, ssl=None, ssl_context=None, timeout=None):
            seen.update(ssl=ssl, ctx=ssl_context)

        def login(self, *a):
            pass
    monkeypatch.setattr(server, "IMAPClient", Spy)
    real_connect = REAL_CONNECT
    real_connect(server.Account(address="a@b.test", password="x", imap_host="imap.b.test", smtp_host="s"))
    assert seen["ssl"] is True and seen["ctx"].minimum_version >= ssl.TLSVersion.TLSv1_2


def test_send_log_is_private(mailbox):
    out = server.draft(to=["x@y.test"], subject="Private", body="b")
    server.send_email(out.split("ID: ")[1].split("\n")[0])
    assert oct(server.SENT_LOG.stat().st_mode & 0o777) == "0o600"


class FakeKeychain:
    def __init__(self):
        self.store = {}

    def get_password(self, service, user):
        return self.store.get((service, user))

    def set_password(self, service, user, password):
        self.store[(service, user)] = password


def test_password_can_live_in_the_keychain(monkeypatch):
    kc = FakeKeychain()
    kc.set_password(server.KEYCHAIN_SERVICE, "me@example.com", "from-keychain")
    monkeypatch.setattr(server, "keychain", lambda: kc)
    monkeypatch.setenv("MAIL_PASSWORD", "")
    server.ENV_FILE.write_text(server.ENV_FILE.read_text().replace("MAIL_PASSWORD=x\n", ""))
    try:
        assert server.all_accounts()[0].password == "from-keychain"
    finally:
        server.ENV_FILE.write_text(server.ENV_FILE.read_text() + "MAIL_PASSWORD=x\n")


def test_the_settings_file_wins_over_the_keychain(monkeypatch):
    kc = FakeKeychain()
    kc.set_password(server.KEYCHAIN_SERVICE, "me@example.com", "from-keychain")
    monkeypatch.setattr(server, "keychain", lambda: kc)
    assert server.all_accounts()[0].password == "x"


def test_pages_tell_browsers_to_stay_on_https(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", "https test passphrase")
    monkeypatch.setenv("PUBLIC_URL", "https://mail.example.com")
    saved = dict(server.pages.HEADERS)
    try:
        app = server.build_server(True).streamable_http_app()
        r = TestClient(app, base_url="https://mail.example.com").get("/settings")
        assert r.headers["strict-transport-security"].startswith("max-age=")
    finally:
        server.pages.HEADERS.clear()
        server.pages.HEADERS.update(saved)
        monkeypatch.setattr(server, "PROVIDER", None)
