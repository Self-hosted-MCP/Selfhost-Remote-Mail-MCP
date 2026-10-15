# SPDX-License-Identifier: AGPL-3.0-only
"""Photo size (hd / smaller) and iPhone HEIC photos, which only become JPG after the user says yes."""
import base64
import email
import io
import random
from email.policy import default as POLICY

import pillow_heif
import shutil

import pytest
from PIL import Image

from mcp.server.mcpserver.exceptions import ToolError

from selfhost_remote_mail_mcp import server

pillow_heif.register_heif_opener()


@pytest.fixture(autouse=True)
def no_uploads():
    shutil.rmtree(server.UPLOADS, ignore_errors=True)
    yield
    shutil.rmtree(server.UPLOADS, ignore_errors=True)


def photo(fmt: str, size=(4000, 3000), mode="RGB") -> bytes:
    """A photo-like picture (smooth colours plus a little grain), so sizes behave like real photos."""
    random.seed(1)
    small = Image.new(mode, (64, 48))
    small.putdata([tuple(random.randrange(256) for _ in mode) for _ in range(64 * 48)])
    image = small.resize(size, Image.BICUBIC)
    out = io.BytesIO()
    image.save(out, fmt, **({"quality": 95} if fmt in ("JPEG", "WEBP", "HEIF") else {}))
    return out.getvalue()


def content(name, data):
    return {"name": name, "base64": base64.b64encode(data).decode()}


def attachments(mailbox):
    msg = email.message_from_bytes(list(mailbox["Drafts"].values())[-1], policy=POLICY)
    return {p.get_filename(): p.get_content() for p in msg.iter_attachments()}


def test_hd_sends_photos_as_they_are(mailbox):
    jpg = photo("JPEG")
    server.draft(subject="x", body="x", attach_content=[content("beach.jpg", jpg)])
    data = attachments(mailbox)["beach.jpg"]
    assert Image.open(io.BytesIO(data)).size == (4000, 3000)


def test_smaller_resizes_and_keeps_formats(mailbox):
    jpg, png = photo("JPEG"), photo("PNG", mode="RGBA")
    server.save_upload("logo.png", png)            # big files come through the upload page
    out = server.draft(subject="x", body="x", photos="smaller", attach_upload=["logo.png"],
                       attach_content=[content("beach.jpg", jpg), content("notes.txt", "hi".encode())])
    files = attachments(mailbox)
    small = Image.open(io.BytesIO(files["beach.jpg"]))
    assert max(small.size) == 2560 and len(files["beach.jpg"]) < len(jpg)
    logo = Image.open(io.BytesIO(files["logo.png"]))
    assert logo.format == "PNG" and logo.mode == "RGBA" and max(logo.size) == 2560   # transparency kept
    assert files["notes.txt"] == "hi" and "beach.jpg" in out


def test_small_photos_stay_untouched(mailbox):
    tiny = photo("JPEG", size=(640, 480))
    server.draft(subject="x", body="x", photos="smaller", attach_content=[content("small.jpg", tiny)])
    assert Image.open(io.BytesIO(attachments(mailbox)["small.jpg"])).size == (640, 480)


def test_heic_asks_first_then_converts_or_keeps(mailbox):
    heic = photo("HEIF", size=(1200, 900))
    with pytest.raises(ToolError) as err:
        server.draft(subject="x", body="x", attach_content=[content("IMG_0042.HEIC", heic)])
    assert "Ask the user first" in str(err.value) and 'heic="jpg"' in str(err.value)
    assert not mailbox["Drafts"]
    out = server.draft(subject="x", body="x", heic="jpg", attach_content=[content("IMG_0042.HEIC", heic)])
    files = attachments(mailbox)
    assert list(files) == ["IMG_0042.jpg"] and Image.open(io.BytesIO(files["IMG_0042.jpg"])).format == "JPEG"
    assert Image.open(io.BytesIO(files["IMG_0042.jpg"])).size == (1200, 900)   # full size
    assert "IMG_0042.jpg" in out
    server.draft(subject="x", body="x", heic="keep", attach_content=[content("IMG_0042.HEIC", heic)])
    assert list(attachments(mailbox)) == ["IMG_0042.HEIC"]


def test_over_the_limit_the_ai_offers_smaller(mailbox, monkeypatch):
    monkeypatch.setenv("ATTACH_MAX_MB", "1")
    jpg = photo("JPEG", size=(3000, 2250))
    assert len(jpg) > 1024 * 1024
    with pytest.raises(ToolError) as err:
        server.draft(subject="x", body="x", attach_content=[content("big.jpg", jpg)])
    assert 'photos="smaller"' in str(err.value) and "Ask the user" in str(err.value)
    server.draft(subject="x", body="x", photos="smaller", attach_content=[content("big.jpg", jpg)])
    assert max(Image.open(io.BytesIO(attachments(mailbox)["big.jpg"])).size) == 2560


def test_bad_choices_are_refused():
    with pytest.raises(ToolError, match='"hd"'):
        server.draft(subject="x", body="x", photos="tiny")
    with pytest.raises(ToolError, match='"jpg" or "keep"'):
        server.draft(subject="x", body="x", heic="png")
