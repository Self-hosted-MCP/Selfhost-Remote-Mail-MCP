"""Add-ons: loading, the API they get, the checks that still apply, and the example add-ons."""
import email
import itertools
from email.policy import default as POLICY
from pathlib import Path

import pytest

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "addons"
_n = itertools.count()


def write_addon(tmp_path, body: str) -> str:
    """A fresh add-on file with a unique name (tools registered by add-ons stay for the whole test run)."""
    name = f"t{next(_n)}"
    (tmp_path / f"{name}.py").write_text(body.replace("NAME", name))
    return name


def draft_id(out: str) -> str:
    return out.split("ID: ")[1].split()[0]


def call(tool: str, **args):
    """Run a tool an add-on registered, as the server would."""
    return server.mcp._tool_manager.get_tool(tool).fn(**args)


def test_an_addon_adds_a_tool(tmp_path):
    name = write_addon(tmp_path, '''"""Test add-on."""
def setup(api):
    @api.tool(api.READ)
    def NAME_ping() -> str:
        """Say pong."""
        return "pong"
''')
    assert server.load_addons(name, tmp_path) == [name]
    assert f"{name}_ping" in server.TOOL_NAMES and server.LOADED_ADDONS[name] == "Test add-on."
    assert call(f"{name}_ping") == "pong"
    assert f"Add-ons: " in server.accounts() and f"{name} (Test add-on.)" in server.accounts()


@pytest.mark.parametrize("body,error", [
    ('def setup(api):\n    @api.tool(api.READ)\n    def draft() -> str:\n        """x"""\n        return ""\n', "already exists"),
    ("x = 1\n", r"setup\(api\)"),
    ('def setup(api):\n    api.setting("OTHER_KEY")\n', "must start with"),
    ('def setup(api):\n    api.internal_header("Subject")\n', "must start with X-"),
])
def test_bad_addons_are_refused(tmp_path, body, error):
    with pytest.raises(RuntimeError, match=error):
        server.load_addons(write_addon(tmp_path, body), tmp_path)


def test_bad_names_and_missing_files(tmp_path):
    with pytest.raises(RuntimeError, match="lowercase"):
        server.load_addons("../evil", tmp_path)
    with pytest.raises(RuntimeError, match="doesn't exist"):
        server.load_addons("nothere", tmp_path)


def test_settings_come_from_the_environment_and_the_settings_file(monkeypatch):
    api = server.AddonAPI("demo")
    assert api.setting("DEMO_KEY", "default") == "default"
    monkeypatch.setenv("DEMO_KEY", "from-env")
    assert api.setting("DEMO_KEY") == "from-env"
    monkeypatch.delenv("DEMO_KEY")
    original = server.ENV_FILE.read_text()
    try:
        server.ENV_FILE.write_text(original + "DEMO_KEY=from-file\n")
        assert api.setting("DEMO_KEY") == "from-file"
    finally:
        server.ENV_FILE.write_text(original)


def test_edit_draft_add_file_and_the_sent_copy(tmp_path, mailbox):
    name = write_addon(tmp_path, '''
HEADER = "X-NAME-Files"
def setup(api):
    api.internal_header(HEADER)

    @api.tool(api.WRITE)
    def NAME_attach(draft_id: str) -> str:
        """Attach a report."""
        def change(msg):
            api.add_file(msg, "report.csv", "text/csv", b"a,b\\n1,2\\n", clean=False)
            msg[HEADER] = "report.csv"
        return api.edit_draft(draft_id, change)

    def trim(copy, headers):
        if headers.get(HEADER):
            for part in list(copy.iter_attachments()):
                copy.get_payload().remove(part)
        return copy
    api.on_sent_copy(trim)
''')
    server.load_addons(name, tmp_path)
    d = draft_id(server.draft(to=["sam@example.org"], subject="Report", body="Here."))
    new = call(f"{name}_attach", draft_id=d)
    raw = list(mailbox["Drafts"].values())[-1]
    assert b"report.csv" in raw and f"X-{name}-Files".encode() in raw
    new = server.draft(edit=new, body="Here it is, edited.").split("ID: ")[1].split()[0]   # editing keeps both
    raw = list(mailbox["Drafts"].values())[-1]
    assert b"report.csv" in raw and f"X-{name}-Files".encode() in raw
    server.send_email(new)
    sent = email.message_from_bytes(server.smtplib.SMTP_SSL.sent[-1].as_bytes(), policy=POLICY)
    assert [p.get_filename() for p in sent.iter_attachments()] == ["report.csv"]     # the receiver gets the file
    assert sent.get(f"X-{name}-Files") is None                                       # the bookkeeping header doesn't leave
    copy = email.message_from_bytes(list(mailbox["Sent"].values())[-1], policy=POLICY)
    assert list(copy.iter_attachments()) == []                                       # the Sent copy was trimmed


def test_add_file_still_refuses_programs(mailbox):
    api = server.AddonAPI("x")
    d = draft_id(server.draft(subject="x", body="x"))
    with pytest.raises(ToolError, match="programs or scripts"):
        api.edit_draft(d, lambda msg: api.add_file(msg, "setup.exe", "application/octet-stream", b"MZ\x90\x00"))


def test_edit_draft_respects_read_only_mailboxes(monkeypatch, mailbox):
    monkeypatch.setenv("MAIL_MODE", "read")
    with pytest.raises(ToolError):
        server.AddonAPI("x").edit_draft("Drafts#1", lambda m: None)


def test_the_example_and_library_addons(mailbox, monkeypatch):
    monkeypatch.setenv("CALENDAR_INVITE_ORGANIZER", "me@example.com")
    server.load_addons("hello,calendar_invite", EXAMPLES)
    assert server.LOADED_ADDONS["hello"].startswith("Says hello")
    assert call("hello", name="Sam") == "Hello, Sam!"
    d = draft_id(server.draft(to=["sam@example.org"], subject="Meet", body="See you."))
    out = call("add_invite", draft_id=d, title="Coffee, then work", start="2026-10-20T15:00:00+01:00", minutes=45)
    assert "invite.ics" in out and "Nothing was sent" in out
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    ics = next(p for p in msg.iter_attachments() if p.get_filename() == "invite.ics").get_content()
    assert "DTSTART:20261020T140000Z" in ics and "DTEND:20261020T144500Z" in ics
    assert "SUMMARY:Coffee\\, then work" in ics and "ORGANIZER:mailto:me@example.com" in ics
    with pytest.raises(ToolError, match="UTC offset"):
        call("add_invite", draft_id=d, title="x", start="2026-10-20T15:00:00")


def test_the_addons_command(capsys, monkeypatch):
    monkeypatch.setenv("MAIL_ADDONS", "hello")
    monkeypatch.setenv("MAIL_ADDONS_DIR", str(EXAMPLES))
    server.show_addons()
    out = capsys.readouterr().out
    assert "hello (own file): Says hello" in out and "tools: hello" in out and "All add-ons load" in out
    monkeypatch.setenv("MAIL_ADDONS", "")
    server.show_addons()
    assert "No add-ons are turned on" in capsys.readouterr().out
