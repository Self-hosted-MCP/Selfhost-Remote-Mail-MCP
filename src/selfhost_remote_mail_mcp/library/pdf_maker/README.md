# PDF maker (`pdf_maker`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Turns text into a clean PDF and attaches it to a draft: a proposal, a summary, meeting notes, a price list. Your AI app writes the text, the server makes the PDF.

| | |
|---|---|
| **Tools it adds** | `make_pdf` |
| **Needs setting up** | No |
| **Works by itself in the background** | No |
| **Sends email by itself** | No: you send the draft as usual |
| **Extra packages** | `fpdf2` (in the add-on extras; the Docker image has it) |

## What it's good for

- **Proposals.** *"Write a one-page proposal for Acme with the three options we discussed, make it a PDF and attach it to the draft."*
- **Meeting notes.** After a call: *"Put these notes in a PDF called Notes-14-October and attach it to my email to the team."*
- **Price lists and summaries.** *"Make a PDF price list with a table: service, time, price."*
- **Turning a long thread into one document.** *"Summarise this thread in a PDF for Maria, with the decisions and open questions as lists."*

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Turn on** next to **PDF maker**.
3. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
4. **Check it works:** ask *"Draft an email to me and attach a one-page PDF with a short test."*

> [!NOTE]
> **On a computer**, it needs the extra package `fpdf2`. Install it once, then restart the server in the background:
>
> ```bash
> uv tool install --force "selfhost-remote-mail-mcp[addons] @ git+https://github.com/Self-hosted-MCP/Selfhost-Remote-Mail-MCP"
> ```
>
> ```bash
> selfhost-remote-mail-mcp service restart
> ```
>
> `selfhost-remote-mail-mcp update` keeps it after that.

Other ways to turn it on: [the library page](../README.md#turn-one-on-and-set-it-up).

## What you can ask

- *"Write a one-page proposal for Acme with the three options we discussed, make it a PDF and attach it to the draft."*
- *"Put these meeting notes in a PDF called Notes-14-October and attach it."*
- *"Make the PDF title 'Studio rates 2027' and add a table of the three packages."*

The text can have headings, **bold**, *italic*, lists, tables and links. Pictures aren't included: they show as their description.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `PDF_MAKER_FONT` | No | Path to a `.ttf` font, for languages the built-in font doesn't cover (see below) |

## Languages

The built-in font, Noto Sans, covers languages written in Latin, Greek and Cyrillic letters, including Vietnamese. For Chinese, Japanese, Korean, Hindi, Arabic or Hebrew, download a free font that covers them (for example Noto Sans CJK or Noto Sans Devanagari from [Google Fonts](https://fonts.google.com/noto)), put it on the server and set `PDF_MAKER_FONT` to its path. Arabic and Hebrew may still show letters in the wrong order. Emoji show as blank spaces.

## Good to know

- **Limits:** up to 100 000 characters and 100 pages per PDF.
- **Check before you send.** The AI writes the words; open the PDF in the draft and read it.
- **For quotes and invoices** with numbers and totals, use [Invoices and quotes](../invoices/README.md) instead.

## Privacy

The PDF is made on your server and holds only the text you asked for. No author or app name is saved inside it. Links in the text stay links, but nothing is ever downloaded.

## If something doesn't work

- **It won't turn on and names `fpdf`:** install the extra package (above).
- **Letters show as boxes or blanks:** the language needs another font. See [Languages](#languages).
- **The AI doesn't know `make_pdf`:** start a new chat. On a computer, quit and reopen the AI app.

## What it needs

- Extra packages: `fpdf2` (in the add-on extras)
- Outside services: none
- Sends email by itself: no
