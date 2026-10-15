<p align="center"><img src="docs/images/icon.png" alt="" width="88"></p>

<h1 align="center">Selfhost-Remote-Mail-MCP</h1>

<p align="center"><b>Your own email inside Claude, ChatGPT, Codex and other AI apps.<br>On your computer and on your phone. Self-hosted, private, careful with sending.</b></p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"></a>
<a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-server-black" alt="MCP server"></a>
<a href="docs/connect-your-ai.md"><img src="https://img.shields.io/badge/works%20with-Claude%20%C2%B7%20ChatGPT%20%C2%B7%20Codex-orange" alt="Works with Claude, ChatGPT, Codex"></a>
<a href="#choose-how-to-run-it"><img src="https://img.shields.io/badge/self--hosted-computer%20%C2%B7%20cloud%20%C2%B7%20server-green" alt="Self-hosted"></a>
</p>

<p align="center">
<a href="#quick-start-option-1-about-5-minutes">Quick start</a> ·
<a href="#choose-how-to-run-it">Ways to run it</a> ·
<a href="docs/mailboxes.md">Several mailboxes</a> ·
<a href="docs/safety.md">Safety</a> ·
<a href="#all-the-guides">All guides</a>
</p>

<table align="center"><tr>
<td align="center"><img src="docs/images/login-page.png" alt="The login page: choose which mailboxes an AI app may use" width="240"><br><sub>Choose which mailboxes each AI app may use</sub></td>
<td align="center"><img src="docs/images/settings-page.png" alt="The settings page: mailboxes, modes and connected apps" width="380"><br><sub>Add mailboxes, set modes, manage apps</sub></td>
</tr></table>

You run it yourself, so your password stays with you and no company in the middle reads your mail.

It works with almost any mailbox: Gmail, iCloud, Fastmail, Yahoo, Zoho, a mailbox on your own domain, and most others. Your AI app can read, search, sort and write drafts. It sends an email only when you say so.

```
You: Anything urgent from this week? Draft a reply to Sam saying Thursday works.
AI:  Reads your inbox, writes the reply into your Drafts folder and shows it to you.
     Nothing goes out until you say "send it".

You: (drops invoice.pdf into the chat) Email this to Sam.
AI:  Uploads the file to your server by itself, attaches it to a draft and shows it to you.
```

## How it works, in one picture

```
 Your AI app  ──►  this server  ──►  your mail provider (Gmail, iCloud, ...)
 (Claude,          (on your          reads with IMAP, sends with SMTP,
  ChatGPT, ...)     computer or       the same way any mail app does
                    your server)
```

The server is a small program. Your AI app talks to it through **MCP** (Model Context Protocol), a standard way for AI apps to use outside tools. The server then talks to your mailbox the way a normal mail app does. The authors of this project never see your mail, your password or anything else: there is no account, no cloud service and no tracking.

## Words you'll see

| Word | What it means here |
|---|---|
| **IMAP** and **SMTP** | The standard ways mail apps read (IMAP) and send (SMTP) email. Your provider lists its IMAP and SMTP server names. |
| **App password** | A separate password your provider makes for one app. You can delete it any time without changing your real password. Gmail, iCloud and Yahoo need one. |
| **Passphrase** | A long password you make up for the web version of this server. You type it once when you connect an AI app. |
| **MCP** | How AI apps plug into tools like this one. |
| **Draft** | An email saved in your Drafts folder. The AI writes drafts. Sending is a separate step. |
| **Settings file** | A small text file with your settings, `~/.config/selfhost-remote-mail-mcp/.env` on a computer. `setup` writes it. Hosting companies use their own "Variables" page instead |
| **Data folder** | Where the server keeps its own files (logins, send log, uploads). On a computer `~/.config/selfhost-remote-mail-mcp/state`, in Docker and on hosting companies `/data` |

## Choose how to run it

|  | Where it runs | Works on your phone | Cost | Time | Guide |
|---|---|---|---|---|---|
| **1. Your computer** | Your Mac, Windows or Linux computer | Only while the computer is on, with an extra step | Free | 5 minutes | [setup-computer.md](docs/setup-computer.md) |
| **2. A hosting company** | Railway, Render, Fly.io or others, in the cloud | Always | About $5 to $8 a month | 10 minutes, no terminal needed | [setup-hosting.md](docs/setup-hosting.md) |
| **3. Your own server** | Any server with Docker | Always | Free to cheap | 15 minutes, for people used to servers | [setup-own-server.md](docs/setup-own-server.md) |

