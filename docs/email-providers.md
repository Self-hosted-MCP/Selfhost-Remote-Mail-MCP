# Email providers

This server logs in to your mailbox the same way any mail app does: **IMAP** to read and **SMTP** to send. This page lists the settings for over 40 providers, and how to get the right password for each.

> [!TIP]
> Add your mailbox on the settings page (or with `selfhost-remote-mail-mcp setup --terminal`). For providers marked **auto** below, it fills in the server names for you. You only type your address and password.

> [!IMPORTANT]
> Most big providers don't accept your normal password from apps. They want an **app password**: a separate password for one app, which you can delete any time without changing your real one. If yours needs one, make it first ([steps below](#how-to-make-an-app-password)).

## What the server needs

You type these on the settings page, under **Add a mailbox**. The server names and ports are under **Server settings** there, and fill in by themselves for the providers marked **auto** below.

| What | Example | On the settings page | In the settings file instead |
|---|---|---|---|
| Your address | `you@gmail.com` | Email address | `MAIL_ADDRESS` |
| Password or app password | `abcd efgh ijkl mnop` | Password or app password | `MAIL_PASSWORD` |
| IMAP server, port 993 | `imap.gmail.com` | IMAP server, IMAP port | `IMAP_HOST`, `IMAP_PORT` |
| SMTP server, port 465 or 587 | `smtp.gmail.com` | SMTP server, SMTP port | `SMTP_HOST`, `SMTP_PORT` |
| Login name, only if it isn't your address | `you` | Login name (and Login name for sending, rarely needed) | `MAIL_USERNAME`, `SMTP_USERNAME` |

**Ports.** IMAP must be 993 (SSL). Every provider on this page offers it. For SMTP, 465 means SSL from the start and 587 means STARTTLS. Both work: use the one your provider lists, or the first one in the tables.

## Big providers

