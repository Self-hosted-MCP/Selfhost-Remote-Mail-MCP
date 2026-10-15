# Your add-ons

> [!NOTE]
> **The add-on pages**
> - [Add-on library](../src/selfhost_remote_mail_mcp/library/README.md): ready-made add-ons to turn on
> - [Add-ons guide](../docs/addons.md): turn one on, write your own, test it
> - **Your add-ons folder** (this page): where your own add-on files go with Docker or a fork

Put add-on files here (for example `decks.py`) when you run the server with Docker, on a hosting company or your own server. They're built into the image, and `MAIL_ADDONS=decks` turns them on.

On your own computer, use `~/.config/selfhost-remote-mail-mcp/addons/` instead.

Ready-made add-ons don't go here: they come with the server, see the [add-on library](../src/selfhost_remote_mail_mcp/library/README.md). How to write your own: [the add-ons guide](../docs/addons.md).
