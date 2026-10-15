# The add-on library

> [!NOTE]
> **The add-on pages**
> - **Add-on library** (this page): ready-made add-ons to turn on
> - [Add-ons guide](../../../docs/addons.md): turn one on, write your own, test it
> - [Your add-ons folder](../../../addons/README.md): where your own add-on files go with Docker or a fork

Ready-made add-ons that come with the server. **All of them are off** until you turn them on, and each one has its own page with what it does, what to ask your AI app and its settings.

| Add-on | What it does | Sends email by itself | Talks to | Extra packages |
|---|---|---|---|---|
| [calendar_invite](calendar_invite/README.md) | Attaches a calendar invite (`.ics`) to a draft | No | Nothing | No |
| [pdf_maker](pdf_maker/README.md) | Turns text into a PDF and attaches it to a draft | No | Nothing | `fpdf2` |
| [invoices](invoices/README.md) | Numbered quotes, proformas and invoices as PDFs, with totals | No | Nothing | `fpdf2` |

Add-ons that need extra packages: the Docker image has them all. On a computer, install them once with `uv tool install --force "selfhost-remote-mail-mcp[addons] @ git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP"`. Updates keep them.

More are added with new versions. Ideas are welcome in the [Share an add-on](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=addon.yml) form.

## Turn one on

**On the settings page** (the web version): open the **Add-ons** tab and press **Turn on**. It works right away; start a new chat in your AI app to use it. If the add-on needs settings (its page says which), add them too.

**On your computer:**

```bash
selfhost-remote-mail-mcp addons enable calendar_invite
```

It adds the name to `MAIL_ADDONS` in your settings file and checks that it loads. Then restart your AI app.

**On a hosting company** (Railway, Render and others): add the name to the `MAIL_ADDONS` variable, like `MAIL_ADDONS=calendar_invite`. Several are separated by commas. The host restarts by itself.

**On your own server (Docker Compose):** add the name to `MAIL_ADDONS` in your `.env` file, then run `docker compose up -d`.

To see them all: `selfhost-remote-mail-mcp addons list`. To turn one off: `selfhost-remote-mail-mcp addons disable calendar_invite`, or remove it from `MAIL_ADDONS`.

## For AI coding agents

To install a library add-on for a user: read its README here, run `addons enable <name>` (or tell the user the `MAIL_ADDONS` line for their host), set the settings its README lists as required, run `selfhost-remote-mail-mcp addons` until it says "All add-ons load", then restart the server. Never put the user's passwords or keys in a chat: settings go in the settings file or the host's variables.

To change a library add-on for one user, copy its `addon.py` to the user's add-ons folder as `<name>.py`. That file then replaces the library one, and `addons` says so.

Writing a new add-on: [docs/addons.md](../../../docs/addons.md).
