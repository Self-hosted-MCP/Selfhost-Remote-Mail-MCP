# Calendar invite (`calendar_invite`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Attaches a calendar invite (`.ics`) to a draft, so the person you write to can add the meeting to their calendar in one tap. Works with Apple Calendar, Google Calendar, Outlook and most others.

| | |
|---|---|
| **Tools it adds** | `add_invite` |
| **Needs setting up** | No. Adding your address as the organizer is optional |
| **Works by itself in the background** | No |
| **Sends email by itself** | No: you send the draft as usual |
| **Extra packages** | None |

## What it's good for

- **Confirming a meeting.** Sam asks to meet on Tuesday. *"Reply that Tuesday at 3 works and attach an invite."* Sam opens it and taps "Add to calendar".
- **Sending a video call link.** *"Add a 45-minute invite for the call on 20 October at 10:00 to that draft, with the Zoom link in the details."* The link shows inside the calendar event.
- **Booking clients or interviews.** Draft the email, attach the invite, check both, send.
- **Together with [Calendar](../caldav/README.md):** *"Find my first free hour on Thursday and send Sam an invite for it."* The AI checks your calendar, then drafts the email with the invite.

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Turn on** next to **Calendar invite**. It needs nothing else.
3. *(Optional)* Press **Set up** and add your email address, so calendar apps show you as the organizer.
4. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
5. **Check it works:** ask *"Draft an email to me with an invite for tomorrow at 10."* Open the draft and tap the `invite.ics` file.

Other ways to turn it on: [the library page](../README.md#turn-one-on-and-set-it-up).

## What you can ask

- *"Draft an email to Sam about coffee on Tuesday at 3pm and attach an invite."*
- *"Add a 45-minute invite for the call on 20 October at 10:00 to that draft, with the video link in the details."*
- *"Attach an invite for the studio visit, Friday 2pm, two hours, at Rua Augusta 10."*

The draft gets the invite as `invite.ics`, with the title, time, length, place and details you asked for. The AI asks for your time zone if it isn't sure.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `CALENDAR_INVITE_ORGANIZER` | No | Your address, shown as the organizer of the meeting |

## Good to know

- **It's an invite to add, not to answer.** The person adds the event to their calendar, but you don't get "accepted" or "declined" back. Ask them to reply to the email instead.
- **Length:** 5 minutes to 24 hours.
- **Nothing goes into your own calendar.** To add the meeting to yours too, ask for it with the [Calendar](../caldav/README.md) add-on.

## Privacy

The invite holds only what you ask for: the title, time, length, place and details. It's made on your server.

## If something doesn't work

- **"Add the UTC offset to the time":** the AI needs your time zone. Tell it, like *"I'm in Lisbon"*.
- **The person's calendar shows the wrong hour:** the time zone was wrong when the invite was made. Ask for a new invite with the right one.
- **The AI doesn't know `add_invite`:** start a new chat. On a computer, quit and reopen the AI app.

## What it needs

- Extra packages: none
- Outside services: none
- Sends email by itself: no
