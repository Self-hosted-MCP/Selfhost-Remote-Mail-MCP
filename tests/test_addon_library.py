"""The add-on library and the toolbox parts library add-ons use: reading mail, new drafts, saved data,
background jobs, web requests and sending."""
import email
import itertools
import os
from email.policy import default as POLICY
from pathlib import Path

import pytest

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server

_n = itertools.count()
LIB = Path(server.__file__).resolve().parent / "library"


def api(**module):
    """An AddonAPI for a made-up add-on, with the module-level settings (SENDS, HOSTS) it would declare."""
    name = f"lib{next(_n)}"
    server.ADDON_INFO[name] = {"source": "test", "sends": module.get("SENDS", False), "hosts": module.get("HOSTS", ())}
    return server.AddonAPI(name)


def put(mailbox, folder, raw: str) -> None:
    from conftest import FakeIMAP
    with FakeIMAP.lock:
        uid = FakeIMAP.next_uid
        FakeIMAP.next_uid += 1
    mailbox[folder][uid] = raw.replace("\n", "\r\n").encode()


def mail(n: int, extra: str = "") -> str:
    return (f"From: Sam <sam@example.org>\nTo: me@example.com\nSubject: Hello {n}\n"
            f"Date: Mon, 12 Oct 2026 10:0{n % 10}:00 +0000\nMessage-ID: <m{n}@example.org>\n{extra}\nBody {n}\n")


@pytest.fixture
def job():
    token = server.ADDON_JOB.set("test.job")
    yield
    server.ADDON_JOB.reset(token)


def test_every_library_addon_has_a_readme_and_a_docstring():
    found = server.library_addons()
    assert "calendar_invite" in found
    for name, about in found.items():
        assert about, f"{name} needs a one-line docstring"
        assert (LIB / name / "README.md").is_file(), f"{name} needs a README.md"
        assert (LIB / name / "__init__.py").is_file()
    index = (LIB / "README.md").read_text()
    assert all(f"[{name}]" in index for name in found)


def test_a_library_addon_loads_by_name_and_an_own_file_wins(tmp_path):
    (tmp_path / "calendar_invite.py").write_text('"""Mine."""\ndef setup(api):\n    pass\n')
    server.LOADED_ADDONS.pop("calendar_invite", None)
    try:
        server.load_addons("calendar_invite", tmp_path)
        assert server.ADDON_INFO["calendar_invite"]["source"].startswith("own file, replaces")
    finally:
        server.LOADED_ADDONS.pop("calendar_invite", None)
    with pytest.raises(RuntimeError, match="Library add-ons: .*calendar_invite"):
        server.load_addons("no_such_addon", tmp_path)


def test_a_missing_package_says_how_to_install(tmp_path):
    (tmp_path / "needy.py").write_text('NEEDS = ["not_a_real_package_xyz"]\ndef setup(api):\n    pass\n')
    with pytest.raises(RuntimeError, match="needs the Python package not_a_real_package_xyz.*add-on extras"):
        server.load_addons("needy", tmp_path)
    (tmp_path / "broken.py").write_text('import not_a_real_package_abc\ndef setup(api):\n    pass\n')
    with pytest.raises(RuntimeError, match="imports not_a_real_package_abc, which isn't installed"):
        server.load_addons("broken", tmp_path)


def test_find_message_and_replies(mailbox):
    put(mailbox, "INBOX", mail(1, "List-Id: <news.example.org>"))
    put(mailbox, "INBOX", mail(2, "In-Reply-To: <out1@example.com>\nReferences: <out1@example.com>"))
    a = api()
    rows = a.find(headers=("List-Id",))
    assert {r["subject"] for r in rows} == {"Hello 1", "Hello 2"}
    first = next(r for r in rows if r["subject"] == "Hello 1")
    assert first["list-id"] == "<news.example.org>" and first["account"] == "me@example.com"
    assert first["message-id"] == "<m1@example.org>" and first["date"].year == 2026
    assert "Body 1" in a.message(first["id"]).get_content()
    replies = a.replies_to("<out1@example.com>")
    assert [r["subject"] for r in replies] == ["Hello 2"]
    with pytest.raises(ToolError, match="Message-ID"):
        a.replies_to("not an id")


