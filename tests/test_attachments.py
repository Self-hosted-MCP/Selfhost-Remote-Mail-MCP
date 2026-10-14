"""New files: the type checks, attach_path / attach_content / attach_upload, the upload page and its clean-up."""
import base64
import email
import io
import re
import shutil
import tarfile
import time
import zipfile
from email.policy import default as POLICY

import pytest
from starlette.testclient import TestClient

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server

JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 64
PDF = b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj\n%%EOF"
EXE = b"MZ\x90\x00" + b"\x00" * 64


def zipped(files: dict, flag_bits: int = 0) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    raw = bytearray(out.getvalue())
    if flag_bits:   # zipfile can't write encrypted zips: set the "password" bit by hand
        for sig, at in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            i = raw.find(sig)
            while i != -1:
                raw[i + at] |= flag_bits
                i = raw.find(sig, i + 4)
    return bytes(raw)


def tar_gz(files: dict) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as t:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return out.getvalue()


@pytest.fixture(autouse=True)
def no_uploads():
    shutil.rmtree(server.UPLOADS, ignore_errors=True)
    yield
    shutil.rmtree(server.UPLOADS, ignore_errors=True)


def level(name, data):
    return server.check_new_file(name, data).level


# ---------------------------------------------------------------- the checks

@pytest.mark.parametrize("name,data", [
    ("photo.jpg", JPG), ("report.pdf", PDF), ("notes.txt", b"hello"), ("list.csv", b"a,b\n1,2"),
    ("invite.ics", b"BEGIN:VCALENDAR\r\nEND:VCALENDAR"), ("letter.docx", zipped({"word/document.xml": b"<w/>"})),
    ("photos.zip", zipped({"a.jpg": JPG, "b.pdf": PDF, "__MACOSX/._a.jpg": b"x"})),
    ("backup.tar.gz", tar_gz({"a.txt": b"hi"})), ("excel.csv", b"\xff\xfea\x00,\x00b\x00"),
])
def test_safe_files(name, data):
    assert level(name, data) == "safe"


@pytest.mark.parametrize("name,data,why", [
    ("setup.exe", EXE, "programs or scripts"),
    ("run.sh", b"#!/bin/sh\necho", "programs or scripts"),
    ("photo.jpg", EXE, "really a program"),
    ("photo.jpg", b"not a picture", "doesn't match"),
    ("notes.txt", b"abc\x00\x00def", "doesn't match"),
    ("strange.xyz", b"data", "isn't on the list"),
    ("noextension", b"data", "isn't on the list"),
    ("gpj\u202eexe.jpg", JPG, "hidden characters"),
    ("tools.zip", zipped({"readme.txt": b"hi", "install.exe": EXE}), "programs or scripts inside"),
    ("tools.zip", zipped({"setup.js": b"alert(1)"}), "programs or scripts inside"),
    ("pics.zip", zipped({"cat.jpg": EXE}), "programs or scripts inside"),
    ("app.tar.gz", tar_gz({"bin/run.sh": b"#!/bin/sh"}), "programs or scripts inside"),
    ("broken.docx", b"PK\x03\x04garbage", "isn't a real"),
])
def test_blocked_files(name, data, why):
    checked = server.check_new_file(name, data)
    assert checked.level == "blocked" and why in checked.why


