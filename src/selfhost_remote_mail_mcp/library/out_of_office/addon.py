# SPDX-License-Identifier: AGPL-3.0-only
"""Out of office: while you're away, answers new emails once per person with your message, and skips mailing lists and robots."""

import datetime as dt
import hashlib
import re
import time
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

from selfhost_remote_mail_mcp.i18n import N_

SENDS = True   # it sends its replies by itself, from its background job (see README)
SETTINGS = [
    {"key": "MESSAGE", "label": N_("Your away message"), "required": True, "lines": 6,
     "help": N_("Sent once to each person who writes to you while you're away. Your signature is added.")},
    {"key": "FROM", "half": True, "label": N_("First day away"), "help": N_("Like 2026-10-20. Empty means from now.")},
    {"key": "UNTIL", "half": True, "label": N_("Last day away"), "help": N_("Like 2026-10-27. Empty means until you turn it off.")},
    {"key": "ONCE_EVERY_DAYS", "half": True, "label": N_("Answer the same person once every"),
     "help": N_("Days. Empty means 4.")},
    {"key": "DAILY_MAX", "half": True, "label": N_("Most replies a day"), "help": N_("Empty means 20, the most allowed.")},
    {"key": "MAILBOXES", "label": N_("Only for these mailboxes"),
     "help": N_("Addresses separated by commas. Empty means every mailbox that may send.")},
    {"key": "TIMEZONE", "label": N_("Your time zone"), "help": N_("For example Europe/Lisbon, so the days match yours.")},
]
SKIP_HEADERS = ("Auto-Submitted", "Precedence", "List-Id", "List-Unsubscribe", "Return-Path",
                "X-Auto-Response-Suppress", "X-Autoreply", "X-Autorespond", "X-Spam-Flag", "X-Spam-Status",
                "Content-Type")
ROBOTS = re.compile(r"^(mailer-daemon|postmaster|no-?reply|do-?not-?reply|bounces?|notifications?|alerts?)\b", re.I)
PER_RUN = 2          # the server sends at most 3 emails a minute in total: leave room for the user
MAX_WAITING = 50
MAX_A_DAY = 20


