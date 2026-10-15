# SPDX-License-Identifier: AGPL-3.0-only
"""Shared PDF code for library add-ons (pdf_maker, invoices). Not an add-on itself.

Uses fpdf2 (pure Python) and the bundled Noto Sans fonts (SIL Open Font License, see fonts/OFL.txt), which cover
Latin, Greek, Cyrillic and Vietnamese. For other scripts a user can point to their own .ttf font."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as etree
from pathlib import Path

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

FONTS = Path(__file__).resolve().parent / "fonts"
logging.getLogger("fontTools").setLevel(logging.WARNING)   # fpdf2's font subsetting is chatty otherwise
MAX_TEXT = 100_000
MAX_PAGES = 100
LINK_SCHEMES = ("http://", "https://", "mailto:")
PDF_CODE = re.compile(rb"/(?:JavaScript|JS|Launch|EmbeddedFiles?|RichMedia)\b")   # same check as the server's


class PdfError(ValueError):
    """Something in the text can't be made into a PDF; the message is for the AI."""


class _Safe(Treeprocessor):
    """Pictures become their description (no files or web addresses are ever fetched), and only web and
    mailto links stay links."""
    keep_links = True

    def run(self, root):
        for parent in root.iter():
            for i, el in enumerate(list(parent)):
                if el.tag == "img":
                    span = etree.Element("span")
                    span.text = f"[{el.get('alt') or 'picture'}]"
                    span.tail = el.tail
                    parent.remove(el)
                    parent.insert(i, span)
                elif el.tag == "a":
                    href = (el.get("href") or "").strip()
                    if not self.keep_links or not href.lower().startswith(LINK_SCHEMES):
                        el.tag = "span"
                        el.attrib.clear()


class _SafeExtension(Extension):
    def __init__(self, keep_links: bool):
        super().__init__()
        self.keep_links = keep_links

    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")   # typed HTML stays plain text
        md.inlinePatterns.deregister("html")
        proc = _Safe(md)
        proc.keep_links = self.keep_links
        md.treeprocessors.register(proc, "safe", 0)


def to_html(text: str, keep_links: bool = True) -> str:
    return markdown.markdown(text, extensions=["tables", "sane_lists", _SafeExtension(keep_links)])