def test_new_draft_and_a_reply_draft(mailbox):
    put(mailbox, "INBOX", mail(3))
    a = api()
    d = a.new_draft(["sam@example.org"], "Plan", "**Hi**", headers={"Auto-Submitted": "auto-replied"}, no_signature=True)
    assert d.startswith("me@example.com:Drafts#")
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    assert msg["Auto-Submitted"] == "auto-replied" and msg["Subject"] == "Plan"
    src = a.find()[0]["id"]
    a.new_draft(["sam@example.org"], "", "Thanks!", reply_to_id=src)
    reply = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    assert reply["Subject"] == "Re: Hello 3" and reply["In-Reply-To"] == "<m3@example.org>"


def test_edit_draft_may_return_a_new_message(mailbox):
    a = api()
    d = a.new_draft(["sam@example.org"], "Old", "old")
    def swap(msg):
        new = email.message.EmailMessage()
        for h in ("From", "To", "Message-ID"):
            new[h] = msg[h]
        new["Subject"] = "New"
        new.set_content("new body")
        return new
    a.edit_draft(d, swap)
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    assert msg["Subject"] == "New"


def test_store_is_encrypted_and_survives(mailbox):
    a = api()
    with a.store() as data:
        data["count"] = 3
    raw = (server.ADDON_DATA / f"{a.name}.json").read_bytes()
    assert b"count" not in raw
    with a.store() as data:
        assert data["count"] == 3
    (server.ADDON_DATA / f"{a.name}.json").write_bytes(b"garbage")
    with pytest.raises(RuntimeError, match="can't be read"):
        with a.store():
            pass


def test_new_mail_starts_from_now_and_then_sees_only_new(mailbox, job):
    put(mailbox, "INBOX", mail(4))
    a = api()
    assert a.new_mail() == []          # first call: only notes where to start
    put(mailbox, "INBOX", mail(5))
    assert [r["subject"] for r in a.new_mail()] == ["Hello 5"]
    assert a.new_mail() == []


def test_new_mail_and_send_need_a_job(mailbox):
    with pytest.raises(ToolError, match="background job"):
        api().new_mail()
    a = api(SENDS=True)
    d = a.new_draft(["sam@example.org"], "x", "y")
    with pytest.raises(ToolError, match="background jobs"):
        a.send(d)


def test_send_needs_sends_and_goes_through_the_normal_path(mailbox, job):
    from conftest import FakeSMTP
    plain = api()
    d = plain.new_draft(["sam@example.org"], "x", "y")
    with pytest.raises(ToolError, match="SENDS = True"):
        plain.send(d)
    sender = api(SENDS=True)
    with pytest.raises(ToolError, match="only sends drafts it made"):
        sender.send(d)                                  # someone else's draft
    d = sender.new_draft(["sam@example.org"], "Away", "I'm away.")
    assert sender.send(d) == "sent to 1 recipient(s)"
    assert FakeSMTP.sent[-1]["Subject"] == "Away" and server.SENT_LOG.exists()


def test_a_nested_store_shares_one_dict(mailbox):
    a = api()
    with a.store() as outer:
        outer["a"] = 1
        with a.store() as inner:
            inner["b"] = 2
            assert inner is outer
    with a.store() as data:
        assert data == {"a": 1, "b": 2}


def test_jobs_with_the_same_name_keep_their_own_timing():
    ran = []
    a = api()
    before = list(server.ADDON_JOBS)
    try:
        a.every(5, lambda: ran.append(1))
        a.every(5, lambda: ran.append(2))
        server.run_jobs_once(now=2_000_000.0)
        assert sorted(ran) == [1, 2]
    finally:
        server.ADDON_JOBS[:] = before


def test_a_short_id_in_a_job_needs_the_mailbox_when_there_are_several(mailbox, job, monkeypatch):
    two = [server.Account(address="me@example.com", password="x", imap_host="i", smtp_host="s"),
           server.Account(address="b@example.com", password="x", imap_host="i", smtp_host="s")]
    monkeypatch.setattr(server, "all_accounts", lambda cfg=None: two)
    put(mailbox, "INBOX", mail(6))
    a = api()
    with pytest.raises(ToolError, match="pass account="):
        a.message("INBOX#1")
    row = a.find(account="me@example.com")[0]
    assert row["id"].startswith("me@example.com:INBOX#") and "Body 6" in a.message(row["id"]).get_content()


