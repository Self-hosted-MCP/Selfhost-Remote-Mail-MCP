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
| [phishing_alert](phishing_alert/README.md) | Gives each email a trust level and warns about scams | No | Nothing | No |
| [follow_ups](follow_ups/README.md) | Tells you which emails you sent got no reply in time | No | Nothing | No |
| [out_of_office](out_of_office/README.md) | Answers new emails with your away message, once per person | **Yes** | Nothing | No |
| [caldav](caldav/README.md) | Reads your calendar, finds free times, adds events (iCloud, Fastmail, Nextcloud…) | No | Your calendar server | `caldav` |
| [webhooks](webhooks/README.md) | Tells a web address of yours when new mail arrives (sender, subject, date) | No | The address you choose | No |

Add-ons that need extra packages: the Docker image has them all. On a computer, install them once with `uv tool install --force "selfhost-remote-mail-mcp[addons] @ git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP"`. Updates keep them.

More are added with new versions. Ideas are welcome in the [Share an add-on](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=addon.yml) form.

## Turn one on and set it up

Everything happens on the settings page of the web version:

1. Open the **Add-ons** tab and press **Turn on**. It works right away.
2. If the add-on needs details (like your business name for invoices), its row says **Needs setting up**. Press **Set up**, fill in the form and press **Save**. The details are saved on your server, encrypted.
3. Start a new chat in your AI app to use it.

You can also just ask your AI app, for example *"I want to make invoices"*. It can't turn add-ons on or type your details itself (so an email can never trick it into changing your bank details), but it gives you the link to the right setup page.

**Without the web version** (the server only on your computer, started by your AI app): use the command line instead. `selfhost-remote-mail-mcp addons list` shows them, `addons enable invoices` turns one on, and its details go in your settings file (each add-on's page lists the names, like `INVOICES_SELLER_NAME`).

Settings in the settings file or your host's variables still work and win over the setup page. Most people never need them.

## For AI coding agents

To install a library add-on for a user: read its README here, run `addons enable <name>` (or tell the user the `MAIL_ADDONS` line for their host), set the settings its README lists as required, run `selfhost-remote-mail-mcp addons` until it says "All add-ons load", then restart the server. Never put the user's passwords or keys in a chat: settings go in the settings file or the host's variables.

To change a library add-on for one user, copy its `addon.py` to the user's add-ons folder as `<name>.py`. That file then replaces the library one, and `addons` says so.

Writing a new add-on: [docs/addons.md](../../../docs/addons.md).
