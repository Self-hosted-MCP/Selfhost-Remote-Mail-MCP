"""A fake mailbox and a fake SMTP server, so the tests never touch real mail."""
import atexit
import email
import os
import shutil
import tempfile
import threading
import time
from email.policy import default as POLICY

import pytest

_tmp = tempfile.mkdtemp(prefix="mail-mcp-test-")
atexit.register(shutil.rmtree, _tmp, ignore_errors=True)
os.environ["MAIL_CONFIG_DIR"] = _tmp
os.environ.pop("MAIL_ENV_FILE", None)
os.environ.pop("DATA_DIR", None)
for _k in list(os.environ):
    if (_k.startswith(("MAIL_", "READ_ONLY_", "LOGIN_", "SEND_")) or _k in ("IMAP_HOST", "SMTP_HOST", "PUBLIC_URL")) \
            and _k != "MAIL_CONFIG_DIR":
        os.environ.pop(_k, None)
with open(os.path.join(_tmp, ".env"), "w") as f:
    f.write("MAIL_ADDRESS=me@example.com\nMAIL_NAME=Me\nMAIL_PASSWORD=x\nIMAP_HOST=imap.test\nSMTP_HOST=smtp.test\n"
            "SEND_DAILY_LIMIT=5\nSEND_MINUTE_LIMIT=2\n")
os.chmod(os.path.join(_tmp, ".env"), 0o600)

from selfhost_remote_mail_mcp import server  # noqa: E402


FOLDERS = ("INBOX", "Drafts", "Sent", "Trash", "Archive")


class FakeIMAP:
    """In-memory mail server: one store per mailbox address, {folder: {uid: raw bytes}}."""
    stores: dict = {}
    next_uid = 1
    lock = threading.Lock()

    def __init__(self, account=None):
        self.address = account.address if account else "me@example.com"
        self.store = FakeIMAP.stores.setdefault(self.address, {f: {} for f in FOLDERS})
        self.cur = None

    def login(self, *a): pass
    def logout(self): pass
    def has_capability(self, cap): return cap in ("MOVE", "UIDPLUS")

    def list_folders(self):
        flags = {"Drafts": (b"\\Drafts",), "Sent": (b"\\Sent",), "Trash": (b"\\Trash",), "Archive": (b"\\Archive",)}
        return [(flags.get(f, ()), b"/", f) for f in self.store]

    def select_folder(self, f, readonly=False):
        self.cur = f
        return {}

    def search(self, crit, charset=None):
        uids = sorted(self.store[self.cur])
        if crit and crit[0] == "HEADER":
            uids = [u for u in uids
                    if email.message_from_bytes(self.store[self.cur][u], policy=POLICY).get(crit[1]) == crit[2]]
        return uids

    def fetch(self, uids, what):
        out = {}
        for u in uids:
            raw = self.store[self.cur].get(u)
            if raw is None:
                continue
            w = what[0]
            if w.startswith("BODY.PEEK[HEADER.FIELDS"):
                names = w[w.index("(") + 1:w.index(")")].split()
                msg = email.message_from_bytes(raw, policy=POLICY)
                head = "".join(f"{n}: {msg[n]}\r\n" for n in names if msg.get(n) is not None) + "\r\n"
                out[u] = {w.replace(".PEEK", "").encode(): head.encode()}
            else:
                out[u] = {b"BODY[]": raw}
        return out

    def append(self, folder, data, flags=()):
        with self.lock:
            uid = FakeIMAP.next_uid
            FakeIMAP.next_uid += 1
            self.store[folder][uid] = data

    def move(self, uids, dest):
        for u in uids:
            self.store[dest][u] = self.store[self.cur].pop(u)

    def folder_status(self, folder, what):
        return {b"MESSAGES": len(self.store.get(folder, {})), b"UNSEEN": 0}

    def add_flags(self, *a): pass
    def remove_flags(self, *a): pass

    def delete_messages(self, uids):
        for u in uids:
            self.store[self.cur].pop(u, None)

    def expunge(self, *a): pass


class FakeSMTP:
    sent: list = []
    fail = False

    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def login(self, *a): pass

    def send_message(self, msg, from_addr, to_addrs):
        if FakeSMTP.fail:
            raise OSError("smtp down")
        time.sleep(0.05)
        msg.sent_from = from_addr
        FakeSMTP.sent.append(msg)


@pytest.fixture(autouse=True)
def mailbox(monkeypatch):
    monkeypatch.setattr(server, "connect", lambda account: FakeIMAP(account))
    monkeypatch.setattr(server.smtplib, "SMTP_SSL", FakeSMTP)
    FakeIMAP.stores = {}
    server._contacts_cache.clear()
    shutil.rmtree(server.ADDON_DATA, ignore_errors=True)   # add-on data is encrypted with the key removed below
    for f in (server.STORE_FILE, server.KEY_FILE):
        if f.exists():
            f.unlink()
    FakeSMTP.sent = []
    FakeSMTP.fail = False
    if server.SENT_LOG.exists():
        server.SENT_LOG.unlink()
    yield FakeIMAP.stores.setdefault("me@example.com", {f: {} for f in FOLDERS})