@pytest.mark.parametrize("name,data,why", [
    ("budget.xlsm", zipped({"xl/workbook.xml": b"<x/>"}), "macros"),
    ("budget.xlsx", zipped({"xl/workbook.xml": b"<x/>", "xl/vbaProject.bin": b"x"}), "macros"),
    ("old.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 32, "macros"),
    ("form.pdf", PDF + b"/OpenAction << /S /JavaScript /JS (app.alert(1)) >>", "code"),
    ("logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>", "scripts"),
    ("page.html", b"<html></html>", "scripts"),
    ("secret.zip", zipped({"a.txt": b"hi"}, flag_bits=1), "password"),
    ("mixed.zip", zipped({"a.txt": b"hi", "data.parquet": b"x"}), "unusual files"),
    ("archive.rar", b"Rar!\x1a\x07\x00", "can't look inside"),
])
def test_suspect_files(name, data, why):
    checked = server.check_new_file(name, data)
    assert checked.level == "suspect" and why in checked.why and name in checked.note


def test_file_names_are_cleaned():
    assert server.clean_file_name("../../etc/passwd.txt") == "passwd.txt"
    assert server.clean_file_name("C:\\Users\\x\\a\tb.pdf") == "ab.pdf"
    assert server.file_kind("Backup.TAR.GZ") == "tar.gz"


# ---------------------------------------------------------------- draft

def saved_draft(mailbox):
    raw = list(mailbox["Drafts"].values())[-1]
    return email.message_from_bytes(raw, policy=POLICY)


def test_attach_content_text_and_base64(mailbox):
    out = server.draft(to=["sam@example.org"], subject="Files", body="Here.", attach_content=[
        {"name": "notes.txt", "text": "remember the milk"},
        {"name": "photo.jpg", "base64": base64.b64encode(JPG).decode()}])
    assert "notes.txt, photo.jpg" in out
    parts = {p.get_filename(): p for p in saved_draft(mailbox).iter_attachments()}
    assert parts["notes.txt"].get_content() == "remember the milk"
    assert parts["photo.jpg"].get_content_type() == "image/jpeg" and parts["photo.jpg"].get_content() == JPG


def test_blocked_file_saves_nothing(mailbox):
    with pytest.raises(ToolError, match="programs or scripts"):
        server.draft(to=["sam@example.org"], subject="x", body="x",
                     attach_content=[{"name": "tool.exe", "base64": base64.b64encode(EXE).decode()}])
    assert not mailbox["Drafts"]


def test_suspect_file_needs_the_users_ok(mailbox):
    xlsm = {"name": "budget.xlsm", "base64": base64.b64encode(zipped({"xl/workbook.xml": b"<x/>"})).decode()}
    with pytest.raises(ToolError) as err:
        server.draft(to=["sam@example.org"], subject="Budget", body="Attached.", attach_content=[xlsm])
    text = str(err.value)
    assert "Ask the user first" in text and "allow_suspect=true" in text and "budget.xlsm contains macros" in text
    assert not mailbox["Drafts"]
    server.draft(to=["sam@example.org"], subject="Budget", body="Attached.", attach_content=[xlsm], allow_suspect=True)
    assert [p.get_filename() for p in saved_draft(mailbox).iter_attachments()] == ["budget.xlsm"]
    assert "macros" not in saved_draft(mailbox).get_body(("plain",)).get_content()   # nothing added for the receiver


def test_content_size_and_total_size_caps(monkeypatch):
    with pytest.raises(ToolError, match="up to"):
        server.draft(subject="x", body="x", attach_content=[{"name": "big.txt", "text": "a" * 2_000_001}])
    monkeypatch.setenv("ATTACH_MAX_MB", "1")
    with pytest.raises(ToolError, match="add up to"):
        server.draft(subject="x", body="x", attach_content=[{"name": f"{i}.txt", "text": "a" * 600_000} for i in range(2)])


def test_attach_path_reads_allowed_folders_only(tmp_path, monkeypatch, mailbox):
    monkeypatch.setenv("ATTACH_FOLDERS", str(tmp_path / "docs"))
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "invoice.pdf").write_bytes(PDF)
    (tmp_path / "docs" / ".secret.txt").write_text("key")
    (tmp_path / "docs" / ".ssh").mkdir()
    (tmp_path / "docs" / ".ssh" / "notes.txt").write_text("key")
    (tmp_path / "other.pdf").write_bytes(PDF)
    (tmp_path / "docs" / "link.pdf").symlink_to(tmp_path / "other.pdf")
    server.draft(to=["sam@example.org"], subject="Invoice", body="x", attach_path=[str(tmp_path / "docs" / "invoice.pdf")])
    assert [p.get_filename() for p in saved_draft(mailbox).iter_attachments()] == ["invoice.pdf"]
    for path, why in [(".secret.txt", "hidden or private"), (".ssh/notes.txt", "hidden or private"),
                      ("../other.pdf", "isn't in a folder"), ("link.pdf", "isn't in a folder"),
                      ("missing.pdf", "not found"), ("", "folder")]:
        with pytest.raises(ToolError, match=why):
            server.draft(subject="x", body="x", attach_path=[str(tmp_path / "docs" / path)])


