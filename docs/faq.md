# Questions people ask

<details>
<summary><b>Is it free?</b></summary>

The software is free and open source (AGPL-3.0 license). Running it on your own computer is free. A hosting company costs about $5 to $8 a month, paid to them. The AI app you use may need its own plan.

</details>

<details>
<summary><b>Who can see my email?</b></summary>

Your mail provider (as always), and the AI app you connect, for the emails it opens. Nobody else. The authors of this project get nothing: no account, no tracking. Details in [privacy.md](privacy.md).

</details>

<details>
<summary><b>Can the AI send emails without asking me?</b></summary>

Only if you let it. Set `send_email` and `schedule_send` to "Always ask" in your AI app and every send waits for your yes. For extra safety you can limit who it may write to (`SEND_ALLOWED_RECIPIENTS`) or turn sending off completely (`MAIL_READ_ONLY=on`). See [safety.md](safety.md).

</details>

<details>
<summary><b>Can it delete my emails?</b></summary>

It can move emails to Trash, like you can. It can't empty the Trash or delete emails for good. Many providers empty the Trash after about 30 days.

</details>

<details>
<summary><b>Does it work with Gmail?</b></summary>

Yes, with an app password. [email-providers.md](email-providers.md) has the steps.

</details>

<details>
<summary><b>Does it work with Outlook or Hotmail?</b></summary>

Not yet. Microsoft no longer accepts passwords from mail apps for those accounts.

</details>

<details>
<summary><b>Can I use two mailboxes?</b></summary>

Yes, up to 5 in one server, at any providers. Each gets a mode (full, draft only, read only) and a name, and each AI app only gets the ones you tick. Add them on the settings page, with `setup --terminal`, or in the settings file. See [mailboxes.md](mailboxes.md).

</details>

<details>
<summary><b>Does it keep a copy of my email?</b></summary>

No. Everything stays in your mailbox. The server keeps only a few small files: settings, a short send log with no names or subjects, and fingerprints of login keys.

</details>

<details>
<summary><b>What happens if my computer is off?</b></summary>

With option 1, the AI app on that computer can't use your mail while it's off, scheduled emails and add-ons wait, the settings page is closed and phone access stops. Scheduled emails more than 2 hours late are held, not sent, so nothing goes out at a strange time. Options 2 and 3 run all the time.

</details>

<details>
<summary><b>Will my provider block it?</b></summary>

It logs in like any mail app (Apple Mail, Thunderbird), so providers treat it the same way. Very large numbers of sends can trigger a provider's spam limits; the default limits (40 a day per mailbox, 3 a minute) stay far below that. Gmail, for example, allows about 500 a day.

</details>

<details>
<summary><b>Can I use it with several AI apps at once?</b></summary>

Yes. Each app connects separately: Claude on your phone and Codex on your computer can both use the same server.

</details>

<details>
<summary><b>What are add-ons?</b></summary>

Extra features that come with the server, all off until you turn them on: a calendar, meeting invites, PDFs, invoices and quotes, a phishing check, follow-up reminders, an out-of-office reply and webhooks for automations. Turn one on in the settings page's **Add-ons** tab, then start a new chat in your AI app. Each one has a page with what it's good for and what to ask: see [the add-on library](../src/selfhost_remote_mail_mcp/library/README.md). You can also write your own ([addons.md](addons.md)).

</details>

<details>
<summary><b>Can it use my calendar?</b></summary>

Yes, with the [Calendar add-on](../src/selfhost_remote_mail_mcp/library/caldav/README.md): your AI app can see your events, find free times, and add, move or delete events. Deleting is always checked with you first, and no one is ever invited or emailed. It works with calendars that use CalDAV with an app password: iCloud, Fastmail, Nextcloud, mailbox.org, Posteo, Zoho and others. Google Calendar only allows Google's own sign-in, and Microsoft 365 and Outlook.com have no CalDAV, so those don't work yet. To send someone an invite instead, use [Calendar invite](../src/selfhost_remote_mail_mcp/library/calendar_invite/README.md), which works with any calendar.

</details>

<details>
<summary><b>What are my server's links?</b></summary>

Your server has one address. Every link is that address with something added at the end.

**Your address**, by where it runs:

| Where it runs | Your address |
|---|---|
| Your computer | `http://localhost:8765`. It only opens on that computer |
| Your computer, reached from your phone | The tunnel's address, like `https://your-computer.your-tailnet.ts.net` |
| A hosting company | The address it gives you, like `https://your-mail.up.railway.app` |
| Your own server or VPS | Your domain, like `https://mail.yourdomain.com` |

It's the `PUBLIC_URL` setting, if you set one.

**What to add to the end:**

| Add | What opens |
|---|---|
| `/mcp` | The link you paste into your AI app |
| `/settings` | The settings page: mailboxes, apps, add-ons, privacy, devices |
| `/settings/addon/caldav` | One add-on's setup page (here the Calendar's) |
| `/upload` | The upload page, for files to attach |
| `/upload/...` | A one-time link your AI app makes for a file. It works once, for 10 minutes |
| `/health` | Shows `ok` when the server runs |
| `/login` | You never open it yourself. Your AI app sends you there to type your passphrase |

**One full example:** with `mail.yourdomain.com`, the settings page is `https://mail.yourdomain.com/settings`, and the link for your AI app is `https://mail.yourdomain.com/mcp`.

