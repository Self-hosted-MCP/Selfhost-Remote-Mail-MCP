# Claude Desktop: one click

Use Claude Desktop on a Mac, Windows or Linux computer? Install the server as a Claude Desktop extension: download one file, double-click it and type a passphrase, with no terminal and nothing else to install. About 3 minutes.

**[Download the extension](https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/releases/latest/download/selfhost-remote-mail-mcp.mcpb)** (`selfhost-remote-mail-mcp.mcpb`, from the newest release)

Or paste one line in a terminal. It downloads the file and opens it in Claude Desktop, so you go straight to step 1 below.

Mac:

```bash
curl -fsSL -o /tmp/selfhost-remote-mail-mcp.mcpb https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/releases/latest/download/selfhost-remote-mail-mcp.mcpb && open -a Claude /tmp/selfhost-remote-mail-mcp.mcpb
```

Windows (PowerShell):

```powershell
iwr https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/releases/latest/download/selfhost-remote-mail-mcp.mcpb -OutFile "$env:TEMP\selfhost-remote-mail-mcp.mcpb"; start "$env:TEMP\selfhost-remote-mail-mcp.mcpb"
```

Linux:

```bash
curl -fsSL -o /tmp/selfhost-remote-mail-mcp.mcpb https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP/releases/latest/download/selfhost-remote-mail-mcp.mcpb && xdg-open /tmp/selfhost-remote-mail-mcp.mcpb
```

You get the same server as [option 1](setup-computer.md), with the same settings page, but Claude Desktop installs and starts it for you.

You need:

- Claude Desktop, signed in,
- your mail settings: address and app password ([email-providers.md](email-providers.md#how-to-make-an-app-password)),
- a passphrase you make up, 12 or more characters. It locks your settings page. Save it in your password manager.

## Install it

1. **Double-click the file you downloaded.** Claude Desktop opens it and shows the name, the tools and a red notice that every extension gets (Anthropic hasn't reviewed it: the code is all on this GitHub page). Click **Install**.
2. **Fill in the form:**
   - **Passphrase for your settings page:** the one you made up. If you set this server up with `setup` before, type that same one.
   - **Keep the settings page running when Claude is closed:** leave it on. Then scheduled emails go out and add-ons such as Calendar keep working when Claude Desktop is closed (Mac and Linux). Off: the settings page only runs while Claude Desktop is open.

   Click **Save**.
3. **Turn it on.** Open **Settings → Extensions → Selfhost Remote Mail MCP** and switch it on, if it isn't already.
4. **Add your mailbox.** Open [http://localhost:8765/settings](http://localhost:8765/settings), type your passphrase and use **Add a mailbox**: address, app password and its mode (full, draft only or read only). The login is tested before anything is saved. The page takes a few seconds to start the first time.
5. **Start a new chat** and ask *"What's new in my inbox?"*

If you can't find the settings page, ask Claude *"Where is my mail settings page?"*

## What it does on your computer

- Claude Desktop keeps the extension in its own folder and runs it with [uv](https://docs.astral.sh/uv/), which brings Python and the exact packages this release was tested with.
- Your settings and mailboxes go in `~/.config/selfhost-remote-mail-mcp/`, the same folder `setup` uses. Mail passwords are stored encrypted. The passphrase is only kept as a scrambled version (hash).
- With **Keep running** on: a login item starts the settings page when you log in, the same one `setup` makes (Mac and Linux; on Windows it runs while Claude Desktop is open).

## Other AI apps

The extension connects **Claude Desktop**. For other apps:

- **Claude on the web and phone, ChatGPT:** these need your server online. Use [option 2](setup-hosting.md) (a hosting company) or [option 3](setup-own-server.md) (your own server).
- **Claude Code, Codex and other apps on the same computer:** install the command too ([option 1](setup-computer.md), steps 1 and 2). It finds the mailboxes you already added, so you don't add them again.

## Update it

Claude Desktop doesn't update an extension you downloaded. Turn on update reminders (*"Tell me when there's a new version"*), and when there's a new release, download the file again and double-click it. Your settings and mailboxes stay.

## Remove it

1. **Settings → Extensions → Selfhost Remote Mail MCP → Configure:** switch **Keep the settings page running** off and save. Wait a few seconds: this removes the login item.
2. Click **Uninstall**.
3. To delete your settings and mailboxes too, delete the folder `~/.config/selfhost-remote-mail-mcp/`. Then delete the app password at your mail provider.

## If something doesn't work

- **Claude doesn't know the mail tools:** check the extension is switched on (step 3), then start a new chat.
- **The settings page doesn't open:** wait a few seconds and reload. Still nothing? Switch the extension off and on again.
- **"needs a passphrase first":** open the extension's **Configure**, type a passphrase of 12 or more characters, save, and switch it off and on.
- **Forgot the passphrase:** with the [command installed](setup-computer.md), run `selfhost-remote-mail-mcp set-passphrase`.
- **Claude Desktop's log** for it: `~/Library/Logs/Claude/mcp-server-Selfhost Remote Mail MCP.log` on a Mac. More help: [troubleshooting.md](troubleshooting.md).

## What we tested

| Step | Tested |
|---|---|
| The file passes Anthropic's own checker (`mcpb validate`) | Yes, on every release |
| Install in Claude Desktop, the form, switching it on, the tools loading | Yes (macOS, Claude Desktop with uv already installed) |
| The passphrase saved as a hash, the login item, the settings page at `localhost:8765` | Yes (macOS) |
| Keep running off: the login item removed, the settings page only while Claude Desktop runs | Yes (macOS) |
| Uninstall: the settings page stops, nothing left running | Yes (macOS) |
| A passphrase under 12 characters: nothing starts until it's fixed | Yes (macOS) |
| A computer without uv installed | Not yet: the extension format says Claude Desktop handles it |
| Windows and Linux | Not yet |
