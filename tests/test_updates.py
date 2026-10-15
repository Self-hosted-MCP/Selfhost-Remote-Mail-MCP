"""Update check (opt-in), the update command (releases only), and the About section."""
import json
import subprocess

import pytest

from selfhost_remote_mail_mcp import server


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    if server.UPDATE_FILE.exists():
        server.UPDATE_FILE.unlink()
    monkeypatch.setattr(server, "current_version", lambda: "0.2.0")


def release(tag="v0.3.0"):
    return lambda: {"tag": tag, "url": f"https://github.com/x/releases/tag/{tag}"}


def test_versions_compare_as_numbers():
    assert server.version_tuple("v0.10.0") > server.version_tuple("0.9.9")
    assert server.version_tuple("v1.0.0-beta") == (-1,)          # anything but a plain release counts lowest


def test_no_check_unless_turned_on(monkeypatch):
    def boom():
        raise AssertionError("must not contact GitHub")
    monkeypatch.setattr(server, "fetch_latest_release", boom)
    assert server.update_status() is None and server.update_line() == ""


def test_check_finds_a_newer_release_and_caches_it(monkeypatch):
    monkeypatch.setenv("UPDATE_CHECK", "on")
    calls = []
    monkeypatch.setattr(server, "fetch_latest_release", lambda: calls.append(1) or release()())
    assert server.update_status()["newer"]
    server.update_status()
    assert len(calls) == 1                                         # at most once a day
    assert "Update available: v0.3.0" in server.update_line()
    assert "Update available: v0.3.0" in server.accounts()


def test_a_failed_check_is_quiet(monkeypatch):
    monkeypatch.setenv("UPDATE_CHECK", "on")
    def down():
        raise OSError("offline")
    monkeypatch.setattr(server, "fetch_latest_release", down)
    assert server.update_status() == {"current": "0.2.0", "latest": "", "url": "", "newer": False}


def test_update_command_installs_the_release_tag(monkeypatch, capsys):
    monkeypatch.setattr(server, "fetch_latest_release", release("v0.3.0"))
    ran = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: ran.append(args) or subprocess.CompletedProcess(args, 0))
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv")
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None if name == "fpdf" else real(name, *a))
    server.run_update()
    assert ran == [["/usr/bin/uv", "tool", "install", "--force",
                    "git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP@v0.3.0"]]
    assert "Updated to v0.3.0" in capsys.readouterr().out
    monkeypatch.setattr(importlib.util, "find_spec", real)   # with the add-on extras, they're kept
    pytest.importorskip("fpdf")
    server.run_update()
    assert ran[-1][-1] == ("selfhost-remote-mail-mcp[addons] @ "
                           "git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP@v0.3.0")


def test_update_command_does_nothing_when_current(monkeypatch, capsys):
    monkeypatch.setattr(server, "fetch_latest_release", release("v0.2.0"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("must not install"))
    server.run_update()
    assert "Up to date" in capsys.readouterr().out


def test_about_section_shows_version_update_and_changelog(monkeypatch):
    monkeypatch.setenv("UPDATE_CHECK", "on")
    monkeypatch.setattr(server, "fetch_latest_release", release("v0.3.0"))
    about = {"version": "0.2.0", "update": server.update_status(), "changelog": server.changelog_html()}
    html = server.pages.settings("c", [], [], None, 5, False, about)
    assert "Version <b>0.2.0</b>" in html and "Update available: v0.3.0" in html
    assert "What&#x27;s new" in html or "What's new" in html
    assert "<h3>" in about["changelog"]
    off = server.pages.settings("c", [], [], None, 5, False, {"version": "0.2.0", "update": None, "changelog": ""})
    assert "Update checks are off" in off
