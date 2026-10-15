# SPDX-License-Identifier: AGPL-3.0-only
"""Private details removed from new attachments: photo location, document authors. And the switches for it."""
import base64
import io
import zipfile

import pytest
from pypdf import PdfReader, PdfWriter

from selfhost_remote_mail_mcp import server


@pytest.fixture(autouse=True)
def default_switches():
    server.PREFS_FILE.unlink(missing_ok=True)
    yield
    server.PREFS_FILE.unlink(missing_ok=True)


def segment(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + (len(payload) + 2).to_bytes(2, "big") + payload


def exif(orientation: int) -> bytes:
    """IFD0 with Orientation and a GPS pointer, plus a GPS block holding a latitude marker."""
    ifd = (b"\x00\x02" + b"\x01\x12\x00\x03\x00\x00\x00\x01" + orientation.to_bytes(2, "big") + b"\x00\x00"
           + b"\x88\x25\x00\x04\x00\x00\x00\x01\x00\x00\x00\x26" + b"\x00\x00\x00\x00")
    return b"Exif\x00\x00" + b"MM\x00\x2a\x00\x00\x00\x08" + ifd + b"GPS 38.7223N 9.1393W"


def jpeg(*extra: bytes) -> bytes:
    return (b"\xff\xd8" + segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00") + b"".join(extra)
            + segment(0xDB, b"\x00" * 65) + segment(0xDA, b"\x00" * 10) + b"\x12\x34image\xff\xd9")


def test_jpeg_loses_location_but_keeps_rotation_and_pixels():
    photo = jpeg(segment(0xE1, exif(6)), segment(0xFE, b"taken at home"))
    clean = server.clean_jpeg(photo)
    assert b"GPS" not in clean and b"taken at home" not in clean
    assert clean.endswith(b"\x12\x34image\xff\xd9") and clean[2:4] == b"\xff\xe0"   # JFIF stays first
    app1 = clean[clean.index(b"Exif\x00\x00") + 6:]
    assert server._exif_orientation(app1) == 6
    assert server.clean_jpeg(jpeg()) is None                                         # nothing to remove
    assert server.check_new_file("photo.jpg", clean).level == "safe"


def test_png_and_webp_lose_text_and_exif():
    def chunk(kind, data):
        return len(data).to_bytes(4, "big") + kind + data + b"\x00\x00\x00\x00"
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", b"x" * 13) + chunk(b"tEXt", b"Author\x00Sam") + \
        chunk(b"eXIf", b"GPS") + chunk(b"IDAT", b"pixels") + chunk(b"IEND", b"")
    clean = server.clean_png(png)
    assert b"Sam" not in clean and b"GPS" not in clean and b"pixels" in clean and clean.endswith(b"IEND\x00\x00\x00\x00")
    body = (b"WEBP" + b"VP8X" + (10).to_bytes(4, "little") + bytes([0x0C]) + b"\x00" * 9
            + b"VP8 " + (4).to_bytes(4, "little") + b"pix!" + b"EXIF" + (3).to_bytes(4, "little") + b"GPS\x00")
    clean = server.clean_webp(b"RIFF" + len(body).to_bytes(4, "little") + body)
    assert b"GPS" not in clean and b"pix!" in clean and clean[20] == 0
    assert int.from_bytes(clean[4:8], "little") == len(clean) - 8


def make_pdf(**meta) -> bytes:
    w = PdfWriter()
    w.add_blank_page(100, 100)
    w.add_metadata(meta)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


def test_pdf_loses_author_keeps_title():
    clean = server.clean_pdf(make_pdf(**{"/Author": "Sam Secret", "/Title": "Invoice", "/Creator": "Word"}))
    meta = PdfReader(io.BytesIO(clean)).metadata or {}
    assert meta.get("/Title") == "Invoice" and "/Author" not in meta and "/Creator" not in meta
    assert "/Producer" not in meta and len(PdfReader(io.BytesIO(clean)).pages) == 1
    signed = make_pdf(**{"/Author": "Sam"}).replace(b"%%EOF", b"/ByteRange [0 1 2 3]\n%%EOF")
    assert server.clean_pdf(signed) is None


def office(core: bytes, app: bytes = b"<Properties><Company>Acme Ltd</Company></Properties>") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("word/document.xml", "<w:document>Hello</w:document>")
    return out.getvalue()


def test_office_files_lose_author_and_company():
    doc = office(b'<cp:coreProperties><dc:creator>Sam Secret</dc:creator><dc:title>Plan</dc:title>'
                 b'<cp:lastModifiedBy>Sam Secret</cp:lastModifiedBy></cp:coreProperties>')
    clean = server.clean_office(doc)
    with zipfile.ZipFile(io.BytesIO(clean)) as z:
        core, app = z.read("docProps/core.xml"), z.read("docProps/app.xml")
        assert z.read("word/document.xml") == b"<w:document>Hello</w:document>"
    assert b"Sam" not in core and b"<dc:title>Plan</dc:title>" in core and b"Acme" not in app
    assert server.check_new_file("plan.docx", clean).level == "safe"


def test_draft_cleans_new_files_and_says_so(mailbox):
    photo = jpeg(segment(0xE1, exif(1)))
    out = server.draft(subject="x", body="x", attach_content=[
        {"name": "beach.jpg", "base64": base64.b64encode(photo).decode()},
        {"name": "notes.txt", "text": "hi"}])
    assert "Privacy: beach.jpg: removed location and camera details" in out and "notes.txt: removed" not in out
    raw = list(mailbox["Drafts"].values())[-1]
    assert b"GPS 38" not in raw and base64.b64encode(b"GPS 38") not in raw


def test_switches_turn_cleaning_off(mailbox, monkeypatch):
    photo = jpeg(segment(0xE1, exif(1)))
    server.set_pref("remove_photo_location", False)
    out = server.draft(subject="x", body="x",
                       attach_content=[{"name": "beach.jpg", "base64": base64.b64encode(photo).decode()}])
    assert "Privacy" not in out
    server.set_pref("remove_photo_location", True)
    monkeypatch.setenv("REMOVE_DOCUMENT_DETAILS", "off")
    assert not server.pref_on("remove_document_details", "REMOVE_DOCUMENT_DETAILS")
    note = server.clean_new_file(server.check_new_file("a.heic", b"\x00\x00\x00\x18ftypheic" + b"\x00" * 16))
    assert "can't be cleaned" in note