def test_attach_path_is_refused_on_the_web_version(monkeypatch):
    monkeypatch.setattr(server, "REMOTE", True)
    with pytest.raises(ToolError, match="upload"):
        server.draft(subject="x", body="x", attach_path=["~/Desktop/a.pdf"])


# ---------------------------------------------------------------- uploads

def test_uploads_are_encrypted_and_attachable(mailbox):
    meta = server.save_upload("photo.jpg", JPG)
    assert re.fullmatch(r"F-[2-9A-Z]{6}", meta["code"])
    meta_path, data_path = server.upload_paths(meta["code"])
    assert JPG not in data_path.read_bytes() and b"photo.jpg" not in meta_path.read_bytes()
    assert oct(data_path.stat().st_mode & 0o777) == "0o600"
    out = server.draft(to=["sam@example.org"], subject="Photo", body="x", attach_upload=["latest"])
    assert "photo.jpg" in out and "deleted from the server in 1 hour" in out
    assert server.list_uploads()[0]["used"]


def test_upload_refuses_programs_and_keeps_suspect_files():
    with pytest.raises(ToolError, match="wasn't uploaded"):
        server.save_upload("photo.jpg", EXE)
    meta = server.save_upload("logo.svg", b"<svg/>")
    assert meta["level"] == "suspect"
    with pytest.raises(ToolError, match="Ask the user first"):
        server.draft(subject="x", body="x", attach_upload=[meta["code"]])


def test_uploads_are_deleted_after_one_hour_or_a_day(mailbox):
    used = server.save_upload("a.pdf", PDF)
    unused = server.save_upload("b.pdf", PDF)
    server.draft(subject="x", body="x", attach_upload=[used["code"].lower()])
    now = time.time()
    assert server.clean_uploads(now + 3500) == 0
    assert server.clean_uploads(now + 3700) == 1
    assert [m["code"] for m in server.list_uploads()] == [unused["code"]]
    assert server.clean_uploads(now + 24 * 3600 + 60) == 1
    assert not list(server.UPLOADS.iterdir())
    with pytest.raises(ToolError, match="no uploaded files"):
        server.load_upload(used["code"])


def test_bad_upload_codes():
    for code in ("../../secret", "F-0000", "latest"):
        with pytest.raises(ToolError):
            server.load_upload(code)


# ---------------------------------------------------------------- the upload page

PASS = "web test passphrase"


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    server._sessions.clear()
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    yield client
    monkeypatch.setattr(server, "PROVIDER", None)


def csrf_of(page):
    return re.search(r'name="csrf" value="([^"]+)"', page)[1]


