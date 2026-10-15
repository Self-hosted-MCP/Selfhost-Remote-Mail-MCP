# webhooks

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

When new mail arrives, tells a web address of yours: who sent it, the subject and the date. Use it to start automations in Zapier, Make, n8n or your own app, like a phone notification for emails from a client.

## What it sends

For each new email in the Inbox, one small JSON message:

```json
{"type": "email.received", "mailbox": "you@example.com", "folder": "INBOX",
 "from": "Sam <sam@example.com>", "subject": "Quote for October",
 "date": "2026-10-14T10:30:00+01:00", "message_id": "<abc@example.com>"}
```

**Never** the email's text, its attachments or the other people it went to. Subjects can hold private details or one-time codes: turn them off with the **Include the subject** setting. The receiver keeps what it gets, under its own privacy rules.

## Turn it on

1. In Zapier (*Webhooks by Zapier → Catch Raw Hook*), Make (*Custom webhook*), n8n (*Webhook* node) or your own app, create an address that accepts POST requests.
2. Make a signing secret: at least 24 random characters, for example from your password manager.
3. On the settings page, open the **Add-ons** tab, press **Set up** next to **Webhooks**, paste the address and the secret, and press **Save**. Then **Turn on**, and **Test connection** to send a test message (`{"type": "test", ...}`) to your receiver.

It checks for new mail every 5 minutes, so messages arrive within about 5 minutes. Mail that was already there when you turned it on isn't sent. It runs in the background, so on a computer it works while the computer is on.

## Checking it really came from your server

Each message is signed the [Standard Webhooks](https://www.standardwebhooks.com/) way: headers `webhook-id`, `webhook-timestamp` and `webhook-signature` (`v1,` + base64 of HMAC-SHA256 over `id.timestamp.body` with your secret).

**If you check signatures with a Standard Webhooks library, use a `whsec_` secret.** Make one with `echo "whsec_$(openssl rand -base64 32)"`. Any other secret (24+ characters) is used as plain text, which suits your own code but not those libraries. Zapier and Make don't check signatures themselves; for them you can also set an **Authorization header** that the receiver checks.

The same email can arrive twice (after a retry): use `webhook-id` to skip repeats.

## When the receiver is down

It tries again every 5 minutes for up to 3 days, keeping at most 500 waiting. Only answers that mean "never" (404, 410, 413, 422) skip a message; anything else, like "busy" or "forbidden", is tried again. If it was off for more than a day, it starts fresh and doesn't send the backlog.

Ask your AI app *"Are my webhooks working?"*: it shows the host, how many were delivered or are waiting, and the last problem.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `WEBHOOKS_URL` | Yes | Where to send. https, or plain http for a service on your own network (like `http://n8n:5678/...`) |
| `WEBHOOKS_SECRET` | Yes | The signing secret, 24+ characters or a `whsec_` secret |
| `WEBHOOKS_AUTH_HEADER` | No | Sent as the `Authorization` header |
| `WEBHOOKS_SUBJECT` | No | `off` leaves the subject out. Default on |
| `WEBHOOKS_MAILBOXES` | No | Only these addresses, separated by commas. Empty: all |

## What it needs

- Extra packages: none
- Outside services: the address you choose
- Sends email by itself: no
- The server running in the background (on a computer, `setup` starts it)
