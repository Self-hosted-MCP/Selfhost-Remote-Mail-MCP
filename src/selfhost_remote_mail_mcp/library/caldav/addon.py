# SPDX-License-Identifier: AGPL-3.0-only
"""Calendar: reads your calendar, finds free times and adds events, for calendars that use CalDAV (iCloud, Fastmail, Nextcloud and others)."""

import datetime as dt
import re
import uuid

from selfhost_remote_mail_mcp.i18n import N_

NEEDS = ["caldav"]
SETTINGS = [
    {"key": "URL", "label": N_("Calendar server address"), "required": True,
     "help": N_("iCloud: https://caldav.icloud.com/ · Fastmail: https://caldav.fastmail.com/dav/ · Nextcloud: "
                "https://your-server/remote.php/dav/ · mailbox.org: https://dav.mailbox.org")},
    {"key": "USERNAME", "label": N_("Login name"), "required": True, "help": N_("Usually your email address.")},
    {"key": "PASSWORD", "label": N_("App password"), "required": True, "secret": True,
     "help": N_("Make one in your calendar provider's security settings. Not your normal password.")},
    {"key": "CALENDAR", "half": True, "label": N_("Calendar name"), "help": N_("Empty means the first one.")},
    {"key": "TIMEZONE", "half": True, "label": N_("Your time zone"), "help": N_("For example Europe/Lisbon. Empty means UTC.")},
    {"key": "WORK_HOURS", "half": True, "label": N_("Hours to offer as free"), "help": N_("Like 09-18 or 09:30-17:30. Empty means 09-18.")},
]
MAX_ADDS_A_DAY = 20


