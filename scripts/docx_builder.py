"""Rendering helpers that build a Word document in the format of the
departmental project-report template.

The template (``A PROJECT REPORT.docx``) is used as the base file so that its
page size, margins, university header banner and page-number footer are kept
exactly. Only the body content is replaced.

Template conventions reproduced here:
    chapter heading   centred, Arial, 28 pt
    section heading   Calibri, 18 pt, bold
    body text         Calibri, 16 pt, justified
    lists             Calibri, 16 pt, justified, List Paragraph style
"""

from __future__ import annotations

import re
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Calibri"
HEAD_FONT = "Arial"
BODY_SIZE = Pt(16)
H1_SIZE = Pt(28)
H2_SIZE = Pt(18)
H3_SIZE = Pt(16)
CODE_FONT = "Consolas"
CODE_SIZE = Pt(9)

# Usable text width of the template page (A4, 1 inch margins).
TEXT_WIDTH_IN = 6.27


class ReportBuilder:
    """Accumulates content into a copy of the departmental template."""

    def __init__(self, template: str | Path):
        self.doc = docx.Document(str(template))
        self._clear_body()
        self.figures: list[tuple[str, str]] = []   # (number, caption)
        self.tables: list[tuple[str, str]] = []    # (number, caption)
        self._bookmark_id = 1000

    # ------------------------------------------------------------------ #
    # setup
    # ------------------------------------------------------------------ #
    def _clear_body(self) -> None:
        """Remove every paragraph and table from the body, keeping sectPr."""
        body = self.doc.element.body
        for child in list(body):
            if child.tag == qn("w:sectPr"):
                continue
            body.remove(child)

    # ------------------------------------------------------------------ #
    # bookmarks and page-reference fields
    #
    # Word, not this script, computes the page numbers. Each heading and
    # caption carries a bookmark; each Contents / List row carries a PAGEREF
    # field pointing at it. ``enable_field_update`` then asks Word to resolve
    # every field when the document is opened.
    # ------------------------------------------------------------------ #
    @staticmethod
    def slug(prefix: str, text: str) -> str:
        """A legal, stable Word bookmark name (letters, digits, underscore)."""
        clean = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_")
        return f"{prefix}{clean}"[:38]

    def bookmark(self, paragraph, name: str) -> None:
        self._bookmark_id += 1
        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), str(self._bookmark_id))
        start.set(qn("w:name"), name)
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), str(self._bookmark_id))
        paragraph._p.insert(0, start)
        paragraph._p.append(end)

    @staticmethod
    def pageref(paragraph, bookmark_name: str, size=Pt(14), font=BODY_FONT) -> None:
        """Append a ``PAGEREF`` field that Word resolves to a page number."""
        def run(child):
            r = OxmlElement("w:r")
            rpr = OxmlElement("w:rPr")
            rf = OxmlElement("w:rFonts")
            rf.set(qn("w:ascii"), font); rf.set(qn("w:hAnsi"), font)
            sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size.pt * 2)))
            rpr.append(rf); rpr.append(sz)
            r.append(rpr); r.append(child)
            return r

        begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
        instr.text = f" PAGEREF {bookmark_name} \\h "
        sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
        placeholder = OxmlElement("w:t"); placeholder.text = "–"
        end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
        for child in (begin, instr, sep, placeholder, end):
            paragraph._p.append(run(child))

    def enable_field_update(self) -> None:
        """Ask Word to refresh every field the first time the file is opened."""
        settings = self.doc.settings.element
        for existing in settings.findall(qn("w:updateFields")):
            settings.remove(existing)
        el = OxmlElement("w:updateFields")
        el.set(qn("w:val"), "true")
        settings.append(el)

    # ------------------------------------------------------------------ #
    # primitives
    # ------------------------------------------------------------------ #
    def _para(self, text="", size=BODY_SIZE, font=BODY_FONT, bold=False, italic=False,
              align=None, space_after=Pt(8), style=None, colour=None, underline=False):
        p = self.doc.add_paragraph(style=style)
        if align is not None:
            p.alignment = align
        pf = p.paragraph_format
        pf.space_after = space_after
        pf.space_before = Pt(0)
        if text:
            run = p.add_run(text)
            run.font.name = font
            run.font.size = size
            run.bold = bold
            run.italic = italic
            run.underline = underline
            if colour:
                run.font.color.rgb = RGBColor(*colour)
        return p

    def page_break(self) -> None:
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def blank(self, n: int = 1) -> None:
        for _ in range(n):
            self._para(space_after=Pt(0))

    # ------------------------------------------------------------------ #
    # headings
    # ------------------------------------------------------------------ #
    def chapter(self, title: str, new_page: bool = True) -> None:
        """Centred Arial 28 pt chapter heading, as in the template."""
        if new_page:
            self.page_break()
        p = self._para(title, size=H1_SIZE, font=HEAD_FONT,
                       align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(18))
        self.bookmark(p, self.slug("_Ch_", title))

    def h2(self, title: str) -> None:
        self._para(title, size=H2_SIZE, bold=True, space_after=Pt(8))

    def h3(self, title: str) -> None:
        self._para(title, size=H3_SIZE, bold=True, italic=True, space_after=Pt(6))

    # ------------------------------------------------------------------ #
    # body content
    # ------------------------------------------------------------------ #
    def p(self, text: str) -> None:
        self._para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    def bullets(self, items: list[str]) -> None:
        for it in items:
            self._para(it, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       style="List Paragraph", space_after=Pt(4))._p  # noqa: B018
            self._bullet_last()

    def _bullet_last(self) -> None:
        """Turn the last paragraph into a real bulleted item."""
        p = self.doc.paragraphs[-1]
        numPr = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
        numId = OxmlElement("w:numId"); numId.set(qn("w:val"), "1")
        numPr.append(ilvl); numPr.append(numId)
        p._p.get_or_add_pPr().append(numPr)

    def numbered(self, items: list[str]) -> None:
        for i, it in enumerate(items, 1):
            self._para(f"{i}.  {it}", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=Pt(4))

    def kv_lines(self, pairs: list[tuple[str, str]]) -> None:
        """Label : value lines, as used on the template's requirements page."""
        for k, v in pairs:
            p = self._para(space_after=Pt(4))
            r1 = p.add_run(f"{k} : ")
            r1.font.name = BODY_FONT; r1.font.size = BODY_SIZE; r1.bold = True
            r2 = p.add_run(v)
            r2.font.name = BODY_FONT; r2.font.size = BODY_SIZE

    # ------------------------------------------------------------------ #
    # figures and tables
    # ------------------------------------------------------------------ #
    def figure(self, path: str | Path, number: str, caption: str,
               width_in: float | None = None) -> None:
        path = Path(path)
        if not path.exists():
            self.p(f"[missing figure: {path.name}]")
            return
        from PIL import Image

        with Image.open(path) as im:
            w_px, h_px = im.size
        aspect = h_px / w_px
        width = width_in or TEXT_WIDTH_IN
        # keep tall figures on a single page
        max_h = 7.6
        if width * aspect > max_h:
            width = max_h / aspect
        width = min(width, TEXT_WIDTH_IN)

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        p.add_run().add_picture(str(path), width=Inches(width))

        cap = self._para(f"Fig. {number}  {caption}", size=Pt(12), italic=True,
                         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(14))
        self.bookmark(cap, self.slug("_Fig_", number))
        self.figures.append((number, caption))
        return cap

    def table(self, number: str, caption: str, headers: list[str], rows: list[list[str]],
              col_widths: list[float] | None = None, font_size: int = 11) -> None:
        cap = self._para(f"Table {number}  {caption}", size=Pt(12), italic=True,
                         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(4))
        if number:
            self.bookmark(cap, self.slug("_Tab_", number))
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER

        hdr = t.rows[0].cells
        for i, h in enumerate(headers):
            hdr[i].text = ""
            para = hdr[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(h)
            run.bold = True
            run.font.name = BODY_FONT
            run.font.size = Pt(font_size)
            self._shade(hdr[i], "D9E2F3")

        for row in rows:
            cells = t.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = ""
                para = cells[i].paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
                run = para.add_run(str(val))
                run.font.name = BODY_FONT
                run.font.size = Pt(font_size)

        if col_widths:
            for r in t.rows:
                for i, w in enumerate(col_widths):
                    r.cells[i].width = Inches(w)

        self._para(space_after=Pt(12))
        self.tables.append((number, caption))

    @staticmethod
    def _shade(cell, hex_colour: str) -> None:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), hex_colour)
        tcPr.append(shd)

    def code(self, text: str, caption: str | None = None) -> None:
        if caption:
            self._para(caption, size=Pt(12), italic=True, space_after=Pt(4))
        for line in text.rstrip("\n").split("\n"):
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.space_after = Pt(0)
            pf.space_before = Pt(0)
            pf.left_indent = Inches(0.18)
            run = p.add_run(line if line.strip() else " ")
            run.font.name = CODE_FONT
            run.font.size = CODE_SIZE
            rpr = run._element.get_or_add_rPr()
            rf = OxmlElement("w:rFonts")
            rf.set(qn("w:ascii"), CODE_FONT)
            rf.set(qn("w:hAnsi"), CODE_FONT)
            rpr.append(rf)
        self._para(space_after=Pt(10))

    # ------------------------------------------------------------------ #
    # output
    # ------------------------------------------------------------------ #
    def save(self, path: str | Path) -> Path:
        path = Path(path)
        self.doc.save(str(path))
        return path

    # ------------------------------------------------------------------ #
    # page estimation (no Word/LibreOffice available on the build machine)
    # ------------------------------------------------------------------ #
    def estimate_pages(self) -> float:
        """Approximate the rendered page count from paragraph metrics.

        A4 page with 1 inch margins leaves about 9.7 inches (698 pt) of text
        height. Line height is taken as 1.15 x font size plus paragraph spacing.
        """
        usable_pt = 698.0
        total_pt = 0.0
        body = self.doc.element.body

        for child in body:
            if child.tag == qn("w:p"):
                total_pt += self._para_height(child)
            elif child.tag == qn("w:tbl"):
                total_pt += self._table_height(child)

        return total_pt / usable_pt

    def _para_height(self, p_el) -> float:
        from docx.text.paragraph import Paragraph

        p = Paragraph(p_el, self.doc)
        # explicit page break
        if "w:br" in p_el.xml and 'w:type="page"' in p_el.xml:
            return 0.0  # handled as a flush; approximated as negligible
        runs = p.runs
        if not runs:
            return 14.0
        size = next((r.font.size.pt for r in runs if r.font.size), 16)
        name = next((r.font.name for r in runs if r.font.name), BODY_FONT)
        text = p.text
        if not text.strip():
            return size * 1.15
        # inline picture
        if "<pic:pic" in p_el.xml or "w:drawing" in p_el.xml:
            import re
            m = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', p_el.xml)
            if m:
                return int(m.group(2)) / 12700.0 + 6  # EMU -> pt
            return 200.0
        # characters per line, roughly
        per_char = 0.47 if name != CODE_FONT else 0.60
        cpl = max(20, int(TEXT_WIDTH_IN * 72 / (size * per_char)))
        lines = max(1, -(-len(text) // cpl))
        spacing = 8.0 if size >= 14 else 4.0
        return lines * size * 1.18 + spacing

    def _table_height(self, tbl_el) -> float:
        rows = tbl_el.findall(qn("w:tr"))
        return len(rows) * 20.0 + 10.0
