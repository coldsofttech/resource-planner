from __future__ import annotations

import io
import re
from datetime import datetime

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text)


def export_to_pdf(
    rows: list[dict[str, str]],
    *,
    title: str = "Export",
    app_title: str = "Resource Planner",
    base_url: str = "",
) -> bytes:
    """
    Render rows to PDF bytes with a branded header, paginated footer, and styled table.

    Layout:
      - Header strip (accent colour) with app title on every page.
      - Footer: "<base_url> (exported on: <date>)" left, "Page X of Y" right.
      - Content: report title then the data table.

    Args:
        rows:      Pre-formatted list of dicts (keys = display column names).
        title:     Report title rendered at the top of the first page.
        app_title: Application name shown in the header strip (HTML tags are stripped).
        base_url:  URL shown in the footer left.

    Returns:
        Raw PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    # oklch(0.55 0.18 270) → #4B65D9
    _PRIMARY = colors.HexColor("#4B65D9")
    _SECONDARY = colors.HexColor("#818CF8")
    _LIGHT_ROW = colors.HexColor("#EEF2FF")
    _BORDER = colors.HexColor("#E0E7FF")
    _TEXT_DARK = colors.HexColor("#1E1B4B")
    _TEXT_MUTED = colors.HexColor("#6B7280")
    _WHITE = colors.white

    headers = list(rows[0].keys()) if rows else []
    page_size = landscape(A4)
    pw, ph = page_size
    margin = 20 * mm

    clean_app_title = _strip_html(app_title)
    exported_on = datetime.now().strftime("%d %b %Y, %H:%M")
    footer_left = (
        f"{base_url} (exported on: {exported_on})"
        if base_url
        else f"Exported on: {exported_on}"
    )

    buffer = io.BytesIO()

    class _NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._page_states: list[dict] = []

        def showPage(self):
            self._page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._page_states)
            for page_num, state in enumerate(self._page_states, start=1):
                self.__dict__.update(state)
                self._draw_chrome(page_num, total)
                rl_canvas.Canvas.showPage(self)
            rl_canvas.Canvas.save(self)

        def _draw_chrome(self, page_num: int, total: int) -> None:
            self.saveState()

            # Header strip
            self.setFillColor(_PRIMARY)
            self.rect(0, ph - 14 * mm, pw, 14 * mm, fill=1, stroke=0)
            self.setFillColor(_WHITE)
            self.setFont("Helvetica-Bold", 11)
            self.drawString(margin, ph - 9 * mm, clean_app_title)

            # Footer rule
            self.setStrokeColor(_BORDER)
            self.setLineWidth(0.5)
            self.line(margin, 16 * mm, pw - margin, 16 * mm)

            # Footer text
            self.setFillColor(_TEXT_MUTED)
            self.setFont("Helvetica", 8)
            self.drawString(margin, 10 * mm, footer_left)
            self.drawRightString(pw - margin, 10 * mm, f"Page {page_num} of {total}")

            self.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
    )

    title_style = ParagraphStyle(
        "ExportTitle",
        fontSize=18,
        textColor=_TEXT_DARK,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    header_cell_style = ParagraphStyle(
        "CellHeader",
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=_WHITE,
        leading=11,
        alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        "Cell",
        fontSize=8,
        fontName="Helvetica",
        leading=10,
        alignment=TA_LEFT,
    )

    elements = [
        Paragraph(title, title_style),
        Spacer(1, 6 * mm),
    ]

    if rows:
        data = [
            [Paragraph(h, header_cell_style) for h in headers],
        ] + [
            [Paragraph(str(row.get(h, "") or ""), cell_style) for h in headers]
            for row in rows
        ]
        available = pw - 2 * margin
        _sample = rows[:50]
        _pad = 16  # 8 pt each side

        natural = []
        for h in headers:
            w = stringWidth(h, "Helvetica-Bold", 9)
            for row in _sample:
                cw = stringWidth(str(row.get(h, "") or ""), "Helvetica", 8)
                if cw > w:
                    w = cw
            natural.append(w + _pad)

        total_natural = sum(natural) or 1
        col_widths = [n / total_natural * available for n in natural]

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
                    ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.5, _SECONDARY),
                    # Data rows
                    ("VALIGN", (0, 1), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_ROW]),
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                ]
            )
        )
        elements.append(table)

    doc.build(elements, canvasmaker=_NumberedCanvas)
    return buffer.getvalue()
