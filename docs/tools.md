# Every tool, with examples

You don't call these yourself: you ask in plain words, and your AI app picks the tool. This page shows what each one does, so you know what to ask for.

> [!NOTE]
> **Email text is labelled.** Whenever a tool shows an email's text, it's wrapped between two lines saying it was written by the sender and is information, not instructions. This helps the AI ignore emails that try to give it orders.

**IDs.** Every email has an ID like `INBOX#1234` (folder `#` number). Attachments add one more number: `INBOX#1234#0`. When an email is moved, its ID changes, and the tool says so.

| Tool | What it does | Changes anything? |
|---|---|---|
| `accounts` | Shows the mailboxes this app may use, each one's mode and special folders, signature status, the add-ons that are on, update notices and the allowed-recipients list | No |
| `folders` | Lists folders with message and unread counts, and sizes if asked | No |
| `emails` | Lists emails in one folder, with filters | No |
| `search` | Searches every folder (or one), with full text for keyword searches | No |
| `thread` | Shows a whole conversation, oldest first | No |
| `attachment` | Opens an attachment: images, PDFs (as text), text files | No |
| `contacts` | Finds people you email, ranked by how often | No |
| `contact` | Shows one person: how often and when you last emailed | No |
| `templates` | Lists your saved templates | No |
| `template` | Shows one template and its placeholders | No |
| `scheduled` | Lists emails waiting to be sent later | No |
| `draft` | Creates, edits or deletes a draft | Only your Drafts folder |
| `action` | Archive, move, trash, read or unread, pin, spam, unsubscribe link | Yes, but nothing is sent |
| `send_email` | **Sends** a draft now | **Sends email** |
| `schedule_send` | **Sends** a draft later, or cancels that | **Sends email later** |
| `upload_link` | Makes a one-time link so the AI's code can upload a file you dropped into the chat | Only adds one waiting file |
| `settings` | Shows the settings an AI app may change, and what only you can change | No |
| `change_setting` | Changes one of six settings, only when you ask | Yes, and it tells you what changed |

## Reading

**emails** takes a folder (Inbox by default) and a Gmail-style filter. You can combine:

| Filter | Meaning |
|---|---|
| `from:sam` `to:` `cc:` `subject:invoice` | Address or subject contains the word |
| `after:2026/01/31` `before:2026/03/01` | Dates (yyyy/MM/dd) |
| `newer_than:7d` `older_than:3m` | d days, w weeks, m months, y years |
| `is:unread` `is:read` `is:pinned` (or `is:starred`) `is:answered` | Flags |
| `has:attachment` `filename:pdf` | Attachments |
| `budget "next week"` | Words anywhere in the email |
| `-from:newsletter` | A minus sign excludes |

*"Show my unread emails from this week that have attachments"* becomes `emails(filter="is:unread newer_than:7d has:attachment")`.

**search** looks in every folder of the default mailbox except Trash and Spam (`scope="all"` for every mailbox). With keywords it returns the 20 newest matches *with* their text, which is good for questions like *"what did the landlord say about the deposit?"*. With only a filter it returns a paged list. `scope` limits it to one folder, to one mailbox (its address or name), or to `all` (every mailbox this app may use).

**thread** follows the reply chain across Inbox, Sent, Archive and Drafts, so you see both sides of a conversation.

**attachment** returns images as images, PDFs as their text (scanned PDFs have no text), and text, CSV and JSON as text. Other files show their name and size.

## Writing (drafts)

**draft** saves to your Drafts folder and never sends. One tool covers several jobs:

