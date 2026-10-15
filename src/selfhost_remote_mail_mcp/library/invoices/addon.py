"""Invoices and quotes: makes a numbered quote, proforma or invoice PDF with totals and attaches it to a draft."""

import datetime as dt
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing_extensions import TypedDict   # pydantic needs this one on Python 3.11

from selfhost_remote_mail_mcp.i18n import N_

NEEDS = ["fpdf"]
SETTINGS = [   # shown on the add-on's setup page (the server settings can set them too: INVOICES_<key>)
    {"key": "SELLER_NAME", "label": N_("Your name or business name"), "required": True},
    {"key": "SELLER_ADDRESS", "label": N_("Your address"), "lines": 3},
    {"key": "SELLER_TAX_ID", "label": N_("Your tax number (VAT number)"),
     "help": N_("Needed on invoices. Quotes and proformas work without it.")},
    {"key": "PAYMENT", "label": N_("How to pay you"), "lines": 3,
     "help": N_("For example: Bank transfer, IBAN PT50 ... Shown on proformas and invoices.")},
    {"key": "TAX_RATE", "half": True, "label": N_("Usual tax rate, in percent"), "help": N_("For example 23. Empty means 0.")},
    {"key": "TAX_LABEL", "half": True, "label": N_("Name of the tax"), "help": N_("For example VAT, IVA or MwSt. Empty means VAT.")},
    {"key": "CURRENCY", "half": True, "label": N_("Currency"), "help": N_("A three-letter code, for example EUR or USD. Empty means EUR.")},
    {"key": "TIMEZONE", "half": True, "label": N_("Your time zone"), "help": N_("For example Europe/Lisbon, so documents get your date.")},
    {"key": "DUE_DAYS", "half": True, "label": N_("Days to pay"), "help": N_("Empty means 30.")},
    {"key": "VALID_DAYS", "half": True, "label": N_("Days a quote stays valid"), "help": N_("Empty means 30.")},
]

KINDS = {"quote": ("Quote", "QUOTE_PREFIX", "Q"), "proforma": ("Proforma invoice", "PROFORMA_PREFIX", "PF"),
         "invoice": ("Invoice", "INVOICE_PREFIX", "INV")}
CENT = Decimal("0.01")
KEEP = 500   # issued documents remembered for the list tool


class Item(TypedDict):
    description: str
    quantity: str | float
    unit_price: str | float


def money(value, what: str, api, allow_zero: bool = True) -> Decimal:
    """A number from the AI: '12.50', 12.5 or '1000'. Commas as decimal marks and odd values are refused."""
    text = str(value).strip()
    if "," in text:
        raise api.ToolError(f"{what}: write {text!r} with a dot for decimals and no thousands separator, e.g. 1234.50.")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise api.ToolError(f"{what}: {text!r} isn't a number.")
    if not number.is_finite() or number < 0 or number > Decimal("1000000000") or (not allow_zero and number == 0):
        raise api.ToolError(f"{what}: {text!r} must be a positive number below 1 000 000 000.")
    return number