def test_jobs_run_when_due_and_a_failing_job_doesnt_stop_others(tmp_path):
    ran = []
    a = api()
    def good():
        ran.append(server.ADDON_JOB.get())
    def bad():
        raise ValueError("boom")
    before = list(server.ADDON_JOBS)
    try:
        a.every(1, bad)
        a.every(1, good)
        assert server.ADDON_JOBS[-1]["every"] == 300   # 5 minutes at least
        out = server.run_jobs_once(now=1_000_000.0)
        assert ran == [f"{a.name}.2.good"] and any("1.bad failed: ValueError" in line for line in out)
        server.run_jobs_once(now=1_000_100.0)          # not due yet
        assert len(ran) == 1
        server.run_jobs_once(now=1_000_400.0)
        assert len(ran) == 2
    finally:
        server.ADDON_JOBS[:] = before


def test_http_only_reaches_listed_hosts(monkeypatch):
    a = api(HOSTS=("api.example.org",))
    with pytest.raises(ToolError, match="may not reach"):
        a.http("GET", "https://evil.example.com/")
    with pytest.raises(ToolError, match="only https"):
        a.http("GET", "http://api.example.org/")
    seen = {}
    class Resp:
        status = 200
        headers = {"X": "1"}
        def read(self, n): return b'{"ok": true}'
        def __enter__(self): return self
        def __exit__(self, *e): pass
    class Opener:
        def open(self, req, timeout):
            seen["url"], seen["body"] = req.full_url, req.data
            return Resp()
    monkeypatch.setattr(server.urllib.request, "build_opener", lambda *h: Opener())
    status, _h, body = a.http("POST", "https://api.example.org/x", json_body={"a": 1})
    assert status == 200 and body == b'{"ok": true}' and seen["body"] == b'{"a": 1}'
    monkeypatch.setenv(f"{a.name.upper()}_URL", "https://hooks.example.net/in")
    assert a.http("GET", "https://hooks.example.net/in")[0] == 200


def test_addons_list_enable_disable(capsys, monkeypatch):
    monkeypatch.delenv("MAIL_ADDONS", raising=False)
    monkeypatch.setattr(server, "load_addons", lambda names, folder: names.split(","))   # tools stay registered
    server.show_addons(["list"])
    assert "calendar_invite:" in capsys.readouterr().out
    try:
        server.show_addons(["enable", "calendar_invite"])
        assert "MAIL_ADDONS=calendar_invite" in server.ENV_FILE.read_text()
        assert "All add-ons load" in capsys.readouterr().out
        server.show_addons(["disable", "calendar_invite"])
        assert "calendar_invite" not in server.read_env().get("MAIL_ADDONS", "")
        with pytest.raises(SystemExit, match="no add-on called"):
            server.show_addons(["enable", "nope"])
        monkeypatch.setenv("MAIL_ADDONS", "")
        with pytest.raises(SystemExit, match="Set it there to: MAIL_ADDONS=calendar_invite"):
            server.show_addons(["enable", "calendar_invite"])
    finally:
        server.write_settings({}, drop=("MAIL_ADDONS",))


def test_calendar_invite_folds_long_lines_and_keeps_details():
    from selfhost_remote_mail_mcp.library.calendar_invite.addon import fold
    long = "SUMMARY:" + "Réunion très importante " * 10
    folded = fold(long)
    assert all(len(part.encode()) <= 75 for part in folded.split("\r\n"))
    assert folded.replace("\r\n ", "") == long


# ---------------------------------------------------------------- pdf_maker and invoices (need the addons extra)

def pdf_text(mailbox, name: str) -> str:
    import io
    from pypdf import PdfReader
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    part = next(p for p in msg.iter_attachments() if p.get_filename() == name)
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(part.get_content())).pages)


@pytest.fixture(scope="module")
def library_tools():
    pytest.importorskip("fpdf")
    for name in ("pdf_maker", "invoices"):
        if name not in server.LOADED_ADDONS:
            server.load_addons(name, Path("/nonexistent"))
    return lambda tool, **args: server.mcp._tool_manager.get_tool(tool).fn(**args)


