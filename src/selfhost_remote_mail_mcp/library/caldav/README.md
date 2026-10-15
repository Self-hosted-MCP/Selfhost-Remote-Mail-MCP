# Calendar (`caldav`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Connects your calendar: your AI app can see your events, find free times, and add, change or delete events.

| | |
|---|---|
| **Tools it adds** | `calendar_events`, `calendar_free`, `add_event`, `edit_event`, `delete_event` |
| **Needs setting up** | Yes: your calendar's address, login and app password |
| **Works by itself in the background** | No, only when you ask |
| **Sends email by itself** | No, and it never invites anyone |
| **Extra packages** | `caldav` (in the add-on extras; the Docker image has it) |

## What it's good for

- **Plan your week.** *"What's on my calendar this week?"* One line per event, from every calendar you use.
- **Answer "when are you free?" in one go.** *"Reply to Sam with three times I'm free next week for an hour."* The AI finds free times in your working hours and writes the reply as a draft.
- **Book things as you talk.** *"Put 'Dentist' on Friday at 3pm for 45 minutes."*
- **Move things when plans change.** *"Move the dentist to 4pm."*
- **Clear your calendar.** *"Delete the gym on Saturday."* The AI shows you the event and asks before it deletes anything.
- **Keep work and home apart.** With more than one calendar, the AI asks which one a new event goes in.

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

> [!NOTE]
> **Not supported:** Google Calendar (it only allows Google's own sign-in, no app passwords), Microsoft 365 and Outlook.com (no CalDAV), Proton (no CalDAV).

## Turn it on

1. **Make an app password** at your calendar provider (for iCloud: appleid.apple.com → Sign-In and Security → App-Specific Passwords). Not your normal password.
2. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
3. **Open the Add-ons tab** and press **Set up** next to **Calendar**.
4. **Fill in** the server address (table above), your login (usually your email address), the app password and your time zone. Press **Save**.
5. **Press Turn on**, then **Test connection**. It lists the calendars it uses and how many events are coming up.
6. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
7. **Check it works:** ask *"What's on my calendar tomorrow?"*

> [!TIP]
> In Claude, set `add_event`, `edit_event` and `delete_event` to **Always ask** (Settings → Connectors → your mail connector). Then nothing changes in your calendar without your tap.

On a computer, install the extra package once (see [the library page](../README.md#turn-one-on-and-set-it-up)). Other ways to turn it on: same page.

## What you can ask

- *"What's on my calendar this week?"*
- *"Am I free Thursday afternoon?"*
- *"When am I free on Thursday for an hour?"*
- *"Put 'Call with Sam' on Monday at 10 for 30 minutes, in my Work calendar."*
- *"Move the dentist to 4pm."* / *"Make lunch 90 minutes."* / *"Add the Zoom link to Friday's call."*
- *"Delete the gym on Saturday."*
- *"Reply to Sam with three times I'm free next week."*
- *"Draft an invite to Sam for my first free hour on Tuesday."* (with [Calendar invite](../calendar_invite/README.md) turned on too)

## How the five tools work

| Tool | What it does |
|---|---|
| `calendar_events` | Your events for up to 31 days, repeating ones included. Each line ends with the event's ID, which the other tools use |
| `calendar_free` | Free times on weekdays inside your working hours, for up to 14 days. Every calendar you use counts as busy, except events marked "free" |
| `add_event` | Adds an event, within the next year. With several calendars and none named, the AI asks you which one |
| `edit_event` | Changes the title, time, length, place or notes. Only what you ask for changes; a new start time keeps the same length |
| `delete_event` | Shows you the event first and asks. It deletes only after you say yes. A repeating event is deleted with all its dates |

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

- **No one is ever invited or emailed.** Calendar servers email guests by themselves, so events added here have no guests. To invite people, use [Calendar invite](../calendar_invite/README.md) on an email draft.
- **Events with guests can't be changed or deleted here,** so no one gets an email you didn't expect. **Repeating events** can be deleted (all their dates) but not changed here. Use your calendar app for those.
- **At most 20 changes a day** (adds, changes and deletes together). New events are within the next year and marked "Added by your mail assistant".
- **Holiday or shared calendars** that are read-only may refuse changes. Leave them out with **Calendars to use** if you don't want them read either.

## Privacy

Your events go to your AI app when it asks, like your emails do. The add-on keeps nothing except a count of today's changes. The app password is saved encrypted on your server.

## If something doesn't work

- **"The calendar login failed":** use an app password, not your normal one, and check the login name. For iCloud, the login is your Apple ID email.
- **"There's no calendar called …":** the names in **Calendars to use** must match your calendar app exactly. Empty means all.
- **Times are off by an hour or more:** set **Your time zone**. Empty means UTC.
- **The AI doesn't know the calendar tools:** start a new chat. On a computer, quit and reopen the AI app.

## What it needs

- Extra packages: `caldav` (in the add-on extras)
- Outside services: your calendar server
- Sends email by itself: no