def test_upload_page_flow(web):
    assert web.get("/upload", follow_redirects=False).headers["location"] == "/settings/upload"
    page = web.get("/settings/upload").text
    assert "Open files" in page and 'value="/settings/upload"' in page
    r = web.post("/settings/login", data={"passphrase": PASS, "next": "/settings/upload"},
                 headers={"origin": "http://localhost"}, follow_redirects=False)
    assert r.headers["location"] == "/settings/upload"
    page = web.get("/settings/upload").text
    assert "Choose a file" in page and 'enctype="multipart/form-data"' in page
    token = csrf_of(page)
    r = web.post("/settings/upload", data={"csrf": token}, files={"file": ("cat.jpg", JPG, "image/jpeg")},
                 headers={"origin": "http://localhost"})
    assert "cat.jpg is uploaded" in r.text and "Not used yet" in r.text
    code = server.list_uploads()[0]["code"]
    assert f"code {code}" in r.text
    r = web.post("/settings/upload", data={"csrf": token}, files={"file": ("cat.jpg", EXE, "image/jpeg")},
                 headers={"origin": "http://localhost"})
    assert "wasn&#x27;t uploaded" in r.text and "really a program" in r.text
    r = web.post("/settings/upload", data={"csrf": token}, files={"file": ("logo.svg", b"<svg/>", "image/svg+xml")},
                 headers={"origin": "http://localhost"})
    assert "Check this: svg images can hold scripts" in r.text
    r = web.post("/settings/upload", data={"csrf": token, "action": "delete", "code": code},
                 headers={"origin": "http://localhost"})
    assert code not in r.text and len(server.list_uploads()) == 1


def test_upload_needs_session_token_and_size(web, monkeypatch):
    r = web.post("/settings/upload", files={"file": ("a.txt", b"x")}, follow_redirects=False)
    assert r.status_code == 303 and not server.list_uploads()
    web.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"})
    token = csrf_of(web.get("/settings/upload").text)
    assert web.post("/settings/upload", data={"csrf": "wrong"}, files={"file": ("a.txt", b"x")},
                    headers={"origin": "http://localhost"}).status_code == 403
    assert web.post("/settings/upload", data={"csrf": token}, files={"file": ("a.txt", b"x")},
                    headers={"origin": "https://evil.example"}).status_code == 403
    monkeypatch.setenv("ATTACH_MAX_MB", "1")
    r = web.post("/settings/upload", data={"csrf": token}, files={"file": ("big.txt", b"a" * 1_200_000)},
                 headers={"origin": "http://localhost"})
    assert "too big" in r.text and not server.list_uploads()


def test_settings_page_links_to_uploads(web):
    web.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"})
    assert 'href="/settings/upload"' in web.get("/settings").text


def test_upload_page_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("LOGIN_PASSPHRASE", PASS)
    monkeypatch.setenv("UPLOAD_PAGE", "off")
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    assert client.get("/upload").status_code == 404 and client.get("/settings/upload").status_code == 404
    monkeypatch.setattr(server, "PROVIDER", None)


def test_upload_page_takes_files_over_one_megabyte(web):
    web.post("/settings/login", data={"passphrase": PASS}, headers={"origin": "http://localhost"})
    token = csrf_of(web.get("/settings/upload").text)
    r = web.post("/settings/upload", data={"csrf": token}, files={"file": ("scan.pdf", PDF + b"x" * 20_000_000)},
                 headers={"origin": "http://localhost"})
    assert "scan.pdf is uploaded" in r.text and server.list_uploads()[0]["size"] > 20_000_000


def test_uploads_can_be_found_by_name(mailbox):
    server.save_upload("Beach-day.jpg", JPG)
    server.save_upload("Invoice October.pdf", PDF)
    server.save_upload("Invoice September.pdf", PDF)
    assert "Beach-day.jpg" in server.draft(subject="x", body="x", attach_upload=["beach-day.JPG"])
    assert "Invoice October.pdf" in server.draft(subject="x", body="x", attach_upload=["october"])
    with pytest.raises(ToolError, match="Several uploaded files match"):
        server.draft(subject="x", body="x", attach_upload=["invoice"])
    with pytest.raises(ToolError, match="Waiting: .*Beach-day.jpg"):
        server.draft(subject="x", body="x", attach_upload=["holiday.jpg"])


def test_the_ai_can_list_waiting_files():
    assert "No files are waiting" in server.draft(mode="files")
    server.save_upload("Beach-day.jpg", JPG)
    server.save_upload("logo.svg", b"<svg/>")
    out = server.draft(mode="files")
    assert out.index("logo.svg") < out.index("Beach-day.jpg") and "not used yet" in out and "SUSPECT: svg" in out
