"""Build STR PDF from report dict."""
import io
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def build_str_pdf(report: dict[str, Any]) -> bytes:
    text = report.get("full_report_text") or _assemble_text(report)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    y = height - margin
    line_height = 14

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, f"FIU-IND STR — {report.get('case_id', 'CASE')}")
    y -= line_height * 2

    c.setFont("Helvetica", 10)
    for line in text.split("\n"):
        if y < margin:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - margin
        # Wrap long lines
        while len(line) > 95:
            c.drawString(margin, y, line[:95])
            line = line[95:]
            y -= line_height
        c.drawString(margin, y, line)
        y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.read()


def _assemble_text(report: dict[str, Any]) -> str:
    return f"""FIU-IND FORM STR-01 (DRAFT)
CASE REF: {report.get('case_id', '')}

NARRATIVE:
{report.get('english_narrative', '')}

RECOMMENDED ACTION:
{report.get('recommended_action', '')}

REGULATORY BASIS:
{report.get('regulatory_basis', '')}
"""
