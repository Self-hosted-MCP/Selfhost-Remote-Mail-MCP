"""Calendar invites: attaches an .ics invite to a draft, so the receiver can add the meeting in one tap."""

import datetime as dt
import uuid

from selfhost_remote_mail_mcp.i18n import N_

SETTINGS = [
    {"key": "ORGANIZER", "label": N_("Your email address, shown as the organizer"),
     "help": N_("Calendar apps show it as who invited them.")},
]


def fold(line: str) -> str:
    """Calendar files keep lines to 75 bytes; longer ones continue on the next line after a space."""
    out, cur = [], b""
    for ch in line:
        b = ch.encode()
        if len(cur) + len(b) > (75 if not out else 74):
            out.append(cur.decode())
            cur = b""
        cur += b
    out.append(cur.decode())
    return "\r\n ".join(out)


def setup(api):
    @api.tool(api.WRITE)
    def add_invite(draft_id: str, title: str, start: str, minutes: int = 30, location: str = "",
                   details: str = "") -> str:
        """Attach a calendar invite (.ics) to a draft. start: ISO time with the UTC offset, e.g.
        '2026-10-20T15:00:00+01:00'. details: optional notes shown in the calendar event (like a video call
        link the user gave you). Nothing is sent; the draft gets a new ID."""
        try:
            begin = dt.datetime.fromisoformat(start)
        except ValueError:
            raise api.ToolError(f"Bad time {start!r}. Use ISO with the UTC offset, e.g. 2026-10-20T15:00:00+01:00.")
        if begin.tzinfo is None:
            raise api.ToolError("Add the UTC offset to the time, e.g. +01:00.")
        if not 5 <= minutes <= 24 * 60:
            raise api.ToolError("minutes must be between 5 and 1440.")
        stamp = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        def clean(text: str) -> str:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)   # no other control characters
            return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Selfhost Mail MCP//calendar_invite//EN",
                 "METHOD:PUBLISH", "BEGIN:VEVENT", f"UID:{uuid.uuid4()}", f"DTSTAMP:{stamp(dt.datetime.now(dt.timezone.utc))}",
                 f"DTSTART:{stamp(begin)}", f"DTEND:{stamp(begin + dt.timedelta(minutes=minutes))}",
                 f"SUMMARY:{clean(title)}"]
        if location:
            lines.append(f"LOCATION:{clean(location)}")
        if details:
            lines.append(f"DESCRIPTION:{clean(details)}")
        organizer = api.setting("CALENDAR_INVITE_ORGANIZER")   # optional: your address, shown as the organizer
        if organizer:
            lines.append(f"ORGANIZER:mailto:{clean(organizer.split()[0])}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        ics = ("\r\n".join(fold(line) for line in lines) + "\r\n").encode()
        name = "invite.ics"
        new_id = api.edit_draft(draft_id, lambda msg: api.add_file(msg, name, "text/calendar", ics))
        return f"Invite '{title}' attached as {name}. Draft ID is now {new_id}. Nothing was sent."
