# invoices

Part of the [add-on library](../README.md), which lists every add-on. How add-ons work: [the add-ons guide](../../../../docs/addons.md).

Makes a numbered **quote**, **proforma invoice** or **invoice** as a PDF, with the totals worked out, and attaches it to a draft.

> [!IMPORTANT]
> **In some countries a PDF like this isn't a legal invoice.** Portugal and Italy require invoices from certified or e-invoicing software, and Spain, France, Poland and Belgium are moving the same way. There, use this add-on for **quotes** and **proformas**, and make the real invoice in your invoicing software. Elsewhere, check with your accountant what your invoices must show.

## What you can ask

- *"Make a quote for Acme: logo design 1200, brand guidelines 800, five social templates at 60 each. Attach it to the draft."*
- *"Turn that into a proforma with 23% VAT."*
- *"Which quotes did I send this month?"*

It adds two tools: `make_invoice` and `invoices` (the list). Nothing is sent: you check the draft and send it.

## What's on it

Your business name, address and tax number. The client's name, address and tax number. The number, date, due date (or "valid until" for a quote) and supply date if you give one. Each line with quantity, unit price and amount. Then net, tax and total, your payment details, and any note.

- **Numbers** go up by one per kind and year (`Q-2026-0001`, `PF-2026-0001`, `INV-2026-0001`), and are never reused. A wrong draft or bad input doesn't use a number. If attaching fails after the PDF is made (a mail server problem), that number is skipped and the AI tells you. To fix an invoice that was sent, make a credit note in your accounting software.
- **Totals** are worked out exactly: each line is rounded to cents, and the tax is worked out once on the total. Unit prices can have up to 4 decimals (like 0.125) and are shown in full.
- **0% tax on an invoice** needs the legal reason, like *"VAT exempt, Art. 53 CIVA"* or *"Reverse charge"*. The AI asks you for it.
- One tax rate per document. Labels are in English.

## Turn it on

On the settings page, open the **Add-ons** tab and press **Turn on**. Then press **Set up** and fill in your details. Or ask your AI app: it gives you the link. Other ways: [the library page](../README.md#turn-one-on-and-set-it-up).

It needs `fpdf2` from the add-on extras (the Docker image has it).

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

## What it needs

- Extra packages: `fpdf2` and `tzdata` (in the add-on extras)
- Outside services: none
- Sends email by itself: no

## Privacy

The PDFs are made on your server. The list of documents (number, date, client name, total) is saved encrypted on your server, the last 500 only.
