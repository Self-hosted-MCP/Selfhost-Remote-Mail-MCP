# follow_ups

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Remembers emails you sent and tells you which ones got no reply in time.

## What you can ask

- *"Remind me if Sam doesn't reply to this in 3 days."*
- *"Which of my emails are still waiting for an answer?"*
- *"Draft a friendly follow-up to the ones that are due."* (the AI writes the drafts; you send them)

It adds three tools: `remind_if_no_reply`, `follow_ups` and `cancel_follow_up`.

- The days count from when you sent the email.
- A real reply clears the reminder by itself. Automatic replies (like someone's out-of-office) and bounces don't count.
- If someone answered in a new email instead of replying, it says *"maybe answered"* so you can check.
- It checks when you ask. Nothing runs in the background, and nothing is sent.

## Turn it on

On the settings page, open the **Add-ons** tab and press **Turn on**. **Set up** lets you add your time zone (optional). Or ask your AI app: it gives you the link. Other ways: [the library page](../README.md#turn-one-on-and-set-it-up).

## Settings

| Setting | Required | What it does |
|---|---|---|
| `FOLLOW_UPS_TIMEZONE` | No | Your time zone, like `Europe/Lisbon`, so due dates match your days |

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: no

## Privacy

Each reminder keeps the email's subject, the people it went to, the dates and your note, saved encrypted on your server. Up to 200 at a time; answered or cancelled ones are deleted.
