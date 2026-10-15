# Changelog

All notable changes to this project. Versions follow [semantic versioning](https://semver.org).

## 0.11.0 (2026-10-14)

- **Settings page in tabs:** each tab (Mailboxes, Apps, Privacy, Devices, ...) now shows only its own section instead of one long page, and after saving a form you stay on its tab.
- **Add-ons tab:** lists every library add-on, on or off, with what it does and a link to its page. Library add-ons turn on and off with one button, right away, without a restart. Add-ons turned on in `MAIL_ADDONS` are marked as such.
- **Docs:** how to connect OpenClaw and Hermes Agent.

## 0.10.0 (2026-10-14)

- **The add-on library:** ready-made add-ons that come with the server, all off until you turn them on. `selfhost-remote-mail-mcp addons list` shows them, `addons enable <name>` and `addons disable <name>` turn one on or off. Each has its own page. The first three:
  - `calendar_invite`: attaches a calendar invite to a draft (moved from `examples/addons`; your `MAIL_ADDONS` setting keeps working). Now with event details, and long lines folded as calendar apps expect.
  - `pdf_maker`: turns text with headings, lists, tables and links into a PDF and attaches it.
  - `invoices`: numbered quotes, proformas and invoices as PDFs, with exact totals, and a list of what you made.
- **Add-on extras:** packages some library add-ons need (`fpdf2`, `tzdata`), already in the Docker image. On a computer: see each add-on's page. `update` keeps them.
- **More for add-on writers:** read emails (`api.find`, `api.message`, `api.replies_to`), make drafts (`api.new_draft`), keep encrypted data (`api.store`), run background jobs (`api.every`, `api.new_mail`), reach outside services they list (`api.http`), and, for add-ons whose job is sending, send through the normal limits (`api.send`). A file of your own replaces the library add-on of the same name.

## 0.9.0 (2026-10-14)

- **The pages in 20 languages:** English, Spanish, Portuguese (Brazil), French, German, Italian, Dutch, Polish, Swedish, Turkish, Russian, Ukrainian, Japanese, Chinese (Simplified and Traditional), Korean, Hindi, Indonesian, Vietnamese and Greek. They follow the browser; `LANGUAGE` can fix one. Missing texts fall back to English.
- **Add any language with an AI agent:** `selfhost-remote-mail-mcp translate <code>` makes the file to fill in, `translate --check <code>` checks it. Your own files win over the shipped ones.
- The AI is told to speak to the user in their own language (tool answers stay in English).

## 0.8.1 (2026-10-14)

- Docs: dropping a file in the chat is described for any AI app that can run code, with Claude as one example.

## 0.8.0 (2026-10-14)

- **Drop a file in the chat, it goes in the email:** the new `upload_link` tool gives the AI a one-time link (one file, 10 minutes, 25 MB), and its code tool uploads the file you dropped into the chat. If it can't, the AI gives you the link to pick the file yourself, with no passphrase. Works in Claude (web, desktop, phone) with code execution on, and in coding apps.
- Upload links keep only a fingerprint, go through the usual file checks, show in the Sign-ins list, and can be turned off on the settings page or with `UPLOAD_LINKS=off`.

## 0.7.0 (2026-10-14)

- **Photo size:** photos go as they are (HD), or smaller when you ask: at most 2560 pixels on the long side, at high quality, often 5 to 10 times lighter. When files are over the size limit, the AI offers to make the photos smaller instead of failing.
- **iPhone HEIC photos:** the AI asks first, then changes them to JPG (full size, location removed) or keeps them as they are.
- New dependencies: Pillow and pillow-heif (about 25 MB installed).

## 0.6.1 (2026-10-14)

- **Where to find the settings:** the login page shows the settings page link, and the `accounts` tool gives the AI the settings and upload links to share once you've connected.
- **Clearer sending choice** on the login page: not ticked, the app writes drafts and you press send; ticked, it can press send for you.
- **Connected apps** on the settings page only lists apps that finished logging in. Unfinished connection attempts (for example a wrong passphrase) are removed after an hour.
- Editing a draft keeps notes that add-ons put on it, like which attachments to leave out of the Sent copy.
- `check` and `help` describe what they do today (several mailboxes, the domain check).
- Docs: a guide to the settings page, section by section; what `check` prints; how to open the settings file; more example requests; every file the server keeps; many small corrections.

## 0.6.0 (2026-10-14)

- **Add-ons:** plug in your own features as small Python files (`MAIL_ADDONS`). An add-on can add tools, change drafts and attach files through the same checks as everything else, and keep large files out of the Sent copy. It can never send email itself. Guide: [docs/addons.md](docs/addons.md).
- Two example add-ons: `hello` (the smallest one) and `calendar_invite` (attaches an `.ics` invite to a draft).
- New command `selfhost-remote-mail-mcp addons` checks that add-ons load and lists their tools.
- New "Share an add-on" form on GitHub. Good add-ons can join the official version.

## 0.5.0 (2026-10-14)

- **Two new tools:** `settings` shows the settings an AI app may change; `change_setting` changes one of six, only when you ask: remove photo location, remove document details, update check, your signature, templates, and files on the upload page. The AI always tells you what it changed.
- **Changes by AI apps** on the settings page: every change an AI app made, for 30 days.
- The update check can now also be switched on or off by asking your AI (`UPDATE_CHECK` in the settings still wins).

## 0.4.0 (2026-10-14)

- **Remember this device:** the settings and upload pages keep a browser signed in for 90 days (on by default), even across restarts. Changing the passphrase signs every browser out.
- **Device log** on the settings page: the browsers signed in now (sign out any of them), and every sign-in of the last 7 days, including wrong passphrases and AI app logins, with device and network address. Turn it off on the page or with `DEVICE_LOG=off`.
- **Privacy for attachments:** photos lose their location, camera and dates (jpg, png, webp); Word, Excel, PowerPoint, OpenDocument and PDF files lose the author and company. On by default, with switches on the settings page (`REMOVE_PHOTO_LOCATION`, `REMOVE_DOCUMENT_DETAILS`).
- **Domain check:** a button per mailbox on the settings page (and in `check`) looks up MX, SPF, DKIM and DMARC for your own domain and says in plain words what to fix. Uses the new `dnspython` dependency.
- **New look:** a lighter purple, lime highlights and small pink details. The settings page has a section bar that stays at the top while you scroll. New icon colour.
- FAQ: opening the settings page, uploading from a phone, typing the passphrase less, a forgotten passphrase, seeing who signed in, photo location, emails in spam.

## 0.3.0 (2026-10-14)

- **Attach new files**, not only ones from other emails: from your computer (`attach_path`, computer version), small files the AI writes (`attach_content`, up to 2 MB), or the new **upload page** (`attach_upload`).
- **Upload page** at `/upload` (web version, behind your passphrase): upload a file, then tell your AI "attach the file I just uploaded" or use its name. The AI can list the waiting files to check with you first. Files are stored encrypted and deleted 1 hour after first going into a draft, or after 24 hours if never used.
- **File checks:** photos, PDFs, documents, audio, video and zips are allowed. Programs and scripts, files whose content doesn't match their name, and zips with programs inside are refused. Suspect files (macros, svg and html, archives that can't be checked) are only attached after you say yes. See [docs/attachments.md](docs/attachments.md).
- New settings: `ATTACH_MAX_MB` (25), `ATTACH_FOLDERS` (your home folder), `UPLOAD_PAGE` (on).

