# SPDX-License-Identifier: AGPL-3.0-only
"""Batch 3 library add-ons: caldav (a fake calendar server) and webhooks (a fake receiver)."""
import base64
import datetime as dt
import hashlib
import hmac
import json
import time
from email.utils import formatdate
from pathlib import Path

import pytest

from conftest import FakeIMAP
from selfhost_remote_mail_mcp import server

pytest.importorskip("caldav")
icalendar = pytest.importorskip("icalendar")


@pytest.fixture(scope="module", autouse=True)
def loaded():
    for name in ("caldav", "webhooks"):
        if name not in server.LOADED_ADDONS:
            server.load_addons(name, Path("/nonexistent"))
    yield


def tool(name, **args):
    return server.mcp._tool_manager.get_tool(name).fn(**args)


# ---------------------------------------------------------------- caldav

class FakeEvent:
    def __init__(self, **fields):
        self.icalendar_component = icalendar.Event()
        for k, v in fields.items():
            self.icalendar_component.add(k, v)


class FakeCalendar:
    def __init__(self, name, items):
        self.name, self.items, self.added = name, items, []

    def get_display_name(self):
        return self.name

    def search(self, start, end, event, expand):
        assert event and expand
        return [e for e in self.items if start <= _as(e.icalendar_component["DTSTART"].dt, start.tzinfo) < end]

    def add_event(self, ical):
        self.added.append(ical)


def _as(v, tz):
    return v if isinstance(v, dt.datetime) else dt.datetime.combine(v, dt.time(0), tz)


@pytest.fixture
def cal(monkeypatch):
    import caldav
    tz = dt.timezone.utc
    day = dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()))   # next Monday
    items = [FakeEvent(summary="Call with Sam", dtstart=dt.datetime.combine(day, dt.time(10), tz),
                       dtend=dt.datetime.combine(day, dt.time(11), tz), location="Zoom"),
             FakeEvent(summary="Lunch", dtstart=dt.datetime.combine(day, dt.time(13), tz),
                       dtend=dt.datetime.combine(day, dt.time(14), tz)),
             FakeEvent(summary="Holiday (free)", dtstart=day, dtend=day + dt.timedelta(days=1), transp="TRANSPARENT"),
             FakeEvent(summary="Cancelled thing", dtstart=dt.datetime.combine(day, dt.time(16), tz),
                       dtend=dt.datetime.combine(day, dt.time(17), tz), status="CANCELLED")]
    calendars = [FakeCalendar("Work", items), FakeCalendar("Home", [])]

    class Client:
        def __init__(self, url, username, password, timeout):
            if password == "wrong":
                from caldav.lib.error import AuthorizationError
                raise AuthorizationError("401")
        def principal(self):
            return type("P", (), {"calendars": lambda self: calendars})()

    monkeypatch.setattr(caldav, "DAVClient", Client)
    for k, v in {"URL": "https://caldav.example.test/", "USERNAME": "me@example.com", "PASSWORD": "app-pass"}.items():
        monkeypatch.setenv(f"CALDAV_{k}", v)
    return day, calendars


def test_events_free_times_and_adding(cal, monkeypatch):
    day, calendars = cal
    out = tool("calendar_events", start_date=day.isoformat(), days=1)
    assert "10:00-11:00 · Call with Sam · Zoom" in out and "Lunch" in out and "Cancelled" not in out
    assert out.endswith("(times in UTC)")
    free = tool("calendar_free", start_date=day.isoformat(), days=1, minutes=30)
    assert free.startswith(f"{day:%a %d %b}: 09:00-10:00, 11:00-13:00, 14:00-18:00")   # the free holiday doesn't block
    out = tool("add_event", title="Dentist, at 3", start=f"{day.isoformat()}T15:00:00+00:00", minutes=45)
    assert out.startswith("Added:") and "No one was invited" in out
    ical = calendars[0].added[-1]
    assert "SUMMARY:Dentist\\, at 3" in ical and "DTEND:" in ical and "ATTENDEE" not in ical and "ORGANIZER" not in ical
    monkeypatch.setenv("CALDAV_CALENDAR", "Home")
    tool("add_event", title="Gym", start=f"{day.isoformat()}T18:00:00+00:00")
    assert calendars[1].added


def test_calendar_errors_are_one_clear_line(cal, monkeypatch):
    day, _ = cal
    with pytest.raises(server.ToolError, match="must be within the next year"):
        tool("add_event", title="x", start="2099-01-01T10:00:00+00:00")
    monkeypatch.setenv("CALDAV_PASSWORD", "wrong")
    with pytest.raises(server.ToolError, match="login failed"):
        tool("calendar_events")
    monkeypatch.setenv("CALDAV_PASSWORD", "app-pass")
    monkeypatch.setenv("CALDAV_CALENDAR", "Nope")
    with pytest.raises(server.ToolError, match="no calendar called"):
        tool("calendar_events")
    monkeypatch.setenv("CALDAV_CALENDAR", "")
    monkeypatch.setenv("CALDAV_WORK_HOURS", "18-09")
    with pytest.raises(server.ToolError, match="before the end"):
        tool("calendar_free", start_date=day.isoformat())


# ---------------------------------------------------------------- webhooks