def test_make_pdf_is_safe_and_readable():
    pytest.importorskip("fpdf")
    from selfhost_remote_mail_mcp.library._pdf import PdfError, make_pdf, MAX_TEXT
    data, pages = make_pdf("# Olá\n\nΕλληνικά, Русский.\n\n<script>x</script>\n\n![x](/etc/passwd)\n\n"
                           "[ok](https://example.com) [no](javascript:alert(1)) [js](https://e.com/JS/x)", "T")
    assert data.startswith(b"%PDF") and pages == 1 and not server.PDF_CODE.search(data)
    import io
    from pypdf import PdfReader
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    assert "Ελληνικά" in text and "Русский" in text and "<script>x</script>" in text and "[x]" in text
    assert b"/Author" not in data and b"javascript" not in data.lower()
    with pytest.raises(PdfError, match="too long"):
        make_pdf("x" * (MAX_TEXT + 1))
    with pytest.raises(PdfError, match="longer than"):
        make_pdf("\n\n".join(["line"] * 6000))


def test_pdf_maker_attaches_to_a_draft(mailbox, library_tools):
    d = server.AddonAPI("t").new_draft(["sam@example.org"], "Proposal", "Attached.")
    out = library_tools("make_pdf", draft_id=d, file_name="Proposal/Acme", text="## Plan\n\n- one\n- two", title="Plan")
    assert "Proposal-Acme.pdf (1 page" in out and "Nothing was sent" in out
    assert "Plan" in pdf_text(mailbox, "Proposal-Acme.pdf")


def test_invoice_totals_numbering_and_rules(mailbox, library_tools, monkeypatch):
    call = library_tools
    d = server.AddonAPI("t").new_draft(["sam@example.org"], "Invoice", "Here it is.")
    items = [{"description": "Logo", "quantity": "3", "unit_price": "0.10"},
             {"description": "Site", "quantity": 1, "unit_price": 1000.005}]
    with pytest.raises(ToolError, match="business details aren.t set up.*INVOICES_SELLER_NAME"):
        call("make_invoice", draft_id=d, kind="quote", client_name="Acme", items=items)
    monkeypatch.setenv("INVOICES_SELLER_NAME", "Studio")
    with pytest.raises(ToolError, match="tax number"):
        call("make_invoice", draft_id=d, kind="invoice", client_name="Acme", items=items)
    monkeypatch.setenv("INVOICES_SELLER_TAX_ID", "PT123")
    with pytest.raises(ToolError, match="tax_note"):
        call("make_invoice", draft_id=d, kind="invoice", client_name="Acme", items=items)
    with pytest.raises(ToolError, match="dot for decimals"):
        call("make_invoice", draft_id=d, kind="quote", client_name="Acme",
             items=[{"description": "x", "quantity": "1", "unit_price": "1,50"}])
    for bad in ("NaN", "-1", "1e999"):
        with pytest.raises(ToolError):
            call("make_invoice", draft_id=d, kind="quote", client_name="Acme",
                 items=[{"description": "x", "quantity": "1", "unit_price": bad}])
    with pytest.raises(ToolError):
        call("make_invoice", draft_id="Drafts#999999", kind="quote", client_name="Acme", items=items)
    year = server.dt.date.today().year
    out = call("make_invoice", draft_id=d, kind="quote", client_name="Acme", items=items, tax_rate="23")
    # 0.30 + 1000.01 (half up) = 1000.31 net; tax 23% of the total, rounded once = 230.07
    assert f"Q-{year}-0001" in out and "1 230.38 EUR" in out and "Nothing was sent" in out   # failed calls used no number
    text = pdf_text(mailbox, f"Quote-Q-{year}-0001.pdf")
    assert "This is a quote, not an invoice." in text and "Valid until" in text and "Studio" in text
    d2 = draft_id_of(out)
    out = call("make_invoice", draft_id=d2, kind="quote", client_name="Beta", items=items[:1])
    assert f"Q-{year}-0002" in out
    out = call("make_invoice", draft_id=draft_id_of(out), kind="invoice", client_name="Beta", items=items[:1],
               tax_note="VAT exempt, Art. 53 CIVA")
    assert f"INV-{year}-0001" in out
    assert "VAT exempt, Art. 53 CIVA" in pdf_text(mailbox, f"Invoice-INV-{year}-0001.pdf")
    listing = call("invoices")
    assert listing.splitlines()[0].startswith(f"INV-{year}-0001") and f"Q-{year}-0001" in listing
    assert call("invoices", kind="quote").count("Q-") == 2


