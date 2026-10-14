"""Calendar invites: attaches an .ics invite to a draft, so the receiver can add the meeting in one tap."""

import datetime as dt
import uuid


def setup(api):
    organizer = api.setting("CALENDAR_INVITE_ORGANIZER")   # optional: your email address, shown as the organizer

    @api.tool(api.WRITE)
    def add_invite(draft_id: str, title: str, start: str, minutes: int = 30, location: str = "") -> str:
        """Attach a calendar invite (.ics) to a draft. start: ISO time with the UTC offset, e.g.
        '2026-10-20T15:00:00+01:00'. Nothing is sent; the draft gets a new ID."""
        try:
            begin = dt.datetime.fromisoformat(start)
        except ValueError:
            raise api.ToolError(f"Bad time {start!r}. Use ISO with the UTC offset, e.g. 2026-10-20T15:00:00+01:00.")
        if begin.tzinfo is None:
            raise api.ToolError("Add the UTC offset to the time, e.g. +01:00.")
        if not 5 <= minutes <= 24 * 60:
            raise api.ToolError("minutes must be between 5 and 1440.")
        stamp = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        clean = lambda text: text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", " ")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Selfhost Mail MCP//calendar_invite//EN",
                 "METHOD:PUBLISH", "BEGIN:VEVENT", f"UID:{uuid.uuid4()}", f"DTSTAMP:{stamp(dt.datetime.now(dt.timezone.utc))}",
                 f"DTSTART:{stamp(begin)}", f"DTEND:{stamp(begin + dt.timedelta(minutes=minutes))}",
                 f"SUMMARY:{clean(title)}"]
        if location:
            lines.append(f"LOCATION:{clean(location)}")
        if organizer:
            lines.append(f"ORGANIZER:mailto:{organizer}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        ics = ("\r\n".join(lines) + "\r\n").encode()
        name = "invite.ics"
        new_id = api.edit_draft(draft_id, lambda msg: api.add_file(msg, name, "text/calendar", ics))
        return f"Invite '{title}' attached as {name}. Draft ID is now {new_id}. Nothing was sent."