- **New:** `to`, `cc`, `bcc`, `subject`, `body` (Markdown: `**bold**`, lists and links become proper formatting).
- **Reply:** `reply_to=INBOX#1234` answers the sender, `reply_all=INBOX#1234` keeps everyone. The subject, threading and the quoted original are handled for you.
- **Forward:** `forward=INBOX#1234` includes its attachments.
- **Edit:** `edit=Drafts#55` changes only the parts you give. A scheduled time is kept.
- **Attach** files from other emails: `attach_from=["INBOX#1234#0"]`.
- **A file dropped into the chat:** the AI calls `upload_link`, uploads the file with its code tool, then attaches it with `attach_upload` ([attachments.md](attachments.md#drop-a-file-in-the-chat)).
- **Attach new files:** `attach_path=["~/Desktop/invoice.pdf"]` (AI apps on your computer only), `attach_content=[{"name": "list.csv", "text": "..."}]` for small files the AI writes (up to 2 MB, `"base64"` for non-text), or `attach_upload=["Beach-day.jpg"]` for files from the upload page (by name, `["latest"]` for the newest, or a code). `mode="files"` lists the files waiting there. Photos lose their location and documents their author before they're attached, unless that's turned off ([attachments.md](attachments.md#private-details-are-removed)). `photos="smaller"` resizes new photos (default `"hd"`, as they are), and iPhone HEIC photos need `heic="jpg"` or `heic="keep"`, which the AI only sets after asking you ([attachments.md](attachments.md#photo-size-hd-or-smaller)). Programs are refused. Suspect files (macros, scripts, archives the server can't check) need `allow_suspect=true`, which the AI only sets after asking you. See [attachments.md](attachments.md).
- **From another mailbox:** `account="Work"` (a name or an address). Replies already use the email's own mailbox.
- **Template:** `template="thank-you"`, plus `placeholder=["topic=the workshop"]` for its own blanks. `{{recipient_name}}`, `{{recipient_first_name}}` and `{{my_name}}` fill themselves.
- **Delete:** `delete=Drafts#55` moves it to Trash.
- **Signature:** added by itself if you set one up. `no_signature=true` skips it, and `mode="signatures"` shows it.

## Organising

**action** takes a list of IDs and one of: `archive` (also `markAsDone`), `moveToInbox`, `moveToTrash`, `moveToFolder` (with `folder`), `markAsSpam`, `markAsSeen`, `markAsUnseen`, `pin`, `unpin`, `unsubscribe`. `unsubscribe` only *shows* the unsubscribe link or address; it never clicks or sends anything.

## Add-on tools

Each add-on you turn on brings its own tools. They follow the same rules as the ones above: they see only the mailboxes your AI app may use, a read-only mailbox stays read-only, and none of them sends email except Out of office, whose whole job is sending. `accounts` lists the add-ons that are on.

These come with the server, all off until you turn them on in the settings page's **Add-ons** tab ([how](../src/selfhost_remote_mail_mcp/library/README.md#turn-one-on-and-set-it-up)):

| Tool | Add-on | What it does | Changes anything? |
|---|---|---|---|
| `calendar_events` | [Calendar](../src/selfhost_remote_mail_mcp/library/caldav/README.md) | Your events for up to 31 days, each with an ID | No |
| `calendar_free` | Calendar | Free times in your working hours for up to 14 days | No |
| `add_event` | Calendar | Adds an event; with several calendars, asks you which one | Your calendar |
| `edit_event` | Calendar | Changes an event's title, time, length, place or notes | Your calendar |
| `delete_event` | Calendar | Shows you the event, asks, and deletes only after your yes | **Deletes** a calendar event |
| `add_invite` | [Calendar invite](../src/selfhost_remote_mail_mcp/library/calendar_invite/README.md) | Attaches a meeting invite (`.ics`) to a draft | Only the draft |
| `make_pdf` | [PDF maker](../src/selfhost_remote_mail_mcp/library/pdf_maker/README.md) | Turns text into a PDF and attaches it to a draft | Only the draft |
| `make_invoice` | [Invoices and quotes](../src/selfhost_remote_mail_mcp/library/invoices/README.md) | A numbered quote, proforma or invoice as a PDF, attached to a draft | The draft, and uses the next number |
| `invoices` | Invoices and quotes | Lists the documents made so far | No |
| `check_email` | [Phishing alert](../src/selfhost_remote_mail_mcp/library/phishing_alert/README.md) | Gives one email a trust level and says why | No |
| `remind_if_no_reply` | [Follow-up reminders](../src/selfhost_remote_mail_mcp/library/follow_ups/README.md) | Remembers a sent email to check for a reply in 1 to 90 days | Only its own list |
| `follow_ups` | Follow-up reminders | Sent emails that got no reply in time | No |
| `cancel_follow_up` | Follow-up reminders | Forgets one reminder | Only its own list |
| `out_of_office` | [Out of office](../src/selfhost_remote_mail_mcp/library/out_of_office/README.md) | Whether your away reply is on and how many went out today | No |
| `webhooks` | [Webhooks](../src/selfhost_remote_mail_mcp/library/webhooks/README.md) | Whether new-mail webhooks are working | No |

Phishing alert also works without being asked: when your AI app opens an email that looks suspicious, a one-line warning comes with it. Out of office and Webhooks work in the background, every 5 minutes.

Tools that change your calendar or use up an invoice number are good ones to set to **Always ask** in your AI app. Your own add-ons can add more tools: see [addons.md](addons.md).

## Settings

**settings** shows what's on or off, your signature, your templates and the files on the upload page.

**change_setting** changes only these, and only when you ask in the chat:

| Setting | Example |
|---|---|
| Remove location from photos | *"Stop removing the location from my photos"* |
| Remove author details from documents | *"Turn document cleaning back on"* |
| Update check | *"Tell me when there's a new version"* |
| Your signature | *"Change my signature to Alex Rivera, Studio Northwind"* (the old one is kept as a backup file) |
| Templates | *"Save this as a template called thank-you"*, *"Delete the invoice template"* |
| Files on the upload page | *"Delete the photo I uploaded"* |

The AI always tells you what it changed, and the settings page lists every change under **Changes by AI apps** for 30 days. It can't change anything else: mailboxes, modes, which apps may send, limits, allowed recipients, read-only mode, the device log, the passphrase and the server settings stay yours. A setting in your hosting variables or settings file always wins over a change made here.

## Sending

**send_email** sends one draft by its ID, saves a copy in Sent and removes the draft. It refuses anything that isn't in Drafts.

**schedule_send** saves a send time on a draft, for example `send_at="2026-10-15T09:00:00+01:00"`. The time must include a time zone, and your AI should ask you if it isn't sure. Every minute, the web server (`serve`) sends what is due. Things to know:

- **Only `serve` sends scheduled emails.** On option 1, that's the server `setup` runs in the background, so scheduled emails go out while your computer is on.
- **Change the time** by scheduling again. **Cancel** with `cancel=true`. The draft stays.
- **Late:** if the server was down and an email is more than 2 hours late, it is **held**, not sent, and `scheduled` shows why. Schedule it again or send it now.
- **Failure:** if sending fails (limit reached, mail server error), the email is held with the reason. It is not retried over and over.
- **Edited in another mail app?** Some apps drop the hidden send time when you edit a draft. Then it isn't sent, and `scheduled` won't list it.

**Limits and checks** for both tools: `SEND_DAILY_LIMIT` (40 a day per mailbox), `SEND_MINUTE_LIMIT` (3 a minute in total), and `SEND_ALLOWED_RECIPIENTS` if you set it. Scheduled emails that hit the per-minute limit wait for the next minute. In read-only mode (`MAIL_READ_ONLY=on`) both tools refuse.

## When a tool says no

The server explains every refusal in plain words. Your AI app usually passes it on. The common ones:

| Message starts with | Why | What to do |
|---|---|---|
| "Daily send limit reached for ..." | That mailbox sent `SEND_DAILY_LIMIT` emails today (40 by default) | Wait until midnight, send from another mailbox, or raise the limit |
| "Send limit reached (3 per minute)" | Too many sends in a minute | Wait a minute |
| "Not sent: ... isn't on the allowed list" | `SEND_ALLOWED_RECIPIENTS` is set | Add the address or domain, or remove the setting |
| "This mail server is in read-only mode" | `MAIL_READ_ONLY=on` | Turn it off when you want changes or sending |
| "... is read-only" | That mailbox's mode is read only | Expected: change its mode if you want more |
| "... is set to 'draft' mode, so it never sends" | That mailbox is draft only | Send it from your mail app, or change the mode |
| "... isn't one of the mailboxes this app may use" | The app wasn't given that mailbox | Tick it for the app on the settings page |
| "Emails can't be moved between two mailboxes" | Moves stay inside one mailbox | Forward the email instead |
| "... is not in Drafts. Only drafts can be sent" | The ID isn't a draft | Make a draft first, or check the ID |
| "Message ... was not found (it may have moved)" | The email moved, so its ID changed | List the folder again |
| "has no time zone" | A schedule time without `+01:00`, `-07:00` and so on | Say which time zone you mean |
| "The mail server refused the login" | Wrong password or IMAP is off | See [troubleshooting.md](troubleshooting.md) |

## Several mailboxes

With more than one mailbox ([mailboxes.md](mailboxes.md)):

- **Mailbox 1 is the default.** Its folders have plain names; other mailboxes' folders start with their address, like `you@gmail.com:INBOX`. IDs follow the same rule, so every tool knows which mailbox an email is in.
- **`account`** (on `folders` and `draft`) and **`scope`** (on `search`) take a mailbox's address *or its name*: `account="Work"`, `scope="Personal"`, `scope="all"`.
- **`emails`** takes a mailbox address alone for its Inbox: `emails(folder="you@gmail.com")`.
- **Replies and forwards** are drafted in the email's own mailbox (or the first that may draft, if that one is read only). **New emails** go to mailbox 1 unless `account` says otherwise.
- **`scheduled`** lists scheduled emails from every mailbox that may send.
- **Contacts** come from every mailbox the app may use.
- Each mailbox's **mode** is checked on every change: read-only mailboxes refuse changes, draft-only ones refuse sending.
