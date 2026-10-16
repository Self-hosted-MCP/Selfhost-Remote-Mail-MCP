# SPDX-License-Identifier: AGPL-3.0-only
"""The Claude Desktop extension (.mcpb): the passphrase from Claude's form, the settings page it starts (faked:
nothing is installed or started), its messages, and the file the release builds."""
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from selfhost_remote_mail_mcp import server
from selfhost_remote_mail_mcp.server import ToolError

from test_service import mac  # noqa: F401  (the fake Mac with launchctl recorded)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def fresh(monkeypatch):
    """No passphrase saved yet, the extension's form filled in, and nothing running on the port."""
    server.write_settings({}, drop=("LOGIN_HASH", "LOGIN_PASSPHRASE"))
    monkeypatch.setenv("MAIL_EXTENSION_PASSPHRASE", "a long passphrase here")
    monkeypatch.setenv("MAIL_EXTENSION_BACKGROUND", "false")
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: False)
    started, real = [], subprocess.Popen

    def popen(cmd, *args, **kw):   # only the settings page is faked; other commands (the keychain) run as usual
        if cmd[-1] != "serve":
            return real(cmd, *args, **kw)
        started.append((cmd, kw))
        return type("P", (), {"terminate": lambda self: None})()
    monkeypatch.setattr(subprocess, "Popen", popen)
    yield started
    server.write_settings({}, drop=("LOGIN_HASH", "PORT"))


def test_the_passphrase_from_the_form_is_saved_once(fresh, capsys):
    server.extension_start()
    assert server.passphrase_ok("a long passphrase here")
    assert "MAIL_EXTENSION_PASSPHRASE" not in server.os.environ   # not passed on to the settings page it starts
    server.os.environ["MAIL_EXTENSION_PASSPHRASE"] = "a different one, typed later"
    server.extension_start()
    assert server.passphrase_ok("a long passphrase here")   # one chosen before (setup, or the first time) stays
    assert capsys.readouterr().out == ""   # stdout is Claude's: nothing printed there


def test_unticked_the_settings_page_runs_only_with_claude(fresh):
    server.extension_start()
    (cmd, kw), = fresh
    assert cmd[-1] == "serve" and kw["env"]["MAIL_STOP_WITH_PARENT"] == "1" and kw["stdin"] == subprocess.PIPE
    assert "MAIL_EXTENSION_PASSPHRASE" not in kw["env"]


def test_a_short_passphrase_starts_nothing(fresh, monkeypatch, capsys):
    monkeypatch.setenv("MAIL_EXTENSION_PASSPHRASE", "short")
    server.extension_start()
    out = capsys.readouterr()
    assert fresh == [] and "12 or more characters" in out.err and out.out == ""
    assert not server.read_env_file().get("LOGIN_HASH")


def test_a_running_settings_page_is_left_alone(fresh, monkeypatch):
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: True)
    server.extension_start()
    assert fresh == []


def test_ticked_it_starts_at_login_like_setup(fresh, mac, monkeypatch, capsys):
    ran, state = mac
    monkeypatch.setenv("MAIL_EXTENSION_BACKGROUND", "true")
    server.write_settings({}, drop=("LOGIN_HASH",))
    monkeypatch.setattr(server, "local_health", lambda port, timeout=1.0, same=False: False)
    server.extension_start()
    assert server.service_installed() and server.service_program() and fresh == []
    assert capsys.readouterr().out == ""
    # Claude Desktop replaced the extension, so the program the login item runs is gone: written again
    monkeypatch.setattr(server, "service_program", lambda: "/gone/selfhost-remote-mail-mcp")
    ran.clear()
    server.extension_start()
    assert ("launchctl", "bootstrap", "gui/501", str(server.service_file())) in ran
    # installed and fine, only not running yet: just started
    monkeypatch.setattr(server, "service_program", lambda: str(ROOT / "pyproject.toml"))   # any file that exists
    ran.clear()
    server.extension_start()
    assert ran and all(c[1] != "bootout" for c in ran)
    # unticked later: the login item an extension added goes, so removing the extension leaves nothing behind
    monkeypatch.setenv("MAIL_EXTENSION_BACKGROUND", "false")
    monkeypatch.setattr(server, "service_program", lambda: "/x/Claude Extensions/local.mcpb.y/.venv/bin/z")
    server.extension_start()
    assert not server.service_installed() and len(fresh) == 1   # the page now runs only with Claude


def test_unticked_a_login_item_from_setup_stays(fresh, mac, monkeypatch):
    server.service_install()
    server.extension_start()
    assert server.service_installed()
    server.run_service(["remove"])


def test_the_login_item_names_its_program(mac):
    server.service_install()
    assert server.service_program() == server.service_command()[0]
    server.run_service(["remove"])
    assert server.service_program() == ""


def test_messages_point_to_the_settings_page(monkeypatch):
    monkeypatch.setattr(server, "EXTENSION", True)
    monkeypatch.setattr(server, "all_accounts", lambda cfg=None: [])
    server.write_settings({"LOGIN_HASH": server.hash_passphrase("a long passphrase here")})
    with pytest.raises(ToolError, match=r"settings page: http://localhost:8765/settings"):
        server.active_accounts()
    server.write_settings({}, drop=("LOGIN_HASH",))
    with pytest.raises(ToolError, match="Settings > Extensions"):
        server.active_accounts()
    monkeypatch.setattr(server, "update_status", lambda: {"newer": True, "latest": "v9.0.0", "current": "0.1.0", "url": "u"})
    assert "download the new .mcpb file" in server.update_line()
    monkeypatch.setattr(server, "EXTENSION", False)
    assert ".mcpb" not in server.update_line()


def test_the_extension_file(tmp_path):
    spec = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    with zipfile.ZipFile(build.build(tmp_path)) as zf:
        names = zf.namelist()
        manifest = json.loads(zf.read("manifest.json"))
    assert manifest["version"] == build.version()
    assert manifest["server"]["type"] == "uv" and manifest["server"]["entry_point"] in names
    assert manifest["server"]["mcp_config"]["args"][-1] == "extension"
    for needed in ("pyproject.toml", "uv.lock", "icon.png", "LICENSE", "NOTICE", "CHANGELOG.md",
                   "src/selfhost_remote_mail_mcp/server.py", "src/selfhost_remote_mail_mcp/locales/pt-BR.json"):
        assert needed in names
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)
    import asyncio
    real = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {t["name"] for t in manifest["tools"]} <= real   # the tools listed in Claude's install screen exist
    assert set(manifest["user_config"]) == {"passphrase", "keep_running"}
    assert manifest["user_config"]["passphrase"]["sensitive"]