@pytest.fixture
def hook(monkeypatch):
    monkeypatch.setenv("WEBHOOKS_URL", "https://hooks.example.test/in/SECRET-TOKEN")
    monkeypatch.setenv("WEBHOOKS_SECRET", "s" * 32)
    job = next(j for j in server.ADDON_JOBS if j["addon"] == "webhooks")
    with server.AddonAPI("webhooks").store() as data:
        data.clear()
    sent, answers = [], []

    class Resp:
        def __init__(self, status): self.status, self.headers = status, {}
        def read(self, n): return b""
        def __enter__(self): return self
        def __exit__(self, *e): pass

    class Opener:
        def open(self, req, timeout):
            sent.append(req)
            status = answers.pop(0) if answers else 200
            if status == "down":
                raise OSError("down")
            if status >= 400:
                import urllib.error
                raise urllib.error.HTTPError(req.full_url, status, "x", {}, None)
            return Resp(status)

    monkeypatch.setattr(server.urllib.request, "build_opener", lambda *h: Opener())

    def run():
        token = server.ADDON_JOB.set(job["name"])
        try:
            job["func"]()
        finally:
            server.ADDON_JOB.reset(token)
    return run, sent, answers


def new_mail(mailbox, subject="Hello", sender="Sam <sam@shop.test>"):
    import email.message
    msg = email.message.EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, "me@example.com", subject
    msg["Date"], msg["Message-ID"] = formatdate(localtime=True), f"<w{time.time_ns()}@shop.test>"
    msg.set_content("PRIVATE BODY")
    with FakeIMAP.lock:
        uid = FakeIMAP.next_uid
        FakeIMAP.next_uid += 1
    mailbox["INBOX"][uid] = msg.as_bytes()


def test_webhook_sends_signed_metadata_only(mailbox, hook):
    run, sent, _ = hook
    new_mail(mailbox)
    run()   # the first run only notes where to start
    assert sent == []
    new_mail(mailbox, subject="Your code is 123456")
    run()
    req = sent[-1]
    body = req.data
    event = json.loads(body)
    assert event["type"] == "email.received" and event["subject"] == "Your code is 123456"
    assert event["from"] == "Sam <sam@shop.test>" and b"PRIVATE BODY" not in body
    h = {k.lower(): v for k, v in req.header_items()}
    mac = hmac.new(b"s" * 32, f"{h['webhook-id']}.{h['webhook-timestamp']}.".encode() + body, hashlib.sha256).digest()
    assert h["webhook-signature"] == "v1," + base64.b64encode(mac).decode()


def test_webhook_retries_keeps_the_id_and_drops_refused(mailbox, hook, monkeypatch):
    run, sent, answers = hook
    run()
    new_mail(mailbox)
    answers[:] = [503]
    run()
    first = {k.lower(): v for k, v in sent[-1].header_items()}["webhook-id"]
    answers[:] = ["down"]
    run()
    answers[:] = [200]
    run()
    assert {k.lower(): v for k, v in sent[-1].header_items()}["webhook-id"] == first and len(sent) == 3
    new_mail(mailbox)
    answers[:] = [404]
    run()
    count = len(sent)
    run()
    assert len(sent) == count   # a refused one isn't retried


def test_webhook_subject_off_and_bad_secret(mailbox, hook, monkeypatch):
    run, sent, _ = hook
    run()
    monkeypatch.setenv("WEBHOOKS_SUBJECT", "off")
    new_mail(mailbox, subject="Password reset")
    run()
    assert json.loads(sent[-1].data)["subject"] is None
    monkeypatch.setenv("WEBHOOKS_SECRET", "short")
    new_mail(mailbox)
    count = len(sent)
    run()
    assert len(sent) == count   # no valid secret: nothing is sent


def test_setup_page_url_is_allowed_for_http(monkeypatch):
    monkeypatch.delenv("WEBHOOKS_URL", raising=False)
    server.save_addon_settings("webhooks", {"WEBHOOKS_URL": "http://n8n:5678/webhook/x"})
    api = server.AddonAPI("webhooks")
    seen = []
    class Opener:
        def open(self, req, timeout):
            seen.append(req.full_url)
            class R:
                status, headers = 200, {}
                def read(self, n): return b""
                def __enter__(self): return self
                def __exit__(self, *e): pass
            return R()
    monkeypatch.setattr(server.urllib.request, "build_opener", lambda *h: Opener())
    assert api.http("POST", "http://n8n:5678/webhook/x", data=b"{}")[0] == 200
    server.ADDON_SETTINGS_FILE.unlink()


# ---------------------------------------------------------------- the review's cases

def test_a_bad_time_zone_never_half_adds_an_event(cal, monkeypatch):
    day, calendars = cal
    before = len(calendars[0].added)
    monkeypatch.setenv("CALDAV_TIMEZONE", "Europe/Lisbn")
    with pytest.raises(server.ToolError, match="time zone"):
        tool("add_event", title="x", start=f"{day.isoformat()}T15:00:00+00:00")
    assert len(calendars[0].added) == before


def test_free_times_never_in_the_past(cal):
    out = tool("calendar_free", start_date="2020-01-06", days=1)
    assert "2020" not in out and "Jan" not in out.split(":")[0] or "No weekdays" in out


def test_webhook_400_is_retried_and_status_and_a_long_pause_resets(mailbox, hook, monkeypatch):
    run, sent, answers = hook
    run()
    new_mail(mailbox)
    answers[:] = [400]
    run()
    answers[:] = [200]
    run()
    assert len(sent) == 2   # Make answers 400 when busy: tried again
    status = tool("webhooks")
    assert status.startswith("Webhooks to hooks.example.test: 1 delivered, 0 waiting.") and "SECRET-TOKEN" not in status
    with server.AddonAPI("webhooks").store() as data:
        data["last_run"] = time.time() - 3 * 86400   # off for days
    new_mail(mailbox)
    count = len(sent)
    run()   # starts fresh: the mail from while it was off isn't sent
    assert len(sent) == count
