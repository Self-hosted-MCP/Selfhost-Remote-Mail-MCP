# SPDX-License-Identifier: AGPL-3.0-only
"""Calendar: reads your calendar, finds free times and adds, changes or deletes events, for calendars that use CalDAV (iCloud, Fastmail, Nextcloud and others)."""

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
    {"key": "CALENDAR", "label": N_("Calendars to use"),
     "help": N_("Names separated by commas. Empty means all your calendars.")},
    {"key": "TIMEZONE", "choices": "timezone", "half": True, "label": N_("Your time zone"), "help": N_("For example Europe/Lisbon. Empty means UTC.")},
    {"key": "WORK_HOURS", "half": True, "label": N_("Hours to offer as free"), "help": N_("Like 09-18 or 09:30-17:30. Empty means 09-18.")},
]
MAX_CHANGES_A_DAY = 20   # adds, changes and deletes together


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

    def calendars_all():
        """Every calendar on the account (a new connection each time keeps things simple), or a clear error."""
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
        return calendars

    def name_of(cal) -> str:
        try:
            return (cal.get_display_name() or "").strip()
        except Exception:
            return ""

    def reading():
        """The calendars to use: the ones named in CALDAV_CALENDAR, or all of them."""
        found = calendars_all()
        typed = [w.strip() for w in s("CALENDAR").split(",") if w.strip()]
        if not typed:
            return found
        chosen = [c for c in found if name_of(c).lower() in {w.lower() for w in typed}]
        missing = [w for w in typed if w.lower() not in {name_of(c).lower() for c in chosen}]
        if missing:
            raise api.ToolError(f"There's no calendar called {missing[0]!r}. " + where())
        return chosen

    def names(cals) -> str:
        return ", ".join((name_of(c) or "(no name)")[:30] for c in cals[:8]) + ("…" if len(cals) > 8 else "")

    def adding(calendar: str):
        """The calendar a new event goes to: the one named, or the only one in use. With several and none named,
        the AI asks the user."""
        cals = reading()
        if calendar.strip():
            for c in cals:
                if name_of(c).lower() == calendar.strip().lower():
                    return c
            raise api.ToolError(f"There's no calendar called {calendar.strip()[:40]!r}. The calendars are: {names(cals)}.")
        if len(cals) == 1:
            return cals[0]
        raise api.ToolError(f"Which calendar? Ask the user, then pass calendar=. The calendars are: {names(cals)}.")

    def find(event_id: str):
        """The event with this ID (its UID) in the calendars in use, with its calendar's name."""
        from caldav.lib import error
        uid = event_id.strip()
        if not uid:
            raise api.ToolError("event_id: copy it from calendar_events.")
        for cal in reading():
            try:
                return cal.get_event_by_uid(uid), name_of(cal)
            except error.NotFoundError:
                continue
            except Exception as exc:
                raise api.ToolError(f"The calendar {name_of(cal)!r} couldn't be read ({type(exc).__name__}). "
                                    + where()) from None
        raise api.ToolError(f"No event with the ID {uid[:80]!r}. Check it with calendar_events.")

    def look(obj) -> tuple:
        """The event's main part, whether it repeats, and whether it has guests (changing those would email them)."""
        parts = [c for c in obj.get_icalendar_instance().subcomponents if c.name == "VEVENT"]
        if not parts:
            raise api.ToolError("That ID isn't an event.")
        main = next((c for c in parts if c.get("RECURRENCE-ID") is None), parts[0])
        repeats = len(parts) > 1 or any(main.get(k) is not None for k in ("RRULE", "RDATE"))
        guests = any(c.get("ATTENDEE") is not None for c in parts)
        return main, repeats, guests

    def summary(comp, tz) -> dict:
        """One event as a dict for when() and the answers."""
        raw_start = comp.get("DTSTART").dt
        all_day = not isinstance(raw_start, dt.datetime)
        if comp.get("DTEND") is not None:
            raw_end = comp.get("DTEND").dt
        elif comp.get("DURATION") is not None:
            raw_end = raw_start + comp.get("DURATION").dt
        else:
            raw_end = raw_start + (dt.timedelta(days=1) if all_day else dt.timedelta(0))
        return {"start": as_dt(raw_start, tz), "end": as_dt(raw_end, tz), "all_day": all_day,
                "title": re.sub(r"\s+", " ", str(comp.get("SUMMARY", "(no title)")))[:80],
                "place": re.sub(r"\s+", " ", str(comp.get("LOCATION", "") or ""))[:60]}

    def count_change() -> str:
        """Counts one change against the daily limit (check and count in one step). Returns today, to give it back."""
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        with api.store() as data:
            adds = {d: c for d, c in data.get("adds", {}).items() if d == today}
            if adds.get(today, 0) >= MAX_CHANGES_A_DAY:
                raise api.ToolError(f"Already {MAX_CHANGES_A_DAY} calendar changes today: that's the daily limit.")
            adds[today] = adds.get(today, 0) + 1
            data["adds"] = adds
        return today

    def give_back(today: str) -> None:
        with api.store() as data:   # nothing changed: give the count back
            data.setdefault("adds", {})[today] = max(0, data.get("adds", {}).get(today, 1) - 1)

    def begin_from(start: str):
        try:
            begin = dt.datetime.fromisoformat(start)
        except ValueError:
            raise api.ToolError("start: use ISO with the UTC offset, e.g. 2026-10-20T15:00:00+01:00.")
        if begin.tzinfo is None:
            raise api.ToolError("Add the UTC offset to start, e.g. +01:00.")
        now = dt.datetime.now(dt.timezone.utc)
        if not now - dt.timedelta(days=1) <= begin <= now + dt.timedelta(days=366):
            raise api.ToolError("The event must be within the next year.")
        return begin

    def check_minutes(minutes: int) -> None:
        if not 5 <= minutes <= 24 * 60:
            raise api.ToolError("minutes must be between 5 and 1440.")

    def clean_text(text: str, n: int) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)[:n]

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
        begin = dt.datetime.combine(start, dt.time(0), tz)
        finish = dt.datetime.combine(start + dt.timedelta(days=days), dt.time(0), tz)
        found = []
        for cal in reading():
            try:
                found += [(name_of(cal), item) for item in cal.search(start=begin, end=finish, event=True, expand=True)]
            except Exception as exc:
                raise api.ToolError(f"The calendar {name_of(cal)!r} couldn't be read ({type(exc).__name__}). "
                                    + where()) from None
        out = []
        for cal_name, item in found[:1000]:
            comp = getattr(item, "icalendar_component", None)
            if comp is None or str(comp.get("STATUS", "")).upper() == "CANCELLED":
                continue
            if comp.get("DTSTART") is None:
                continue
            out.append({**summary(comp, tz), "calendar": cal_name[:40], "id": str(comp.get("UID", "") or ""),
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

    def test() -> str:
        tz = zone()
        cals = reading()
        found = events(dt.datetime.now(tz).date(), 7, tz)
        return f"Connected. Using {len(cals)} calendar(s): {names(cals)}. {len(found)} event(s) in the next 7 days."

    api.on_test(test)

    @api.tool(api.READ)
    def calendar_events(start_date: str = "", days: int = 7) -> str:
        """The user's calendar events from start_date (YYYY-MM-DD, default today) for `days` days (1 to 31),
        repeating events included. One line each, ending with the event's ID for edit_event and delete_event.
        Changes nothing."""
        tz = zone()
        days = max(1, min(days, 31))
        found = events(day_from(start_date, tz), days, tz)
        if not found:
            return "No events." + zone_note(tz)
        several = len({e["calendar"] for e in found}) > 1
        lines = [f"{when(e)} · {e['title']}" + (f" · {e['place']}" if e["place"] else "")
                 + (f" · [{e['calendar']}]" if several and e["calendar"] else "")
                 + (f" · id: {e['id']}" if e["id"] else "") for e in found[:100]]
        return "\n".join(lines) + zone_note(tz)

    @api.tool(api.READ)
    def calendar_free(start_date: str = "", days: int = 5, minutes: int = 30) -> str:
        """Free times in the user's working hours on weekdays (all calendars read count as busy), from start_date (default today) for `days` days
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
    def add_event(title: str, start: str, minutes: int = 60, location: str = "", details: str = "",
                  calendar: str = "") -> str:
        """Add an event to the user's own calendar. Only when the user asked for it. start: ISO time with the
        UTC offset, e.g. '2026-10-20T15:00:00+01:00'. calendar: its name; with several calendars and none given,
        the answer lists them: ask the user which one. No one is invited: to invite people, attach an invite to an
        email draft instead. Within the next year only."""
        begin = begin_from(start)
        check_minutes(minutes)
        tz = zone()   # checked before anything is added, so a bad setting never half-adds an event
        target = adding(calendar)
        today = count_change()

        def esc(text: str, n: int) -> str:
            text = clean_text(text, n)
            return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

        stamp = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        note = (details.strip() + "\n\n" if details.strip() else "") + "Added by your mail assistant."
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Selfhost Mail MCP//caldav//EN", "BEGIN:VEVENT",
                 f"UID:{uuid.uuid4()}", f"DTSTAMP:{stamp(dt.datetime.now(dt.timezone.utc))}", f"DTSTART:{stamp(begin)}",
                 f"DTEND:{stamp(begin + dt.timedelta(minutes=minutes))}", f"SUMMARY:{esc(title, 200)}",
                 f"DESCRIPTION:{esc(note, 2000)}"]
        if location.strip():
            lines.append(f"LOCATION:{esc(location, 200)}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        from selfhost_remote_mail_mcp.library.calendar_invite.addon import fold
        ical = "\r\n".join(fold(line) for line in lines) + "\r\n"
        try:
            target.add_event(ical)
        except Exception as exc:
            give_back(today)
            raise api.ToolError(f"The event couldn't be added ({type(exc).__name__}). " + where()) from None
        e = {"start": begin.astimezone(tz), "end": (begin + dt.timedelta(minutes=minutes)).astimezone(tz), "all_day": False}
        return f"Added to {name_of(target)[:40] or 'your calendar'}: {when(e)} · {title.strip()[:80]}{zone_note(tz)}. No one was invited."

    @api.tool(api.WRITE)
    def edit_event(event_id: str, title: str = "", start: str = "", minutes: int = 0, location: str = "",
                   details: str = "") -> str:
        """Change an event in the user's calendar. Only when the user asked for it. event_id: from
        calendar_events. Only what you pass changes; empty or 0 leaves it as it is. start: ISO time with the UTC
        offset, e.g. '2026-10-20T15:00:00+01:00'; without minutes the length stays the same. details replaces the
        notes. Repeating events and events with guests are refused: the user changes those in their calendar app."""
        if not (title.strip() or start.strip() or minutes or location.strip() or details.strip()):
            raise api.ToolError("Nothing to change: pass title, start, minutes, location or details.")
        new_begin = begin_from(start) if start.strip() else None
        if minutes:
            check_minutes(minutes)
        tz = zone()
        obj, cal_name = find(event_id)
        main, repeats, guests = look(obj)
        if repeats:
            raise api.ToolError("That event repeats. Change it in your calendar app, so the right dates change.")
        if guests:
            raise api.ToolError("That event has guests, and changing it here could email them. Change it in your calendar app.")
        old = summary(main, tz)
        if (new_begin is None and minutes) and old["all_day"]:
            raise api.ToolError("That's an all-day event: pass start too, to give it a time.")
        length = dt.timedelta(minutes=minutes) if minutes else (
            dt.timedelta(hours=1) if old["all_day"] else old["end"] - old["start"])
        today = count_change()
        try:
            with obj.edit_icalendar_component() as comp:
                if title.strip():
                    comp.pop("SUMMARY", None)
                    comp.add("SUMMARY", clean_text(title, 200))
                if location.strip():
                    comp.pop("LOCATION", None)
                    comp.add("LOCATION", clean_text(location, 200))
                if details.strip():
                    comp.pop("DESCRIPTION", None)
                    comp.add("DESCRIPTION", clean_text(details, 2000))
                if new_begin is not None or minutes:
                    begin = new_begin or old["start"]
                    for key in ("DTSTART", "DTEND", "DURATION"):
                        comp.pop(key, None)
                    comp.add("DTSTART", begin.astimezone(dt.timezone.utc))
                    comp.add("DTEND", (begin + length).astimezone(dt.timezone.utc))
                comp.pop("DTSTAMP", None)
                comp.add("DTSTAMP", dt.datetime.now(dt.timezone.utc))
                comp["SEQUENCE"] = int(comp.get("SEQUENCE", 0) or 0) + 1
                new = summary(comp, tz)
            obj.save()
        except api.ToolError:
            give_back(today)
            raise
        except Exception as exc:
            give_back(today)
            raise api.ToolError(f"The event couldn't be changed ({type(exc).__name__}). " + where()) from None
        return (f"Changed in {cal_name[:40] or 'your calendar'}: {when(new)} · {new['title']}"
                + (f" · {new['place']}" if new["place"] else "") + f"{zone_note(tz)}. Before: {when(old)} · {old['title']}.")

    @api.tool(api.DELETE)
    def delete_event(event_id: str, confirm: bool = False) -> str:
        """Delete an event from the user's calendar. Only when the user asked for it. event_id: from
        calendar_events. Always double check: call first without confirm, show the user the event in the answer
        and ask them; only after they said yes, call again with confirm=true. A repeating event is deleted with all
        its dates. Events with guests are refused: the user deletes those in their calendar app."""
        tz = zone()
        obj, cal_name = find(event_id)
        main, repeats, guests = look(obj)
        if guests:
            raise api.ToolError("That event has guests, and deleting it here could email them. Delete it in your calendar app.")
        e = summary(main, tz)
        what = (f"{when(e)} · {e['title']}" + (f" · {e['place']}" if e["place"] else "")
                + f" in {cal_name[:40] or 'your calendar'}" + (", and every date it repeats on" if repeats else ""))
        if not confirm:
            return (f"Not deleted yet. This would delete: {what}{zone_note(tz)}. Ask the user if this is the right "
                    f"event; only if they say yes, call delete_event again with confirm=true.")
        today = count_change()
        try:
            obj.delete()
        except Exception as exc:
            give_back(today)
            raise api.ToolError(f"The event couldn't be deleted ({type(exc).__name__}). " + where()) from None
        return f"Deleted: {what}{zone_note(tz)}."
