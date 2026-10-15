# SPDX-License-Identifier: AGPL-3.0-only
"""Follow-up reminders: remembers emails you sent and tells you which ones got no reply in time."""

import datetime as dt
import re
import secrets
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

from selfhost_remote_mail_mcp.i18n import N_

SETTINGS = [
    {"key": "TIMEZONE", "choices": "timezone", "label": N_("Your time zone"), "help": N_("For example Europe/Lisbon, so due dates match your days.")},
]
MAX_OPEN = 200
ROBOTS = re.compile(r"^(mailer-daemon|postmaster|no-?reply|do-?not-?reply|bounces?|notifications?)\b", re.I)


def plain_subject(subject: str) -> str:
    return re.sub(r"^\s*((re|aw|sv|fw|fwd|wg|tr|res|rif)\s*:\s*)+", "", subject or "", flags=re.I).strip().lower()


def setup(api):
    def today() -> dt.date:
        zone = api.setting("FOLLOW_UPS_TIMEZONE")
        if zone:
            from zoneinfo import ZoneInfo
            try:
                return dt.datetime.now(ZoneInfo(zone)).date()
            except Exception:
                pass
        return dt.date.today()

    def mine() -> set[str]:
        return {a.lower() for a in api.mailboxes()}

    @api.tool(api.WRITE)
    def remind_if_no_reply(email_id: str, days: int = 3, note: str = "") -> str:
        """Remember an email the user sent, and list it in follow_ups if nobody replied within `days` days of
        sending (1 to 90). note: a few words for later. Nothing is sent."""
        if not 1 <= days <= 90:
            raise api.ToolError("days must be between 1 and 90.")
        msg = api.message(email_id)
        sender = parseaddr(str(msg.get("From", "")))[1].lower()
        if sender not in mine():
            raise api.ToolError("That email wasn't sent by the user. Pick one from their Sent folder.")
        message_id = str(msg.get("Message-ID", "")).strip()
        if not message_id:
            raise api.ToolError("That email has no Message-ID, so replies to it can't be found.")
        try:
            sent = parsedate_to_datetime(str(msg.get("Date"))).date()
        except (TypeError, ValueError):
            sent = today()
        to = [a.lower() for _, a in getaddresses([str(msg.get(h, "")) for h in ("To", "Cc")]) if a]
        with api.store() as data:
            items = data.setdefault("reminders", {})
            if sum(1 for r in items.values() if r["account"] in mine()) >= MAX_OPEN:
                raise api.ToolError(f"There are already {MAX_OPEN} reminders. Cancel some first.")
            code = "R-" + secrets.token_hex(3).upper()
            while code in items:
                code = "R-" + secrets.token_hex(3).upper()
            items[code] = {"message_id": message_id, "account": sender, "to": to[:20],
                           "subject": str(msg.get("Subject", ""))[:150], "sent": sent.isoformat(),
                           "due": (sent + dt.timedelta(days=days)).isoformat(), "note": note.strip()[:200]}
        who = to[0] if to else "them"
        return f"Reminder {code}: if {who} hasn't replied by {(sent + dt.timedelta(days=days)).isoformat()}, it shows in follow_ups."

    @api.tool(api.READ)
    def follow_ups(show: str = "due") -> str:
        """Emails the user sent that got no reply yet. show="due": only those past their date (default);
        show="all": also the ones still waiting. Replies found are cleared automatically. Each due line has the
        email's ID: draft a follow-up with the draft tool (reply_to=<ID>) if the user wants."""
        allowed, now = mine(), today()
        with api.store() as data:
            items = dict(data.get("reminders", {}))
        lines, done = [], []
        for code, r in sorted(items.items(), key=lambda kv: kv[1]["due"]):
            if r["account"] not in allowed:
                continue
            due = dt.date.fromisoformat(r["due"]) <= now
            if not due and show != "all":
                continue
            if not due:   # not due yet: no need to look for replies
                lines.append(f"{code}: waiting until {r['due']} · to {r['to'][0] if r['to'] else '?'} · \"{r['subject'][:60]}\""
                             + (f" · {r['note']}" if r["note"] else ""))
                continue
            try:
                replies = [x for x in api.replies_to(r["message_id"], r["account"], headers=("Auto-Submitted",))
                           if parseaddr(x["from"])[1].lower() not in allowed
                           and not ROBOTS.match(parseaddr(x["from"])[1])
                           and (x.get("auto-submitted") or "no").lower() == "no"]
            except Exception:   # one mailbox problem shouldn't hide the whole list
                lines.append(f"{code}: couldn't be checked right now · \"{r['subject'][:60]}\"")
                continue
            if replies:
                done.append(code)
                continue
            probably = ""
            if due and r["to"]:
                after = dt.date.fromisoformat(r["sent"]).strftime("%Y/%m/%d")
                for row in api.find(filter=f"from:{r['to'][0]} after:{after}", account=r["account"], limit=20):
                    if plain_subject(row["subject"]) == plain_subject(r["subject"]):
                        probably = " (maybe answered without being linked: check)"
                        break
            where = api.locate(r["message_id"], r["account"]) if due else ""
            to = r["to"][0] if r["to"] else "?"
            lines.append(f"{code}: {'due' if due else 'waiting'} since {r['due']} · to {to} · \"{r['subject'][:60]}\""
                         + (f" · {r['note']}" if r["note"] else "") + probably + (f" · ID {where}" if where else ""))
        if done:
            with api.store() as data:
                for code in done:
                    data.get("reminders", {}).pop(code, None)
        head = f"{len(done)} got a reply and were cleared. " if done else ""
        if not lines:
            return head + ("Nothing is due." if show != "all" else "No reminders.")
        return head + "\n".join(lines)

    @api.tool(api.WRITE)
    def cancel_follow_up(code: str) -> str:
        """Forget one reminder, by its code (like R-1A2B). Nothing is sent."""
        code = code.strip().upper()
        with api.store() as data:
            r = data.get("reminders", {}).get(code)
            if not r or r["account"] not in mine():
                raise api.ToolError(f"There's no reminder {code}.")
            data["reminders"].pop(code)
        return f"Reminder {code} cancelled."