## 0.2.0 (2026-10-14)

- **Several mailboxes:** up to 5 (`MAX_MAILBOXES`), at any providers, from the settings file (`MAIL_2_*` ...), `setup`, or the new settings page. The older `READ_ONLY_*` settings still work.
- **A mode per mailbox:** full, draft only (never sends) or read only, enforced by the server.
- **Names for mailboxes**, like "Work". Tools accept them instead of addresses. Rename any mailbox on the settings page.
- **Per-app choices:** the login page asks which mailboxes an AI app may use; change it later or disconnect apps on the settings page.
- **Settings page** at `/settings`: add, test, rename, edit and remove mailboxes; choose mailboxes per app. Passphrase sign-in, locked-down cookie, CSRF and same-origin checks. Passwords stored encrypted (`MAIL_SECRET_KEY`).
- **Server icon:** an envelope mark for AI apps that show server icons, plus a favicon.
- Unreachable mail servers give a clear message instead of a crash.
- **Updates, opt-in:** `UPDATE_CHECK=on` shows "Update available" on the settings page and in the `accounts` tool; `selfhost-remote-mail-mcp update`; a GitHub Action for forks on hosting companies; `scripts/update.sh` for own servers. Official releases only. The settings page shows the version and recent changes.
- **Send permission per app:** "Allow sending" on the login page, off by default; change it on the settings page.
- **Checked against the MCP security guidance:** access keys now last 1 hour and are refused if issued for another server; the settings cookie uses the `__Host-` prefix on HTTPS; the login page warns when an app returns to `localhost`; line breaks in addresses or subjects are refused (header injection); PDFs are read up to 50 pages.
- **More encryption by default:** `setup` keeps mail passwords in the system keychain; mail connections use a strict TLS setting (certificate always checked, TLS 1.2 or newer); the send log is private (owner-only); HTTPS pages send HSTS.
- **Daily send limit is now per mailbox, 40 by default** (was 20 in total). The per-minute limit (3) still counts all mailboxes together.

## 0.1.0 (2026-10-14)

First public version.

- 15 tools: read, search, threads, attachments, drafts (new, reply, reply-all, forward, edit, delete), organising, contacts, templates, send now, scheduled send.
- Two ways to run: `stdio` for apps on the same computer, `serve` for web and phone apps with a passphrase login (OAuth 2.1).
- Three ways to host: your computer, Railway or Render, your own server with Docker and Caddy.
- Safety: separate sending tools, daily and per-minute limits, allowed recipients, read-only mode, a read-only second mailbox, no double sends, scheduled emails held when something is wrong, email text labelled as untrusted.
- Privacy: send log without names or subjects by default, login keys stored only as fingerprints, no telemetry.
- `setup` wizard with known providers, and `check` to test the login without sending.
- Starter files in `examples/`: five signature designs that work in light and dark mail apps, two plain signatures, and five templates (thank you, follow-up, reschedule, invoice reminder, out of office).
- Signatures get a clean plain-text copy: one line per row, links keep their address.
