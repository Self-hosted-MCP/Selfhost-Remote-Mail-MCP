# Option 3: run it on your own server

Always on, works from your phone, free or cheap. About 15 minutes if you are comfortable with a terminal and a domain.

You need:

- a server with [Docker](https://docs.docker.com/engine/install/): any VPS (Hetzner, DigitalOcean Droplet, Vultr, Akamai Linode, IONOS, OVHcloud, an Oracle Cloud free server), a home server, or a Raspberry Pi 4 or newer. The smallest plan of any of them is plenty,
- a domain or subdomain you control, for example `mail.yourdomain.com`,
- your mail settings ([email-providers.md](email-providers.md)) and a login passphrase (12+ characters). Save it in your password manager (Apple Passwords, Google Password Manager, 1Password ...) with your server's address, so your phone fills it in for you.

## With Docker Compose (includes free HTTPS)

`docker-compose.yml` runs two containers: the mail server, and [Caddy](https://caddyserver.com), which gets and renews the HTTPS certificate by itself.

```
 AI apps  ──https──►  Caddy (ports 80, 443)  ──►  mail server (port 8765, private)  ──►  your mailbox
                      free certificate,                 │
                      renewed by itself                 ▼
                                                 mail-data volume
                                           (logins, send log, signature)
```

1. **Point your domain at the server.** In your DNS settings, add an `A` record for `mail.yourdomain.com` with your server's IP address. Ports 80 and 443 must be open.

2. **Get the code and settings:**

   ```bash
   git clone https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP.git
   cd Selfhost-Remote-Mail-MCP
   cp .env.example .env
   ```

3. **Fill in `.env`:** your mail settings, `LOGIN_PASSPHRASE`, `MAIL_SECRET_KEY` (a long random value, for mailboxes added on the settings page) and `MAIL_DOMAIN=mail.yourdomain.com` (no `https://`). Then lock it: `chmod 600 .env`. More mailboxes: [mailboxes.md](mailboxes.md).

4. **Start it:**

   ```bash
   docker compose up -d --build
   ```

5. **Check it:** `https://mail.yourdomain.com/health` should say `ok`. Logs: `docker compose logs -f mail`.

Your AI app's server address is `https://mail.yourdomain.com/mcp`. See [connect-your-ai.md](connect-your-ai.md).

**Make it safer.** Only ports 80 and 443 need to be open; the mail server itself isn't exposed, only Caddy is. Add `MAIL_READ_ONLY=on` or `SEND_ALLOWED_RECIPIENTS` to `.env` if you want ([safety.md](safety.md#pick-a-safety-level)), then run `docker compose up -d` again.

**Update:** `./scripts/update.sh` moves to the newest official release and restarts. It can run weekly by itself: [updates.md](updates.md).

Everything that must survive restarts (login tokens, send log) is kept in the `mail-data` Docker volume. To add a signature or templates, copy them in:

```bash
docker compose cp signature.html mail:/data/signature.html
```

## More ways to run it

### Already have a reverse proxy, Coolify, Dokploy or similar?

Skip Caddy and run only the `Dockerfile`:

- **Build:** Dockerfile in the repository root.
- **Port:** 8765 (or set `PORT`).
- **Persistent storage:** mount a volume at `/data`.
- **Health check:** `GET /health`.
- **Environment:** your mail settings, `LOGIN_PASSPHRASE` and `PUBLIC_URL=https://your-domain`.

On Coolify, if a password contains `$`, tick **Is Literal** on that variable so it isn't changed.

<details>
<summary><b>nginx instead of Caddy</b></summary>

If your server already runs nginx with a certificate, point a site at the mail server:

```nginx
server {
    listen 443 ssl;
    server_name mail.yourdomain.com;
    # ssl_certificate and ssl_certificate_key as for your other sites

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_buffering off;          # the MCP connection streams its answers
        proxy_read_timeout 3600s;
    }
}
```

Run the mail container with `-p 127.0.0.1:8765:8765` so only nginx can reach it, and set `PUBLIC_URL=https://mail.yourdomain.com`.

</details>

<details>
<summary><b>Without Docker</b></summary>

Install it as in [setup-computer.md](setup-computer.md), run `selfhost-remote-mail-mcp serve` as a systemd service, and put any HTTPS reverse proxy (Caddy, nginx, Traefik) in front of `127.0.0.1:8765`.

</details>

<details>
<summary><b>Running two copies</b></summary>

Two copies of this server must never use the same mailbox with *separate* `/data` folders, or scheduled emails could be sent twice. During a normal redeploy, where old and new containers briefly share the same volume, a lock file makes sure each email goes out once. To stop a second copy from sending scheduled emails, set `SCHEDULED_SEND=off` on it.

</details>

## Stop or remove it

- **Stop:** `docker compose down` (your logins and send log are kept in the volume).
- **Remove everything:** `docker compose down -v` deletes the containers and the stored data. Then delete the app password at your mail provider and remove the connector from your AI apps.

## What we tested

| Step | Tested |
|---|---|
| `docker compose up --build`: image builds, both containers start, Docker health check turns healthy | Yes (macOS with Colima) |
| HTTPS through Caddy, then the full passphrase login and all 15 tools through it | Yes, with Caddy's local certificate for `localhost` |
| Logins kept after a restart (the `mail-data` volume) | Yes |
| Several mailboxes, mailbox ticks on the login page, the settings page (sign-in, rename, refusing a broken mailbox, blocking forms from other sites) and the icon, inside Docker | Yes (version 0.2.0) |
| Send permission per app, 1-hour login keys, the `__Host-` cookie, HTTPS-only pages (HSTS), the About section and changelog, inside Docker | Yes (latest 0.2.0 code) |
| A real public domain with a Let's Encrypt certificate | Not yet: that part is Caddy's standard behaviour |
| The Dockerfile on Coolify | Yes, an earlier private version of this server runs on Coolify every day |
