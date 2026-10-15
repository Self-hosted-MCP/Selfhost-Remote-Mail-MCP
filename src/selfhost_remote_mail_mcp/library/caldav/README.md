# caldav

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Connects your calendar: your AI app can see your events, find free times and add events.

## What you can ask

- *"What's on my calendar this week?"*
- *"When am I free on Thursday for an hour?"*
- *"Put 'Dentist' on Friday at 3pm for 45 minutes."*
- *"Reply to Sam with three times I'm free next week."*

It adds three tools: `calendar_events`, `calendar_free` and `add_event`. Adding an event never invites anyone (calendar servers would email invitations by themselves); to invite people, use [calendar_invite](../calendar_invite/README.md) on an email draft.

## Which calendars work

Calendars that use **CalDAV** with an app password:

| Calendar | Server address |
|---|---|
| iCloud | `https://caldav.icloud.com/` (app password from appleid.apple.com) |
| Fastmail | `https://caldav.fastmail.com/dav/` |
| Nextcloud | `https://your-server/remote.php/dav/` |
| mailbox.org | `https://dav.mailbox.org` |
| Posteo | `https://posteo.de:8443/` |
| Zoho | The CalDAV address Zoho shows in its calendar settings |

**Not supported:** Google Calendar (it only allows Google's own sign-in), Microsoft 365 and Outlook.com (no CalDAV), Proton (no CalDAV).

## Turn it on

1. On the settings page, open the **Add-ons** tab and press **Set up** next to **Calendar**.
2. Enter the server address, your login and an **app password**, and your time zone. Press **Save**.
3. Press **Turn on**, then start a new chat in your AI app.

It needs the Python package `caldav` from the add-on extras; the Docker image has it.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `CALDAV_URL` | Yes | The calendar server's address (above) |
| `CALDAV_USERNAME` | Yes | Your login, usually your email address |
| `CALDAV_PASSWORD` | Yes | An app password, not your normal password |
| `CALDAV_CALENDAR` | No | The calendar's name. Empty: the first one (check it isn't a holidays calendar) |
| `CALDAV_TIMEZONE` | No | Your time zone, like `Europe/Lisbon`. Empty: UTC |
| `CALDAV_WORK_HOURS` | No | The hours offered as free, like `09-18` (default) or `09:30-17:30` |

## Good to know

- Free times look at one calendar, on weekdays, inside your working hours. Events marked "free" don't block time.
- Your AI app only adds events when you ask, at most 20 a day, within the next year, each marked "Added by your mail assistant".
- Your calendar's events go to your AI app when it asks, like your emails do.

## What it needs

- Extra packages: `caldav` (in the add-on extras)
- Outside services: your calendar server
- Sends email by itself: no
