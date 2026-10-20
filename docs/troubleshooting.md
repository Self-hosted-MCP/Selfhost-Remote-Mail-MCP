# Troubleshooting

> [!TIP]
> Start here: `selfhost-remote-mail-mcp check` tests the logins and, for your own domain, its anti-spam records. It sends nothing. On a hosting company, look at the service's logs.

## Login and connection

<details>
<summary>"The mail server refused the login"</summary>

- Most providers need an **app password**, not your normal one ([email-providers.md](email-providers.md)).
- Check the login name: some hosts want one that isn't the full address. On the settings page it's under the mailbox's **Server and password** (or `MAIL_USERNAME` in the settings file).
- Zoho, GMX, WEB.DE, mail.com, Yandex, QQ and 163: IMAP has to be turned on in the mail settings first.
- Outlook.com and Hotmail don't work (Microsoft requires its own sign-in).

</details>

<details>
<summary>"nodename nor servname provided" or "Name or service not known"</summary>

The server name is misspelled, or your network blocks it. Check the IMAP and SMTP servers: on the settings page under the mailbox's **Server and password**, or `IMAP_HOST` and `SMTP_HOST` if the mailbox is in the settings file.

</details>

<details>
<summary>SMTP: "wrong version number" or a timeout</summary>

The SMTP port and encryption don't match. Try 587 if you had 465, or the other way round: on the settings page under **Server and password** (or `SMTP_PORT` in the settings file).

</details>

<details>
<summary>"No drafts folder was found"</summary>

Your provider names its folders unusually. Run the `folders` tool and look for your drafts folder; folders marked with a special role are found automatically. Open an issue with the folder names you see.

</details>

## The server on your computer

