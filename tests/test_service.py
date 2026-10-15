# SPDX-License-Identifier: AGPL-3.0-only
"""setup on a computer: the passphrase, the web version starting by itself at login (faked: nothing is
installed), the service command, and the AI pointing to the local pages."""
import plistlib
import subprocess

import pytest

from selfhost_remote_mail_mcp import server
from selfhost_remote_mail_mcp.server import ToolError

REAL_LOCAL_HEALTH = server.local_health   # before the tests' stand-in replaces it


@pytest.fixture
def mac(monkeypatch):
    """A Mac where every launchctl call is recorded, and the web version answers once it's started."""
    monkeypatch.setattr(server.sys, "platform", "darwin")
    monkeypatch.setattr(server.os, "getuid", lambda: 501, raising=False)
    ran, state = [], {"running": False, "fail": False}

    def run(*cmd):
        ran.append(cmd)
        if cmd[:2] == ("launchctl", "print"):
            return 0 if state["running"] else 113
        if cmd[1] in ("bootstrap", "kickstart"):
            state["running"] = not state["fail"]
        if cmd[1] == "bootout":
            state["running"] = False
        return 1 if state["fail"] else 0

    monkeypatch.setattr(server, "_run", run)
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: state["running"])
    monkeypatch.setattr(server, "port_free", lambda port: True)
    monkeypatch.setattr(server, "wait_for_server", lambda port, seconds=20: state["running"])
    server.write_settings({"LOGIN_HASH": server.hash_passphrase("a long passphrase here")})
    yield ran, state
    server.write_settings({}, drop=("LOGIN_HASH", "PORT", "SCHEDULED_SEND", "ADDON_JOBS"))


def test_install_writes_a_login_item_and_starts_it(mac):
    ran, state = mac
    assert server.service_install() and state["running"]
    plist = plistlib.loads(server.service_file().read_bytes())
    assert plist["Label"] == "com.selfhost-remote-mail-mcp" and plist["ProgramArguments"][-1] == "serve"
    assert plist["RunAtLoad"] and plist["KeepAlive"] == {"SuccessfulExit": False}
    assert plist["EnvironmentVariables"]["MAIL_CONFIG_DIR"] == str(server.CONFIG_DIR)   # same folders as here
    assert "PASSWORD" not in server.service_file().read_text() and "LOGIN" not in server.service_file().read_text()
    assert ("launchctl", "bootstrap", "gui/501", str(server.service_file())) in ran
    server.service_install()   # again: loads the rewritten file instead of restarting the old one
    assert ran[-2:] == [("launchctl", "bootout", "gui/501/com.selfhost-remote-mail-mcp"),
                        ("launchctl", "bootstrap", "gui/501", str(server.service_file()))]


def test_a_web_version_started_another_way_is_left_alone(mac, monkeypatch, capsys):
    ran, state = mac
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: True)   # your own systemd service
    monkeypatch.setattr(server, "port_free", lambda port: False)
    assert server.service_install() and not server.service_installed()
    assert "already runs at http://localhost:8765" in capsys.readouterr().out
    assert "PORT" not in server.read_env_file() and ran == []   # its port and settings untouched


def test_the_passphrase_must_be_in_the_settings_file(mac, monkeypatch):
    server.write_settings({}, drop=("LOGIN_HASH",))
    monkeypatch.setenv("LOGIN_PASSPHRASE", "only in this terminal")   # the background copy wouldn't see it
    assert not server.service_install() and not server.service_installed()


def test_only_this_copy_counts_for_the_local_pages(monkeypatch):
    import io

    class Resp(io.BytesIO):
        def __init__(self, copy):
            super().__init__(b"ok")
            self.headers = {"X-Mail-MCP-Copy": copy}
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(server, "local_health", REAL_LOCAL_HEALTH)   # the real one, with a fake answer
    monkeypatch.setattr(server, "PROVIDER", None)
    monkeypatch.setattr(server.urllib.request, "urlopen", lambda url, timeout: Resp("someone-else"))
    assert server.local_health(8765) and not server.local_health(8765, same=True) and server.pages_url() == ""
    monkeypatch.setattr(server.urllib.request, "urlopen", lambda url, timeout: Resp(server.copy_id()))
    assert server.pages_url() == "http://localhost:8765"


def test_systemd_paths_are_quoted(mac, monkeypatch):
    monkeypatch.setattr(server.sys, "platform", "linux")
    monkeypatch.setattr(server, "service_command", lambda: ["/home/a b/100%/$bin", "serve"])
    assert 'ExecStart="/home/a b/100%%/$$bin" "serve"' in server.service_write().read_text()


