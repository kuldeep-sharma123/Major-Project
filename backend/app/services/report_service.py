"""
Report Service Module
Generates production-grade reports in Excel (.xlsx), PDF (.pdf), and Allure formats.
"""
from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from loguru import logger

from app.config import settings
from app.services.storage_service import storage_service


class ReportService:
    """Generates detailed Excel and PDF test execution reports."""

    def __init__(self):
        self.reports_dir = Path(settings.reports_path)

    async def generate_excel_report(
        self,
        project_name: str,
        run_data: Dict[str, Any],
        results: List[Dict[str, Any]],
        defects: List[Dict[str, Any]],
    ) -> str:
        """
        Creates an executive multi-sheet Excel report with formatting, stats, and defects.
        """
        filename = f"report_{project_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.xlsx"
        target_path = self.reports_dir / filename

        wb = openpyxl.Workbook()
        
        # ── Sheet 1: Executive Summary ──────────────────────────────────────────
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary.views.sheetView[0].showGridLines = True

        # Header styling
        title_font = Font(name="Calibri", size=18, bold=True, color="1E3A8A")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        pass_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        fail_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

        ws_summary["A1"] = f"AI Autonomous Testing Agent - Executive Report"
        ws_summary["A1"].font = title_font
        ws_summary["A2"] = f"Project: {project_name} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"

        summary_rows = [
            ("Execution Status", run_data.get("status", "completed").upper()),
            ("Total Tests Executed", run_data.get("total_tests", len(results))),
            ("Passed Tests", run_data.get("passed", 0)),
            ("Failed Tests", run_data.get("failed", 0)),
            ("Skipped Tests", run_data.get("skipped", 0)),
            ("Pass Rate (%)", f"{run_data.get('pass_rate', 0)}%"),
            ("Duration", f"{run_data.get('duration_seconds', 0)} seconds"),
            ("Identified Defects", len(defects)),
        ]

        ws_summary.append([])
        for label, val in summary_rows:
            ws_summary.append([label, val])

        for row in range(4, 4 + len(summary_rows)):
            ws_summary.cell(row=row, column=1).font = Font(bold=True)
            ws_summary.cell(row=row, column=1).fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")

        # ── Sheet 2: Detailed Results ───────────────────────────────────────────
        ws_results = wb.create_sheet(title="Test Results")
        headers = ["Test Name", "Status", "Duration (s)", "Error Message", "Analysis / Root Cause"]
        ws_results.append(headers)

        for col_idx, _ in enumerate(headers, 1):
            cell = ws_results.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

        for res in results:
            st = res.get("status", "passed").upper()
            row = [
                res.get("name", res.get("test_name", "Test")),
                st,
                res.get("duration_seconds", 0.0),
                res.get("error_message", "") or "N/A",
                res.get("failure_analysis", {}).get("root_cause", "") if isinstance(res.get("failure_analysis"), dict) else "",
            ]
            ws_results.append(row)
            curr_row = ws_results.max_row
            status_cell = ws_results.cell(row=curr_row, column=2)
            if st == "PASSED":
                status_cell.fill = pass_fill
            elif st == "FAILED":
                status_cell.fill = fail_fill

        # ── Sheet 3: Defects & RCA ──────────────────────────────────────────────
        ws_defects = wb.create_sheet(title="Defects & Root Cause")
        defect_headers = ["Defect Title", "Severity", "Root Cause Category", "Explanation", "Suggested AI Fix"]
        ws_defects.append(defect_headers)
        for col_idx, _ in enumerate(defect_headers, 1):
            cell = ws_defects.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

        for d in defects:
            ws_defects.append([
                d.get("title", "Defect"),
                d.get("severity", "medium").upper(),
                d.get("root_cause_category", d.get("failure_type", "General")),
                d.get("root_cause", "N/A"),
                d.get("suggested_fix", "N/A"),
            ])

        # Auto-adjust column widths
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 60)

        wb.save(target_path)
        logger.info(f"📊 Excel report generated at: {target_path}")
        return f"/storage/reports/{filename}"

    async def generate_pdf_report(
        self,
        project_name: str,
        run_data: Dict[str, Any],
        results: List[Dict[str, Any]],
        defects: List[Dict[str, Any]],
    ) -> str:
        """
        Creates an enterprise-styled PDF report using ReportLab.
        """
        filename = f"report_{project_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
        target_path = self.reports_dir / filename

        doc = SimpleDocTemplate(
            str(target_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E3A8A"),
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#64748B"),
        )
        h2_style = ParagraphStyle(
            "H2Style",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=8,
        )

        elements = []

        # Header
        elements.append(Paragraph("AI Autonomous Testing Agent", title_style))
        elements.append(Paragraph(f"Execution Audit & Quality Report — {project_name}", subtitle_style))
        elements.append(Paragraph(f"Generated at: {datetime.utcnow().strftime('%B %d, %Y - %H:%M:%S UTC')}", subtitle_style))
        elements.append(Spacer(1, 15))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6"), spaceAfter=15))

        # Metrics Table
        total = run_data.get("total_tests", len(results))
        passed = run_data.get("passed", 0)
        failed = run_data.get("failed", 0)
        skipped = run_data.get("skipped", 0)
        pass_rate = f"{run_data.get('pass_rate', 0)}%"

        summary_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Tests", str(total), "Pass Rate", pass_rate],
            ["Passed", str(passed), "Failed", str(failed)],
            ["Skipped", str(skipped), "Defects Found", str(len(defects))],
        ]

        t_summary = Table(summary_data, colWidths=[120, 140, 120, 140])
        t_summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 20))

        # Test Results Table
        elements.append(Paragraph("Test Results Summary", h2_style))
        results_rows = [["Test Name", "Status", "Duration (s)", "Details"]]
        for r in results[:25]:  # Display top 25 in PDF
            st = str(r.get("status", "passed")).upper()
            name = str(r.get("name", r.get("test_name", "Test")))[:35]
            dur = f"{r.get('duration_seconds', 0.0):.1f}s"
            err = (r.get("error_message") or "Pass")[:40]
            results_rows.append([name, st, dur, err])

        t_results = Table(results_rows, colWidths=[180, 80, 80, 180])
        t_results.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_results)

        # Defects section if any
        if defects:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("AI Root Cause Analysis & Detected Defects", h2_style))
            defect_rows = [["Severity", "Defect Title", "Root Cause & Fix"]]
            for d in defects[:15]:
                sev = str(d.get("severity", "medium")).upper()
                title = str(d.get("title", "Issue"))[:30]
                rc = f"Cause: {d.get('root_cause', '')[:50]}\nFix: {d.get('suggested_fix', '')[:50]}"
                defect_rows.append([sev, title, rc])

            t_defects = Table(defect_rows, colWidths=[70, 170, 280])
            t_defects.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#991B1B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            elements.append(t_defects)

        doc.build(elements)
        logger.info(f"📄 PDF report generated at: {target_path}")
        return f"/storage/reports/{filename}"


report_service = ReportService()

def get_report_service() -> ReportService:
    return report_service

