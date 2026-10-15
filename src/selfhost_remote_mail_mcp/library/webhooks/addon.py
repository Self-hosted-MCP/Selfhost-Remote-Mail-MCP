# SPDX-License-Identifier: AGPL-3.0-only
"""Webhooks: tells a web address of yours when new mail arrives (sender, subject and date, never the email itself), for automations."""

import base64
import binascii
import datetime as dt
import hashlib
import hmac
import json
import secrets
import time
from email.utils import parseaddr

from selfhost_remote_mail_mcp.i18n import N_

SETTINGS = [
    {"key": "URL", "label": N_("Web address to send to"), "required": True, "secret": True,
     "help": N_("From Zapier, Make, n8n or your own app. https, or http for a service on your own network.")},
    {"key": "SECRET", "label": N_("Signing secret"), "required": True, "secret": True,
     "help": N_("At least 24 random characters (or a whsec_ secret). Your receiver uses it to check each message really came from your server.")},
    {"key": "AUTH_HEADER", "label": N_("Authorization header"), "secret": True,
     "help": N_("Optional. Sent as the Authorization header, for receivers that check one.")},
    {"key": "SUBJECT", "half": True, "label": N_("Include the subject"),
     "help": N_("on or off. Subjects can hold codes and private details. Empty means on.")},
    {"key": "MAILBOXES", "half": True, "label": N_("Only for these mailboxes"),
     "help": N_("Addresses separated by commas. Empty means all.")},
]
PER_RUN = 50
RUN_BUDGET = 60          # seconds per run at most, so a slow receiver never holds up other add-ons
DROP = {404, 410, 413, 422}   # the receiver will never take this one: skip it; anything else is tried again
MAX_WAITING = 500
KEEP_TRYING = 3 * 86400


def setup(api):
    s = lambda key, default="": api.setting(f"WEBHOOKS_{key}", default)

    def key_bytes() -> bytes | None:
        secret = s("SECRET")
        if secret.startswith("whsec_"):
            try:
                raw = base64.b64decode(secret[6:], validate=True)
            except (binascii.Error, ValueError):
                return None
            return raw if len(raw) >= 24 else None
        return secret.encode() if len(secret) >= 24 else None

    def signed(event_id: str, body: bytes, key: bytes) -> dict[str, str]:
        """Standard Webhooks headers: a fresh timestamp and signature on every try, the same id."""
        ts = str(int(time.time()))
        mac = hmac.new(key, f"{event_id}.{ts}.".encode() + body, hashlib.sha256).digest()
        headers = {"webhook-id": event_id, "webhook-timestamp": ts,
                   "webhook-signature": "v1," + base64.b64encode(mac).decode(), "Content-Type": "application/json"}
        if s("AUTH_HEADER"):
            headers["Authorization"] = s("AUTH_HEADER")
        return headers

    def run() -> None:
        now = time.time()
        with api.store() as data:
            if now - data.get("last_run", now) > 86400:   # off for over a day: start fresh, never send a backlog
                data.pop("_new_mail", None)
                data["waiting"] = []
            data["last_run"] = now
        rows = api.new_mail("INBOX")   # always read, so turning it on never sends old mail
        url, key = s("URL").strip(), key_bytes()
        if not url or key is None:
            if rows:
                api.log("not sending: the address or the signing secret (24+ characters, or a valid whsec_) is missing")
                with api.store() as data:
                    data["last_error"] = f"{dt.date.today()}: the address or signing secret isn't set up"
            return
        chosen = {a.strip().lower() for a in s("MAILBOXES").split(",") if a.strip()}
        with_subject = s("SUBJECT", "on").strip().lower() not in ("off", "no", "false", "0")
        with api.store() as data:
            waiting = [w for w in data.get("waiting", []) if now - w["first"] < KEEP_TRYING]
            if len(waiting) < len(data.get("waiting", [])):
                api.log(f"{len(data['waiting']) - len(waiting)} webhook message(s) given up after 3 days")
            for row in rows:
                if chosen and row["account"] not in chosen:
                    continue
                event = {"type": "email.received", "mailbox": row["account"], "folder": "INBOX",
                         "from": row["from"][:200], "subject": row["subject"][:200] if with_subject else None,
                         "date": row["date"].isoformat() if row["date"] else None,
                         "message_id": row["message-id"][:300] or None}
                waiting.append({"id": "msg_" + secrets.token_hex(12), "event": event, "first": now})
            data["waiting"] = waiting[-MAX_WAITING:]
        started = time.monotonic()
        for _ in range(PER_RUN):
            if time.monotonic() - started > RUN_BUDGET:
                return
            with api.store() as data:
                if not data["waiting"]:
                    return
                item = data["waiting"][0]
            body = json.dumps(item["event"], ensure_ascii=False, separators=(",", ":")).encode()
            try:
                status, _h, _b = api.http("POST", url, data=body, headers=signed(item["id"], body, key), timeout=15,
                                          max_bytes=1024)
            except Exception:   # unreachable: try again next run, and don't hold up other add-ons' jobs
                with api.store() as data:
                    data["last_error"] = f"{dt.date.today()}: couldn't reach it"
                api.log("webhook not delivered: receiver unreachable")
                return
            with api.store() as data:
                if 200 <= status < 300 or status in DROP:
                    if data["waiting"] and data["waiting"][0]["id"] == item["id"]:
                        data["waiting"].pop(0)
                    if not 200 <= status < 300:
                        data["last_error"] = f"{dt.date.today()}: refused with {status}, skipped"
                        api.log(f"webhook refused with {status}; skipped")
                    else:
                        data["sent"] = data.get("sent", 0) + 1
                else:
                    data["last_error"] = f"{dt.date.today()}: answered {status}, will retry"
                    api.log(f"webhook answered {status}; will retry")
                    return

    api.every(5, run)

    def test() -> str:
        url, key = s("URL").strip(), key_bytes()
        if not url:
            raise api.ToolError("Add the web address first.")
        if key is None:
            raise api.ToolError("The signing secret must be 24+ characters, or a valid whsec_ secret.")
        body = json.dumps({"type": "test", "message": "A test from your mail server."}).encode()
        status, _h, _b = api.http("POST", url, data=body, headers=signed("msg_test_" + secrets.token_hex(6), body, key),
                                  timeout=15, max_bytes=1024)
        if 200 <= status < 300:
            return f"Connected: the receiver accepted a test message ({status})."
        raise api.ToolError(f"The receiver answered {status}, so it didn't accept the test message.")

    api.on_test(test)

    @api.tool(api.READ)
    def webhooks() -> str:
        """Whether new-mail webhooks are on and working: where they go (the host only), how many were delivered,
        how many are waiting and the last problem. The user changes them on the setup page; you can't."""
        from urllib.parse import urlparse
        url = s("URL").strip()
        with api.store() as data:
            sent, waiting, error = data.get("sent", 0), len(data.get("waiting", [])), data.get("last_error", "")
        link = api.setup_link()
        if not url or key_bytes() is None:
            return "Webhooks aren't set up yet." + (f" Set up: {link}" if link else "")
        try:
            host = urlparse(url).hostname or "?"
        except ValueError:
            host = "?"
        return (f"Webhooks to {host}: {sent} delivered, {waiting} waiting." + (f" Last problem: {error}." if error else "")
                + (f" Change it: {link}" if link else ""))