def draft_id_of(out: str) -> str:
    return out.split("Draft ID is now ")[1].split(".")[0]


def test_pdf_title_that_looks_like_code_and_slow_text(monkeypatch):
    pytest.importorskip("fpdf")
    from selfhost_remote_mail_mcp.library import _pdf
    data, _pages = _pdf.make_pdf("[link](https://example.com)", "Notes on /JS bundles")
    assert not server.PDF_CODE.search(data)
    monkeypatch.setattr(_pdf, "TIME_LIMIT", 2)
    with pytest.raises(_pdf.PdfError, match="longer than 2 seconds"):
        _pdf.make_pdf("`" * 60000)


def test_unit_prices_keep_their_decimals(mailbox, library_tools, monkeypatch):
    monkeypatch.setenv("INVOICES_SELLER_NAME", "Studio")
    d = server.AddonAPI("t").new_draft(["sam@example.org"], "Quote", "Here.")
    out = library_tools("make_invoice", draft_id=d, kind="quote", client_name="Acme",
                        items=[{"description": "Stamp", "quantity": "1", "unit_price": "0.125"}])
    number = out.split("Quote ")[1].split(" ")[0]
    text = pdf_text(mailbox, f"Quote-{number}.pdf")
    assert "0.125 EUR" in text and "0.13 EUR" in text
    with pytest.raises(ToolError, match="4 decimals"):
        library_tools("make_invoice", draft_id=draft_id_of(out), kind="quote", client_name="Acme",
                      items=[{"description": "x", "quantity": "1", "unit_price": "0.12345"}])


def test_calendar_text_has_no_raw_control_characters(mailbox, monkeypatch):
    server.load_addons("calendar_invite", Path("/nonexistent")) if "calendar_invite" not in server.LOADED_ADDONS else None
    d = server.AddonAPI("t").new_draft(["sam@example.org"], "Meet", "Hi")
    server.mcp._tool_manager.get_tool("add_invite").fn(draft_id=d, title="A\rB\x07C", start="2026-10-20T15:00:00+01:00",
                                                       details="line 1\r\nline 2")
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    ics = next(p for p in msg.iter_attachments() if p.get_filename() == "invite.ics").get_content()
    assert "SUMMARY:A\\nBC" in ics and "DESCRIPTION:line 1\\nline 2" in ics


def test_the_settings_page_lists_the_library(monkeypatch):
    monkeypatch.setitem(server.LOADED_ADDONS, "my_own", "Mine: does a thing.")
    rows = server.addon_rows()
    names = [r["name"] for r in rows]
    assert {"calendar_invite", "pdf_maker", "invoices"} <= set(names) and names[-1] == "my_own"
    mine = next(r for r in rows if r["name"] == "my_own")
    assert mine["about"] == "Mine: does a thing." and mine["on"] and not mine["library"] and mine["in_settings"]
    from selfhost_remote_mail_mcp import pages
    html = pages.settings("t", [], [], None, 5, False, None, False, None, None, None, rows)
    assert 'href="#addons"' in html and "pdf_maker" in html and "Your own" in html
    assert f'{pages.LIBRARY_URL}/pdf_maker' in html and "MAIL_ADDONS" in html


def test_settings_page_buttons_turn_library_addons_on_and_off(monkeypatch):
    monkeypatch.delenv("MAIL_ADDONS", raising=False)
    server.unload_addon("calendar_invite")
    act = lambda name, action: server.settings_action(None, "addon", {"name": name, "action": action})
    kind, text = act("calendar_invite", "on")
    assert kind == "ok" and "calendar_invite is on" in text
    assert "add_invite" in server.TOOL_NAMES and server.mcp._tool_manager.get_tool("add_invite")
    assert server.page_addons() == ["calendar_invite"]
    kind, text = act("calendar_invite", "off")
    assert kind == "ok" and "add_invite" not in server.TOOL_NAMES
    assert server.mcp._tool_manager.get_tool("add_invite") is None and server.page_addons() == []
    assert act("../evil", "on")[0] == "error" and "no add-on called" in act("nope", "on")[1]
    monkeypatch.setenv("MAIL_ADDONS", "calendar_invite")
    assert "Change it there" in act("calendar_invite", "off")[1]
    rows = {r["name"]: r for r in server.addon_rows()}
    assert rows["calendar_invite"]["in_settings"] is True


