"""The web pages over real HTTP requests: settings login, sessions, forged forms, the icon."""
import asyncio
import json
import re
import time

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


def test_remember_this_device_lasts_90_days_and_survives_a_restart(web, monkeypatch):
    client, _ = web
    r = client.post("/settings/login", data={"passphrase": PASS, "remember": "yes"},
                    headers={"origin": "http://localhost"}, follow_redirects=False)
    cookie = r.headers["set-cookie"]
    assert f"Max-Age={90 * 24 * 3600}" in cookie
    token = cookie.split("=", 1)[1].split(";")[0]
    saved = server.SESSIONS_FILE.read_text()
    assert token not in saved and server.token_key(token) in saved          # only a fingerprint is stored
    server._sessions.clear()                                                 # a restart
    monkeypatch.setattr(server, "_sessions_loaded", False)
    assert "Open settings" not in client.get("/settings").text
    monkeypatch.setenv("LOGIN_PASSPHRASE", "a brand new passphrase")         # a new passphrase signs it out
    assert "Open settings" in client.get("/settings").text


def test_without_remember_the_sign_in_ends_with_the_browser(web):
    client, _ = web
    r = client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"},
                    follow_redirects=False)
    token = r.headers["set-cookie"].split("=", 1)[1].split(";")[0]
    assert "Max-Age" not in r.headers["set-cookie"]
    assert server.token_key(token) not in server.SESSIONS_FILE.read_text()
    assert 'name="remember" value="yes" checked' in server.pages.settings_login()


def test_sign_out_forgets_a_remembered_device(web):
    client, _ = web
    client.post("/settings/login", data={"passphrase": PASS, "remember": "yes"}, headers={"origin": "http://localhost"})
    csrf = re.search(r'name="csrf" value="([^"]+)"', client.get("/settings").text)[1]
    client.post("/settings/logout", data={"csrf": csrf}, headers={"origin": "http://localhost"})
    assert server.SESSIONS_FILE.read_text() == "{}" or "Open settings" in client.get("/settings").text
    assert "Open settings" in client.get("/settings").text


IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
          "Version/18.0 Mobile/15E148 Safari/604.1")


@pytest.fixture
def fresh_log():
    for f in (server.SIGNINS_FILE, server.PREFS_FILE):
        f.unlink(missing_ok=True)
    yield
    for f in (server.SIGNINS_FILE, server.PREFS_FILE):
        f.unlink(missing_ok=True)


def test_device_names():
    assert server.device_name(IPHONE) == "iPhone · Safari"
    mac_chrome = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    assert server.device_name(mac_chrome) == "Mac · Chrome"
    assert server.device_name("") == "Unknown device"


def test_device_log_shows_devices_and_sign_ins(web, fresh_log):
    client, _ = web
    client.post("/settings/login", data={"passphrase": "wrong one!"}, headers={"origin": "http://localhost"})
    client.post("/settings/login", data={"passphrase": PASS, "remember": "yes"},
                headers={"origin": "http://localhost", "user-agent": IPHONE, "x-forwarded-for": "203.0.113.7"})
    page = client.get("/settings").text
    assert "iPhone · Safari" in page and "This device" in page and "from 203.0.113.7" in page
    assert "Wrong passphrase" in page and "Sign-ins, last 7 days" in page
    events = server.recent_signins()
    assert [e["ok"] for e in events] == [True, False] and events[0]["where"] == "Settings page"


def test_sign_in_history_keeps_7_days(fresh_log):
    old = {"time": time.time() - 8 * 24 * 3600, "ok": True, "where": "x", "ip": "1", "device": "d"}
    new = {**old, "time": time.time() - 3600}
    server.private_write(server.SIGNINS_FILE, json.dumps([new, old]))
    assert server.recent_signins() == [new]


