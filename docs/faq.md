# Questions people ask

<details>
<summary><b>Is it free?</b></summary>

The software is free (MIT license). Running it on your own computer is free. A hosting company costs about $5 to $8 a month, paid to them. The AI app you use may need its own plan.

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

Yes, up to 5 in one server, at any providers. Each gets a mode (full, draft only, read only) and a name, and each AI app only gets the ones you tick. Add them on the settings page, with `setup`, or in the settings file. See [mailboxes.md](mailboxes.md).

</details>

<details>
<summary><b>Does it keep a copy of my email?</b></summary>

No. Everything stays in your mailbox. The server keeps only a few small files: settings, a short send log with no names or subjects, and fingerprints of login keys.

</details>

<details>
<summary><b>What happens if my computer is off?</b></summary>

With option 1, the AI app on that computer can't use your mail while it's off, scheduled emails wait, and phone access stops. Scheduled emails more than 2 hours late are held, not sent, so nothing goes out at a strange time. Options 2 and 3 run all the time.

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
<summary><b>How do I update it?</b></summary>

- Computer: `selfhost-remote-mail-mcp update`
- Hosting company: the **Update from official releases** action in your fork
- Own server: `./scripts/update.sh`

Each only installs official releases. Turn on `UPDATE_CHECK=on` to be told when there's one, or let it update by itself: [updates.md](updates.md).

</details>

<details>
<summary><b>How do I remove it completely?</b></summary>

See "Deleting everything" in [privacy.md](privacy.md#deleting-everything), then uninstall it (computer: `uv tool uninstall selfhost-remote-mail-mcp`; hosting: delete the service; own server: `docker compose down -v`).

</details>

<details>
<summary><b>Can I change the code?</b></summary>

Yes. Fork it, change it, share it, under the MIT license. Please keep the credit ([README](../README.md#credits)). [AGENTS.md](../AGENTS.md) explains the code, and [CONTRIBUTING.md](../CONTRIBUTING.md) explains how to send changes back.

</details>
