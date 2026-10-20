# Security policy

This server holds the keys to someone's mailbox, so security reports are very welcome.

## Supported versions

Only the newest release gets security fixes. Every update path (the `update` command, the fork action, `scripts/update.sh`) follows published releases, so updating is the fix. See [docs/updates.md](docs/updates.md).

| Version | Security fixes |
|---|---|
| Latest release ([see Releases](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/releases/latest)) | Yes |
| Any older version | No, please update |

## Reporting a problem

Please **don't** open a public issue, discussion or pull request for a security problem.

1. Go to the **Security** tab of this repository and click **[Report a vulnerability](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/security/advisories/new)**. Only the maintainer sees it.
2. Tell me:
   - the version (from the settings page, or `selfhost-remote-mail-mcp version`) and how you run it (computer, Docker, hosting company, own server)
   - what you found and which part of the code it's in, if you know
   - the steps to reproduce it
   - what an attacker could do with it, and what they need first (for example the passphrase, or access to the computer)
3. Remove real passwords, passphrases, tokens, email addresses and email content. Use a test mailbox if you need one.

There's no email contact. Use private reporting.

## What happens next

| When | What |
|---|---|
| Within 3 days | You get a first answer saying the report arrived |
| Within 10 days | I confirm the problem (or explain why it isn't one) and agree on a plan |
| Usually within 30 days | A fixed release is published |
| After the release | The advisory is published, with a CVE when it's useful |

This is a project run in spare time, so a date can slip. If it does, you'll hear why. Please keep the problem private until the fixed release is out, or until 90 days have passed, whichever comes first.

## Credit

If you'd like, you're named in the published advisory and in [CHANGELOG.md](CHANGELOG.md). Tell me the name or GitHub account to use, or say you'd rather stay anonymous. There's no paid bug bounty.

## Testing in good faith

If you follow this policy, I won't take any action against you for your research. Please:

- test only on a server and mailbox that you own, or have permission to test
- never read, change or delete other people's email
- never send real email to other people, or spam, from a test server
- stop and report as soon as you see someone else's data
- don't run denial-of-service tests against someone else's server

## In scope

- Anything that lets someone without the passphrase use the server.
- Any way to send email, or to get around a mailbox's mode (read only or draft only), an app's mailbox choice or send permission, or the limits of `change_setting`, that bypasses the rules in [AGENTS.md](AGENTS.md#rules-that-must-never-break).
- Ways to reach the upload page or the settings page without the passphrase, to reuse an upload link, or to attach a file from outside `ATTACH_FOLDERS`.
- Ways for an add-on's tools to get around the add-on rules (sending email, skipping file checks or mailbox modes).
- Leaks of passwords, tokens or email content (logs, error messages, tool output to the wrong client).
- Ways for email content or an attachment to make the server itself do something (not the AI model, which is covered by [docs/safety.md](docs/safety.md)).
- Problems in how the server stores logins, tokens or the send log in the data folder.

## Out of scope

- An AI model following instructions hidden in an email. That's prompt injection, a known limit of today's AI models. The server's defences are described in [docs/safety.md](docs/safety.md), and improvements to them are welcome as normal issues.
- Weak passphrases chosen by a user, or a settings file shared by its owner.
- Problems that need someone who already controls your computer or server.
- Problems in your email provider, hosting company or AI app. Please report those to them.
- Problems in a dependency that this project doesn't use in a harmful way. Dependabot already watches them; tell me if a known one does affect this project.
- Missing security headers or reports from automated scanners without a real attack that works.

## Keeping your own server safe

- Update when a new release comes out.
- Use a long, random passphrase and an app password from your provider, never your real email password.
- Give each AI app only the mailboxes it needs, and leave sending off unless you want it.
- Check **Connected apps** (and **Sign-ins**, if the device log is on) on the settings page now and then, and remove what you don't recognise.
- More in [docs/safety.md](docs/safety.md) and [docs/privacy.md](docs/privacy.md).