def test_sign_out_another_device(web, fresh_log):
    client, _ = web
    other = TestClient(client.app, base_url="http://localhost")
    other.post("/settings/login", data={"passphrase": PASS, "remember": "yes"},
               headers={"origin": "http://localhost", "user-agent": IPHONE})
    csrf, page = sign_in(client)
    other_id = next(d["id"] for d in server.signed_in_devices() if d["device"] == "iPhone · Safari")
    r = client.post("/settings/device", data={"csrf": csrf, "action": "signout", "id": other_id},
                    headers={"origin": "http://localhost"})
    assert "That device is signed out" in r.text
    assert "Open settings" in other.get("/settings").text and "Open settings" not in client.get("/settings").text


def test_device_log_can_be_turned_off(web, fresh_log, monkeypatch):
    client, _ = web
    client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost", "user-agent": IPHONE})
    csrf = re.search(r'name="csrf" value="([^"]+)"', client.get("/settings").text)[1]
    r = client.post("/settings/device", data={"csrf": csrf, "action": "log_off"}, headers={"origin": "http://localhost"})
    assert "history is deleted" in r.text and "Turn on the device log" in r.text
    assert not server.SIGNINS_FILE.exists() and "iPhone · Safari" not in r.text
    client.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost", "user-agent": IPHONE})
    assert not server.SIGNINS_FILE.exists()
    csrf = re.search(r'name="csrf" value="([^"]+)"', client.get("/settings").text)[1]   # a new sign-in, a new token
    client.post("/settings/device", data={"csrf": csrf, "action": "log_on"}, headers={"origin": "http://localhost"})
    assert server.device_log_on()
    monkeypatch.setenv("DEVICE_LOG", "off")
    assert not server.device_log_on() and "DEVICE_LOG=off" in client.get("/settings").text


def test_ai_app_logins_are_logged(web, monkeypatch, fresh_log):
    client, provider = web
    c = OAuthClientInformationFull(client_id="app2", client_name="Claude", client_id_issued_at=1,
                                   redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")])
    asyncio.run(provider.register_client(c))
    params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                 redirect_uri_provided_explicitly=True)
    req = asyncio.run(provider.authorize(c, params)).split("req=")[1]
    client.post("/login", data={"req": req, "passphrase": PASS, "mailbox": ["me@example.com"]}, follow_redirects=False)
    assert server.recent_signins()[0]["where"] == "AI app login: Claude"


def test_connected_apps_only_lists_apps_that_logged_in(web):
    client, provider = web
    def register(cid, issued):
        c = OAuthClientInformationFull(client_id=cid, client_name="Claude", client_id_issued_at=issued,
                                       redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")])
        asyncio.run(provider.register_client(c))
        return c
    tried = register("tried", int(time.time()))
    done = register("done", int(time.time()))
    params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                 redirect_uri_provided_explicitly=True)
    req = asyncio.run(provider.authorize(done, params)).split("req=")[1]
    client.post("/login", data={"req": req, "passphrase": PASS, "mailbox": ["me@example.com"]}, follow_redirects=False)
    csrf, page = sign_in(client)
    assert page.count("Choose mailboxes") == 1 and 'value="done"' in page and 'value="tried"' not in page
    provider.clients["tried"].client_id_issued_at = int(time.time()) - 7200   # an attempt from 2 hours ago
    register("later", int(time.time()))
    assert "tried" not in provider.clients and "done" in provider.clients and "later" in provider.clients


def test_login_page_and_accounts_point_to_the_settings_page(web, monkeypatch):
    client, provider = web
    c = OAuthClientInformationFull(client_id="links", client_name="Claude", client_id_issued_at=int(time.time()),
                                   redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")])
    asyncio.run(provider.register_client(c))
    params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                 redirect_uri_provided_explicitly=True)
    req = asyncio.run(provider.authorize(c, params)).split("req=")[1]
    assert "manage everything" in client.get(f"/login?req={req}").text and "http://localhost/settings" in client.get(f"/login?req={req}").text
    out = server.accounts()
    assert "Settings page for the user: http://localhost/settings (files to attach: http://localhost/upload)" in out
