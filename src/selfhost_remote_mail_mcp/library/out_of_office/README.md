# out_of_office

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

While you're away, answers new emails with your message, once per person.

> [!IMPORTANT]
> **This add-on sends email by itself**, without asking each time: that's its job. It only sends your away message, only to people who wrote to you, and follows every sending limit of the server.

## Turn it on

1. On the settings page, open the **Add-ons** tab and press **Set up** next to **Out of office**.
2. Write your away message and, if you like, the first and last day you're away. Press **Save**.
3. Press **Turn on**.

Your AI app can tell you whether it's on (*"Is my out of office on?"*) and give you the setup link, but it can't change it. Other ways: [the library page](../README.md#turn-one-on-and-set-it-up). It checks for new mail every 5 minutes in the background, so on a computer it works while the computer is on.

## Who gets an answer

Only real people who wrote to you directly, once every few days each (4 by default). It never answers:

- mailing lists, newsletters and anything bulk
- robots: no-reply addresses, bounces, other automatic replies
- mail where you're only in Bcc
- mail that failed your provider's sender checks (so a forged address never gets your reply)
- spam, and old mail from before it was turned on or while the server was down
- your own addresses

Your reply doesn't quote their email. Changing the message or the days starts fresh: everyone can get the new message once.

## Limits

- At most 20 replies a day (`DAILY_MAX`, 20 is the most). They count toward the mailbox's normal daily limit (`SEND_DAILY_LIMIT`, 40 by default), so your own sending still has room.
- At most 2 per check, so your own sending is never blocked by the per-minute limit.
- It does nothing when the server is read-only or `SEND_ALLOWED_RECIPIENTS` is set.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `OUT_OF_OFFICE_MESSAGE` | Yes | Your away message. Your signature is added |
| `OUT_OF_OFFICE_FROM` | No | First day away, like `2026-10-20`. Empty: from now |
| `OUT_OF_OFFICE_UNTIL` | No | Last day away. Empty: until you turn it off |
| `OUT_OF_OFFICE_ONCE_EVERY_DAYS` | No | Answer the same person once every this many days. Default 4 |
| `OUT_OF_OFFICE_DAILY_MAX` | No | Most replies a day. Default and most: 20 |
| `OUT_OF_OFFICE_MAILBOXES` | No | Only these addresses, separated by commas. Empty: every mailbox that may send |
| `OUT_OF_OFFICE_TIMEZONE` | No | Your time zone, like `Europe/Lisbon` |

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: **yes**, your away message only
- The server running in the background (on a computer, `setup` starts it)
