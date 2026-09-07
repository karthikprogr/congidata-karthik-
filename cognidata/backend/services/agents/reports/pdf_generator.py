"""
PDF Generator — reportlab PDF with styled tables, stats, insights.
"""
import io
from typing import Optional
import pandas as pd


def generate_pdf(df: pd.DataFrame, title: str = "COGNIDATA Report",
                 insights: str = "", sql_results: str = "") -> bytes:
    """Generate a styled PDF report and return as bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle("title", parent=styles["Title"],
                                     fontSize=20, textColor=colors.HexColor("#6366f1"),
                                     alignment=TA_CENTER)
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#6366f1")))
        story.append(Spacer(1, 0.3*cm))

        # Dataset overview
        story.append(Paragraph("Dataset Overview", styles["Heading2"]))
        overview_data = [
            ["Metric", "Value"],
            ["Rows", str(len(df))],
            ["Columns", str(len(df.columns))],
            ["Missing Values", str(int(df.isnull().sum().sum()))],
            ["Memory", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB"],
        ]
        t = Table(overview_data, colWidths=[6*cm, 10*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f8ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Statistics table
        story.append(Paragraph("Statistical Summary", styles["Heading2"]))
        nums = df.select_dtypes(include="number")
        if not nums.empty:
            desc = nums.describe().round(2)
            stat_data = [["Column"] + list(desc.index)]
            for col in desc.columns:
                stat_data.append([col] + [str(v) for v in desc[col].values])
            t2 = Table(stat_data)
            t2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",   (0, 0), (-1, -1), 8),
                ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f8ff")]),
                ("PADDING",    (0, 0), (-1, -1), 4),
            ]))
            story.append(t2)
            story.append(Spacer(1, 0.5*cm))

        # SQL results
        if sql_results:
            story.append(Paragraph("Query Results", styles["Heading2"]))
            story.append(Paragraph(sql_results[:1000], styles["Normal"]))
            story.append(Spacer(1, 0.3*cm))

        # AI Insights
        if insights:
            story.append(Paragraph("AI Insights", styles["Heading2"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#6366f1")))
            story.append(Spacer(1, 0.2*cm))
            for line in insights.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
                    story.append(Spacer(1, 0.1*cm))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        # Fallback: plain text PDF-like bytes
        content = f"{title}\n\nDataset: {len(df)} rows × {len(df.columns)} columns\n\n{insights}"
        return content.encode()
