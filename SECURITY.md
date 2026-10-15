# Security

This server holds the keys to someone's mailbox, so security reports are very welcome.

## Reporting a problem

Please **don't** open a public issue for a security problem. Use GitHub's [private reporting](https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP/security/advisories/new) instead (the **Security** tab of this repository → **Report a vulnerability**). Include what you found, how to reproduce it and what an attacker could do with it. You'll get an answer as soon as possible.

## In scope

- Anything that lets someone without the passphrase use the server.
- Any way to send email, or to get around a mailbox's mode (read only or draft only), an app's mailbox choice or send permission, or the limits of `change_setting`, that bypasses the rules in [AGENTS.md](AGENTS.md#rules-that-must-never-break).
- Ways to reach the upload page or the settings page without the passphrase, or to attach a file from outside `ATTACH_FOLDERS`.
- Ways for an add-on's tools to get around the add-on rules (sending email, skipping file checks or mailbox modes).
- Leaks of passwords, tokens or email content (logs, error messages, tool output to the wrong client).
- Ways for email content to make the server itself do something (not the AI model, which is covered by [docs/safety.md](docs/safety.md)).

## Out of scope

- An AI model following instructions hidden in an email. That's prompt injection, a known limit of today's AI models. The server's defences are described in [docs/safety.md](docs/safety.md), and improvements to them are welcome as normal issues.
- Weak passphrases chosen by a user.
