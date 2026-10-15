# Follow-up reminders (`follow_ups`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Remembers emails you sent and tells you which ones got no reply in time.

| | |
|---|---|
| **Tools it adds** | `remind_if_no_reply`, `follow_ups`, `cancel_follow_up` |
| **Needs setting up** | No. Your time zone is optional |
| **Works by itself in the background** | No: it checks when you ask |
| **Sends email by itself** | No: the AI writes follow-up drafts, you send them |
| **Extra packages** | None |

## What it's good for

- **Pitches and proposals.** *"Remind me if Acme doesn't reply to this in 5 days."* A week later: *"Which of my emails are still waiting?"*
- **Unpaid invoices.** Send the invoice, then *"Remind me in 14 days if there's no answer."*
- **A Monday routine.** *"Show my due follow-ups and draft a friendly nudge for each."* You read the drafts and send the ones you like.
- **Job applications or press requests.** Keep track of who never wrote back, without a spreadsheet.

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Turn on** next to **Follow-up reminders**.
3. *(Optional)* Press **Set up** and choose your time zone, so "in 3 days" matches your days.
4. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
5. **Check it works:** open an email you sent and ask *"Remind me if nobody replies to this in 1 day."* Then *"Show all my follow-ups."*

Other ways to turn it on: [the library page](../README.md#turn-one-on-and-set-it-up).

## What you can ask

- *"Remind me if Sam doesn't reply to this in 3 days."*
- *"Which of my emails are still waiting for an answer?"*
- *"Show all my follow-ups, also the ones not due yet."*
- *"Draft a friendly follow-up to the ones that are due."* (the AI writes the drafts; you send them)
- *"Forget the reminder for the Acme pitch."*

## How it works

- The days count from when you sent the email, 1 to 90 days.
- A real reply clears the reminder by itself. Automatic replies (like someone's out-of-office) and bounces don't count.
- If someone answered in a new email instead of replying, it says *"maybe answered"* so you can check.
- It checks when you ask. Nothing runs in the background, and nothing is sent.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `FOLLOW_UPS_TIMEZONE` | No | Your time zone, like `Europe/Lisbon`, so due dates match your days |

## Privacy

Each reminder keeps the email's subject, the people it went to, the dates and your note, saved encrypted on your server. Up to 200 at a time; answered or cancelled ones are deleted.

## If something doesn't work

- **A reminder stays after they replied:** they probably wrote a new email instead of replying. It shows *"maybe answered"*; cancel it if so.
- **Nothing reminds me on its own:** it only checks when you ask. Ask *"Any follow-ups due?"*, or make it part of a morning routine with your AI app.
- **The AI doesn't know the tools:** start a new chat. On a computer, quit and reopen the AI app.

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: no
