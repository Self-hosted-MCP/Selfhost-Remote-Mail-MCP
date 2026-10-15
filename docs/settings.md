# Every setting

Settings come from **environment variables** (what hosting dashboards call "Variables") and/or a **settings file**. When both have a value, the environment variable wins.

> [!NOTE]
> Most changes to the settings file count from the next request, no restart needed. These need a restart: `PORT`, `HOST`, `PUBLIC_URL`, `ALLOWED_REDIRECT_HOSTS`, `SETTINGS_PAGE`, `UPLOAD_PAGE`, `SCHEDULED_SEND`, `MAIL_ADDONS` and `MAIL_ADDONS_DIR`. On a hosting company, changing a variable restarts the server by itself.

The settings file is `~/.config/selfhost-remote-mail-mcp/.env`, or whatever `MAIL_ENV_FILE` points to. `selfhost-remote-mail-mcp setup` writes it for you. One `KEY=value` per line, `#` for comments, no quotes needed.

## Your mailbox (mailbox 1)

Required unless you add every mailbox on the [settings page](mailboxes.md).

| Setting | Required | Default | What it is |
|---|---|---|---|
| `MAIL_ADDRESS` | Yes | | Your email address |
| `MAIL_PASSWORD` | Yes | | Password or app password ([email-providers.md](email-providers.md)) |
| `IMAP_HOST` | Yes | | Server for reading, e.g. `imap.gmail.com` |
| `SMTP_HOST` | Yes | | Server for sending, e.g. `smtp.gmail.com` |
| `MAIL_LABEL` | | | A short name, like `Work` |
| `MAIL_MODE` | | `full` | `full`, `draft` (never sends) or `read` (read only) |
| `IMAP_PORT` | | `993` | IMAP over SSL |
| `SMTP_PORT` | | `465` | `465` = SSL, `587` = STARTTLS |
| `MAIL_NAME` | | | Your name on outgoing mail |
| `MAIL_USERNAME` | | your address | Login name, if different from the address |
| `SMTP_USERNAME` | | `MAIL_USERNAME` | Login name for sending only, if it differs from the reading one (iCloud sometimes needs this) |
| `MAIL_SIGNATURE` | | | A simple signature, `\n` for new lines. `signature.html` or `signature.md` in the config folder win over it |

## Several mailboxes

Mailboxes 2 to 5 use the same settings with their number: `MAIL_2_...`, `MAIL_3_...` and so on. The whole guide is [mailboxes.md](mailboxes.md).

| Setting | Default | What it is |
|---|---|---|
| `MAIL_2_ADDRESS` | | The address. A numbered mailbox exists once this is set |
| `MAIL_2_PASSWORD` | | Its password or app password |
| `MAIL_2_IMAP_HOST`, `MAIL_2_IMAP_PORT` | mailbox 1's | Its IMAP server, if it isn't the same as mailbox 1's |
| `MAIL_2_SMTP_HOST`, `MAIL_2_SMTP_PORT` | mailbox 1's | Its SMTP server |
| `MAIL_2_NAME` | mailbox 1's | Name on outgoing mail |
| `MAIL_2_USERNAME`, `MAIL_2_SMTP_USERNAME` | its address | Login names, if different |
| `MAIL_2_MODE` | `full` | `full`, `draft` or `read` |
| `MAIL_2_LABEL` | | A short name, like `Personal` |
| `MAX_MAILBOXES` | `5` | Most mailboxes one server holds |
| `READ_ONLY_ADDRESS`, `READ_ONLY_PASSWORD`, `READ_ONLY_USERNAME` | | The older way to add one read-only mailbox on mailbox 1's server. Still works |

## Settings page

| Setting | Default | What it is |
|---|---|---|
| `SETTINGS_PAGE` | `on` | `off` removes the settings page (`/settings`) from the web version |
| `DEVICE_LOG` | `on` | `off` stops the device log: no list of signed-in browsers' devices and addresses, no 7-day sign-in history. It can also be turned off on the settings page |
| `MAIL_SECRET_KEY` | | A long random value that encrypts the passwords of mailboxes added on the settings page. Keep it apart from the data folder, for example in your hosting company's secret variables. If it isn't set, the server makes `secret.key` in the data folder instead |

## Sending

| Setting | Default | What it is |
|---|---|---|
| `SEND_DAILY_LIMIT` | `40` | Most emails **each mailbox** sends per day (now and scheduled together). Resets at midnight |
| `SEND_MINUTE_LIMIT` | `3` | Most emails sent per minute, **all mailboxes together** |
| `SCHEDULED_SEND` | `on` | `off` stops this copy from sending scheduled emails (`serve` only) |

## Safety and privacy

| Setting | Default | What it does |
|---|---|---|
| `MAIL_READ_ONLY` | `off` | `on` makes every mailbox read-only at once: the AI can read and search, but can't draft, move, flag, delete or send anything. Good for trying it out. For one mailbox, use its mode instead |
| `SEND_ALLOWED_RECIPIENTS` | empty (anyone) | Only allow sending to these addresses and domains, separated by commas. Example: `me@example.com,@mycompany.com`. Anyone else is refused, even if the AI tries |
| `SEND_LOG_DETAILS` | `off` | `on` also writes who each email went to and its subject in `sent.log` and in the server's log lines. Off keeps only times and counts |

