# SPDX-License-Identifier: AGPL-3.0-only
"""Files that the web version and an AI app's copy on the same computer both change: no lost changes,
no clashing temporary files, one secret key."""
import json
import threading

from selfhost_remote_mail_mcp import server


def at_once(*jobs):
    threads = [threading.Thread(target=job) for job in jobs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_writes_at_the_same_moment_dont_clash(tmp_path):
    target, errors = tmp_path / "file.json", []

    def write(n):
        def job():
            try:
                for i in range(30):
                    server.private_write(target, json.dumps({"n": n, "i": i}))
            except Exception as exc:
                errors.append(exc)
        return job

    at_once(*(write(n) for n in range(6)))
    assert errors == [] and json.loads(target.read_text())["i"] == 29
    assert [p.name for p in tmp_path.iterdir()] == ["file.json"]   # no temporary files left behind
    assert target.stat().st_mode & 0o777 == 0o600


def test_no_settings_change_is_lost():
    server.PREFS_FILE.unlink(missing_ok=True)
    names = [f"switch_{n}" for n in range(8)]
    at_once(*(lambda name=name: server.set_pref(name, True) for name in names),
            lambda: server.set_page_addon("pdf_maker", True))
    prefs = server.read_prefs()
    assert all(prefs.get(name) is True for name in names) and prefs["addons"] == ["pdf_maker"]
    server.PREFS_FILE.unlink()


def test_no_change_list_entry_or_setting_is_lost():
    server.CHANGES_FILE.unlink(missing_ok=True)
    at_once(*(lambda n=n: server.record_change(f"change {n}") for n in range(8)))
    assert len(json.loads(server.CHANGES_FILE.read_text())) == 8
    at_once(*(lambda n=n: server.write_settings({f"TEST_SHARED_{n}": "x"}) for n in range(8)))
    text = server.ENV_FILE.read_text()
    assert all(f"TEST_SHARED_{n}=x" in text for n in range(8))
    server.write_settings({}, drop=tuple(f"TEST_SHARED_{n}" for n in range(8)))


def test_one_secret_key_even_when_two_start_at_once(monkeypatch):
    monkeypatch.delenv("MAIL_SECRET_KEY", raising=False)
    saved = server.KEY_FILE.read_bytes() if server.KEY_FILE.exists() else None
    server.KEY_FILE.unlink(missing_ok=True)
    tokens = []
    at_once(*(lambda: tokens.append(server.secret_box().encrypt(b"hello")) for _ in range(8)))
    box = server.secret_box()
    assert [box.decrypt(t) for t in tokens] == [b"hello"] * 8   # every copy used the same key
    if saved is not None:
        server.KEY_FILE.write_bytes(saved)
