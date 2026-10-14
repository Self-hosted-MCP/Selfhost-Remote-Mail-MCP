"""The domain check: SPF, DKIM, DMARC and MX in plain words, with DNS answers faked."""
import re

import pytest
from starlette.testclient import TestClient

from selfhost_remote_mail_mcp import server


def fake_dns(monkeypatch, records: dict, mx: bool = True):
    monkeypatch.setattr(server, "dns_txt", lambda name: records.get(name, []))
    monkeypatch.setattr(server, "dns_has_mx", lambda domain: mx)


def levels(rows):
    return {name: level for name, level, _ in rows}


def account(address="me@example.com"):
    return next(a for a in server.all_accounts() if a.address == address)


def test_a_well_set_up_domain(monkeypatch, mailbox):
    mailbox["Sent"][900] = (b"DKIM-Signature: v=1; a=rsa-sha256; d=example.com; s=sel9;\r\n b=abc\r\n"
                            b"From: me@example.com\r\nSubject: hi\r\n\r\nbody")
    fake_dns(monkeypatch, {"example.com": ["v=spf1 include:_spf.example.net ~all"],
                           "sel9._domainkey.example.com": ["v=DKIM1; k=rsa; p=MIIB"],
                           "_dmarc.example.com": ["v=DMARC1; p=quarantine"]})
    rows = server.check_domain(account())
    assert levels(rows) == {"Receiving (MX)": "good", "SPF": "good", "DKIM": "good", "DMARC": "good"}
    assert 'key "sel9"' in rows[2][2]


@pytest.mark.parametrize("records,name,level,words", [
    ({}, "SPF", "bad", "Missing"),
    ({"example.com": ["v=spf1 a", "v=spf1 mx"]}, "SPF", "bad", "two SPF records"),
    ({"example.com": ["v=spf1 +all"]}, "SPF", "bad", "+all"),
    ({"example.com": ["v=spf1 mx all"]}, "SPF", "bad", "+all"),
    ({"example.com": ["v=spf1 mx ?all"]}, "SPF", "warn", "?all"),
    ({}, "DMARC", "bad", "_dmarc.example.com"),
    ({"_dmarc.example.com": ["v=DMARC1; p=none; rua=mailto:x@example.com"]}, "DMARC", "warn", "p=none"),
    ({"_dmarc.example.com": ["v=DMARC1; p=reject"]}, "DMARC", "good", "p=reject"),
    ({}, "DKIM", "warn", "Not found"),
    ({"google._domainkey.example.com": ["v=DKIM1; p=MIIB"]}, "DKIM", "good", '"google"'),
])
def test_each_record(monkeypatch, records, name, level, words):
    fake_dns(monkeypatch, records)
    row = next(r for r in server.check_domain(account()) if r[0] == name)
    assert row[1] == level and words in row[2]


def test_missing_mx_and_big_providers(monkeypatch):
    fake_dns(monkeypatch, {}, mx=False)
    assert levels(server.check_domain(account()))["Receiving (MX)"] == "bad"
    gmail = server.Account(address="me@gmail.com", password="x", imap_host="i", smtp_host="s")
    assert server.check_domain(gmail)[0][1] == "good" and "provider" in server.check_domain(gmail)[0][2]


def test_settings_page_runs_the_check(monkeypatch):
    fake_dns(monkeypatch, {"example.com": ["v=spf1 -all"]})
    monkeypatch.setenv("LOGIN_PASSPHRASE", "web test passphrase")
    monkeypatch.setenv("PUBLIC_URL", "http://localhost")
    client = TestClient(server.build_server(True).streamable_http_app(), base_url="http://localhost")
    client.post("/settings/login", data={"passphrase": "web test passphrase"}, headers={"origin": "http://localhost"})
    page = client.get("/settings").text
    assert "Check domain" in page
    csrf = re.search(r'name="csrf" value="([^"]+)"', page)[1]
    r = client.post("/settings/mailbox", data={"csrf": csrf, "action": "domain", "address": "me@example.com"},
                    headers={"origin": "http://localhost"})
    assert "Domain check: example.com" in r.text and "DMARC" in r.text and 'class="msg error"' in r.text
    monkeypatch.setattr(server, "PROVIDER", None)
