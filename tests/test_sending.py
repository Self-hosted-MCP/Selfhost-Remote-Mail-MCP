# SPDX-License-Identifier: AGPL-3.0-only
"""Sending, limits and scheduled send, against the fake mailbox in conftest.py."""
import datetime as dt
import email
import re
import threading
from email.policy import default as POLICY

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from conftest import FakeSMTP
from selfhost_remote_mail_mcp import server

NOW = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
LATER = NOW + dt.timedelta(hours=3)


def new_id(text: str, marker: str) -> str:
    return re.search(r"Drafts#\d+", text.split(marker)[1])[0]


def make_draft(subject="Hi", to=("you@example.org",)) -> str:
    return new_id(server.draft(to=list(to), subject=subject, body="Hello there.\n\nBest,"), "ID: ")


def schedule(draft_id: str, when: dt.datetime = LATER) -> str:
    return new_id(server.schedule_send(draft_id, when.isoformat()), "New draft ID: ")


def header(mailbox, draft_id, name):
    uid = int(draft_id.split("#")[1])
    return email.message_from_bytes(mailbox["Drafts"][uid], policy=POLICY).get(name)


def write_log(rows):
    server.STATE_DIR.mkdir(parents=True, exist_ok=True)
    server.SENT_LOG.write_text("".join("\t".join(r) + "\n" for r in rows))


def ago(minutes):
    """A log time `minutes` ago, but never before today's midnight, so the daily-limit tests work at any hour."""
    now = dt.datetime.now()
    return max(now - dt.timedelta(minutes=minutes), now.replace(hour=0, minute=0, second=0, microsecond=0)
               ).isoformat(timespec="seconds")


# ---- sending now

def test_send_moves_to_sent_and_logs_message_id(mailbox):
    d = make_draft("One")
    mid = header(mailbox, d, "Message-ID")
    assert server.send_email(d).startswith("Sent to you@example.org")
    assert len(FakeSMTP.sent) == 1
    assert not mailbox["Drafts"] and len(mailbox["Sent"]) == 1
    row = server.SENT_LOG.read_text().strip().split("\t")
    assert row[3] == server.log_key(mid) and mid not in server.SENT_LOG.read_text()
    assert row[1] == "1 recipient(s)" and row[2] == ""          # private by default: no who, no subject


def test_minute_limit_blocks_and_keeps_draft(mailbox):
    server.send_email(make_draft("A"))
    server.send_email(make_draft("B"))
    third = make_draft("C")
    with pytest.raises(server.MinuteLimit):
        server.send_email(third)
    assert int(third.split("#")[1]) in mailbox["Drafts"]


def test_daily_limit_counts_new_and_old_log_rows(mailbox):
    write_log([[ago(5 + i), "a", "b", f"<x{i}@t>"] for i in range(5)])
    with pytest.raises(ToolError, match="Daily send limit"):
        server.send_email(make_draft())
    write_log([[ago(5 + i), "a", "b"] for i in range(5)])   # rows from before Message-IDs were logged
    with pytest.raises(ToolError, match="Daily send limit"):
        server.send_email(make_draft())


def test_never_sends_same_message_twice(mailbox):
    d = make_draft("Dup")
    write_log([[ago(60), "a", "Dup", header(mailbox, d, "Message-ID")]])
    assert "already sent" in server.send_email(d)
    assert not FakeSMTP.sent and not mailbox["Drafts"]


def test_parallel_sends_respect_the_limit():
    ids = [make_draft(f"T{i}") for i in range(3)]
    errors = []

    def go(i):
        try:
            server.send_email(i)
        except ToolError as e:
            errors.append(e)
    threads = [threading.Thread(target=go, args=(i,)) for i in ids]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(FakeSMTP.sent) == 2 and len(errors) == 1


# ---- schedule_send checks

@pytest.mark.parametrize("value, error", [
    ((NOW + dt.timedelta(days=3)).isoformat()[:19], "time zone"),
    ("2020-01-01T09:00:00+00:00", "past"),
    ("tomorrow 9am", "Bad time"),
    ((NOW + dt.timedelta(days=400)).isoformat(), "year"),
])
def test_schedule_rejects_bad_times(value, error):
    with pytest.raises(ToolError, match=error):
        server.schedule_send(make_draft(), value)


def test_schedule_needs_a_draft_with_recipients():
    with pytest.raises(ToolError, match="send_at"):
        server.schedule_send(make_draft())
    with pytest.raises(ToolError, match="Only drafts"):
        server.schedule_send("INBOX#1", LATER.isoformat())
    no_one = new_id(server.draft(subject="No one", body="x"), "ID: ")
    with pytest.raises(ToolError, match="no recipients"):
        server.schedule_send(no_one, LATER.isoformat())


def test_schedule_list_edit_cancel(mailbox):
    d = new_id(server.schedule_send(make_draft("Later"), LATER.astimezone(
        dt.timezone(dt.timedelta(hours=-7))).isoformat()), "New draft ID: ")
    assert header(mailbox, d, server.SCHEDULE_HEADER)
    assert sum(b"Later" in r for r in mailbox["Drafts"].values()) == 1
    listed = server.scheduled()
    assert "Later" in listed and "HELD" not in listed
    edited = server.draft(edit=d, body="Changed.\n\nBest,")
    d = new_id(edited, "ID: ")
    assert "Still scheduled" in edited and header(mailbox, d, server.SCHEDULE_HEADER)
    d = server.schedule_send(d, cancel=True).split("stays as ")[1].rstrip(".")
    assert not header(mailbox, d, server.SCHEDULE_HEADER)
    assert server.scheduled() == "Nothing is scheduled."
    assert "wasn't scheduled" in server.schedule_send(d, cancel=True)


