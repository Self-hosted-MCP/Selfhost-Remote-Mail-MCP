# Phishing alert (`phishing_alert`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Checks emails for signs of phishing or a scam, and gives each one a simple **trust level**: high, medium or low, with the main reason in one line.

| | |
|---|---|
| **Tools it adds** | `check_email` |
| **Needs setting up** | No |
| **Works by itself** | Yes, each time your AI app opens an email |
| **Sends email by itself** | No |
| **Extra packages** | None |

## What it's good for

- **The "your account is locked" email.** You don't have to ask. When the AI opens it, a warning comes along, and the AI tells you *"careful, this looks like a scam: the sender isn't really PayPal"*.
- **Fake invoices with attachments.** *"Is this invoice from Sam real?"* It flags a file like `invoice.pdf.exe`, or a reply address that goes to someone else.
- **Sorting a messy inbox.** *"Go through today's mail and tell me which ones look risky."*
- **Before you click.** *"Is the link in this email safe?"* It tells you when a link shows one address and goes to another.
- **Seeing every warning sign.** *"Check this email and show me every warning sign."* The detailed answer lists all of them.

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Turn on** next to **Phishing alert**. It needs no setup.
3. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
4. **Check it works:** open your Spam folder with the AI (*"Check the newest email in Spam for phishing"*). Scam emails there usually get a medium or low trust level.

Other ways to turn it on: [the library page](../README.md#turn-one-on-and-set-it-up).

## How it works

- **Automatically:** whenever your AI app opens an email, it's checked. If the trust is medium or low, one short line goes along with the email, like *"phishing check, trust low: the sender failed your provider's DMARC check"*, so the AI can tell you. A trusted email adds nothing.
- **When you ask:** *"Is this email safe?"* The answer is one line. Ask for details to see every warning sign.

It never moves, deletes or opens anything, and it never visits links.

## What it looks at

- **Your provider's sender checks** (SPF, DKIM, DMARC). Only the checks your own provider added count, never ones the sender could have written.
- **Names that pretend:** a sender called "PayPal" who isn't PayPal, or a name showing a different address.
- **Lookalike domains:** `paypa1.com`, `paypal-secure.com`, or letters from another alphabet that look Latin, and lookalikes of your own domain.
- **Links that hide where they go:** a link showing `paypal.com` that really goes elsewhere, or a bare internet address. Normal newsletter tracking links are recognised and not counted.
- **Risky files:** programs, documents pretending to be programs (`invoice.pdf.exe`), web pages sent as files, macros, password-protected zips.
- **A reply address** that sends your answer to a personal mailbox instead of the company.

> [!WARNING]
> **A high trust level means no warning signs were found, not that the email is certainly safe.** If an email asks for passwords, payments or something urgent, check with the sender another way, like a phone number you already know.

## What you can ask

- *"Is this email safe?"*
- *"Check this email for phishing and show me every warning sign."*
- *"Which of today's emails look risky?"*

## Privacy

Everything is checked on your server. Nothing is looked up online and no link is ever opened. It keeps nothing.

## If something doesn't work

- **No warnings ever show up:** that's normal for a clean inbox. Trusted emails add nothing. Try one from your Spam folder.
- **A newsletter you trust gets "medium":** some senders set up their sender checks badly. The reason line says which check failed, so you can judge it yourself.
- **The AI doesn't know `check_email`:** start a new chat. On a computer, quit and reopen the AI app.

## What it needs

- Extra packages: none
- Outside services: none. Everything is checked on your server
- Sends email by itself: no
- What it costs your AI app: a short line only on emails that look suspicious
