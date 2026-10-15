# Things to ask

You talk to your AI app in plain words. It picks the right tool. Here are ways to ask, grouped by job. Change the names and dates to yours.

> [!TIP]
> If the app doesn't use the mail tools by itself, start with *"Use the mail tools:"*.

## Catch up

- *What's new in my inbox today?*
- *Show my unread emails from the last 3 days, newest first.*
- *Anything urgent this week? Give me one line per email.*
- *Which emails am I waiting on a reply for? Check my Sent folder for the last 2 weeks.*
- *Summarise the conversation with Sam about the lease.*

## Find things

- *Find the email with the Berlin flight booking.*
- *Search for invoices from Acme since January that have a PDF attached.*
- *What did the landlord say about the deposit?*
- *Open the attachment in that email and tell me the total.*
- *Who do I email the most? When did I last write to Priya?*

## Write

- *Draft a reply to Sam: Thursday works, 3pm at the office.*
- *Reply to everyone on that thread saying I'll send the files tomorrow.*
- *Forward the Acme invoice to accounts@mycompany.com with a short note.*
- *Write a new email to jo@example.com about rescheduling, friendly and short.*
- *Use my "thank-you" template for Ana, topic: the workshop.*
- *Use my follow-up template for Sam about the proposal.*
- *Draft my invoice reminder for Priya: invoice 2026-14, 450 euros, due 1 October.*
- *Change the draft to Sam: make it shorter and add that I'll bring the contract.*

The AI saves a draft and shows it to you. Nothing is sent yet.

## Attach files

- *(drop a file into the chat)* *Email this to Sam with a short note.*
- *Attach the PDF from Sam's last email to my reply.*
- *Put this list in a CSV and attach it.*
- *Attach a calendar invite for Thursday 3pm.*
- *Which files did I upload?* then *Attach the photo I just uploaded.*
- *Attach the beach photos, but make them smaller.*
- *Send that iPhone photo as a JPG.*
- *Attach ~/Desktop/invoice.pdf* (AI apps on your computer)

## Settings

- *Change my signature to Alex Rivera, Studio Northwind, northwind.studio.*
- *Save this email as a template called follow-up.*
- *Stop removing the location from my photos.* (the AI tells you what it changed)
- *Tell me when there's a new version.*

## Send

- *Send that draft.*
- *Send the draft to Sam tomorrow at 9am my time.*
- *What's scheduled to go out?*
- *Cancel the scheduled email to Sam.*

If you set the sending tools to "Always ask" (recommended), your app asks you to confirm each one.

## Tidy up

- *Archive every newsletter older than a month in my inbox.*
- *Move all emails from the bank to the Finance folder.*
- *Mark everything from noreply addresses as read.*
- *Pin the email from my accountant.*
- *Which of these newsletters have an unsubscribe link? Don't click anything.*

The AI can move emails to Trash, but it can't empty the Trash or delete your emails for good.

## Several mailboxes

If you have more than one (named, say, *Work*, *Personal* and *Archive*):

- *Which mailboxes can you use?*
- *Search all my mailboxes for the Berlin booking.*
- *What's new in Personal today?*
- *Draft this from Work.*
- *Search Archive for the 2024 tax letters.*

## With add-ons

These need the add-on turned on first, in the settings page's **Add-ons** tab ([how](../src/selfhost_remote_mail_mcp/library/README.md#turn-one-on-and-set-it-up)).

**[Calendar](../src/selfhost_remote_mail_mcp/library/caldav/README.md)**

- *What's on my calendar this week?*
- *When am I free on Thursday for an hour?*
- *Reply to Sam with three times I'm free next week.*
- *Put "Dentist" on Friday at 3pm for 45 minutes.*
- *Move the dentist to 4pm.* / *Delete the gym on Saturday.* (it shows you the event and asks first)

**[Calendar invite](../src/selfhost_remote_mail_mcp/library/calendar_invite/README.md)**

- *Reply that Tuesday at 3 works and attach an invite.*
- *Add a 45-minute invite for the call on 20 October at 10:00, with the Zoom link in the details.*

**[PDF maker](../src/selfhost_remote_mail_mcp/library/pdf_maker/README.md)**

- *Write a one-page proposal for Acme with the three options, make it a PDF and attach it.*
- *Put these meeting notes in a PDF and attach it to my email to the team.*

**[Invoices and quotes](../src/selfhost_remote_mail_mcp/library/invoices/README.md)**

- *Make a quote for Acme: logo design 1200, brand guidelines 800. Attach it to my reply.*
- *Turn that into a proforma with 23% VAT.*
- *Which quotes did I send this month?*

**[Phishing alert](../src/selfhost_remote_mail_mcp/library/phishing_alert/README.md)**

- *Is this email safe?*
- *Which of today's emails look risky?*

**[Follow-up reminders](../src/selfhost_remote_mail_mcp/library/follow_ups/README.md)**

- *Remind me if Sam doesn't reply to this in 3 days.*
- *Which of my emails are still waiting for an answer? Draft a friendly nudge for each.*

**[Out of office](../src/selfhost_remote_mail_mcp/library/out_of_office/README.md)** and **[Webhooks](../src/selfhost_remote_mail_mcp/library/webhooks/README.md)** work by themselves. You set them up on the settings page; your AI app can only tell you how they're doing:

- *Is my out of office on?*
- *Are my webhooks working?*

## Asking well

- **Say which email.** "The one from Sam about the lease" works better than "that email".
- **Ask for a plan before a big clean-up.** *"Which emails would you archive? Don't do it yet."* Then say yes.
- **Give the time zone when scheduling** if you travel: *"9am New York time"*.
- **Never paste passwords into the chat.** The server already has what it needs.
