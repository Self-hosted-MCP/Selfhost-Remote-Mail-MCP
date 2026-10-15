# Out of office (`out_of_office`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

While you're away, answers new emails with your message, once per person.

| | |
|---|---|
| **Tools it adds** | `out_of_office` (shows whether it's on) |
| **Needs setting up** | Yes: your away message |
| **Works by itself in the background** | Yes, every 5 minutes |
| **Sends email by itself** | **Yes**, your away message only |
| **Extra packages** | None |

> [!IMPORTANT]
> **This add-on sends email by itself**, without asking each time: that's its job. It only sends your away message, only to people who wrote to you, and follows every sending limit of the server.

## What it's good for

- **Holidays.** Set the first and last day before you leave. It starts and stops by itself.
- **A busy week or a deadline.** *"I'm answering emails slowly until Friday, for urgent things call the studio."* Turn it off when you're back.
- **Moving or a new address.** Tell everyone who writes to the old mailbox where to reach you, with `Mailboxes` set to that one address.
- **Only one of your mailboxes.** Away from work but not from personal mail? List just the work address.

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Set up** next to **Out of office**.
3. **Write your away message.** Your signature is added for you. If you like, add the first and last day you're away. Press **Save**.
4. **Press Turn on.**
5. **Check it works:** ask your AI app *"Is my out of office on?"* (start a new chat first). It says for which days and how many replies went out today.

> [!WARNING]
> **On a computer, it only answers while your computer is on**, because it checks for new mail in the background. It needs the server running there: check with `selfhost-remote-mail-mcp service status`. For holidays, a hosting company or your own server is more reliable.

Your AI app can tell you whether it's on and give you the setup link, but it can't change it. Other ways to turn it on: [the library page](../README.md#turn-one-on-and-set-it-up).

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
- It stays off on a second copy of the server where `ADDON_JOBS=off` is set, so two copies never both answer.

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

## Privacy

It remembers who it answered and when (to answer once each), saved encrypted on your server. It reads only the sender and headers of new mail, not the text.

## If something doesn't work

- **Nobody gets an answer:** check the days (it waits for the first day), and that the mailbox may send (mode **full**). Newsletters and robots are skipped on purpose.
- **On a computer, nothing happens:** the server in the background must run. `selfhost-remote-mail-mcp service status`.
- **Someone got it twice:** only after the number of days in **Once every** passed, or after you changed the message.

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: **yes**, your away message only
- The server running in the background (on a computer, `setup` starts it)