def setup(api):
    from selfhost_remote_mail_mcp.library._pdf import PdfError, finish, new_pdf

    s = lambda key, default="": api.setting(f"INVOICES_{key}", default)

    def today() -> dt.date:
        zone = s("TIMEZONE")
        if not zone:
            return dt.date.today()
        from zoneinfo import ZoneInfo
        try:
            return dt.datetime.now(ZoneInfo(zone)).date()
        except Exception:
            raise api.ToolError(f"INVOICES_TIMEZONE={zone} isn't a time zone name like Europe/Lisbon.")

    def fmt(value: Decimal, currency: str) -> str:
        """Money with 2 decimals, or up to 4 for a unit price like 0.125, so lines always add up."""
        places = max(2, min(4, -value.normalize().as_tuple().exponent))
        return f"{value:,.{places}f} {currency}".replace(",", " ")

    def render(doc: dict) -> bytes:
        pdf = new_pdf(f"{doc['label']} {doc['number']}", s("FONT"))
        W = pdf.epw
        pdf.set_font("Body", "B", 20)
        pdf.cell(W * 0.6, 10, doc["label"])
        pdf.set_font("Body", size=10)
        pdf.multi_cell(W * 0.4, 5, f"No. {doc['number']}\nDate: {doc['date']}" +
                       (f"\nSupply date: {doc['supply_date']}" if doc["supply_date"] else "") +
                       (f"\nDue: {doc['due']}" if doc["due"] else "") +
                       (f"\nValid until: {doc['valid']}" if doc["valid"] else ""), align="R")
        pdf.ln(6)
        top = pdf.get_y()
        bottom = top + 30
        for i, (head, lines) in enumerate((("From", doc["seller"]), ("To", doc["client"]))):
            pdf.set_xy(pdf.l_margin + i * W / 2, top)
            pdf.set_font("Body", "B", 9)
            pdf.cell(W / 2, 5, head)
            pdf.set_xy(pdf.l_margin + i * W / 2, top + 5)
            pdf.set_font("Body", size=10)
            pdf.multi_cell(W / 2 - 4, 5, "\n".join(x for x in lines if x))
            bottom = max(bottom, pdf.get_y())
        pdf.set_y(bottom + 4)
        pdf.set_font("Body", size=10)
        with pdf.table(col_widths=(50, 12, 19, 19), text_align=("LEFT", "RIGHT", "RIGHT", "RIGHT"),
                       line_height=6, borders_layout="HORIZONTAL_LINES") as table:
            row = table.row()
            for h in ("Description", "Qty", "Unit price", "Amount"):
                row.cell(h)
            for item in doc["items"]:
                row = table.row()
                row.cell(item["description"])
                row.cell(f"{item['quantity'].normalize():f}")
                row.cell(fmt(item["unit_price"], doc["currency"]))
                row.cell(fmt(item["amount"], doc["currency"]))
        pdf.ln(4)
        if pdf.will_page_break(25):   # net, tax and total stay on one page
            pdf.add_page()
        rate = f"{doc['rate'].normalize():f}"
        for label, value, bold in (("Net", doc["net"], False), (f"{doc['tax_label']} {rate}%", doc["tax"], False),
                                   ("Total", doc["total"], True)):
            pdf.set_font("Body", "B" if bold else "", 12 if bold else 10)
            pdf.cell(W * 0.75, 7, label, align="R")
            pdf.cell(W * 0.25, 7, fmt(value, doc["currency"]), align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Body", size=9.5)
        pdf.ln(4)
        for text in doc["notes"]:
            if text:
                pdf.multi_cell(W, 5, text)
                pdf.ln(2)
        return finish(pdf)

    @api.tool(api.WRITE)
    def make_invoice(draft_id: str, kind: str, client_name: str, items: list[Item], client_address: str = "",
                     client_tax_id: str = "", tax_rate: str = "", tax_note: str = "", currency: str = "",
                     supply_date: str = "", notes: str = "") -> str:
        """Make a numbered quote, proforma or invoice as a PDF and attach it to a draft. Nothing is sent.

        kind: "quote" (an offer), "proforma" (a payment request before the real invoice) or "invoice".
        items: [{"description": "Logo design", "quantity": "1", "unit_price": "400.00"}], prices before tax, dot
        for decimals. tax_rate: percent, e.g. "23" (default: the user's setting). tax_note: required on an
        invoice with 0% tax, the legal reason (e.g. "VAT exempt, Art. 53 CIVA" or "Reverse charge").
        Important: in Portugal and Italy (and soon Spain, France, Poland, Belgium) a legal invoice must come from
        certified or e-invoicing software. There, use quote or proforma, and tell the user this PDF isn't a
        legal invoice. Numbers are never reused: to fix an invoice, the user issues a credit note in their
        accounting software."""
        kind = kind.strip().lower()
        if kind not in KINDS:
            raise api.ToolError('kind must be "quote", "proforma" or "invoice".')
        label, prefix_key, prefix_default = KINDS[kind]
        seller = s("SELLER_NAME")
        where = (f"on the add-on's setup page: {api.setup_link()} (give the user this link)" if api.setup_link()
                 else "in the settings file (INVOICES_SELLER_NAME and the others, see the add-on's page)")
        if not seller:
            raise api.ToolError(f"The user's business details aren't set up yet. They add them {where}.")
        if kind == "invoice" and not s("SELLER_TAX_ID"):
            raise api.ToolError(f"An invoice needs the user's tax number. They add it {where}.")
        if not client_name.strip():
            raise api.ToolError("client_name is needed.")
        if not 1 <= len(items) <= 100:
            raise api.ToolError("items needs 1 to 100 lines.")
        rate = money(tax_rate or s("TAX_RATE", "0"), "tax_rate", api)
        if rate > 100:
            raise api.ToolError("tax_rate is a percent between 0 and 100, e.g. 23.")
        if kind == "invoice" and rate == 0 and not tax_note.strip():
            raise api.ToolError("An invoice with 0% tax needs tax_note: the legal reason (ask the user), e.g. "
                                "'VAT exempt under Art. 53 CIVA' or 'Reverse charge'.")
        currency = (currency or s("CURRENCY", "EUR")).strip().upper()[:3]
        lines = []
        for n, item in enumerate(items, 1):
            desc = str(item.get("description", "")).strip()
            if not desc:
                raise api.ToolError(f"Line {n} needs a description.")
            qty = money(item.get("quantity", "1"), f"line {n} quantity", api, allow_zero=False)
            price = money(item.get("unit_price", ""), f"line {n} unit_price", api)
            if -price.normalize().as_tuple().exponent > 4 or -qty.normalize().as_tuple().exponent > 4:
                raise api.ToolError(f"Line {n}: use at most 4 decimals in quantity and unit_price.")
            lines.append({"description": desc[:300], "quantity": qty, "unit_price": price,
                          "amount": (qty * price).quantize(CENT, ROUND_HALF_UP)})
        net = sum((x["amount"] for x in lines), Decimal(0))
        tax = (net * rate / 100).quantize(CENT, ROUND_HALF_UP)   # once, on the total
        if supply_date:
            try:
                dt.date.fromisoformat(supply_date)
            except ValueError:
                raise api.ToolError("supply_date: use YYYY-MM-DD.")
        issued = today()
        days = lambda key: int(money(s(key, "30"), key, api))
        api.message(draft_id)   # a wrong draft ID fails here, before a number is used
        with api.store() as data:   # holds the lock, so two calls never get the same number
            year_key = f"{kind}-{issued.year}"
            count = data.setdefault("counters", {}).get(year_key, 0) + 1
            number = f"{s(prefix_key, prefix_default)}-{issued.year}-{count:04d}"
            doc = {"label": label, "number": number, "date": issued.isoformat(), "supply_date": supply_date,
                   "due": (issued + dt.timedelta(days=days("DUE_DAYS"))).isoformat() if kind != "quote" else "",
                   "valid": (issued + dt.timedelta(days=days("VALID_DAYS"))).isoformat() if kind == "quote" else "",
                   "seller": [seller, s("SELLER_ADDRESS").replace("\\n", "\n"),
                              f"Tax no. {s('SELLER_TAX_ID')}" if s("SELLER_TAX_ID") else ""],
                   "client": [client_name.strip()[:200], client_address.replace("\\n", "\n")[:400],
                              f"Tax no. {client_tax_id[:40]}" if client_tax_id else ""],
                   "items": lines, "rate": rate, "net": net, "tax": tax, "total": net + tax,
                   "currency": currency, "tax_label": s("TAX_LABEL", "VAT"),
                   "notes": [tax_note.strip()[:300], notes.strip()[:2000],
                             s("PAYMENT").replace("\\n", "\n") if kind != "quote" else "",
                             "This is a quote, not an invoice." if kind == "quote" else "",
                             "This is a proforma invoice, not a tax invoice." if kind == "proforma" else ""]}
            try:
                pdf = render(doc)
            except PdfError as exc:
                raise api.ToolError(str(exc))
            data["counters"][year_key] = count   # saved when this block ends: the number is used from now on
            log = data.setdefault("issued", [])
            log.append({"number": number, "kind": kind, "date": doc["date"], "client": doc["client"][0],
                        "total": f"{doc['total']:.2f} {currency}"})
            del log[:-KEEP]
        file_name = f"{label.split()[0]}-{number}.pdf"
        try:
            new_id = api.edit_draft(draft_id, lambda msg: api.add_file(msg, file_name, "application/pdf", pdf,
                                                                        clean=False))
        except Exception as exc:
            raise api.ToolError(f"{label} {number} was made but couldn't be attached ({exc}). The number is now "
                                "used: make it again to get the next one, and tell the user this number was "
                                "skipped.") from None
        return (f"{label} {number} for {client_name.strip()}: total {fmt(doc['total'], currency)} "
                f"({fmt(net, currency)} + {fmt(tax, currency)} {doc['tax_label']}). Attached as {file_name}. Draft "
                f"ID is now {new_id}. Nothing was sent. Ask the user to check it before sending.")

    @api.tool(api.READ)
    def invoices(kind: str = "", limit: int = 20) -> str:
        """List the quotes, proformas and invoices made so far, newest first (number, date, client, total).
        kind filters: "quote", "proforma" or "invoice". Changes nothing."""
        with api.store() as data:
            rows = [r for r in reversed(data.get("issued", [])) if not kind or r["kind"] == kind.strip().lower()]
        rows = rows[:max(1, min(limit, 200))]
        if not rows:
            return "None made yet."
        return "\n".join(f"{r['number']} · {r['date']} · {r['client']} · {r['total']}" for r in rows)