If you installed the [Claude Desktop extension](claude-desktop-extension.md#if-something-doesnt-work), start with its own checks.

On a computer, `setup` runs the server in the background, so you have the settings page at `http://localhost:8765/settings`. Start with `selfhost-remote-mail-mcp service status`: it says whether it's set to start at login and whether it runs.

<details>
<summary>The settings page doesn't open at localhost:8765</summary>

- Run `selfhost-remote-mail-mcp service status`. **Not installed:** run `selfhost-remote-mail-mcp service install`. **Not running:** run `selfhost-remote-mail-mcp service start`.
- Setup may have picked another port because 8765 was taken (it said so, like "this one uses 8766"). Open that one, or look for `PORT=` in the settings file.
- Still nothing? Read its log: on a Mac `~/Library/Logs/selfhost-remote-mail-mcp.log`, on Linux `journalctl --user -u selfhost-remote-mail-mcp`.

</details>

<details>
<summary>"It doesn't answer yet" or "Couldn't start it in the background"</summary>

The server started but stopped again, usually for one of these reasons, which its log shows:

- **No passphrase in the settings file.** One set only in a terminal doesn't count, because the background server doesn't see it. Run `selfhost-remote-mail-mcp set-passphrase`, then `service restart`.
- **An add-on can't load**, for example one that needs extra packages. See [the add-on library](../src/selfhost_remote_mail_mcp/library/README.md#if-an-add-on-doesnt-show-up).

</details>

<details>
<summary>"On this system, start-at-login isn't automatic yet" (Windows)</summary>

On Windows, start it by hand with `selfhost-remote-mail-mcp serve`, or let Task Scheduler start it when you log in ([steps](setup-computer.md#keep-it-running-in-the-background)).

</details>

<details>
<summary>"This server's web version already runs ..., started another way"</summary>

Setup found this server already running on this computer, for example as your own systemd service or in a terminal window. It leaves that one alone and changes nothing. Use it as it is, or stop it and run `selfhost-remote-mail-mcp service install` to have setup manage it.

</details>

<details>
<summary>A Mac asks whether the server may use the keychain</summary>

That happens for passwords that `setup --terminal` kept in the keychain, the first time the background server reads them, and again after some updates. Choose **Always Allow**. Until you answer, that mailbox can't log in. Mailboxes added on the settings page don't use the keychain.

</details>

<details>
<summary>Linux: logins fail after a restart, but work after I log in</summary>

The Linux keychain (Secret Service) unlocks only when you log in to the desktop. A password kept there can't be read before that. Add the mailbox on the settings page instead (its password is stored encrypted in the data folder), or put it in the settings file.

</details>

<details>
<summary>Scheduled emails or add-ons stop when the computer sleeps</summary>

They work only while the computer is on and awake. Emails scheduled while it was off go out when it's back, unless they're more than 2 hours late. Those are held, not sent, so nothing goes out at a strange time. For always-on, use [a hosting company](setup-hosting.md) or [your own server](setup-own-server.md).

</details>

## Your AI app

<details>
<summary>The app doesn't show the mail tools</summary>

- Same-computer apps: use the **full path** to `selfhost-remote-mail-mcp` ([connect-your-ai.md](connect-your-ai.md#before-you-start-the-command-path)), and restart the app after changing its settings.
- Run `selfhost-remote-mail-mcp stdio` in a terminal yourself. It should wait silently (press Ctrl+C to stop). If it prints an error instead, that's the problem.

</details>

<details>
<summary>"Redirect not allowed" on the login page</summary>

Your AI app isn't on the allowed list. Add its domain to `ALLOWED_REDIRECT_HOSTS`, for example `ALLOWED_REDIRECT_HOSTS=claude.ai,claude.com,chatgpt.com,openai.com,vscode.dev,myapp.example`.

</details>

<details>
<summary>"This login link expired"</summary>

The login page waits 10 minutes. Start connecting again from your AI app.

</details>

<details>
<summary>The login page names an app or website I don't know</summary>

Don't type your passphrase. Close the page. Someone may be trying to connect to your server. Your server is still safe as long as nobody knows your passphrase.

</details>

<details>
<summary>"Too many wrong tries"</summary>

Five wrong passphrases lock the login for 15 minutes. Wait, then try again.

</details>

<details>
<summary>The app connected yesterday but now asks to log in again</summary>

On a hosting company without a volume or disk at `/data`, logins are forgotten on every restart. Add the volume ([setup-hosting.md](setup-hosting.md)).

</details>

<details>
<summary>The login page opens but the app then fails</summary>

`PUBLIC_URL` must be exactly the address the app uses, with `https://` and without `/mcp`. Render and Railway set it themselves. On your own server, it comes from `MAIL_DOMAIN`.

</details>

<details>
<summary>`serve` says "Set a login passphrase first"</summary>

Set `LOGIN_PASSPHRASE` (12+ characters) or run `selfhost-remote-mail-mcp set-passphrase`.

</details>

## Add-ons and settings

<details>
<summary>The server stops at start-up with "add-on ..."</summary>

An add-on in `MAIL_ADDONS` has a problem, and the message says which and why. Run `selfhost-remote-mail-mcp addons` to check them without starting the server, and see the table at the end of [addons.md](addons.md#when-something-goes-wrong). To start without it, remove its name from `MAIL_ADDONS`.

</details>

<details>
<summary>"... can't be changed by an AI app" or "turned off in the server settings"</summary>

AI apps may only change six settings when you ask ([tools.md](tools.md#settings)). Everything else is yours, on the settings page or in the settings file. "Turned off in the server settings" means the settings file or hosting variables say `off`, which always wins. Change it there.

</details>

<details>
<summary>My AI app doesn't know an add-on's tools</summary>

Start a new chat after turning an add-on on. Old chats keep the tools they started with. An AI app on your computer (Claude Desktop, Claude Code, Codex) needs a restart: quit and reopen it. More in [the add-on library](../src/selfhost_remote_mail_mcp/library/README.md#if-an-add-on-doesnt-show-up).

</details>

<details>
<summary>An add-on says "Needs setting up", or won't turn on</summary>

- **Needs setting up:** a required detail is empty. Press **Set up** next to it on the settings page and fill in the required fields. Calendar and Webhooks have a **Test connection** button to check them.
- **Won't turn on and names a package** (`fpdf`, `caldav`): on a computer, install the add-on extras and restart ([how](../src/selfhost_remote_mail_mcp/library/README.md#turn-one-on-and-set-it-up)). The Docker image already has them.

</details>

<details>
<summary>Out of office or Webhooks do nothing</summary>

They check for new mail every 5 minutes in the background. Check that the add-on is on and set up, and on a computer that the server runs (`selfhost-remote-mail-mcp service status`). They stay off on a copy of the server where `ADDON_JOBS=off` is set: on a computer, setup sets that when you said another copy already uses the same mailboxes, so the other copy does it. Ask your AI app *"Is my out of office on?"* or *"Are my webhooks working?"* to see the last problem.

</details>

## Several mailboxes

<details>
<summary>"... isn't one of the mailboxes this app may use"</summary>

The AI app wasn't given that mailbox when it connected. Tick it for the app on the settings page (**Connected apps → Choose mailboxes**), or connect the app again and tick it on the login page.

</details>

<details>
<summary>"This AI app may not use any mailbox"</summary>

Every mailbox ticked for this app was removed. Choose new ones on the settings page, or connect the app again.

</details>

<details>
<summary>"... is set to 'draft' mode, so it never sends"</summary>

That mailbox is draft only. Send the draft from your mail app, or change the mailbox's mode (settings page or `MAIL_n_MODE`).

</details>

<details>
<summary>A mailbox I added on the settings page disappeared</summary>

The server couldn't unlock its password, usually because `MAIL_SECRET_KEY` changed or the `secret.key` file was lost. The server log says "can't unlock the password". Put the old key back, or add the mailbox again.

</details>

<details>
<summary>The settings page says 404</summary>

`SETTINGS_PAGE=off` is set. On a computer, also check that the server runs in the background: `selfhost-remote-mail-mcp service status`, and if it isn't, `selfhost-remote-mail-mcp service install`.

</details>

## Sending

<details>
<summary>My emails land in the receiver's spam</summary>

If you use your own domain, press **Check domain** on the settings page (or run `selfhost-remote-mail-mcp check`) and fix what shows red or yellow. See [mailboxes.md](mailboxes.md#check-your-domain). New domains and emails with many links also land in spam more often.

</details>

<details>
<summary>"Daily send limit reached for ..." or "Send limit reached (3 per minute)"</summary>

The limits are working. Wait, or raise `SEND_DAILY_LIMIT` or `SEND_MINUTE_LIMIT`.

</details>

<details>
<summary>A scheduled email didn't go out</summary>

- Is `serve` running? Only the web server sends scheduled emails. On a computer: `selfhost-remote-mail-mcp service status`.
- Ask for the `scheduled` list. A **HELD** email shows the reason. Schedule it again or send it now.
- Not in the list? The draft was probably edited in another mail app, which dropped the hidden send time. Schedule it again.
- Is `SCHEDULED_SEND=off` set? (setup sets it when another copy of the server uses the same mailboxes, because that copy sends them.)

</details>

<details>
<summary>"Not sent: ... isn't on the allowed list"</summary>

`SEND_ALLOWED_RECIPIENTS` is set and that address isn't on it. Add the address or its `@domain`, or remove the setting.

</details>

<details>
<summary>"This mail server is in read-only mode"</summary>

`MAIL_READ_ONLY=on` is set. Change it to `off` (or remove it) and restart when you want the AI to draft, sort or send.

</details>

<details>
<summary>The sent email isn't in my Sent folder</summary>

The server saves a copy in the folder marked as Sent. If your provider also saves one by itself (Gmail does), you may see two. Delete one; nothing was sent twice.

</details>

## Times look wrong

Times in the send log and in tool answers use the server's time zone. Set `TZ`, for example `TZ=America/New_York`.

## Still stuck?

Open an issue with the [**Something doesn't work**](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/issues/new?template=bug_report.yml) form. It asks for what's needed. Remove passwords and addresses first: issues are public.

Provider trouble? Use the [**My email provider doesn't work**](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/issues/new?template=provider_request.yml) form.
