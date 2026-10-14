"""The settings the AI may show and change (only six), and the list of changes on the settings page."""
import re
import shutil

import pytest
from starlette.testclient import TestClient

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server


@pytest.fixture(autouse=True)
def clean_state():
    files = (server.PREFS_FILE, server.CHANGES_FILE, server.SIGNATURE, server.SIGNATURE_HTML,
             server.SIGNATURE.with_name("signature.md.old"), server.SIGNATURE_HTML.with_name("signature.html.old"))
    for f in files:
        f.unlink(missing_ok=True)
    shutil.rmtree(server.TEMPLATES, ignore_errors=True)
    shutil.rmtree(server.UPLOADS, ignore_errors=True)
    yield
    for f in files:
        f.unlink(missing_ok=True)
    shutil.rmtree(server.TEMPLATES, ignore_errors=True)
    shutil.rmtree(server.UPLOADS, ignore_errors=True)


def test_settings_shows_what_may_change():
    out = server.settings()
    assert "photo_location: on" in out and "document_details: on" in out and "update_check: off" in out
    assert "signature: none" in out and "device log" in out and "Only the user can change everything else" in out
    assert "device_log:" not in out


def test_switches_and_the_change_list():
    out = server.change_setting("photo_location", "off")
    assert "Remove location from photos turned off" in out and "Tell the user" in out
    assert not server.pref_on("remove_photo_location", "REMOVE_PHOTO_LOCATION")
    server.change_setting("update_check", "on")
    assert server.update_check_on()
    changes = server.recent_changes()
    assert [c["what"] for c in changes] == ["Update check turned on", "Remove location from photos turned off"]
    assert changes[0]["app"] == "An app on this computer"
    with pytest.raises(ToolError, match='"on" or "off"'):
        server.change_setting("document_details", "maybe")


@pytest.mark.parametrize("setting", ["device_log", "send_limit", "mailbox", "allowed_recipients", "passphrase"])
def test_everything_else_is_refused(setting):
    with pytest.raises(ToolError, match="can't be changed by an AI app"):
        server.change_setting(setting, "on")


def test_server_settings_win(monkeypatch):
    monkeypatch.setenv("REMOVE_DOCUMENT_DETAILS", "off")
    with pytest.raises(ToolError, match="Only the user can change"):
        server.change_setting("document_details", "on")
    monkeypatch.setenv("UPDATE_CHECK", "off")
    with pytest.raises(ToolError, match="Only the user"):
        server.change_setting("update_check", "on")


def test_signature_change_keeps_the_old_one():
    server.SIGNATURE_HTML.write_text("<b>Old</b>")
    server.change_setting("signature", "**Alex Rivera**  \nStudio Northwind")
    assert "Alex Rivera" in server.signature()[0]
    assert server.SIGNATURE_HTML.with_name("signature.html.old").read_text() == "<b>Old</b>"
    out = server.change_setting("signature", "off")
    assert server.signature() == ("", "") and "Signature removed" in out


def test_templates_add_change_delete():
    server.change_setting("template", name="Thank You!", value="Subject: Thanks\n---\nHi {{recipient_first_name}},\n\nThanks!")
    t = server.find_template("thank-you")
    assert t["subject"] == "Thanks" and "{{recipient_first_name}}" in t["body"]
    assert "changed" in server.change_setting("template", name="thank-you", value="Subject: Thanks again\n---\nHi")
    server.change_setting("template", name="thank-you", value="delete")
    assert not server.load_templates() and (server.TEMPLATES / "thank-you.md.old").exists()
    with pytest.raises(ToolError, match="needs a name"):
        server.change_setting("template", name="!!!", value="x")


def test_delete_an_upload():
    server.save_upload("notes.txt", b"hello")
    assert "notes.txt deleted" in server.change_setting("delete_upload", "notes.txt")
    assert not server.list_uploads()


def test_changes_show_on_the_settings_page(monkeypatch):
    server.change_setting("photo_location", "off")
    monkeypatch.setenv("LOGIN_PASSPHRASE", "web test passphrase")
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    client.post("/settings/login", data={"passphrase": "web test passphrase"}, headers={"origin": "http://localhost"})
    page = client.get("/settings").text
    assert "Changes by AI apps" in page and "Remove location from photos turned off" in page
    assert 'href="#changes"' in page
    monkeypatch.setattr(server, "PROVIDER", None)
