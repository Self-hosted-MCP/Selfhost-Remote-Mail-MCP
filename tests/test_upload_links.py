"""One-time upload links: an AI app's code (or the user, in a browser) sends one file, without the passphrase."""
import re
import shutil
import time

import pytest
from starlette.testclient import TestClient

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server

PASS = "web test passphrase"
PDF = b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj\n%%EOF"
EXE = b"MZ\x90\x00" + b"\x00" * 64


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    for f in (server.PREFS_FILE, server.SIGNINS_FILE):
        f.unlink(missing_ok=True)
    shutil.rmtree(server.UPLOADS, ignore_errors=True)
    server._upload_links.clear()
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    yield client
    server._upload_links.clear()
    shutil.rmtree(server.UPLOADS, ignore_errors=True)
    for f in (server.PREFS_FILE, server.SIGNINS_FILE):
        f.unlink(missing_ok=True)
    monkeypatch.setattr(server, "PROVIDER", None)


def link(**args) -> str:
    out = server.upload_link(**args)
    return re.search(r"http://localhost/upload/(\S+)", out)[1]


def test_the_ai_uploads_once_and_the_file_is_waiting(web, mailbox):
    out = server.upload_link(file_name="invoice.pdf", size_mb=0.1)
    assert "curl -sS -F" in out and "works once" in out and "Settings > Capabilities" in out
    token = re.search(r"/upload/(\S+)", out)[1]
    assert token not in str(server._upload_links)                       # only a fingerprint is kept
    r = web.post(f"/upload/{token}", files={"file": ("invoice.pdf", PDF)})
    assert r.status_code == 200 and r.json()["ok"] and r.json()["name"] == "invoice.pdf"
    assert web.post(f"/upload/{token}", files={"file": ("again.pdf", PDF)}).status_code == 410   # used up
    draft = server.draft(subject="x", body="x", attach_upload=["invoice.pdf"])
    assert "invoice.pdf" in draft
    assert server.recent_signins()[0]["where"] == "Upload link: invoice.pdf"


def test_refused_files_can_try_again_a_few_times(web):
    token = link()
    r = web.post(f"/upload/{token}", files={"file": ("setup.exe", EXE)})
    assert r.status_code == 422 and "programs or scripts" in r.json()["error"]
    assert web.post(f"/upload/{token}", files={"file": ("ok.pdf", PDF)}).status_code == 200


def test_bad_expired_and_too_many_links(web, monkeypatch):
    assert web.post("/upload/not-a-real-link", files={"file": ("a.pdf", PDF)}).status_code == 410
    token = link()
    server._upload_links[server.token_key(token)]["expires"] = time.time() - 1
    assert web.post(f"/upload/{token}", files={"file": ("a.pdf", PDF)}).status_code == 410
    server._upload_links.clear()
    for _ in range(server.LINK_MAX_OPEN):
        link()
    with pytest.raises(ToolError, match="already 5 open"):
        link()


def test_checks_before_uploading(web, monkeypatch):
    with pytest.raises(ToolError, match="aren't allowed"):
        server.upload_link(file_name="tool.exe")
    with pytest.raises(ToolError, match="more than the"):
        server.upload_link(file_name="video.mp4", size_mb=40)
    monkeypatch.setenv("ATTACH_MAX_MB", "1")
    token = link()
    r = web.post(f"/upload/{token}", files={"file": ("big.pdf", PDF + b"x" * 1_300_000)})
    assert r.status_code == 413


def test_the_user_can_open_the_link_in_a_browser(web):
    token = link()
    page = web.get(f"/upload/{token}", headers={"accept": "text/html"})
    assert page.status_code == 200 and "Choose a file" in page.text and "Up to 25 MB" in page.text
    assert page.headers["x-frame-options"] == "DENY"
    r = web.post(f"/upload/{token}", files={"file": ("photo.pdf", PDF)},
                 headers={"accept": "text/html", "origin": "http://localhost"})
    assert "photo.pdf is uploaded" in r.text
    r = web.get(f"/upload/{token}", headers={"accept": "text/html"})
    assert r.status_code == 410 and "Ask your AI app for a new one" in r.text
    other = link()
    assert web.post(f"/upload/{other}", files={"file": ("a.pdf", PDF)},
                    headers={"origin": "https://evil.example"}).status_code == 403


def test_links_can_be_turned_off(web, monkeypatch):
    token = link()
    server.set_pref("upload_links", False)
    assert web.post(f"/upload/{token}", files={"file": ("a.pdf", PDF)}).status_code == 404
    with pytest.raises(ToolError, match="turned off"):
        server.upload_link()
    server.set_pref("upload_links", True)
    monkeypatch.setenv("UPLOAD_LINKS", "off")
    with pytest.raises(ToolError, match="turned off"):
        server.upload_link()


def test_not_on_the_computer_version(monkeypatch):
    monkeypatch.setattr(server, "PROVIDER", None)   # stdio: no web server, so no links
    with pytest.raises(ToolError, match="attach_path"):
        server.upload_link()
