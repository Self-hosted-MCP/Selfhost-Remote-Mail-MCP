# Invoices and quotes (`invoices`)

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Makes a numbered **quote**, **proforma invoice** or **invoice** as a PDF, with the totals worked out, and attaches it to a draft.

| | |
|---|---|
| **Tools it adds** | `make_invoice`, `invoices` (the list) |
| **Needs setting up** | Yes: your business name (and your tax number for invoices) |
| **Works by itself in the background** | No |
| **Sends email by itself** | No: you check the draft and send it |
| **Extra packages** | `fpdf2` (in the add-on extras; the Docker image has it) |

> [!IMPORTANT]
> **In some countries a PDF like this isn't a legal invoice.** Portugal and Italy require invoices from certified or e-invoicing software, and Spain, France, Poland and Belgium are moving the same way. There, use this add-on for **quotes** and **proformas**, and make the real invoice in your invoicing software. Elsewhere, check with your accountant what your invoices must show.

## What it's good for

- **Answering "how much?" with a proper quote.** A client asks for a price. *"Make a quote for Acme: logo design 1200, brand guidelines 800, five social templates at 60 each. Attach it to my reply."*
- **Asking for a deposit.** *"Turn that into a proforma with 23% VAT."* The client pays, then you make the real invoice.
- **Invoicing where a PDF invoice is fine.** *"Invoice Acme for the October retainer, 2000, due in 14 days."*
- **Keeping track.** *"Which quotes did I send this month?"* / *"What was the total on PF-2026-0003?"*
- **Foreign clients.** *"Quote in USD, 0% tax, reverse charge."*

## Turn it on

1. **Open your settings page** and type your passphrase: `https://your-address/settings`, or on a computer `http://localhost:8765/settings`.
2. **Open the Add-ons tab** and press **Set up** next to **Invoices and quotes**.
3. **Fill in your details:** at least your business name. For invoices, also your tax number. Add your address, payment details (like your IBAN), currency and usual tax rate if you want them on every document. Press **Save**.
4. **Press Turn on.**
5. **Start a new chat** in your AI app. An AI app on your computer: quit and reopen it first.
6. **Check it works:** ask *"Draft an email to me with a test quote for 1 item at 100."* Open the PDF. The test uses up quote number 1, which is fine.

> [!TIP]
> In Claude, set `make_invoice` to **Always ask** (Settings → Connectors → your mail connector), so no number is used without your OK.

On a computer, install the extra package once (see [the library page](../README.md#turn-one-on-and-set-it-up)). Other ways to turn it on: same page.

## What you can ask

- *"Make a quote for Acme: logo design 1200, brand guidelines 800, five social templates at 60 each. Attach it to the draft."*
- *"Turn that into a proforma with 23% VAT."*
- *"Invoice Maria Silva, Rua Augusta 10 Lisboa, NIF 123456789, for 3 photo sessions at 250."*
- *"Which quotes did I send this month?"*

## What's on it

Your business name, address and tax number. The client's name, address and tax number. The number, date, due date (or "valid until" for a quote) and supply date if you give one. Each line with quantity, unit price and amount. Then net, tax and total, your payment details, and any note.

- **Numbers** go up by one per kind and year (`Q-2026-0001`, `PF-2026-0001`, `INV-2026-0001`), and are never reused. A wrong draft or bad input doesn't use a number. If attaching fails after the PDF is made (a mail server problem), that number is skipped and the AI tells you. To fix an invoice that was sent, make a credit note in your accounting software.
- **Totals** are worked out exactly: each line is rounded to cents, and the tax is worked out once on the total. Unit prices can have up to 4 decimals (like 0.125) and are shown in full.
- **0% tax on an invoice** needs the legal reason, like *"VAT exempt, Art. 53 CIVA"* or *"Reverse charge"*. The AI asks you for it.
- One tax rate per document, up to 100 lines. Labels are in English.

## Settings

Fill these in on the add-on's **Set up** page. The names below are for the settings file, if you use one instead (it wins over the page).

| Setting | Required | What it does |
|---|---|---|
| `INVOICES_SELLER_NAME` | Yes | Your name or business name |
| `INVOICES_SELLER_ADDRESS` | No | Your address. In the settings file, use `\n` between lines |
| `INVOICES_SELLER_TAX_ID` | For invoices | Your tax number (VAT number) |
| `INVOICES_PAYMENT` | No | How to pay, e.g. `Bank transfer\nIBAN PT50 ...`. Shown on proformas and invoices |
| `INVOICES_CURRENCY` | No | Default `EUR` |
| `INVOICES_TAX_RATE` | No | Default tax in percent, e.g. `23`. Default `0` |
| `INVOICES_TAX_LABEL` | No | The tax's name on the PDF. Default `VAT` (e.g. `IVA`, `MwSt`) |
| `INVOICES_DUE_DAYS` | No | Days to pay a proforma or invoice. Default `30` |
| `INVOICES_VALID_DAYS` | No | Days a quote stays valid. Default `30` |
| `INVOICES_QUOTE_PREFIX`, `INVOICES_PROFORMA_PREFIX`, `INVOICES_INVOICE_PREFIX` | No | Default `Q`, `PF`, `INV` |
| `INVOICES_TIMEZONE` | No | Your time zone, e.g. `Europe/Lisbon`, so late-evening documents get the right date. Default: the server's |
| `INVOICES_FONT` | No | Path to a `.ttf` font for names in other scripts, like `PDF_MAKER_FONT` |

## Good to know

- **Only you can change your bank details.** You change them on the setup page. The AI can't, so an email can never make it put someone else's IBAN on your invoice.
- **Check every PDF before you send it.** The AI reads amounts from your words; the totals are exact, but a misheard price isn't.

## Privacy

The PDFs are made on your server. The list of documents (number, date, client name, total) is saved encrypted on your server, the last 500 only.

## If something doesn't work

- **"The user's business details aren't set up yet":** open **Set up** and fill in your business name.
- **"An invoice needs the user's tax number":** add it on the setup page, or make a quote or proforma instead.
- **"write 1.234,50 with a dot for decimals":** say prices like `1234.50`, without a thousands separator.
- **It won't turn on and names `fpdf`:** install the extra package (see [the library page](../README.md#turn-one-on-and-set-it-up)).

## What it needs

- Extra packages: `fpdf2` and `tzdata` (in the add-on extras)
- Outside services: none
- Sends email by itself: no
