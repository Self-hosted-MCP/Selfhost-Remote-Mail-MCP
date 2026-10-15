# Languages

The web pages (login, settings, upload, upload link) come in **20 languages**, and an AI agent can add more with one command.

Your AI app already talks to you in your own language: the tools answer in English, and the AI explains in yours. So only the pages need translating.

## Which language you see

The pages follow your **browser's language**. If there's no file for it, you see English. To pick one for everyone, add a setting:

```
LANGUAGE=pt-BR
```

The settings page says which language it's using, under **About this server**.

| Language | Code | | Language | Code |
|---|---|---|---|---|
| English | `en` | | Russian | `ru` |
| Spanish | `es` | | Ukrainian | `uk` |
| Portuguese (Brazil) | `pt-BR` | | Japanese | `ja` |
| French | `fr` | | Chinese (Simplified) | `zh-CN` |
| German | `de` | | Chinese (Traditional) | `zh-TW` |
| Italian | `it` | | Korean | `ko` |
| Dutch | `nl` | | Hindi | `hi` |
| Polish | `pl` | | Indonesian | `id` |
| Swedish | `sv` | | Vietnamese | `vi` |
| Turkish | `tr` | | Greek | `el` |

The translations were made with AI and checked by a second AI pass for natural wording, not by native speakers. If something reads oddly, please [fix it](#fix-a-translation).

What stays in English everywhere: setting names (`MAIL_READ_ONLY=on`), file names, commands and the docs, so they always match each other. To read a docs page in your language, ask your AI app: *"Explain this page in Polish."*

## Add a language with your AI agent

Give an AI coding agent (Claude Code, Codex, Cursor and others) this request:

> *"Add Thai to my Selfhost-Remote-Mail-MCP pages: run `selfhost-remote-mail-mcp translate th`, translate every text in natural Thai, then run `selfhost-remote-mail-mcp translate --check th` until it passes."*

What happens:

1. `selfhost-remote-mail-mcp translate th` makes `th.json` in your settings folder's `locales/` (in Docker: `/data/locales/`). It lists every English text of the pages, with an empty space for each translation.
2. The agent fills them in. Each `{placeholder}` and HTML tag (like `<b>`) stays exactly as in English.
3. `selfhost-remote-mail-mcp translate --check th` makes sure nothing is missing or broken.
4. Restart the server. Browsers set to Thai now see the pages in Thai.

Missing texts show in English, so a half-done file still works. When the project gets new texts, run `translate th` again: it keeps what's translated and adds only the new ones.

Right-to-left languages (Arabic, Hebrew, Persian) translate the same way. The page layout itself isn't mirrored yet, so their pages read correctly but are aligned to the left.

## Fix a translation

Your own files in `locales/` win over the ones that come with the server. To fix one text for yourself, run `selfhost-remote-mail-mcp translate de`: it copies the German file into your folder, where you can change any line. Check it with `translate --check de`.

To fix it for everyone, open a pull request that changes `src/selfhost_remote_mail_mcp/locales/<code>.json`, or open an issue with the old and new wording. New languages are welcome the same way.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `LANGUAGE` | empty (follow the browser) | Show the pages in one language, for example `de` or `zh-TW` |
| `MAIL_LOCALES_DIR` | `<config folder>/locales` | Where your own translation files are |