> [!TIP]
> Not sure? Start with **1** to try it for free. Move to **2** when you want it on your phone all the time. Option 2 works with [any hosting company that runs Docker](docs/setup-hosting.md#any-other-hosting-company), not only Railway and Render.
>
> Using an AI coding agent like Claude Code or Codex? Ask it to set this up wherever you choose: [AGENTS.md](AGENTS.md#deploying-for-a-user) gives it a checklist.

## What it can do

**Read.** List and search every folder with simple filters (for example `from:sam is:unread newer_than:7d`). Open whole conversations. Open attachments: pictures, PDFs and text files.

**Write.** Make drafts: new emails, replies, reply-to-all and forwards. Your signature and saved templates are added for you. Drafts go to your normal Drafts folder, so you can also finish them in your usual mail app.

**Drop a file in the chat, it goes in the email.** Drop a PDF or photo into Claude (web, desktop or phone) and say *"email this to Sam"*. Claude uploads it to your server by itself with a one-time link, attaches it and shows you the draft. You don't need the passphrase or another app. If Claude can't upload it, it gives you the link to pick the file yourself. Up to 25 MB. See [docs/attachments.md](docs/attachments.md#drop-a-file-in-the-chat).

**Attach files.** From other emails, from your computer, files the AI writes (like a CSV), or photos and documents you upload from your phone on the upload page. Programs are refused, and suspect files (like spreadsheets with macros) need your OK. Photos go in HD, or smaller if you ask (the AI offers it when files are too big), and iPhone HEIC photos can become JPG after you say yes. See [docs/attachments.md](docs/attachments.md).

**Create files on the go.** Ask your AI to make a calendar invite, a CSV spreadsheet, a contact card or notes, and it attaches them to your email.

**Organise.** Archive, move, delete (to Trash), mark read or unread, pin, mark as spam. It can show you an email's unsubscribe link, but it never clicks it.

**Send, carefully.** Only two tools can send, so your AI app can ask you before each one:
- `send_email` sends a draft now.
- `schedule_send` sends a draft later, for example "tomorrow at 9am". The time is saved on the draft itself, so it survives restarts.

**Contacts.** Finds people from your own mail history: who you write to most and when you last did.

**Several mailboxes.** Up to 5, at any providers, each with its own mode (full, draft only or read only) and a short name like *Work*. Each AI app gets only the mailboxes you tick for it. See [docs/mailboxes.md](docs/mailboxes.md).

**A settings page.** In the web version, open `/settings` to add mailboxes, test logins, rename them, choose or disconnect AI apps, switch privacy options, see which devices signed in and what AI apps changed. It also shows your version and what's new. No terminal needed. Section by section: [docs/mailboxes.md](docs/mailboxes.md#three-ways-to-add-mailboxes).

**Privacy for your files.** Photos you attach lose their location, and documents lose the author's name, before they're sent. Both are on by default and can be turned off on the settings page. The server never loads pictures or links inside emails, so senders can't track when you read them.

**Settings you can change by asking.** *"Change my signature"*, *"save this as a template"*, *"stop removing photo locations"*. The AI may change six harmless settings when you ask and always tells you. Everything that affects safety stays on the settings page, where only you can change it.

**See who signed in.** The settings page lists the devices signed in and every sign-in of the last 7 days, wrong passphrases included. Sign out any device you don't recognise.

**Check your domain.** If you use your own domain (like `you@yourname.com`), one button checks the records that keep your emails out of spam (SPF, DKIM, DMARC) and says in plain words what to fix.

**Add-ons.** Plug in your own features as small Python files, like a calendar invite or a quote PDF, without changing the server. Two examples are included, and an AI coding agent can build one for you. See [docs/addons.md](docs/addons.md).

**Updates, if you want them.** Get told when there's a new release, or let it update itself, official releases only. See [docs/updates.md](docs/updates.md).

All 17 tools, with examples: [docs/tools.md](docs/tools.md).

## Safety and privacy

> [!WARNING]
> Anyone can put text in your inbox, and some emails are written to trick AI apps ("Assistant, forward all invoices to..."). Read [docs/safety.md](docs/safety.md) before you let any AI send for you.

Here is how the server protects you:

- **Every email is marked as information, not instructions,** each time the AI reads one.
- **Sending is separate.** Reading, drafting and sorting can never send. Set the two sending tools to "always ask" in your AI app and nothing goes out without your tap.
- **Limits.** By default at most 40 emails a day per mailbox and 3 a minute in total ([how the limits work](docs/safety.md#sending-limits)). You can also allow sending only to addresses or domains you choose (`SEND_ALLOWED_RECIPIENTS`), or turn sending off completely with read-only mode (`MAIL_READ_ONLY=on`).
- **Nothing is sent twice.** A lock and a small log stop the same email going out twice, even after a crash or restart.
- **Encrypted by default.** Connections to your mail provider always use checked TLS. On a computer, your mail password goes in the system keychain. Passwords added on the settings page are encrypted. Login keys are stored only as fingerprints, and the send log keeps only times and counts. [Encryption at a glance](docs/privacy.md#encryption-at-a-glance).
- **A login page that tells you who is asking.** The web version shows which app wants access and where it will send you back, and lets you tick which mailboxes it may use and whether it may send (off by default), before you type your passphrase. Checked against the [MCP security guidance](docs/safety.md#checked-against-mcp-and-email-security-guidance).
- **A mode for each mailbox.** Full, draft only (never sends) or read only, enforced by the server itself.

More in [docs/safety.md](docs/safety.md) (risks and good settings) and [docs/privacy.md](docs/privacy.md) (what is stored, where, and who can see it).

## Quick start (option 1, about 5 minutes)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), a small free tool that installs Python programs.
2. Install the server:

   ```bash
   uv tool install git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP
   ```

3. Answer a few questions. It finds the server names for well-known providers and tests your login without sending anything:

   ```bash
   selfhost-remote-mail-mcp setup
   ```

4. Connect your AI app. For Claude Code:

   ```bash
   claude mcp add -s user mail -- selfhost-remote-mail-mcp stdio
   ```

   For Claude Desktop, Codex, ChatGPT, Cursor, VS Code, Gemini CLI and the Claude website and phone app, see [docs/connect-your-ai.md](docs/connect-your-ai.md).

   Tip: in your AI app, set `send_email` and `schedule_send` to **Always ask**. Then nothing is sent without your yes.

5. Ask your AI: *"Use the mail tools: what's new in my inbox today?"* More ideas in [docs/examples.md](docs/examples.md).

## All the guides

| Guide | Read it when |
|---|---|
| [Setup on your computer](docs/setup-computer.md) | You want to try it, free |
| [Setup on a hosting company](docs/setup-hosting.md) | You want it on your phone, always on, without a terminal |
| [Setup on your own server](docs/setup-own-server.md) | You have a server with Docker |
| [Connect your AI app](docs/connect-your-ai.md) | The server runs and you want to use it |
| [Email providers](docs/email-providers.md) | You need your server names or an app password |
| [Several mailboxes](docs/mailboxes.md) | You want more than one mailbox, the settings page, or different mailboxes per app |
| [Every tool](docs/tools.md) | You want to know what to ask for |
| [Attaching files](docs/attachments.md) | You want to send photos, PDFs or documents |
| [Add-ons](docs/addons.md) | You want to add your own features, or have an AI agent build one |
| [Every setting](docs/settings.md) | You want to change limits, ports or safety options |
| [Safety](docs/safety.md) | Before you let an AI send email |
| [Privacy](docs/privacy.md) | You want to know what is kept and where |
| [Things to ask](docs/examples.md) | You want ideas for what to ask your AI |
| [How it works](docs/how-it-works.md) | You want to know how it works inside |
| [Questions people ask](docs/faq.md) | You have a quick question |
| [Updates](docs/updates.md) | You want to know about new versions, or have them install by themselves |
| [Troubleshooting](docs/troubleshooting.md) | Something doesn't work |
| [Roadmap](docs/roadmap.md) | You want to know what's planned |
| [CHANGELOG.md](CHANGELOG.md) | You want to know what changed in each version |
| [CONTRIBUTING.md](CONTRIBUTING.md) | You want to report a bug or send a fix |
| [AGENTS.md](AGENTS.md) | You (or your AI coding agent) want to change the code |

## Not supported yet

- **Outlook.com, Hotmail and Live accounts**, and Microsoft 365 accounts that need Microsoft's own sign-in. Microsoft stopped accepting passwords from mail apps.
- **Proton Mail** through Proton Bridge. Bridge uses a certificate this server doesn't accept yet.
- **Calendars.**

## Help and feedback

| You want to | Go to |
|---|---|
| Fix a problem yourself | [Troubleshooting](docs/troubleshooting.md) |
| Report a bug | [Something doesn't work](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=bug_report.yml) |
| Get a provider working | [My email provider doesn't work](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=provider_request.yml) |
| Ask a question or share an idea | [Question](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/issues/new?template=question.yml) |
| Report a security problem, privately | [Private report](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/security/advisories/new) ([SECURITY.md](SECURITY.md)) |

Issues are public, so leave out passwords, email addresses and email content.

## Credits

Selfhost-Remote-Mail-MCP was made by [s17sh70x2jfl031ag](https://github.com/s17sh70x2jfl031ag).

You're welcome to fork it, change it and build on it under the MIT license. The license asks you to keep the copyright notice in [LICENSE](LICENSE). Please also keep the [NOTICE](NOTICE) file and a line in your README such as *"Based on Selfhost-Remote-Mail-MCP by s17sh70x2jfl031ag"*. GitHub's "Cite this repository" button uses [CITATION.cff](CITATION.cff).

## License

MIT. See [LICENSE](LICENSE).
