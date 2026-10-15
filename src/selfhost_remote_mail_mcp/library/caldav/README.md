# caldav

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Connects your calendar: your AI app can see your events, find free times, and add, change or delete events.

## What you can ask

- *"What's on my calendar this week?"*
- *"When am I free on Thursday for an hour?"*
- *"Put 'Dentist' on Friday at 3pm for 45 minutes."*
- *"Move the dentist to 4pm."*
- *"Delete the gym on Saturday."*
- *"Reply to Sam with three times I'm free next week."*

It adds five tools: `calendar_events`, `calendar_free`, `add_event`, `edit_event` and `delete_event`. Adding an event never invites anyone (calendar servers would email invitations by themselves); to invite people, use [calendar_invite](../calendar_invite/README.md) on an email draft.

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
3. Press **Turn on**, then **Test connection**: it lists the calendars it uses and how many events are coming up.
4. Start a new chat in your AI app.

It needs the Python package `caldav` from the add-on extras; the Docker image has it.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `CALDAV_URL` | Yes | The calendar server's address (above) |
| `CALDAV_USERNAME` | Yes | Your login, usually your email address |
| `CALDAV_PASSWORD` | Yes | An app password, not your normal password |
| `CALDAV_CALENDAR` | No | The calendars your AI app can see and change, names separated by commas. Empty: all of them |
| `CALDAV_TIMEZONE` | No | Your time zone, like `Europe/Lisbon`. Empty: UTC |
| `CALDAV_WORK_HOURS` | No | The hours offered as free, like `09-18` (default) or `09:30-17:30` |

## Good to know

- Free times look at every calendar it uses, on weekdays, inside your working hours. Events marked "free" don't block time.
- With more than one calendar, your AI app asks you which one a new event goes in.
- Your AI app only adds, changes or deletes events when you ask, at most 20 changes a day. New events are within the next year, each marked "Added by your mail assistant".
- **Deleting is always double checked:** your AI app first shows you the event and asks. It deletes only after you say yes.
- Repeating events can be deleted (all their dates), but not changed here. Events with guests can't be changed or deleted here, so no one gets an email you didn't expect. Use your calendar app for those.
- Your calendar's events go to your AI app when it asks, like your emails do.

## What it needs

- Extra packages: `caldav` (in the add-on extras)
- Outside services: your calendar server
- Sends email by itself: no
