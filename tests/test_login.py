"""The web login: tokens kept only as fingerprints, the client cap and the login page."""
import asyncio
import json
import time

from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

from selfhost_remote_mail_mcp import server


def new_provider():
    if server.OAUTH_FILE.exists():
        server.OAUTH_FILE.unlink()
    return server.PassphraseOAuth("https://mail.example.com", ["claude.ai"])


def client(cid="c1", name="Claude"):
    return OAuthClientInformationFull(client_id=cid, client_name=name, client_id_issued_at=1,
                                      redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")])


def test_tokens_are_stored_only_as_fingerprints():
    p = new_provider()
    tok = p.issue("c1", ["mail"], None)
    saved = server.OAUTH_FILE.read_text()
    assert tok.access_token not in saved and tok.refresh_token not in saved
    assert server.token_key(tok.access_token) in saved
    loaded = asyncio.run(p.load_access_token(tok.access_token))
    assert loaded and loaded.token == tok.access_token
    assert asyncio.run(p.load_access_token(server.token_key(tok.access_token))) is None   # the fingerprint itself is useless
    reloaded = server.PassphraseOAuth("https://mail.example.com", ["claude.ai"])           # survives a restart
    assert asyncio.run(reloaded.load_access_token(tok.access_token))


def test_refresh_works_once():
    p = new_provider()
    tok = p.issue("c1", ["mail"], None)
    c = client()
    r = asyncio.run(p.load_refresh_token(c, tok.refresh_token))
    new = asyncio.run(p.exchange_refresh_token(c, r, []))
    assert new.access_token != tok.access_token
    assert asyncio.run(p.load_refresh_token(c, tok.refresh_token)) is None


def test_client_list_is_capped():
    p = new_provider()
    for i in range(p.MAX_CLIENTS + 5):   # all registered just now, so none is cleaned away as an old attempt
        c = client(f"c{i}")
        c.client_id_issued_at = int(time.time()) + i
        asyncio.run(p.register_client(c))
    assert len(json.loads(server.OAUTH_FILE.read_text())["clients"]) == p.MAX_CLIENTS


def test_login_page_names_the_app_and_is_locked_down(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", "a good long passphrase")
    p = new_provider()
    asyncio.run(p.register_client(client(name="Claude <script>")))
    params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                 redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                 redirect_uri_provided_explicitly=True)
    req = asyncio.run(p.authorize(client(), params)).split("req=")[1]
    page = server.login_page(p, req)
    html = page.body.decode()
    assert "Claude &lt;script&gt;" in html and "claude.ai" in html and "<script>" not in html
    assert page.headers["x-frame-options"] == "DENY" and page.headers["cache-control"] == "no-store"
    assert "s17sh70x2jfl031ag" in html
    assert "expired" in server.login_page(p, "unknown").body.decode()
    assert p.complete_login(req, "wrong", ["me@example.com"]) is None
    assert p.complete_login(req, "a good long passphrase", ["me@example.com"]).startswith("https://claude.ai/")
    assert p.grants["c1"] == ["me@example.com"]



def test_access_keys_are_short_lived_and_only_for_this_server():
    p = new_provider()
    assert p.ACCESS_TTL <= 3600
    ours = p.issue("c1", ["mail"], "https://mail.example.com/mcp")
    other = p.issue("c1", ["mail"], "https://some-other-server.example/mcp")
    none = p.issue("c1", ["mail"], None)
    assert asyncio.run(p.load_access_token(ours.access_token))
    assert asyncio.run(p.load_access_token(none.access_token))
    assert asyncio.run(p.load_access_token(other.access_token)) is None


def test_send_permission_is_saved_at_login(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", "a good long passphrase")
    p = new_provider()
    for cid, allow in (("a", True), ("b", False)):
        c = client(cid)
        asyncio.run(p.register_client(c))
        params = AuthorizationParams(state="s", scopes=["mail"], code_challenge="x" * 43,
                                     redirect_uri=AnyUrl("https://claude.ai/api/mcp/auth_callback"),
                                     redirect_uri_provided_explicitly=True)
        req = asyncio.run(p.authorize(c, params)).split("req=")[1]
        p.complete_login(req, "a good long passphrase", ["me@example.com"], allow_send=allow)
    assert p.senders == {"a"}
    assert server.PassphraseOAuth("https://mail.example.com", ["claude.ai"]).senders == {"a"}   # saved


def test_login_page_warns_about_localhost_apps():
    page = server.pages.login("Some app", "localhost", "r", [("me@example.com", "full", "")])
    assert "localhost" in page and "your own computer" in page and 'name="allow_send"' in page
    page = server.pages.login("Claude", "claude.ai", "r", [("me@example.com", "draft", "")])
    assert "your own computer" not in page and 'name="allow_send"' not in page
