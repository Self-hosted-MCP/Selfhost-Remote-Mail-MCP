"""PDF maker: turns text (headings, lists, tables, links) into a PDF and attaches it to a draft."""

import re

NEEDS = ["fpdf"]


def setup(api):
    from selfhost_remote_mail_mcp.library._pdf import PdfError, make_pdf as render

    font = api.setting("PDF_MAKER_FONT")   # optional: a .ttf for scripts Noto Sans lacks (Chinese, Hindi, ...)

    @api.tool(api.WRITE)
    def make_pdf(draft_id: str, file_name: str, text: str, title: str = "") -> str:
        """Make a PDF from text and attach it to a draft. text is markdown: # headings, **bold**, *italic*, lists,
        tables and links. Pictures aren't supported. title (optional) is printed at the top and saved as the
        PDF's title. file_name like 'Proposal-Acme'. Nothing is sent; the draft gets a new ID."""
        name = re.sub(r"[^\w .()-]+", "-", file_name or "").strip(" .-")[:80] or "Document"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        try:
            data, pages = render(text, title.strip(), font)
        except PdfError as exc:
            raise api.ToolError(str(exc))
        new_id = api.edit_draft(draft_id, lambda msg: api.add_file(msg, name, "application/pdf", data, clean=False))
        size = f"{len(data) / 1024:.0f} KB"
        return (f"{name} ({pages} page{'s' if pages != 1 else ''}, {size}) attached. Draft ID is now {new_id}. "
                "Nothing was sent.")