| Provider | IMAP | SMTP | Password | Setup | Notes |
|---|---|---|---|---|---|
| Gmail | `imap.gmail.com` | `smtp.gmail.com` 465 / 587 | App password | auto | Needs 2-Step Verification. Your normal password stopped working for apps in March 2025 |
| Google Workspace | `imap.gmail.com` | `smtp.gmail.com` 465 / 587 | App password | | Your admin must allow IMAP and app passwords |
| iCloud Mail | `imap.mail.me.com` | `smtp.mail.me.com` 587 | App-specific password | auto | Needs two-factor sign-in. [See the iCloud note](#icloud) |
| Yahoo Mail | `imap.mail.yahoo.com` | `smtp.mail.yahoo.com` 465 / 587 | App password | auto | |
| AOL Mail | `imap.aol.com` | `smtp.aol.com` 465 | App password | auto | |
| Fastmail | `imap.fastmail.com` | `smtp.fastmail.com` 465 / 587 | App password | auto | Not on the Basic plan |
| Zoho Mail | `imap.zoho.com` | `smtp.zoho.com` 465 / 587 | Normal, or app password with 2FA | auto | [See the Zoho note](#zoho) |
| Comcast / Xfinity | `imap.comcast.net` | `smtp.comcast.net` 587 / 465 | Normal | auto | Turn on **Third Party Access Security** under Settings → Security |

## Privacy-focused providers

| Provider | IMAP | SMTP | Password | Setup | Notes |
|---|---|---|---|---|---|
| Posteo | `posteo.de` | `posteo.de` 465 / 587 | App password | auto | |
| mailbox.org | `imap.mailbox.org` | `smtp.mailbox.org` 465 / 587 | Normal or app password | auto | |
| Runbox | `mail.runbox.com` | `mail.runbox.com` 465 / 587 | Normal | auto | New accounts can only send after confirming a second address or paying |
| Migadu | `imap.migadu.com` | `smtp.migadu.com` 465 | The mailbox's own password, not your admin login | | For your own domain |
| Purelymail | `imap.purelymail.com` | `smtp.purelymail.com` 465 / 587 | Normal, or app password with 2FA | | For your own domain |
| Infomaniak | `mail.infomaniak.com` | `mail.infomaniak.com` 587 / 465 | A separate mail password made for each device | | |
| Proton Mail | Not supported yet | | | | [See below](#not-supported) |
| Tuta | Not supported | | | | No IMAP at all |

## Europe

| Provider | IMAP | SMTP | Password | Setup | Notes |
|---|---|---|---|---|---|
| GMX (.com) | `imap.gmx.com` | `mail.gmx.com` 587 / 465 | Normal | auto | Turn IMAP on in settings first. It switches itself off after a long time unused |
| GMX (.net, .de) | `imap.gmx.net` | `mail.gmx.net` 587 / 465 | Normal | auto | Turn IMAP on in settings first |
| WEB.DE | `imap.web.de` | `smtp.web.de` 587 / 465 | Normal, or app password with 2FA | auto | Turn IMAP on in settings first |
| mail.com | `imap.mail.com` | `smtp.mail.com` 587 / 465 | Normal | auto | Only with mail.com Premium (paid), and IMAP turned on |
| Zoho Mail (EU) | `imap.zoho.eu` | `smtp.zoho.eu` 465 / 587 | Normal, or app password with 2FA | auto | [See the Zoho note](#zoho) |
| Yandex Mail | `imap.yandex.com` | `smtp.yandex.com` 465 | App password, type "Mail" | auto | Turn on IMAP and "App passwords" in mail settings |
| Mail.ru | `imap.mail.ru` | `smtp.mail.ru` 465 | "Password for external applications" | auto | |
| T-Online | `secureimap.t-online.de` | `securesmtp.t-online.de` 465 | A separate mail password from the Telekom customer centre | | Settings from secondary sources: check them in your account |
| Orange.fr | `imap.orange.fr` | `smtp.orange.fr` 465 | A generated mail password (Espace client → Connexion et sécurité) | | |
| Libero (Italy) | `imapmail.libero.it` | `smtp.libero.it` 465 | Normal, or "Password Sicura" | | Settings from secondary sources: check them in your account |

## Asia

| Provider | IMAP | SMTP | Password | Setup | Notes |
|---|---|---|---|---|---|
| QQ Mail | `imap.qq.com` | `smtp.qq.com` 465 | Authorization code (授权码) | | Turn on the IMAP/SMTP service in settings |
| NetEase 163 | `imap.163.com` | `smtp.163.com` 465 | Authorization code (授权码) | | Turn on IMAP/SMTP in settings |
| Naver Mail | `imap.naver.com` | `smtp.naver.com` 465 or 587 | App password with 2-step verification | | Turn on IMAP/SMTP in settings. Sources differ on the SMTP port |
| Zoho Mail (India) | probably `imap.zoho.in` | probably `smtp.zoho.in` | Normal, or app password with 2FA | | Copy the exact names from your Zoho settings |

QQ, 163 and Naver settings come from secondary sources, because the official pages couldn't be checked. Copy the exact values from your account's settings if they differ.

## Email on your own domain (web hosts)

If your address is on your own domain (like `you@yourstudio.com`), the settings come from whoever hosts that email.

| Host | IMAP | SMTP | Password | Notes |
|---|---|---|---|---|
| Namecheap Private Email | `mail.privateemail.com` | `mail.privateemail.com` 465 / 587 | Mailbox password or app password | |
| Hostinger | `imap.hostinger.com` | `smtp.hostinger.com` 465 / 587 | Mailbox password, or app password with 2FA | |
| IONOS (US) | `imap.ionos.com` | `smtp.ionos.com` 465 / 587 | Mailbox password | Hosted Exchange uses other servers |
| IONOS (Germany) | `imap.ionos.de` | `smtp.ionos.de` 465 / 587 | Mailbox password | |
| GoDaddy Workspace Email | `imap.secureserver.net` | `smtpout.secureserver.net` 465 / 587 | Mailbox password | Being retired. If GoDaddy moved you to Microsoft 365, it won't work ([see below](#not-supported)) |
| DreamHost | `imap.dreamhost.com` | `smtp.dreamhost.com` 587 | Mailbox password | |
| OVHcloud (Europe) | `ssl0.ovh.net` | `ssl0.ovh.net` 465 / 587 | Mailbox password | Americas and Asia-Pacific: `imap.mail.ovh.ca` |
| Rackspace Email | `secure.emailsrvr.com` | `secure.emailsrvr.com` 465 | Webmail password | |
| cPanel, Plesk and most shared hosting | usually `mail.yourdomain.com` | usually `mail.yourdomain.com` 465 | Mailbox password | Your host's "email settings" or "mail client setup" page has the exact names |

Not on the list? Search for "*your provider* IMAP settings" and look for the provider's own help page.

## Not supported

| Provider | Why |
|---|---|
| **Outlook.com, Hotmail, Live, MSN** | Since 16 September 2024 Microsoft only allows its own sign-in (OAuth) for these. Passwords and app passwords no longer work. |
| **Microsoft 365** (work and school) | Microsoft turned off password logins for IMAP in 2022. Also applies to GoDaddy and other hosts that moved customers to Microsoft 365. |
| **Proton Mail** | Proton needs its Bridge app on your computer (paid plans only). Bridge uses a self-signed certificate, which this server doesn't accept yet. |
| **Tuta** | No IMAP or SMTP at all, by design. |
| **HEY** | Only HEY's own apps can open the mailbox. |
| **Amazon WorkMail** | Takes no new customers and shuts down on 31 March 2027. |

Microsoft and Proton support are on the [roadmap](roadmap.md).

## How to make an app password

<details>
<summary><b>Gmail and Google Workspace</b></summary>

1. Turn on [2-Step Verification](https://myaccount.google.com/signinoptions/twosv). It's required.
2. Open [App passwords](https://myaccount.google.com/apppasswords), type a name like "Mail MCP" and click **Create**.
3. Copy the 16-letter password. Spaces don't matter.
4. Google Workspace: if you don't see App passwords, your admin has to allow them and turn IMAP on.

</details>

<details>
<summary><b>iCloud</b></summary>

1. Turn on two-factor authentication for your Apple Account, if it isn't already.
2. Go to [account.apple.com](https://account.apple.com) → **Sign-In and Security → App-Specific Passwords**.
3. Click **+**, name it "Mail MCP" and copy the password.

</details>

<details>
<summary><b>Yahoo and AOL</b></summary>

1. Open **Account Info → Account Security**.
2. Click **Generate app password** (or "Manage app passwords").
3. Name it "Mail MCP" and copy the password.

</details>

<details>
<summary><b>Fastmail</b></summary>

1. Go to **Settings → Privacy & Security → Manage app passwords**.
2. Click **New app password**, choose access to **IMAP and SMTP**, and copy it.

</details>

<details>
<summary><b>Zoho</b></summary>

1. First turn IMAP on: **Settings → Mail Accounts → IMAP Access**.
2. If two-factor sign-in is on: **My Account → Security → App Passwords**, generate one and copy it.

</details>

<details>
<summary><b>Yandex</b></summary>

1. In mail settings, turn on IMAP and "App passwords and OAuth tokens".
2. In your Yandex ID, create an app password of type **Mail** and copy it.

</details>

<details>
<summary><b>GMX, WEB.DE and mail.com</b></summary>

1. Open **Settings → POP3 & IMAP** and turn on access.
2. Use your normal password. With two-factor sign-in on, WEB.DE wants an app-specific password from its security settings.

</details>

<details>
<summary><b>QQ Mail and NetEase 163</b></summary>

1. In mail settings, find the IMAP/SMTP service and turn it on.
2. The page gives you an **authorization code** (授权码). Use it as the password.

</details>

## Provider notes

### iCloud

Apple's IMAP login name is often just the part before the @ (`you`, not `you@icloud.com`), while sending needs the full address. Try your full address first. If the login fails, open **Server settings** when adding the mailbox and set **Login name** to `you` and **Login name for sending** to `you@icloud.com`. In the settings file, that's:

```
MAIL_USERNAME=you
SMTP_USERNAME=you@icloud.com
```

`setup --terminal` sets this up for you when you give it the short login name.

### Zoho

Zoho uses different servers depending on your account:

- **Free or personal accounts:** `imap.zoho.com` and `smtp.zoho.com`.
- **Paid organisation accounts:** `imappro.zoho.com` and `smtppro.zoho.com`.
- **Accounts in Europe or India:** the same names ending in `.eu` or `.in`.

New free accounts may not get IMAP at all. The exact names for your account are in **Settings → Mail Accounts → IMAP Access**.

### Gmail sends twice into Sent?

Gmail saves a copy of everything you send by itself, and this server saves one too. You may see two copies in Sent. Nothing was sent twice.

## Sources

All settings were checked against each provider's own help pages in October 2026, except where a row says "secondary sources". Providers change their settings now and then. If something here is out of date, please open an issue with a link to the provider's page.
