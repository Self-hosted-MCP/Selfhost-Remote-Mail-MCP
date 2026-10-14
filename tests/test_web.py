"""The web pages over real HTTP requests: settings login, sessions, forged forms, the icon."""
import asyncio
import re

import pytest
from starlette.testclient import TestClient

from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

from selfhost_remote_mail_mcp import server

PASS = "web test passphrase"


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    if server.OAUTH_FILE.exists():
        server.OAUTH_FILE.unlink()
    server._sessions.clear()
    app_server = server.build_server(True)
    client = TestClient(app_server.streamable_http_app(), base_url="http://localhost")
    yield client, server.PROVIDER
    monkeypatch.setattr(server, "PROVIDER", None)


def sign_in(client):
    r = client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"},
                    follow_redirects=False)
    assert r.status_code == 303
    page = client.get("/settings").text
    return re.search(r'name="csrf" value="([^"]+)"', page)[1], page


def test_icon_and_favicon(web):
    client, _ = web
    assert client.get("/icon.svg").headers["content-type"].startswith("image/svg+xml")
    r = client.get("/favicon.ico")
    assert r.headers["content-type"] == "image/png" and r.content.startswith(b"\x89PNG")


def test_settings_needs_the_passphrase(web):
    client, provider = web
    assert "Open settings" in client.get("/settings").text
    r = client.post("/settings/login", data={"passphrase": "wrong one!"}, headers={"origin": "http://localhost"})
    assert r.status_code == 401 and "Wrong passphrase" in r.text
    assert len(provider.failures) == 1


def test_session_cookie_is_locked_down(web):
    client, _ = web
    r = client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"},
                    follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/settings" in cookie


def test_settings_page_shows_mailboxes_and_headers(web):
    client, _ = web
    csrf, page = sign_in(client)
    assert "me@example.com" in page and "Add a mailbox" in page and "Connected apps" in page
    r = client.get("/settings")
    assert r.headers["x-frame-options"] == "DENY" and "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_forms_need_the_page_token_and_same_origin(web, mailbox):
    client, _ = web
    csrf, _ = sign_in(client)
    form = {"action": "test", "address": "me@example.com"}
    assert client.post("/settings/mailbox", data=form, headers={"origin": "http://localhost"}).status_code == 403
    r = client.post("/settings/mailbox", data={**form, "csrf": csrf}, headers={"origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.post("/settings/mailbox", data={**form, "csrf": csrf}, headers={"origin": "http://localhost"})
    assert r.status_code == 200 and "logins work" in r.text


def test_signed_out_forms_do_nothing(web):
    client, _ = web
    r = client.post("/settings/mailbox", data={"action": "delete", "address": "me@example.com", "confirm": "yes"},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/settings"


def test_sign_out(web):
    client, _ = web
    csrf, _ = sign_in(client)
    client.post("/settings/logout", data={"csrf": csrf}, headers={"origin": "http://localhost"})
    assert "Open settings" in client.get("/settings").text


def test_login_page_saves_the_ticked_mailboxes(web, monkeypatch):
    monkeypatch.setenv("MAIL_2_ADDRESS", "work@example.org")
    monkeypatch.setenv("MAIL_2_PASSWORD", "w")
    client, provider = web
    c = OAuthClientInformationFull(client_id="app", client_name="Claude", client_id_issued_at=1,
                                   redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")])
    asyncio.run(provider.register_client(c))
    params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                 redirect_uri_provided_explicitly=True)
    req = asyncio.run(provider.authorize(c, params)).split("req=")[1]
    page = client.get(f"/login?req={req}").text
    assert 'value="work@example.org" checked' in page and 'value="me@example.com" checked' in page
    r = client.post("/login", data={"req": req, "passphrase": PASS}, headers={"origin": "http://localhost"})
    assert r.status_code == 400 and "Tick at least one mailbox" in r.text
    r = client.post("/login", data={"req": req, "passphrase": PASS, "mailbox": ["work@example.org", "evil@x.test"]},
                    follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"].startswith("https://claude.ai/")
    assert provider.grants["app"] == ["work@example.org"]       # unknown addresses are ignored


def test_settings_page_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("SETTINGS_PAGE", "off")
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    assert client.get("/settings").status_code == 404
    monkeypatch.setattr(server, "PROVIDER", None)



def test_https_cookie_uses_the_host_prefix(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "https://mail.example.com")
    saved = dict(server.pages.HEADERS)
    try:
        client = TestClient(server.build_server(True).streamable_http_app(), base_url="https://mail.example.com")
        r = client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "https://mail.example.com"},
                        follow_redirects=False)
        cookie = r.headers["set-cookie"]
        assert cookie.startswith("__Host-mailmcp_settings=") and "Path=/;" in cookie and "Secure" in cookie
        assert "Open settings" not in client.get("/settings").text      # the session works with the new name
    finally:
        server.pages.HEADERS.clear()
        server.pages.HEADERS.update(saved)
        monkeypatch.setattr(server, "PROVIDER", None)
