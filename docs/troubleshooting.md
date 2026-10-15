# Troubleshooting

> [!TIP]
> Start here: `selfhost-remote-mail-mcp check` tests the logins and, for your own domain, its anti-spam records. It sends nothing. On a hosting company, look at the service's logs.

## Login and connection

<details>
<summary>"The mail server refused the login"</summary>

- Most providers need an **app password**, not your normal one ([email-providers.md](email-providers.md)).
- Check `MAIL_USERNAME`: some hosts want a login name that isn't the full address.
- Zoho, GMX, WEB.DE, mail.com, Yandex, QQ and 163: IMAP has to be turned on in the mail settings first.
- Outlook.com and Hotmail don't work (Microsoft requires its own sign-in).

</details>

<details>
<summary>"nodename nor servname provided" or "Name or service not known"</summary>

The server name is misspelled, or your network blocks it. Check `IMAP_HOST` and `SMTP_HOST`.

</details>

<details>
<summary>SMTP: "wrong version number" or a timeout</summary>

The SMTP port and encryption don't match. Try `SMTP_PORT=587` if you had 465, or the other way round.

</details>

<details>
<summary>"No drafts folder was found"</summary>

Your provider names its folders unusually. Run the `folders` tool and look for your drafts folder; folders marked with a special role are found automatically. Open an issue with the folder names you see.

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

Open an issue with the [**Something doesn't work**](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=bug_report.yml) form. It asks for what's needed. Remove passwords and addresses first: issues are public.

Provider trouble? Use the [**My email provider doesn't work**](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=provider_request.yml) form.