def test_a_failed_setup_leaves_no_tools_behind(tmp_path):
    (tmp_path / "halfway.py").write_text('def setup(api):\n    @api.tool(api.READ)\n    def halfway_tool() -> str:\n'
                                         '        """x"""\n        return ""\n    raise ValueError("broken")\n')
    with pytest.raises(ValueError):
        server.load_addons("halfway", tmp_path)
    assert "halfway_tool" not in server.TOOL_NAMES and server.mcp._tool_manager.get_tool("halfway_tool") is None


def test_a_page_addon_that_fails_doesnt_stop_the_start(monkeypatch, capsys):
    monkeypatch.delenv("MAIL_ADDONS", raising=False)
    monkeypatch.setattr(server, "page_addons", lambda: ["invoices"])
    def broken(names=None, folder=None):
        if names == "invoices":
            raise RuntimeError("add-on invoices needs the Python package fpdf")
        return []
    monkeypatch.setattr(server, "load_addons", broken)
    server.load_startup_addons()
    assert "invoices (turned on on the settings page) didn't load" in capsys.readouterr().err


def test_odd_prefs_files_and_the_command_line(monkeypatch, capsys):
    monkeypatch.delenv("MAIL_ADDONS", raising=False)
    server.private_write(server.PREFS_FILE, "[1, 2]")
    assert server.page_addons() == [] and server.pref_on("device_log", "DEVICE_LOG") is True
    server.set_page_addon("pdf_maker", True)
    assert server.page_addons() == ["pdf_maker"]
    monkeypatch.setattr(server, "load_addons", lambda names, folder: names.split(","))
    server.show_addons(["list"])
    assert "[on] pdf_maker" in capsys.readouterr().out
    server.show_addons(["disable", "pdf_maker"])
    assert server.page_addons() == [] and "turned on on the settings page" in capsys.readouterr().out
    server.PREFS_FILE.unlink()


def test_own_file_with_a_library_name_is_marked(monkeypatch):
    monkeypatch.setitem(server.LOADED_ADDONS, "invoices", "Mine.")
    monkeypatch.setitem(server.ADDON_INFO, "invoices", {"source": "own file, replaces the library one"})
    row = next(r for r in server.addon_rows() if r["name"] == "invoices")
    assert row["own_file"] is True
    from selfhost_remote_mail_mcp import pages
    html = pages.settings("t", [], [], None, 5, False, None, False, None, None, None, [row])
    assert "Your own" in html and f"{pages.LIBRARY_URL}/invoices" not in html
    assert "@supports selector(:has(a))" in html


