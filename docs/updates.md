# Updates

New versions come out as **official releases** on GitHub (`v0.3.0`, `v0.4.0` …), each with notes on what changed. Everything below only ever installs a release, never unfinished work.

> [!IMPORTANT]
> This server holds your mail passwords, so an update means trusting new code. So everything here is **off until you turn it on**, and the changelog is always one click away. Read what changed, then update.

## Know when there's an update

Add one setting:

```
UPDATE_CHECK=on
```

The server then asks GitHub once a day which release is newest. That request carries no information about you: no login, no address, no usage. When there's something new:

- the **settings page** shows "Update available: vX.Y.Z" with a link to what's new,
- the **`accounts` tool** tells your AI app, so it can mention it to you.

The settings page always shows your version and the latest changes under **About this server → What's new**, whether checks are on or not. The full history is in [CHANGELOG.md](../CHANGELOG.md).

## Update by hand

| How you run it | Update |
|---|---|
| Your computer | `selfhost-remote-mail-mcp update`, then restart your AI app. The server in the background restarts by itself (Mac, Linux) |
| A hosting company | Run the **Update from official releases** action in your fork (see below), or merge the release tag yourself |
| Your own server | `./scripts/update.sh` in your copy of the project |

## Update by itself (optional)

### On your computer

`selfhost-remote-mail-mcp update` installs the newest release with uv and does nothing if you're up to date. To run it every week:

<details>
<summary><b>Mac</b></summary>

Save as `~/Library/LaunchAgents/com.selfhost-remote-mail-mcp.update.plist` (replace `YOU` with your user name):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.selfhost-remote-mail-mcp.update</string>
  <key>ProgramArguments</key>
  <array><string>/Users/YOU/.local/bin/selfhost-remote-mail-mcp</string><string>update</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer></dict>
  <key>StandardOutPath</key><string>/tmp/selfhost-remote-mail-mcp-update.log</string>
</dict>
</plist>
```

Turn it on with `launchctl bootstrap gui/$(id -u)` and that path.

</details>

<details>
<summary><b>Linux</b></summary>

`crontab -e`, then add:

```
0 9 * * 1 $HOME/.local/bin/selfhost-remote-mail-mcp update >> $HOME/.cache/mail-mcp-update.log 2>&1
```

</details>

<details>
<summary><b>Windows</b></summary>

In Task Scheduler, create a weekly task that runs `selfhost-remote-mail-mcp` with the argument `update`.

</details>

`update` restarts the server running in the background by itself (Mac and Linux). Otherwise run `selfhost-remote-mail-mcp service restart`.

### Claude Desktop extension

Claude Desktop doesn't update an extension you downloaded. When there's a new release, [download the file again](claude-desktop-extension.md#update-it) and double-click it. Your settings and mailboxes stay.

### On a hosting company (Railway, Render, Fly.io …)

Deployed with the Railway or Render button? Railway: turn on auto updates in the service's **Settings → Source**. Render: **Manual Deploy → Deploy latest reference**. Both then run the newest official release.

Deployed from a fork on Railway? Your fork contains a ready-made GitHub Action, **Update from official releases**. Once a week it merges the newest release into your fork, and your hosting company rebuilds by itself.

1. In your fork on GitHub, open **Actions** and click **I understand my workflows, go ahead and enable them**.
2. Open **Settings → Secrets and variables → Actions → Variables** and add a variable `AUTO_UPDATE` with the value `on`.
3. To try it now: **Actions → Update from official releases → Run workflow**.

How it stays safe:

- It only runs in forks where you set `AUTO_UPDATE=on`, never in the original project.
- It only merges a published release, never unfinished work.
- Your own changes in the fork are kept. If a release clashes with them, it stops and asks you to update by hand; nothing is half-merged.
- The step it uses to read your code is pinned to an exact version, so a changed third-party tool can't slip in.

### On your own server (Docker Compose)

`scripts/update.sh` moves your copy to the newest release and runs `docker compose up -d --build`. It refuses to run if you changed any of the project's files (your `.env` doesn't count). Using the ready-made image instead ([how](setup-own-server.md#ready-made-image-no-build))? Then updating is `docker compose pull && docker compose up -d`, no script needed. To run the script weekly, add to `crontab -e`:

```
0 4 * * 1 /path/to/Selfhost-Remote-Mail-MCP/scripts/update.sh >> /var/log/mail-mcp-update.log 2>&1
```

Already using **Coolify, Dokploy** or similar? Point it at a release tag instead of `main`, and change the tag when you want to update.

## Going back

- **Computer:** `uv tool install --force git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP@vX.Y.Z` (the version you want, for example `v0.6.0`), then `selfhost-remote-mail-mcp service restart`.
- **Own server:** `git checkout vX.Y.Z && docker compose up -d --build` (the version you want). With the ready-made image: set `image: ghcr.io/s17sh70x2jfl031ag/selfhost-remote-mail-mcp:X.Y.Z`, then `docker compose up -d`.
- **Hosting company:** revert the update commit in your fork; the host rebuilds.

Your settings, mailboxes and logins live in the data folder, which updates never touch.