Easy to mix up:

- `localhost` only works on the computer the server runs on, never from your phone.
- `PUBLIC_URL` is the address alone, without `/mcp` at the end.
- An old one-time `/upload/...` link stops working. Ask your AI app for a new one.

</details>

<details>
<summary><b>How do I open the settings page?</b></summary>

Go to your server's address with `/settings` on the end, like `https://mail.example.com/settings`, and type your passphrase. On your own computer it's `http://localhost:8765/settings`. If it doesn't open there, run `selfhost-remote-mail-mcp service status`. All the other links are in the question above.

</details>

<details>
<summary><b>How do I send a photo or PDF from my phone?</b></summary>

Open `https://your-address/upload` (on a computer: `http://localhost:8765/upload`), choose the file and press **Upload**. Then tell your AI app: *"Attach the file I just uploaded to the email to Sam."* More in [attachments.md](attachments.md).

</details>

<details>
<summary><b>Do I have to type my passphrase every time?</b></summary>

No. AI apps stay connected for up to 90 days. On the settings and upload pages, keep **Remember this device** ticked and that browser stays signed in for 90 days. Let your phone or password manager save the passphrase too, so it fills in with Face ID or a fingerprint when you need it again.

</details>

<details>
<summary><b>Do photos I send show where I took them?</b></summary>

Not when you attach them through this server. It removes the location from jpg, png and webp photos, and the author's name from documents, before they're attached. You can turn this off on the settings page. See [attachments.md](attachments.md#private-details-are-removed).

</details>

<details>
<summary><b>Can the pages be in my language?</b></summary>

Yes. The login, settings and upload pages come in 20 languages and follow your browser. Any other language can be added by an AI agent with one command. The AI itself already talks to you in your language. See [languages.md](languages.md).

</details>

<details>
<summary><b>Can I drop a file into the chat and have it emailed?</b></summary>

Yes, in AI apps that connect over the internet and can run code. Drop it in and say *"email this to Sam"*. Your AI app uploads it to your server with a one-time link and attaches it. AI apps on your own computer attach the file straight from its folder instead. Some apps need their code tool turned on first (in Claude: **Settings → Capabilities → Code execution and file creation**). If your app can't upload, it gives you the link to pick the file yourself. See [attachments.md](attachments.md#drop-a-file-in-the-chat).

</details>

<details>
<summary><b>My photos are too big to send. What can I do?</b></summary>

Ask: *"Make the photos smaller."* They're resized to look the same on screens, often 5 to 10 times lighter. If the files are over the 25 MB limit, the AI offers this by itself. See [attachments.md](attachments.md#photo-size-hd-or-smaller).

</details>

<details>
<summary><b>My emails land in spam. Can it help?</b></summary>

If you use your own domain, yes: press **Check domain** on the settings page. It checks SPF, DKIM and DMARC and says what to fix. See [mailboxes.md](mailboxes.md#check-your-domain).

</details>

<details>
<summary><b>Can the AI change my settings?</b></summary>

Only six, and only when you ask: removing photo location, removing document details, the update check, your signature, templates, and files on the upload page. It always tells you what it changed, and the settings page lists every change. Mailboxes, sending, limits and everything about safety stay yours. See [tools.md](tools.md#settings).

</details>

<details>
<summary><b>I forgot my passphrase. What now?</b></summary>

Set a new one. Nothing is lost, because the passphrase only guards the pages. It doesn't unlock any stored data.

- Hosting company: change `LOGIN_PASSPHRASE` in its variables. The server restarts with the new one.
- Own server or computer: run `selfhost-remote-mail-mcp set-passphrase`, or change `LOGIN_PASSPHRASE` in the settings file, then restart.

Mailboxes and connected AI apps keep working. Browsers signed in to the settings page are signed out and need the new passphrase.

</details>

<details>
<summary><b>Can I see who signed in?</b></summary>

Yes. The settings page lists the browsers signed in to it, and every sign-in of the last 7 days, including wrong passphrases and AI app logins, with the device and network address. Sign out any device you don't recognise, then change your passphrase. You can turn this log off on the same page.

</details>

<details>
<summary><b>How do I update it?</b></summary>

- Computer: `selfhost-remote-mail-mcp update`
- Hosting company: the **Update from official releases** action in your fork
- Own server: `./scripts/update.sh`, or with the ready-made image `docker compose pull && docker compose up -d`

Each only installs official releases. Turn on `UPDATE_CHECK=on` (or ask your AI: *"Tell me when there's a new version"*) to be told when there's one, or let it update by itself: [updates.md](updates.md).

</details>

<details>
<summary><b>How do I remove it completely?</b></summary>

See "Deleting everything" in [privacy.md](privacy.md#deleting-everything), then uninstall it (computer: `selfhost-remote-mail-mcp service remove`, then `uv tool uninstall selfhost-remote-mail-mcp`; hosting: delete the service; own server: `docker compose down -v`).

</details>

<details>
<summary><b>Can I change the code?</b></summary>

Yes. Fork it, change it, share it, under the AGPL-3.0 license. If you share a changed version or run one for other people, offer them its source code too (set `SOURCE_URL`). Please keep the credit ([README](../README.md#credits)). [AGENTS.md](../AGENTS.md) explains the code, and [CONTRIBUTING.md](../CONTRIBUTING.md) explains how to send changes back.

</details>