def setup(api):
    s = lambda key, default="": api.setting(f"CALDAV_{key}", default)

    def zone():
        from zoneinfo import ZoneInfo
        name = s("TIMEZONE").strip()
        try:
            return ZoneInfo(name) if name else dt.timezone.utc
        except Exception:
            raise api.ToolError(f"CALDAV_TIMEZONE={name!r} isn't a time zone name like Europe/Lisbon.")

    def zone_note(tz) -> str:
        return " (times in UTC)" if tz is dt.timezone.utc else ""

    def where() -> str:
        link = api.setup_link()
        return f"Check the calendar settings: {link}" if link else "Check the CALDAV_ settings."

    def calendar():
        """The chosen calendar, or a clear error. A new connection each time keeps things simple."""
        import caldav
        from caldav.lib import error
        url, user, password = s("URL").strip(), s("USERNAME").strip(), s("PASSWORD")
        if not (url and user and password):
            raise api.ToolError("The calendar isn't set up yet. " + where())
        from urllib.parse import urlparse
        import ipaddress
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            host = ""
        try:
            private = not ipaddress.ip_address(host).is_global
        except ValueError:
            private = host == "localhost" or host.endswith(".local") or "." not in host
        if not (url.lower().startswith("https://") or (url.lower().startswith("http://") and private)):
            raise api.ToolError("The calendar address must start with https:// (http only on your own network). " + where())
        try:
            extra = {"features": "icloud"} if host.endswith("icloud.com") else {}
            try:
                client = caldav.DAVClient(url=url, username=user, password=password, timeout=20, **extra)
            except TypeError:
                client = caldav.DAVClient(url=url, username=user, password=password, timeout=20)
            calendars = client.principal().calendars()
        except error.AuthorizationError:
            raise api.ToolError("The calendar login failed: check the login name and app password. " + where()) from None
        except Exception as exc:
            raise api.ToolError(f"The calendar server couldn't be reached ({type(exc).__name__}). " + where()) from None
        if not calendars:
            raise api.ToolError("No calendars were found on that account. " + where())
        wanted = s("CALENDAR").strip().lower()
        if not wanted:
            return calendars[0]
        for cal in calendars:
            try:
                name = (cal.get_display_name() or "").strip().lower()
            except Exception:
                name = ""
            if name == wanted:
                return cal
        raise api.ToolError(f"There's no calendar called {s('CALENDAR')!r}. " + where())

    def day_from(text: str, tz) -> dt.date:
        if not text.strip():
            return dt.datetime.now(tz).date()
        try:
            return dt.date.fromisoformat(text.strip()[:10])
        except ValueError:
            raise api.ToolError("start_date: use YYYY-MM-DD.")

    def as_dt(value, tz, end: bool = False):
        """An event time as an aware datetime in tz. Dates are all-day (start of that day); floating times count
        as the user's zone."""
        if isinstance(value, dt.datetime):
            return (value if value.tzinfo else value.replace(tzinfo=tz)).astimezone(tz)
        return dt.datetime.combine(value, dt.time(0), tz)

    def events(start: dt.date, days: int, tz) -> list[dict]:
        cal = calendar()
        begin = dt.datetime.combine(start, dt.time(0), tz)
        finish = dt.datetime.combine(start + dt.timedelta(days=days), dt.time(0), tz)
        try:
            found = cal.search(start=begin, end=finish, event=True, expand=True)
        except Exception as exc:
            raise api.ToolError(f"The calendar couldn't be read ({type(exc).__name__}). " + where()) from None
        out = []
        for item in found[:500]:
            comp = getattr(item, "icalendar_component", None)
            if comp is None or str(comp.get("STATUS", "")).upper() == "CANCELLED":
                continue
            dtstart = comp.get("DTSTART")
            if dtstart is None:
                continue
            raw_start = dtstart.dt
            all_day = not isinstance(raw_start, dt.datetime)
            if comp.get("DTEND") is not None:
                raw_end = comp.get("DTEND").dt
            elif comp.get("DURATION") is not None:
                raw_end = raw_start + comp.get("DURATION").dt
            else:
                raw_end = raw_start + (dt.timedelta(days=1) if all_day else dt.timedelta(0))
            title = re.sub(r"\s+", " ", str(comp.get("SUMMARY", "(no title)")))[:80]
            place = re.sub(r"\s+", " ", str(comp.get("LOCATION", "") or ""))[:60]
            out.append({"start": as_dt(raw_start, tz), "end": as_dt(raw_end, tz), "all_day": all_day,
                        "title": title, "place": place,
                        "free": str(comp.get("TRANSP", "")).upper() == "TRANSPARENT"})
        return sorted(out, key=lambda e: e["start"])

    def hours() -> tuple[dt.time, dt.time]:
        text = s("WORK_HOURS").strip() or "09-18"
        m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*-\s*(\d{1,2})(?::(\d{2}))?", text)
        if not m:
            raise api.ToolError(f"CALDAV_WORK_HOURS={text!r}: use 09-18 or 09:30-17:30.")
        try:
            a = dt.time(int(m.group(1)), int(m.group(2) or 0))
            b = dt.time(int(m.group(3)), int(m.group(4) or 0)) if m.group(3) != "24" else dt.time(23, 59)
        except ValueError:
            raise api.ToolError(f"CALDAV_WORK_HOURS={text!r}: use 09-18 or 09:30-17:30.") from None
        if a >= b:
            raise api.ToolError(f"CALDAV_WORK_HOURS={text!r}: the start must be before the end.")
        return a, b

    def when(e: dict) -> str:
        if e["all_day"]:
            last = e["end"] - dt.timedelta(days=1)
            return f"{e['start']:%a %d %b}" + (f" to {last:%a %d %b}" if last.date() > e["start"].date() else "") + ", all day"
        same = e["end"].date() == e["start"].date()
        return f"{e['start']:%a %d %b %H:%M}-{e['end']:%H:%M}" if same else f"{e['start']:%a %d %b %H:%M} to {e['end']:%a %d %b %H:%M}"

    @api.tool(api.READ)
    def calendar_events(start_date: str = "", days: int = 7) -> str:
        """The user's calendar events from start_date (YYYY-MM-DD, default today) for `days` days (1 to 31),
        repeating events included. One line each. Changes nothing."""
        tz = zone()
        days = max(1, min(days, 31))
        found = events(day_from(start_date, tz), days, tz)
        if not found:
            return "No events." + zone_note(tz)
        lines = [f"{when(e)} · {e['title']}" + (f" · {e['place']}" if e["place"] else "") for e in found[:100]]
        return "\n".join(lines) + zone_note(tz)

    @api.tool(api.READ)
    def calendar_free(start_date: str = "", days: int = 5, minutes: int = 30) -> str:
        """Free times in the user's working hours on weekdays, from start_date (default today) for `days` days
        (1 to 14), each at least `minutes` long (15 to 480). One line per day. Changes nothing."""
        tz = zone()
        days, minutes = max(1, min(days, 14)), max(15, min(minutes, 480))
        start = max(day_from(start_date, tz), dt.datetime.now(tz).date())   # no free times in the past
        a, b = hours()
        busy = [(e["start"], e["end"]) for e in events(start, days, tz) if not e["free"]]
        now = dt.datetime.now(tz)
        lines = []
        for i in range(days):
            day = start + dt.timedelta(days=i)
            if day.weekday() >= 5:
                continue
            lo, hi = dt.datetime.combine(day, a, tz), dt.datetime.combine(day, b, tz)
            if day == now.date():
                rounded = now + dt.timedelta(minutes=(15 - now.minute % 15) % 15)
                lo = max(lo, rounded.replace(second=0, microsecond=0))
            slots, cursor = [], lo
            for bs, be in sorted((x for x in busy if x[1] > lo and x[0] < hi), key=lambda x: x[0]):
                if bs - cursor >= dt.timedelta(minutes=minutes):
                    slots.append((cursor, bs))
                cursor = max(cursor, be)
            if hi - cursor >= dt.timedelta(minutes=minutes):
                slots.append((cursor, hi))
            lines.append(f"{day:%a %d %b}: " + (", ".join(f"{x:%H:%M}-{y:%H:%M}" for x, y in slots) or "no free time"))
        return ("\n".join(lines) or "No weekdays in that range.") + zone_note(tz)

    @api.tool(api.WRITE)
    def add_event(title: str, start: str, minutes: int = 60, location: str = "", details: str = "") -> str:
        """Add an event to the user's own calendar. Only when the user asked for it. start: ISO time with the
        UTC offset, e.g. '2026-10-20T15:00:00+01:00'. No one is invited: to invite people, attach an invite to an
        email draft instead. Within the next year only."""
        try:
            begin = dt.datetime.fromisoformat(start)
        except ValueError:
            raise api.ToolError("start: use ISO with the UTC offset, e.g. 2026-10-20T15:00:00+01:00.")
        if begin.tzinfo is None:
            raise api.ToolError("Add the UTC offset to start, e.g. +01:00.")
        now = dt.datetime.now(dt.timezone.utc)
        if not now - dt.timedelta(days=1) <= begin <= now + dt.timedelta(days=366):
            raise api.ToolError("The event must be within the next year.")
        if not 5 <= minutes <= 24 * 60:
            raise api.ToolError("minutes must be between 5 and 1440.")
        tz = zone()   # checked before anything is added, so a bad setting never half-adds an event
        today = now.date().isoformat()
        with api.store() as data:   # check and count in one step
            adds = {d: c for d, c in data.get("adds", {}).items() if d == today}
            if adds.get(today, 0) >= MAX_ADDS_A_DAY:
                raise api.ToolError(f"Already {MAX_ADDS_A_DAY} events added today: that's the daily limit.")
            adds[today] = adds.get(today, 0) + 1
            data["adds"] = adds

        def clean(text: str, n: int) -> str:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)[:n]
            return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

        stamp = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        note = (details.strip() + "\n\n" if details.strip() else "") + "Added by your mail assistant."
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Selfhost Mail MCP//caldav//EN", "BEGIN:VEVENT",
                 f"UID:{uuid.uuid4()}", f"DTSTAMP:{stamp(now)}", f"DTSTART:{stamp(begin)}",
                 f"DTEND:{stamp(begin + dt.timedelta(minutes=minutes))}", f"SUMMARY:{clean(title, 200)}",
                 f"DESCRIPTION:{clean(note, 2000)}"]
        if location.strip():
            lines.append(f"LOCATION:{clean(location, 200)}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        from selfhost_remote_mail_mcp.library.calendar_invite.addon import fold
        ical = "\r\n".join(fold(line) for line in lines) + "\r\n"
        try:
            calendar().add_event(ical)
        except Exception as exc:
            with api.store() as data:   # not added: give the count back
                data.setdefault("adds", {})[today] = max(0, data.get("adds", {}).get(today, 1) - 1)
            if isinstance(exc, api.ToolError):
                raise
            raise api.ToolError(f"The event couldn't be added ({type(exc).__name__}). " + where()) from None
        e = {"start": begin.astimezone(tz), "end": (begin + dt.timedelta(minutes=minutes)).astimezone(tz), "all_day": False}
        return f"Added: {when(e)} · {title.strip()[:80]}{zone_note(tz)}. No one was invited."