def test_install_needs_a_passphrase_and_a_free_port(mac, monkeypatch, capsys):
    server.write_settings({}, drop=("LOGIN_HASH",))
    assert not server.service_install() and not server.service_installed()   # it wouldn't start without one
    server.write_settings({"LOGIN_HASH": server.hash_passphrase("a long passphrase here")})
    monkeypatch.setattr(server, "port_free", lambda port: port != 8765)   # Docker already uses 8765
    assert server.service_install()
    assert server.read_env()["PORT"] == "8766" and "Port 8765 is taken" in capsys.readouterr().out
    server.run_service(["remove"])
    server.write_settings({}, drop=("PORT",))
    server.run_service(["install"])   # the address it names is the new port's
    assert "Settings page: http://localhost:8766/settings" in capsys.readouterr().out


def test_no_automatic_start_on_other_systems(monkeypatch, capsys):
    monkeypatch.setattr(server.sys, "platform", "win32")
    assert not server.service_install() and "Keep it running in the background" in capsys.readouterr().out


def test_linux_gets_a_user_service(mac, monkeypatch):
    ran, _ = mac
    monkeypatch.setattr(server.sys, "platform", "linux")
    server.service_install()
    unit = server.service_file().read_text()
    assert "ExecStart=" in unit and '"serve"' in unit and "Restart=on-failure" in unit and "WantedBy=default.target" in unit
    assert ("systemctl", "--user", "enable", "--now", "selfhost-remote-mail-mcp.service") in ran


def test_service_command(mac, capsys):
    ran, state = mac
    server.run_service(["status"])
    assert "Not installed. Not running." in capsys.readouterr().out
    with pytest.raises(SystemExit, match="isn't installed"):
        server.run_service(["restart"])
    server.run_service(["install"])
    assert "Settings page: http://localhost:8765/settings" in capsys.readouterr().out
    server.run_service(["stop"])
    assert not state["running"]
    server.run_service(["start"])
    assert state["running"] and "Running at http://localhost:8765" in capsys.readouterr().out
    server.run_service(["remove"])
    assert not server.service_installed() and not state["running"] and "Your settings and mailboxes are kept" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="Use:"):
        server.run_service(["explode"])


def test_setup_asks_the_passphrase_and_about_another_copy(mac, monkeypatch, capsys):
    server.write_settings({}, drop=("LOGIN_HASH",))
    answers = iter(["a long passphrase here", "a long passphrase here"])
    monkeypatch.setattr(server.getpass, "getpass", lambda prompt="": next(answers))
    monkeypatch.setattr(server, "ask", lambda q, default="": "y")   # yes, a server already uses these mailboxes
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    server.setup([])
    cfg = server.read_env()
    assert server.passphrase_ok("a long passphrase here") and cfg["SCHEDULED_SEND"] == "off" and cfg["ADDON_JOBS"] == "off"
    assert opened == ["http://localhost:8765/settings"] and "Add your mailbox on the settings page" in capsys.readouterr().out
    monkeypatch.setattr(server, "ask", lambda q, default="": pytest.fail("asked again"))
    server.setup([])   # the second time it asks nothing


def test_a_second_copy_runs_no_add_on_jobs(monkeypatch):
    started = []
    monkeypatch.setattr(server, "MODE", "serve")
    monkeypatch.setattr(server, "_jobs_started", False)
    monkeypatch.setattr(server, "ADDON_JOBS", [{"name": "x"}])
    monkeypatch.setattr(server.threading, "Thread", lambda **k: type("T", (), {"start": lambda s: started.append(1)})())
    monkeypatch.setenv("ADDON_JOBS", "off")
    server.start_jobs()
    assert started == []
    monkeypatch.setenv("ADDON_JOBS", "on")
    server.start_jobs()
    assert started == [1]


def test_update_restarts_the_web_version(mac, monkeypatch, capsys):
    server.service_install()
    monkeypatch.setattr(server, "fetch_latest_release", lambda: {"tag": "v99.0.0", "url": "u"})
    monkeypatch.setattr(subprocess, "run", lambda args, **k: subprocess.CompletedProcess(args, 0))
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv")
    ran, _ = mac
    server.run_update()
    assert ran[-1][:3] == ("launchctl", "kickstart", "-k") and "The web version restarted" in capsys.readouterr().out


def test_the_ai_on_this_computer_points_to_the_local_pages(monkeypatch):
    monkeypatch.setattr(server, "PROVIDER", None)   # an AI app's own copy (stdio)
    with pytest.raises(ToolError, match=r"attach_path\)\.$"):   # no web version running: no page to name
        server.upload_link()
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: True)
    with pytest.raises(ToolError, match="upload it on http://localhost:8765/upload"):
        server.upload_link()
    assert "Settings page for the user: http://localhost:8765/settings" in server.accounts()
    assert server.AddonAPI("caldav").setup_link() == "http://localhost:8765/settings/addon/caldav"
