# phishing_alert

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Checks emails for signs of phishing or a scam, and gives each one a simple **trust level**: high, medium or low, with the main reason in one line.

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

A high trust level means no warning signs were found, not that the email is certainly safe. If an email asks for passwords, payments or something urgent, check with the sender another way.

## Turn it on

On the settings page, open the **Add-ons** tab and press **Turn on**. It needs no setup. Or ask your AI app: it gives you the link. Other ways: [the library page](../README.md#turn-one-on-and-set-it-up).

## What it needs

- Extra packages: none
- Outside services: none. Everything is checked on your server
- Sends email by itself: no
- What it costs your AI app: a short line only on emails that look suspicious
