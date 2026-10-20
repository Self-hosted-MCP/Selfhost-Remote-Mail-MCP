# The add-on library

> [!NOTE]
> **The add-on pages**
> - **Add-on library** (this page): ready-made add-ons to turn on
> - [Add-ons guide](../../../docs/addons.md): turn one on, write your own, test it
> - [Your add-ons folder](../../../addons/README.md): where your own add-on files go with Docker or a fork

Ready-made add-ons that come with the server. **All of them are off** until you turn them on. Each one has its own page with what it's good for, how to turn it on, what to ask your AI app and its settings.

## Pick one by what you want to do

| You want to | Add-on | Setup |
|---|---|---|
| See your calendar, find free times, add, move or delete events | [Calendar](caldav/README.md) (`caldav`) | Your calendar login |
| Send someone a meeting invite they add in one tap | [Calendar invite](calendar_invite/README.md) | None |
| Send a proposal, notes or a price list as a PDF | [PDF maker](pdf_maker/README.md) | None |
| Send numbered quotes, proformas and invoices | [Invoices and quotes](invoices/README.md) | Your business details |
| Know if an email is a scam before you click | [Phishing alert](phishing_alert/README.md) | None |
| Remember to chase emails nobody answered | [Follow-up reminders](follow_ups/README.md) | None |
| Answer people while you're on holiday | [Out of office](out_of_office/README.md) | Your away message |
| Start an automation when new mail arrives | [Webhooks](webhooks/README.md) | A web address and a secret |

## All of them at a glance

| Add-on | What it does | Works by itself in the background | Sends email by itself | Talks to | Extra packages |
|---|---|---|---|---|---|
| [calendar_invite](calendar_invite/README.md) | Attaches a calendar invite (`.ics`) to a draft | No | No | Nothing | No |
| [pdf_maker](pdf_maker/README.md) | Turns text into a PDF and attaches it to a draft | No | No | Nothing | `fpdf2` |
| [invoices](invoices/README.md) | Numbered quotes, proformas and invoices as PDFs, with totals | No | No | Nothing | `fpdf2` |
| [phishing_alert](phishing_alert/README.md) | Gives each email a trust level and warns about scams | No | No | Nothing | No |
| [follow_ups](follow_ups/README.md) | Tells you which emails you sent got no reply in time | No | No | Nothing | No |
| [out_of_office](out_of_office/README.md) | Answers new emails with your away message, once per person | Yes, every 5 minutes | **Yes** | Nothing | No |
| [caldav](caldav/README.md) | Reads your calendar, finds free times, adds, changes and deletes events (iCloud, Fastmail, Nextcloud…) | No | No | Your calendar server | `caldav` |
| [webhooks](webhooks/README.md) | Tells a web address of yours when new mail arrives (sender, subject, date) | Yes, every 5 minutes | No | The address you choose | No |

More are added with new versions. Ideas are welcome in the [Share an add-on](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/issues/new?template=addon.yml) form.

## Turn one on and set it up

Everything happens on your settings page. It's the same page on every kind of server:

| Where your server runs | Your settings page |
|---|---|
| Your computer | `http://localhost:8765/settings` |
| A hosting company or your own server | `https://your-address/settings` |

1. Open your settings page and type your passphrase.
2. Open the **Add-ons** tab and press **Turn on** next to the add-on. It works right away, with no restart.
3. If the add-on needs details (like your business name for invoices), its row says **Needs setting up**. Press **Set up**, fill in the form and press **Save**. The details are saved on your server, encrypted. Calendar and Webhooks also have a **Test connection** button.
4. Start a new chat in your AI app, so it sees the new tools. An AI app on your computer (Claude Desktop, Claude Code, Codex): quit and reopen it first.
5. Try it: each add-on's page has a question to check it works.

> [!TIP]
> You can also ask your AI app, for example *"I want to make invoices"*. It can't turn add-ons on or type your details itself, so an email can never trick it into changing your bank details. It gives you the link to the right setup page instead.

> [!IMPORTANT]
> **Calendar, PDF maker and Invoices need extra packages.** The Docker image has them all. On a computer, install them once, then restart the server in the background:
>
> ```bash
> uv tool install --force "selfhost-remote-mail-mcp[addons] @ git+https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP"
> ```
>
> ```bash
> selfhost-remote-mail-mcp service restart
> ```
>
> `selfhost-remote-mail-mcp update` keeps them after that.

**Prefer the terminal?** `selfhost-remote-mail-mcp addons list` shows them, `addons enable invoices` turns one on, and its details go in your settings file (each add-on's page lists the names, like `INVOICES_SELLER_NAME`). Then restart the server (on a computer: `selfhost-remote-mail-mcp service restart`) and your AI app.

Settings in the settings file or your host's variables still work and win over the setup page. Most people never need them.

## Ask before it acts

In your AI app you can set each tool to "Always ask" (in Claude: **Settings → Connectors**, then the mail connector's tools). Good ones to set:

| Tool | Add-on | Why |
|---|---|---|
| `delete_event` | Calendar | It already asks you once. "Always ask" adds your own tap |
| `add_event`, `edit_event` | Calendar | Changes your real calendar |
| `make_invoice` | Invoices | Uses up the next number |

Tools that only look, like `calendar_events` or `check_email`, can stay on "Always allow".

## If an add-on doesn't show up

- **The AI app doesn't know the new tools:** start a new chat. On a computer, quit and reopen the AI app. Old chats keep the tools they started with.
- **"Needs setting up" stays on:** a required setting is empty. Open **Set up** and fill in the fields marked as required.
- **It won't turn on and names a missing package** (`fpdf`, `caldav`): install the extra packages (see above).
- **Out of office or Webhooks do nothing on a computer:** they work only while the server runs in the background. Check with `selfhost-remote-mail-mcp service status`. They also stay off on a second copy of the server where `ADDON_JOBS=off` is set.
- **Still stuck:** ask your AI app *"Which add-ons are on?"*. The `settings` tool lists each add-on and its setup link.

## For AI coding agents

To install a library add-on for a user: read its README here, run `addons enable <name>` (or tell the user the `MAIL_ADDONS` line for their host), set the settings its README lists as required, run `selfhost-remote-mail-mcp addons` until it says "All add-ons load", then restart the server. Never put the user's passwords or keys in a chat: settings go in the settings file or the host's variables.

To change a library add-on for one user, copy its `addon.py` to the user's add-ons folder as `<name>.py`. That file then replaces the library one, and `addons` says so.

Writing a new add-on: [docs/addons.md](../../../docs/addons.md).