def setup(api):
    from selfhost_remote_mail_mcp.server import all_accounts, config, is_on, server_read_only

    s = lambda key, default="": api.setting(f"OUT_OF_OFFICE_{key}", default)

    def today() -> dt.date:
        zone = s("TIMEZONE")
        if zone:
            from zoneinfo import ZoneInfo
            try:
                return dt.datetime.now(ZoneInfo(zone)).date()
            except Exception:
                pass
        return dt.date.today()

    def number(key: str, default: int, top: int) -> int:
        try:
            return max(1, min(int(s(key) or default), top))
        except ValueError:
            return default

    def window() -> tuple[dt.date | None, dt.date | None]:
        def day(key):
            try:
                return dt.date.fromisoformat(s(key).strip()) if s(key).strip() else None
            except ValueError:
                return None
        return day("FROM"), day("UNTIL")

    def active() -> bool:
        start, end = window()
        now = today()
        return bool(s("MESSAGE").strip()) and (start is None or start <= now) and (end is None or now <= end)

    def boxes() -> set[str]:
        chosen = {a.strip().lower() for a in s("MAILBOXES").split(",") if a.strip()}
        return {a.address for a in all_accounts(config()) if a.mode == "full" and (not chosen or a.address in chosen)}

    def skip(row: dict, own: set[str]) -> bool:
        """Mail that must never get an automatic answer (RFC 3834 and common practice)."""
        sender = parseaddr(row["from"])[1].lower()
        if not sender or sender in own or ROBOTS.match(sender):
            return True
        if (row.get("auto-submitted") or "no").strip().lower() != "no":
            return True
        if (row.get("precedence") or "").strip().lower() in ("bulk", "list", "junk"):
            return True
        if row.get("list-id") or row.get("list-unsubscribe") or row.get("x-autoreply") or row.get("x-autorespond"):
            return True
        if (row.get("return-path") or "").strip() == "<>":
            return True   # a bounce (an empty return path); a missing one is fine
        if re.search(r"\b(oof|all)\b", row.get("x-auto-response-suppress") or "", re.I):
            return True
        if (row.get("x-spam-flag") or "").strip().lower() == "yes" or (row.get("x-spam-status") or "").lower().startswith("yes"):
            return True
        if "multipart/report" in (row.get("content-type") or "").lower():
            return True
        if row["date"] and time.time() - row["date"].timestamp() > 2 * 86400:
            return True   # old mail (the server was down): no late replies
        addressed = {a.lower() for _, a in getaddresses([row.get("to", ""), row.get("cc", "")])}
        return row["account"] not in addressed   # Bcc, mailing lists, forwards

    def sender_checked(email_id: str, account: str, sender: str) -> bool:
        """Only answer mail whose sender passed your provider's own checks, so a forged address never gets a
        reply: DMARC pass for the sender's domain, or a DKIM signature from it."""
        checks = api.sender_checks(api.message(email_id, account)) or {}
        domain = sender.rsplit("@", 1)[-1]
        same = lambda d: domain == d or domain.endswith("." + d)
        if checks.get("dmarc") == "pass" and same(checks.get("header.from", domain)):
            return True
        return any(same(d) for d in checks.get("dkim.domains", []))

    def run() -> None:
        cfg = config()
        rows = api.new_mail("INBOX", headers=SKIP_HEADERS)   # always read, so nothing old is answered later
        if server_read_only(cfg) or cfg.get("SEND_ALLOWED_RECIPIENTS") or not active():
            return
        own = {a.address for a in all_accounts(cfg)}
        allowed = boxes()
        fingerprint = hashlib.sha256("|".join([s("FROM"), s("UNTIL"), s("MESSAGE")]).encode()).hexdigest()[:16]
        once = number("ONCE_EVERY_DAYS", 4, 60)
        daily_max = number("DAILY_MAX", 20, MAX_A_DAY)
        now, day = time.time(), today().isoformat()
        with api.store() as data:
            if data.get("fingerprint") != fingerprint:   # a new away period or message: start fresh
                data.update(fingerprint=fingerprint, answered={}, waiting=[])
            waiting = [w for w in data.get("waiting", []) if now - w["at"] < 86400]
            for row in rows:
                if row["account"] in allowed and not skip(row, own):
                    waiting.append({"id": row["id"], "account": row["account"],
                                    "sender": parseaddr(row["from"])[1].lower(),
                                    "subject": row["subject"][:80], "at": now})
            data["waiting"] = waiting[-MAX_WAITING:]
        sent = 0
        while sent < PER_RUN:
            with api.store() as data:
                if not data["waiting"] or data.setdefault("days", {}).get(day, 0) >= daily_max:
                    return   # nothing waiting, or today's replies are used up: the rest waits (up to a day)
                item = data["waiting"].pop(0)
                key = f"{item['account']}|{item['sender']}"
                if now - data["answered"].get(key, 0) < once * 86400:
                    continue
            try:
                if not sender_checked(item["id"], item["account"], item["sender"]):
                    continue
            except Exception:   # moved or deleted meanwhile: skip it, never block the others
                continue
            with api.store() as data:
                if now - data["answered"].get(key, 0) < once * 86400:
                    continue
                data["answered"][key] = now   # marked before sending: a crash never answers twice
                data["answered"] = {k: v for k, v in data["answered"].items() if now - v < 60 * 86400}
                counts = data.setdefault("days", {})
                counts[day] = counts.get(day, 0) + 1
                data["days"] = {d: c for d, c in counts.items() if d >= (today() - dt.timedelta(days=7)).isoformat()}
            subject = re.sub(r"^\s*(re\s*:\s*)+", "", item["subject"], flags=re.I)
            try:
                draft = api.new_draft([item["sender"]], f"Re: {subject}"[:90], s("MESSAGE"), reply_to_id=item["id"],
                                      account=item["account"], quote=False,
                                      headers={"Auto-Submitted": "auto-replied", "X-Auto-Response-Suppress": "All"})
            except Exception as exc:
                api.log(f"an away reply couldn't be written: {type(exc).__name__}")
                continue
            try:
                api.send(draft, item["account"])
                sent += 1
            except Exception as exc:
                api.log(f"an away reply wasn't sent: {type(exc).__name__}")
                try:
                    api.delete_draft(draft, item["account"])
                except Exception:
                    pass
                return

    api.every(5, run)

    @api.tool(api.READ)
    def out_of_office() -> str:
        """Whether the out-of-office reply is on, for which days, and how many were sent today. The user turns
        it on and writes the message on its setup page; you can't change it, only give them the link."""
        start, end = window()
        with api.store() as data:
            count = data.get("days", {}).get(today().isoformat(), 0)
        link = api.setup_link()
        if not s("MESSAGE").strip():
            return "Out of office isn't set up yet." + (f" Set up: {link}" if link else "")
        when = f"{start or 'now'} to {end or 'until turned off'}"
        state = "replying now" if active() else "not replying now"
        warn = " No last day is set, so it keeps replying until it's turned off." if end is None else ""
        return f"Out of office: {state} ({when}). Replies today: {count}.{warn}" + (f" Change it: {link}" if link else "")
