# calendar_invite

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Attaches a calendar invite (`.ics`) to a draft, so the person you write to can add the meeting to their calendar in one tap. Works with Apple Calendar, Google Calendar, Outlook and most others.

## What you can ask

- *"Draft an email to Sam about coffee on Tuesday at 3pm and attach an invite."*
- *"Add a 45-minute invite for the call on 20 October at 10:00 to that draft, with the video link in the details."*

It adds one tool, `add_invite`. The draft gets the invite as `invite.ics`. Nothing is sent: you send the draft as usual.

## Turn it on

On the settings page, open the **Add-ons** tab and press **Turn on**. It works without any setup; **Set up** lets you add your address as the organizer. Or ask your AI app: it gives you the link. Other ways: [the library page](../README.md#turn-one-on-and-set-it-up).

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `CALENDAR_INVITE_ORGANIZER` | No | Your address, shown as the organizer of the meeting |

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: no

## Privacy

The invite holds only what you ask for: the title, time, length, place and details. It's made on your server.