## Web server (`serve`)

| Setting | Default | What it is |
|---|---|---|
| `LOGIN_PASSPHRASE` | | Your login passphrase, 12+ characters. Easiest for hosting dashboards |
| `LOGIN_HASH` | | A scrambled passphrase written by `set-passphrase`. Wins over `LOGIN_PASSPHRASE` |
| `PUBLIC_URL` | see below | The public `https://` address, without `/mcp` |
| `HOST` | `127.0.0.1` | Network address to listen on. Docker images use `0.0.0.0` |
| `PORT` | `8765` | Port to listen on. Railway and Render set it themselves |
| `ALLOWED_REDIRECT_HOSTS` | `claude.ai,claude.com,chatgpt.com,openai.com,vscode.dev` | Web apps allowed to receive the login. Apps on your own computer (localhost) are always allowed |
| `SOURCE_URL` | empty | Only for a changed version that other people use: the address of its source code. The page footers and the settings page link to it, as the AGPL license asks. Leave it empty if you run the project unchanged |

`serve` refuses to start without a passphrase. If `PUBLIC_URL` isn't set, it uses the address Render (`RENDER_EXTERNAL_URL`) or Railway (`RAILWAY_PUBLIC_DOMAIN`) provides, and otherwise `http://localhost:PORT`, which only works on the same computer.

## Attachments

| Setting | Default | What it does |
|---|---|---|
| `ATTACH_MAX_MB` | `25` | Most MB of new files per email, and per upload |
| `REMOVE_PHOTO_LOCATION` | `on` | `off` keeps the location and camera details in attached photos. Can also be turned off on the settings page |
| `REMOVE_DOCUMENT_DETAILS` | `on` | `off` keeps the author and company in attached documents. Can also be turned off on the settings page |
| `ATTACH_FOLDERS` | `~` | Folders the computer version may attach files from, separated by commas. Hidden files are never allowed |
| `UPLOAD_PAGE` | `on` | `off` removes the upload page (`/upload`) from the web version. See [attachments.md](attachments.md) |
| `UPLOAD_LINKS` | `on` | `off` turns off one-time upload links, which let an AI app upload a file you dropped into the chat. Can also be turned off on the settings page. See [attachments.md](attachments.md#drop-a-file-in-the-chat) |

## Updates

| Setting | Default | What it does |
|---|---|---|
| `UPDATE_CHECK` | `off` | `on`: once a day, ask GitHub which release is newest, and show "Update available" on the settings page and in the `accounts` tool. Nothing about you is sent. Your AI can also turn it on or off when you ask; setting it here locks it. See [updates.md](updates.md) |

## Language

| Setting | Default | What it does |
|---|---|---|
| `LANGUAGE` | empty | Show the web pages in one language, like `de`. Empty: follow each browser. See [languages.md](languages.md) |
| `MAIL_LOCALES_DIR` | `<config folder>/locales` | Where your own translation files are. Must be an environment variable |

## Add-ons

| Setting | Default | What it does |
|---|---|---|
| `MAIL_ADDONS` | empty | Add-ons to turn on, by name, separated by commas. See [addons.md](addons.md) |
| `MAIL_ADDONS_DIR` | `<config folder>/addons` | The folder add-ons are loaded from. Docker images use `/app/addons` |
| `<NAME>_...` | | An add-on's own settings start with its name in capitals, like `CALENDAR_INVITE_ORGANIZER` |

## Folders

| Setting | Default | What it is |
|---|---|---|
| `MAIL_CONFIG_DIR` | `~/.config/selfhost-remote-mail-mcp` | Your folder: settings file, `signature.html`, `signature.md`, `templates/` |
| `MAIL_ENV_FILE` | `<config folder>/.env` | Use a settings file somewhere else. This one and the two around it must be environment variables, since they say where the settings file is |
| `DATA_DIR` | `<config folder>/state` | The server's own files: logins, send log, mailboxes added on the settings page, uploads, switches, devices and the AI change list. Every file is listed in [privacy.md](privacy.md#what-the-server-keeps). Docker images use `/data` |
| `TZ` | system | Time zone for the send log and the times you see, e.g. `Europe/London`. Must be a real environment variable (or a hosting variable); the settings file can't set it |

## Files in your config folder

- `signature.html`: added under every draft as written, except notes inside `<!-- -->`, which are removed. A clean plain-text copy is made from it. Five designs are in [examples/signatures](../examples/signatures/).
- `signature.md`: a simpler signature in plain text or Markdown, if there's no `signature.html`.
- `templates/*.md`: one template per file. Optional `Subject:` and `To:` lines, then a line with `---`, then the body. Placeholders look like `{{topic}}`. The [examples folder](../examples/) has five ready templates and seven signatures to copy.
