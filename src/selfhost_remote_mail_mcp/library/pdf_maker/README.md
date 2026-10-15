# pdf_maker

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Turns text into a clean PDF and attaches it to a draft: a proposal, a summary, meeting notes, a price list. Your AI app writes the text, the server makes the PDF.

## What you can ask

- *"Write a one-page proposal for Acme with the three options we discussed, make it a PDF and attach it to the draft."*
- *"Put these meeting notes in a PDF called Notes-14-October and attach it."*

It adds one tool, `make_pdf`. The text can have headings, **bold**, *italic*, lists, tables and links. Pictures aren't included: they show as their description. Nothing is sent: you send the draft as usual.

## Turn it on

```bash
selfhost-remote-mail-mcp addons enable pdf_maker
```

Or press **Turn on** in the **Add-ons** tab of the settings page, or add `pdf_maker` to `MAIL_ADDONS`. More ways: [the library page](../README.md#turn-one-on).

It needs the Python package `fpdf2`. The Docker image already has it. On a computer, install the add-on extras once:

```bash
uv tool install --force "selfhost-remote-mail-mcp[addons] @ git+https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP"
```

After that, `selfhost-remote-mail-mcp update` keeps the extras.

## Settings

| Setting | Required | What it does |
|---|---|---|
| `PDF_MAKER_FONT` | No | Path to a `.ttf` font, for languages the built-in font doesn't cover (see below) |

## Languages

The built-in font, Noto Sans, covers languages written in Latin, Greek and Cyrillic letters, including Vietnamese. For Chinese, Japanese, Korean, Hindi, Arabic or Hebrew, download a free font that covers them (for example Noto Sans CJK or Noto Sans Devanagari from [Google Fonts](https://fonts.google.com/noto)), put it on the server and set `PDF_MAKER_FONT` to its path. Arabic and Hebrew may still show letters in the wrong order. Emoji show as blank spaces.

## What it needs

- Extra packages: `fpdf2` (in the add-on extras)
- Outside services: none. Links in the text stay links, but nothing is ever downloaded
- Sends email by itself: no

## Limits

Up to 100 000 characters and 100 pages per PDF.

## Privacy

The PDF is made on your server and holds only the text you asked for. No author or app name is saved inside it.