def test_two_turn_ons_at_once_load_once(monkeypatch):
    import threading
    monkeypatch.delenv("MAIL_ADDONS", raising=False)
    server.unload_addon("calendar_invite")
    results = []
    threads = [threading.Thread(target=lambda: results.append(server.settings_action(
        None, "addon", {"name": "calendar_invite", "action": "on"}))) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert [k for k, _ in results] == ["ok", "ok"] and server.TOOL_NAMES.count("add_invite") == 1
    assert "calendar_invite" in server.LOADED_ADDONS
    server.settings_action(None, "addon", {"name": "calendar_invite", "action": "off"})


def test_addon_setup_page_saves_settings_encrypted(monkeypatch):
    for k in ("INVOICES_SELLER_NAME", "INVOICES_SELLER_TAX_ID", "INVOICES_PAYMENT"):
        monkeypatch.delenv(k, raising=False)
    fields = server.addon_fields("invoices")
    assert fields[0] == {"key": "SELLER_NAME", "label": "Your name or business name", "help": "", "required": True,
                         "lines": 1, "secret": False}
    assert server.addon_missing("invoices") == ["Your name or business name"]
    kind, text = server.settings_action(None, "addon_setup", {"name": "invoices", "INVOICES_SELLER_NAME": " Studio\x07 ",
                                                             "INVOICES_PAYMENT": "Bank\r\nIBAN PT50"})
    assert kind == "ok" and "invoices is set up" in text
    assert server.addon_setting_value("INVOICES_SELLER_NAME", "invoices") == ("Studio", "page")
    assert server.addon_setting_value("INVOICES_PAYMENT", "invoices")[0] == "Bank\nIBAN PT50"
    assert b"Studio" not in server.ADDON_SETTINGS_FILE.read_bytes() and server.addon_missing("invoices") == []
    api = server.AddonAPI("invoices")
    assert api.setting("INVOICES_SELLER_NAME") == "Studio"
    monkeypatch.setenv("INVOICES_SELLER_NAME", "From the server")   # server settings win, and aren't changed here
    assert api.setting("INVOICES_SELLER_NAME") == "From the server"
    server.settings_action(None, "addon_setup", {"name": "invoices", "INVOICES_SELLER_NAME": "Other"})
    monkeypatch.delenv("INVOICES_SELLER_NAME")
    assert api.setting("INVOICES_SELLER_NAME") == "Studio"
    server.settings_action(None, "addon_setup", {"name": "invoices", "INVOICES_SELLER_NAME": ""})
    assert server.addon_missing("invoices") == ["Your name or business name"]
    assert server.settings_action(None, "addon_setup", {"name": "nope"})[0] == "error"
    server.ADDON_SETTINGS_FILE.unlink()


def test_addon_setup_page_html_and_the_ai_gets_the_link(monkeypatch):
    from selfhost_remote_mail_mcp import pages
    row = {"name": "invoices", "about": "", "on": False, "library": True, "in_settings": False}
    fields = [{**f, "full": "INVOICES_" + f["key"], "value": "<b>x</b>" if f["key"] == "SELLER_NAME" else "",
               "where": "", "has_value": False} for f in server.addon_fields("invoices")]
    html = pages.addon_setup("t", row, fields, None)
    assert "&lt;b&gt;x&lt;/b&gt;" in html and 'name="INVOICES_PAYMENT"' in html and "<textarea" in html
    assert 'href="/settings#addons"' in html and 'value="setup"' in html
    monkeypatch.setattr(server, "MODE", "serve")
    out = server.settings()
    assert "/settings/addon/invoices" in out and "needs setting up" in out
    rows = {r["name"]: r for r in server.addon_rows()}
    assert rows["invoices"]["fields"] and rows["invoices"]["missing"] and not rows["pdf_maker"]["fields"]
    html = pages.settings("t", [], [], None, 5, False, None, False, None, None, None, list(rows.values()))
    assert 'href="/settings/addon/invoices"' in html and "Needs setting up" in html


def test_setup_settings_survive_a_changed_key_and_secrets_can_be_removed(monkeypatch):
    monkeypatch.delenv("INVOICES_SELLER_NAME", raising=False)
    server.save_addon_settings("invoices", {"INVOICES_SELLER_NAME": "Studio"})
    saved = server.ADDON_SETTINGS_FILE.read_bytes()
    server.ADDON_SETTINGS_FILE.write_bytes(b"not readable with this key")
    with pytest.raises(ToolError, match="Nothing was overwritten"):
        server.save_addon_settings("invoices", {"INVOICES_TAX_RATE": "23"})
    assert server.ADDON_SETTINGS_FILE.read_bytes() == b"not readable with this key"
    server.ADDON_SETTINGS_FILE.write_bytes(saved)
    assert server.addon_setting_value("INVOICES_SELLER_NAME", "invoices") == ("Studio", "page")
    assert server.addon_setting_value("INVOICES_SELLER_NAME", "other") == ("", "")   # each add-on its own values
    fields = [{"key": "TOKEN", "label": "Token", "secret": True}, {"key": "ONE", "label": "One line"}]
    monkeypatch.setitem(server.ADDON_INFO, "secretive", {"fields": server.clean_fields(fields)})
    monkeypatch.setitem(server.LOADED_ADDONS, "secretive", "x")
    act = lambda form: server.settings_action(None, "addon_setup", {"name": "secretive", **form})
    act({"SECRETIVE_TOKEN": "abc", "SECRETIVE_ONE": "a\nb"})
    assert server.addon_setting_value("SECRETIVE_ONE", "secretive")[0] == "a b"
    act({"SECRETIVE_TOKEN": ""})
    assert server.addon_setting_value("SECRETIVE_TOKEN", "secretive")[0] == "abc"   # empty box keeps it
    act({"SECRETIVE_TOKEN": "", "SECRETIVE_TOKEN__clear": "1"})
    assert server.addon_setting_value("SECRETIVE_TOKEN", "secretive")[0] == ""
    server.ADDON_SETTINGS_FILE.unlink()