def new_pdf(title: str = "", font_path: str = ""):
    """An A4 page set up with the fonts, page numbers in the footer and no author details."""
    from fpdf import FPDF

    class Doc(FPDF):
        def add_page(self, *a, **k):
            if self.page >= MAX_PAGES:
                raise PdfError(f"The PDF would be longer than {MAX_PAGES} pages. Make the text shorter.")
            super().add_page(*a, **k)

        def footer(self):
            self.set_y(-12)
            self.set_font(self.base_font, size=8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, f"{self.page_no()} / {{nb}}", align="C")
            self.set_text_color(0, 0, 0)

    pdf = Doc(format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(True, margin=18)
    if font_path:
        path = Path(font_path).expanduser()
        if not path.is_file() or path.suffix.lower() not in (".ttf", ".otf"):
            raise PdfError(f"The font file {font_path} doesn't exist or isn't a .ttf/.otf font.")
        for style in ("", "B", "I", "BI"):
            pdf.add_font("Body", style, str(path))
    else:
        for style, name in (("", "Regular"), ("B", "Bold"), ("I", "Italic"), ("BI", "BoldItalic")):
            pdf.add_font("Body", style, str(FONTS / f"NotoSans-{name}.ttf"))
    pdf.base_font = "Body"
    pdf.set_font("Body", size=10.5)
    pdf.set_producer("")
    pdf.set_creator("")
    if title:
        pdf.set_title(title)
    pdf.add_page()
    return pdf


def styles() -> dict:
    """Headings in near-black bold instead of fpdf2's dark red; links in a calm blue; code in the body font
    (the built-in code font has no Greek, Cyrillic or accents beyond Latin-1)."""
    from fpdf.fonts import FontFace, TextStyle
    from fpdf.html import DEFAULT_TAG_STYLES
    out = {}
    for tag, style in DEFAULT_TAG_STYLES.items():
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            out[tag] = TextStyle(font_style="B", font_size_pt=min(style.size_pt or 12, 20), color=(22, 20, 42),
                                 t_margin=style.t_margin, l_margin=style.l_margin, b_margin=style.b_margin)
        elif tag == "a":
            out[tag] = FontFace(emphasis="U", color=(69, 54, 210))
        elif tag == "code":
            out[tag] = FontFace(family="Body")
        elif tag == "pre":
            out[tag] = TextStyle(font_family="Body", t_margin=style.t_margin, l_margin=style.l_margin,
                                 b_margin=style.b_margin)
    return out


def finish(pdf) -> bytes:
    return bytes(pdf.output())


TIME_LIMIT = 30   # seconds; some odd markdown takes very long to read, so it runs in its own process


def _render(text: str, title: str, font_path: str) -> tuple[bytes, int]:
    # Try with everything, then without the title in the PDF's details, then without links too: a title or a
    # link that looks like PDF code (e.g. "/JS") would make the server refuse the file.
    for keep_title, keep_links in ((True, True), (False, True), (False, False)):
        pdf = new_pdf(title if keep_title else "", font_path)
        if title:
            pdf.set_font("Body", "B", 18)
            pdf.multi_cell(0, 9, title)
            pdf.ln(3)
            pdf.set_font("Body", size=10.5)
        try:
            pdf.write_html(to_html(text, keep_links), font_family="Body",
                           li_prefix_color=(60, 60, 60), warn_on_tags_not_matching=False, tag_styles=styles())
        except PdfError:
            raise
        except Exception as exc:
            raise PdfError(f"This text can't be laid out as a PDF ({type(exc).__name__}: {exc}). "
                           "Simplify it, for example a smaller table.") from None
        data = finish(pdf)
        if not PDF_CODE.search(data):
            return data, pdf.page_no()
    raise PdfError("The PDF couldn't be made safely from this text. Try rewording it.")


def make_pdf(text: str, title: str = "", font_path: str = "") -> tuple[bytes, int]:
    """A PDF of markdown text (headings, lists, tables, bold, italic, links, code). Returns (bytes, pages).
    It's made by a separate Python process that is stopped after TIME_LIMIT seconds."""
    import base64
    import json
    import subprocess
    import sys
    if len(text) > MAX_TEXT:
        raise PdfError(f"The text is too long for one PDF ({len(text)} characters, {MAX_TEXT} at most).")
    job = json.dumps({"text": text, "title": title, "font": font_path})
    try:
        done = subprocess.run([sys.executable, "-I", "-m", __name__], input=job.encode(), capture_output=True,
                              timeout=TIME_LIMIT)
    except subprocess.TimeoutExpired:
        raise PdfError(f"Making this PDF took longer than {TIME_LIMIT} seconds, so it was stopped. "
                       "Simplify the text (fewer odd symbols like [ or `).") from None
    try:
        result = json.loads(done.stdout)
    except ValueError:
        raise PdfError(f"The PDF couldn't be made (exit code {done.returncode}).") from None
    if "error" in result:
        raise PdfError(result["error"])
    return base64.b64decode(result["pdf"]), result["pages"]


def _main() -> None:
    """python -m ...library._pdf: reads {"text", "title", "font"} on stdin, writes {"pdf", "pages"} or
    {"error"} on stdout."""
    import base64
    import json
    import sys
    job = json.loads(sys.stdin.buffer.read())
    try:
        data, pages = _render(job["text"], job.get("title", ""), job.get("font", ""))
        out = {"pdf": base64.b64encode(data).decode(), "pages": pages}
    except PdfError as exc:
        out = {"error": str(exc)}
    except Exception as exc:
        out = {"error": f"The PDF couldn't be made ({type(exc).__name__})."}
    sys.stdout.write(json.dumps(out))