# ---- the scheduler

def test_scheduler_sends_when_due_and_strips_internal_headers(mailbox):
    schedule(make_draft("Due"))
    assert server.run_scheduled_once() == [] and not FakeSMTP.sent
    log = server.run_scheduled_once(now=LATER + dt.timedelta(seconds=30))
    assert log[0].startswith("sent") and len(FakeSMTP.sent) == 1
    assert all(FakeSMTP.sent[0].get(h) is None for h in server.INTERNAL_HEADERS)
    assert not mailbox["Drafts"]


def test_scheduler_holds_missed_emails_until_rescheduled(mailbox):
    schedule(make_draft("Missed"))
    log = server.run_scheduled_once(now=LATER + dt.timedelta(hours=3))
    assert not FakeSMTP.sent and "missed" in log[0]
    assert "HELD" in server.scheduled() and "server was down" in server.scheduled()
    assert server.run_scheduled_once(now=LATER + dt.timedelta(hours=4)) == []
    held = next(f"Drafts#{u}" for u in mailbox["Drafts"])
    assert not header(mailbox, schedule(held), server.SCHEDULE_ERROR)


def test_scheduler_holds_on_smtp_failure():
    schedule(make_draft("Fail"))
    FakeSMTP.fail = True
    log = server.run_scheduled_once(now=LATER + dt.timedelta(minutes=1))
    assert log[0].startswith("failed")
    assert "smtp down" in server.scheduled()
    assert not server.SENT_LOG.exists()


def test_scheduler_waits_on_minute_limit_then_sends(mailbox):
    for i in range(3):
        schedule(make_draft(f"S{i}"))
    log = server.run_scheduled_once(now=LATER + dt.timedelta(minutes=1))
    assert len(FakeSMTP.sent) == 2 and any(line.startswith("waiting") for line in log)
    assert "HELD" not in server.scheduled()
    rows = [line.split("\t") for line in server.SENT_LOG.read_text().splitlines()]
    write_log([[ago(2), *r[1:]] for r in rows])
    server.run_scheduled_once(now=LATER + dt.timedelta(minutes=2))
    assert len(FakeSMTP.sent) == 3 and not mailbox["Drafts"]


def test_two_schedulers_at_once_send_once():
    schedule(make_draft("Once"))
    threads = [threading.Thread(target=server.run_scheduled_once, kwargs={"now": LATER + dt.timedelta(minutes=1)})
               for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(FakeSMTP.sent) == 1


def test_scheduler_holds_unreadable_time(mailbox):
    d = make_draft("Weird")
    uid = int(d.split("#")[1])
    msg = email.message_from_bytes(mailbox["Drafts"][uid], policy=POLICY)
    msg[server.SCHEDULE_HEADER] = "next tuesday"
    mailbox["Drafts"][uid] = msg.as_bytes()
    log = server.run_scheduled_once()
    assert not FakeSMTP.sent and "unreadable" in log[0]


# ---- privacy and safety settings

def test_log_details_only_when_asked(monkeypatch):
    monkeypatch.setenv("SEND_LOG_DETAILS", "on")
    server.send_email(make_draft("Visible"))
    row = server.SENT_LOG.read_text().strip().split("\t")
    assert row[1] == "you@example.org" and row[2] == "Visible"


def test_allowed_recipients(monkeypatch, mailbox):
    monkeypatch.setenv("SEND_ALLOWED_RECIPIENTS", "@example.org, boss@work.test")
    server.send_email(make_draft("Ok", to=("you@example.org",)))
    server.send_email(make_draft("Ok2", to=("BOSS@work.test",)))
    stranger = make_draft("No", to=("you@example.org", "x@evil.test"))
    with pytest.raises(ToolError, match="x@evil.test"):
        server.send_email(stranger)
    with pytest.raises(ToolError, match="allowed list"):
        server.schedule_send(stranger, LATER.isoformat())
    assert len(FakeSMTP.sent) == 2


def test_read_only_mode_blocks_every_change(monkeypatch, mailbox):
    d = make_draft("Before")
    monkeypatch.setenv("MAIL_READ_ONLY", "on")
    assert "READ-ONLY MODE" in server.accounts()
    for call in (lambda: server.send_email(d), lambda: server.draft(to=["a@b.test"], subject="x", body="y"),
                 lambda: server.action("pin", [d]), lambda: server.schedule_send(d, LATER.isoformat())):
        with pytest.raises(ToolError, match="read-only mode"):
            call()
    assert not FakeSMTP.sent and len(mailbox["Drafts"]) == 1
    assert server.run_scheduled_once(now=LATER) == []


def test_email_text_is_marked_untrusted(mailbox):
    d = make_draft("Hello")
    out = server.thread(d)
    assert server.UNTRUSTED_START in out and server.UNTRUSTED_END in out


def test_daily_limit_counts_each_mailbox_on_its_own(monkeypatch, mailbox):
    monkeypatch.setenv("MAIL_2_ADDRESS", "work@example.org")
    monkeypatch.setenv("MAIL_2_PASSWORD", "w")
    me, work = server.mailbox_key("me@example.com"), server.mailbox_key("work@example.org")
    write_log([[ago(5 + i), "1 recipient(s)", "", f"k{i}", me] for i in range(5)])   # me@ used all 5
    with pytest.raises(ToolError, match="me@example.com"):
        server.send_email(make_draft("Mine"))
    d = re.search(r"ID: (\S+)", server.draft(to=["x@y.test"], subject="Work", body="b", account="work@example.org"))[1]
    server.send_email(d)                                                                # work@ still may
    assert FakeSMTP.sent[-1].sent_from == "work@example.org"
    assert server.SENT_LOG.read_text().splitlines()[-1].split("\t")[4] == work
