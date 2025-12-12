#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate a 5-page tenant billing PDF + per-page PNGs.

Outputs:
- tenant-bill-complex-form/output/tenant-bill-5pages.pdf
- tenant-bill-complex-form/output/tenant-bill-page-1.png ... page-5.png

This script avoids system-level browser/apt deps by using:
- reportlab (PDF generation)
- PyMuPDF (PDF -> PNG rendering)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


PDF_FONT = "STSong-Light"  # built-in CID font (supports Chinese)
EN_FONT = "Helvetica"
EN_FONT_BOLD = "Helvetica-Bold"


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float


def ensure_output_dir() -> str:
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def set_style(c: canvas.Canvas) -> None:
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)


def draw_box(c: canvas.Canvas, b: Box, lw: float = 0.8) -> None:
    c.setLineWidth(lw)
    c.rect(b.x, b.y, b.w, b.h, stroke=1, fill=0)


def draw_label(c: canvas.Canvas, text: str, x: float, y: float, size: int = 9) -> None:
    c.setFont(PDF_FONT, size)
    c.drawString(x, y, text)


def draw_label_en(c: canvas.Canvas, text: str, x: float, y: float, size: int = 9, bold: bool = False) -> None:
    c.setFont(EN_FONT_BOLD if bold else EN_FONT, size)
    c.drawString(x, y, text)


def draw_field(
    c: canvas.Canvas,
    label: str,
    b: Box,
    value: str = "",
    label_size: int = 9,
    value_size: int = 10,
    padding: float = 3,
) -> None:
    """A labeled field: label at top-left, with a rectangle for value."""

    # label
    draw_label(c, label, b.x, b.y + b.h + 2, size=label_size)

    # box
    draw_box(c, b)

    if value:
        c.setFont(PDF_FONT, value_size)
        c.drawString(b.x + padding, b.y + b.h - value_size - 2, value)


def draw_field_en(
    c: canvas.Canvas,
    label: str,
    b: Box,
    value: str = "",
    label_size: int = 8,
    value_size: int = 9,
    padding: float = 3,
) -> None:
    """English labeled field."""

    draw_label_en(c, label, b.x, b.y + b.h + 2, size=label_size, bold=False)
    draw_box(c, b)
    if value:
        c.setFont(EN_FONT, value_size)
        c.drawString(b.x + padding, b.y + b.h - value_size - 2, value)


def draw_checkbox(c: canvas.Canvas, label: str, x: float, y: float, checked: bool = False) -> None:
    size = 9
    box = Box(x, y, 10, 10)
    draw_box(c, box, lw=0.8)
    if checked:
        c.setLineWidth(1.2)
        c.line(x + 2, y + 5, x + 4, y + 2)
        c.line(x + 4, y + 2, x + 8, y + 9)
    draw_label(c, label, x + 14, y + 2, size=size)


def draw_checkbox_en(c: canvas.Canvas, label: str, x: float, y: float, checked: bool = False) -> None:
    size = 8
    box = Box(x, y, 10, 10)
    draw_box(c, box, lw=0.8)
    if checked:
        c.setLineWidth(1.2)
        c.line(x + 2, y + 5, x + 4, y + 2)
        c.line(x + 4, y + 2, x + 8, y + 9)
    draw_label_en(c, label, x + 14, y + 2, size=size, bold=False)


def draw_hline(c: canvas.Canvas, x1: float, x2: float, y: float, lw: float = 0.8) -> None:
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)


def draw_vline(c: canvas.Canvas, x: float, y1: float, y2: float, lw: float = 0.8) -> None:
    c.setLineWidth(lw)
    c.line(x, y1, x, y2)


def draw_table(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    col_widths: list[float],
    row_h: float,
    rows: list[list[str]],
    header: list[str] | None = None,
    font_size: int = 8,
) -> float:
    """Draw a simple grid table.

    y_top is the top edge of the table.
    Returns y_bottom.
    """

    ncols = len(col_widths)
    assert all(len(r) == ncols for r in rows), "row column count mismatch"
    if header is not None:
        assert len(header) == ncols, "header column count mismatch"

    total_w = sum(col_widths)
    nrows = len(rows) + (1 if header else 0)
    table_h = nrows * row_h
    y_bottom = y_top - table_h

    # outer
    draw_box(c, Box(x, y_bottom, total_w, table_h), lw=0.9)

    # vertical lines
    x_cursor = x
    for w in col_widths[:-1]:
        x_cursor += w
        draw_vline(c, x_cursor, y_bottom, y_top, lw=0.6)

    # horizontal lines
    for i in range(1, nrows):
        y_line = y_top - i * row_h
        draw_hline(c, x, x + total_w, y_line, lw=0.6)

    # text
    c.setFont(PDF_FONT, font_size)
    pad_x = 2
    pad_y = 2

    def draw_row_text(row: list[str], y_row_top: float) -> None:
        x_cell = x
        for j, text in enumerate(row):
            # clamp to one line; keep short
            safe = (text or "").replace("\n", " ")
            c.drawString(x_cell + pad_x, y_row_top - row_h + pad_y, safe)
            x_cell += col_widths[j]

    y_cursor = y_top
    if header:
        # light gray header background
        c.setFillColor(colors.whitesmoke)
        c.rect(x, y_cursor - row_h, total_w, row_h, stroke=0, fill=1)
        c.setFillColor(colors.black)
        draw_row_text(header, y_cursor)
        y_cursor -= row_h

    for r in rows:
        draw_row_text(r, y_cursor)
        y_cursor -= row_h

    return y_bottom


def draw_footer(c: canvas.Canvas, page_no: int, total_pages: int) -> None:
    w, h = A4
    margin = 15 * mm
    c.setFont(PDF_FONT, 8)
    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.drawString(margin, margin * 0.7, f"第 {page_no} / {total_pages} 页")
    c.drawRightString(w - margin, margin * 0.7, f"打印时间：{dt}")


def draw_footer_en(c: canvas.Canvas, page_no: int, total_pages: int) -> None:
    w, _h = A4
    margin = 15 * mm
    c.setFont(EN_FONT, 8)
    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.drawString(margin, margin * 0.7, f"Page {page_no} / {total_pages}")
    c.drawRightString(w - margin, margin * 0.7, f"Generated: {dt}")


def draw_header(c: canvas.Canvas, page_no: int, total_pages: int) -> None:
    w, h = A4
    margin = 15 * mm

    c.setFont(PDF_FONT, 16)
    c.drawString(margin, h - margin - 2, "租户账单（复杂表单）")

    c.setFont(PDF_FONT, 9)
    c.drawRightString(w - margin, h - margin + 2, "Tenant Billing Statement (Complex Form)")

    # separator
    draw_hline(c, margin, w - margin, h - margin - 8, lw=1.0)

    # meta line
    c.setFont(PDF_FONT, 9)
    c.drawString(margin, h - margin - 22, "用途：对账/开票/付款申请；请用黑色签字笔填写，金额单位：人民币（元）")


def draw_header_en(c: canvas.Canvas, page_no: int, total_pages: int) -> None:
    w, h = A4
    margin = 15 * mm

    c.setFont(EN_FONT_BOLD, 16)
    c.drawString(margin, h - margin - 2, "Tenant Billing Statement (Complex Form)")

    c.setFont(EN_FONT, 9)
    c.drawRightString(w - margin, h - margin + 2, "For reconciliation / invoicing / payment request")

    draw_hline(c, margin, w - margin, h - margin - 8, lw=1.0)

    c.setFont(EN_FONT, 9)
    c.drawString(
        margin,
        h - margin - 22,
        "Please fill in with black ink. Currency: CNY (RMB). See pages 2–4 for details; terms on page 5.",
    )


def money(v: float) -> str:
    return f"{v:,.2f}"


def generate_mock_data() -> dict:
    # Realistic but fictional sample data
    return {
        "invoice_no": "TB-2025-EN-001",
        "billing_period": "2025-12-01 to 2025-12-31",
        "issue_date": "2025-12-12",
        "currency": "CNY",
        "payee": "Greenfield Property Management Co., Ltd.",
        "payer": "Acme Robotics (Shanghai) Co., Ltd.",
        "property_address": "No. 88 Innovation Rd, Pudong, Shanghai",
        "unit": "Tower B · Suite 1203",
        "payment_due": "2026-01-05",
        "bank_name": "Bank of China, Shanghai Pudong Branch",
        "bank_account_name": "Greenfield Property Management Co., Ltd.",
        "bank_account_no": "6222 0000 1234 5678 901",
        "swift": "BKCHCNBJ300",
        "payment_ref": "TB-2025-EN-001 / Acme Robotics",
        "contacts": {
            "payee_contact": "Lily Chen",
            "payee_email": "billing@greenfield.example",
            "payee_phone": "+86 21 5555 0123",
            "payer_contact": "Michael Brown",
            "payer_email": "ap@acmerobotics.example",
            "payer_phone": "+86 21 5555 0456",
        },
        "invoice_info": {
            "legal_name": "Acme Robotics (Shanghai) Co., Ltd.",
            "tax_id": "91310000MA1KXXXXXX",
            "address_phone": "No. 99 Finance Ave, Shanghai / +86 21 5555 0789",
            "bank": "ICBC Shanghai Branch / 1022 0000 9876 5432 10",
        },
        "deliver_to": "ap@acmerobotics.example (PDF invoice preferred)",
        "lease_area_sqm": "168.5",
        "parking_spots": "1",
        "parking_fee": 800.00,
        "access_cards": "3",
        "access_deposit": 300.00,
        "other_deposit": 0.00,
        "deposit_refund_or_deduction": 0.00,
    }


def page_en_1(c: canvas.Canvas, d: dict) -> None:
    w, h = A4
    margin = 15 * mm
    y = h - margin - 40

    draw_label_en(c, "1. Basic information", margin, y + 10, size=11, bold=True)

    block_h = 95
    draw_box(c, Box(margin, y - block_h, w - 2 * margin, block_h), lw=1.0)

    left = margin + 6
    top = y - 10

    col_w = (w - 2 * margin - 18) / 2
    row_h = 18

    fields = [
        ("Invoice No.", d["invoice_no"]),
        ("Billing period", d["billing_period"]),
        ("Issue date", d["issue_date"]),
        ("Currency", d["currency"]),
        ("Payee (landlord/PM)", d["payee"]),
        ("Payer (tenant)", d["payer"]),
        ("Property address", d["property_address"]),
        ("Unit", d["unit"]),
    ]

    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        x = left + col * (col_w + 6)
        y_field_top = top - row * row_h
        draw_field_en(c, label, Box(x, y_field_top - row_h + 2, col_w, row_h - 6), value=value)

    y2 = y - block_h - 25
    draw_label_en(c, "2. Summary (amounts in CNY)", margin, y2 + 10, size=11, bold=True)

    sum_h = 90
    draw_box(c, Box(margin, y2 - sum_h, w - 2 * margin, sum_h), lw=1.0)

    # Pre-compute totals from the same mock tables used on later pages
    charges_subtotal = 24500.00 + 1500.00 + 320.00 + 260.00 + 180.00
    vat = round(charges_subtotal * 0.06, 2)  # example VAT 6%
    gross = charges_subtotal + vat
    received = 10000.00
    carryover = -500.00  # credit
    adjustment = -300.00  # discount
    closing = gross - received + carryover + adjustment

    x = margin + 6
    y_top = y2 - 10
    col_w3 = (w - 2 * margin - 18) / 3
    row_h2 = 22

    sum_fields = [
        ("Charges subtotal", money(charges_subtotal)),
        ("Tax (VAT 6%)", money(vat)),
        ("Gross due", money(gross)),
        ("Amount received", money(received)),
        ("Carryover (credit/arrears)", money(carryover)),
        ("Adjustments (discount/true-up)", money(adjustment)),
        ("Closing balance (payable/refundable)", money(closing)),
        ("Payment due date", d["payment_due"]),
        ("Payment reference", d["payment_ref"]),
    ]

    for i, (label, value) in enumerate(sum_fields):
        col = i % 3
        row = i // 3
        bx = x + col * (col_w3 + 6)
        by = y_top - row * row_h2
        draw_field_en(c, label, Box(bx, by - row_h2 + 2, col_w3, row_h2 - 6), value=value)

    y3 = y2 - sum_h - 25
    draw_label_en(c, "3. Payment information", margin, y3 + 10, size=11, bold=True)

    pay_h = 140
    draw_box(c, Box(margin, y3 - pay_h, w - 2 * margin, pay_h), lw=1.0)

    left = margin + 6
    top = y3 - 10

    draw_label_en(c, "Payment method (select one):", left, top, size=9, bold=False)
    cb_y = top - 16
    draw_checkbox_en(c, "Bank transfer", left, cb_y, checked=True)
    draw_checkbox_en(c, "Cash", left + 110, cb_y, checked=False)
    draw_checkbox_en(c, "Alipay", left + 190, cb_y, checked=False)
    draw_checkbox_en(c, "WeChat", left + 270, cb_y, checked=False)
    draw_checkbox_en(c, "Cheque", left + 350, cb_y, checked=False)

    bank_top = cb_y - 20
    col_w2 = (w - 2 * margin - 18) / 2
    row_h3 = 20

    bank_fields = [
        ("Account name", d["bank_account_name"]),
        ("Bank", d["bank_name"]),
        ("Account number", d["bank_account_no"]),
        ("SWIFT / routing (if any)", d["swift"]),
        ("Payment reference (memo)", d["payment_ref"]),
        ("Due date", d["payment_due"]),
    ]

    for i, (label, value) in enumerate(bank_fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w2 + 6)
        by = bank_top - row * row_h3
        draw_field_en(c, label, Box(bx, by - row_h3 + 2, col_w2, row_h3 - 6), value=value)

    note_y = y3 - pay_h + 10
    c.setFont(EN_FONT, 8)
    c.drawString(
        margin + 8,
        note_y,
        "Note: This page is a summary. Line-item details are on pages 2–4; terms & attachments on page 5.",
    )


def page_en_2(c: canvas.Canvas, d: dict) -> None:
    w, h = A4
    margin = 15 * mm
    y = h - margin - 40
    draw_label_en(c, "4. Charges detail (rent / management fee / other)", margin, y + 10, size=11, bold=True)

    x = margin
    y_top = y - 5

    col_widths = [
        18 * mm,  # Date
        33 * mm,  # Item
        28 * mm,  # Period
        14 * mm,  # Qty
        18 * mm,  # Unit price
        14 * mm,  # Tax
        22 * mm,  # Amount
        28 * mm,  # Notes
    ]
    header = ["Date", "Item", "Billing period", "Qty", "Unit", "Tax", "Amount", "Notes"]

    line_items = [
        ("2025-12-01", "Base rent", "Dec 2025", "1", "24,500.00", "6%", "24,500.00", "Per lease"),
        ("2025-12-01", "Property mgmt fee", "Dec 2025", "1", "1,500.00", "6%", "1,500.00", "Monthly"),
        ("2025-12-01", "Cleaning service", "Dec 2025", "1", "320.00", "6%", "320.00", "Common area"),
        ("2025-12-01", "Minor repair", "WO#R-2198", "1", "260.00", "6%", "260.00", "Invoice attached"),
        ("2025-12-01", "Insurance surcharge", "Dec 2025", "1", "180.00", "0%", "180.00", "Non-taxable"),
    ]

    rows = [list(r) for r in line_items]
    # pad to 15 rows to keep layout stable
    while len(rows) < 15:
        rows.append(["", "", "", "", "", "", "", ""])

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=16, rows=rows, header=header, font_size=7)

    charges_subtotal = 24500.00 + 1500.00 + 320.00 + 260.00 + 180.00
    vat = round((24500.00 + 1500.00 + 320.00 + 260.00) * 0.06, 2)  # last line non-taxable
    gross = charges_subtotal + vat

    y2 = y_bottom - 25
    draw_label_en(c, "Subtotal & notes", margin, y2 + 10, size=11, bold=True)

    box_h = 120
    draw_box(c, Box(margin, y2 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y2 - 12

    draw_field_en(c, "Charges subtotal", Box(left, top - 18, 70 * mm, 14), value=money(charges_subtotal))
    draw_field_en(c, "Tax subtotal", Box(left + 75 * mm, top - 18, 60 * mm, 14), value=money(vat))
    draw_field_en(c, "Gross total", Box(left + 140 * mm, top - 18, 45 * mm, 14), value=money(gross))

    text_box = Box(left, y2 - box_h + 12, w - 2 * margin - 12, 70)
    draw_label_en(
        c,
        "Notes (payment purpose, discounts, contract clause reference, etc.):",
        text_box.x,
        text_box.y + text_box.h + 6,
        size=9,
        bold=False,
    )
    draw_box(c, text_box)
    c.setFont(EN_FONT, 8)
    c.drawString(text_box.x + 4, text_box.y + text_box.h - 14, "Discount applied: CNY 300.00 (Service goodwill).")
    c.drawString(text_box.x + 4, text_box.y + text_box.h - 28, "Carryover credit from last period: CNY 500.00.")


def page_en_3(c: canvas.Canvas, d: dict) -> None:
    w, h = A4
    margin = 15 * mm
    y = h - margin - 40
    draw_label_en(c, "5. Utilities (metering / allocation)", margin, y + 10, size=11, bold=True)

    x = margin
    y_top = y - 5

    col_widths = [
        30 * mm,  # Utility
        22 * mm,  # Meter ID
        20 * mm,  # Prev
        20 * mm,  # Curr
        18 * mm,  # Usage
        18 * mm,  # Unit
        20 * mm,  # Amount
        32 * mm,  # Rule/notes
    ]
    header = ["Utility", "Meter ID", "Prev", "Curr", "Usage", "Unit", "Amount", "Rule / notes"]

    utility_rows = [
        ["Electricity", "E-1203", "12,480", "12,760", "280", "1.10", money(308.00), "kWh x rate"],
        ["Water", "W-1203", "3,120", "3,160", "40", "6.50", money(260.00), "m³ x rate"],
        ["Gas", "—", "—", "—", "—", "—", money(0.00), "Not applicable"],
        ["HVAC", "—", "—", "—", "—", "—", money(0.00), "Included in rent"],
        ["Internet", "—", "—", "—", "1", "180.00", money(180.00), "Monthly"],
        ["Waste disposal", "—", "—", "—", "1", "120.00", money(120.00), "Monthly"],
        ["Common area allocation", "—", "—", "—", "—", "—", money(0.00), "N/A this period"],
        ["Other", "", "", "", "", "", "", ""],
    ]

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=18, rows=utility_rows, header=header, font_size=7)

    y2 = y_bottom - 20
    draw_label_en(c, "Allocation method (if applicable):", margin, y2 + 6, size=10, bold=False)

    cb_y = y2 - 14
    draw_checkbox_en(c, "By leased area (sqm)", margin + 2, cb_y, checked=True)
    draw_field_en(c, "Leased area", Box(margin + 120, cb_y - 2, 40 * mm, 12), value=d["lease_area_sqm"])

    cb_y2 = cb_y - 16
    draw_checkbox_en(c, "By headcount", margin + 2, cb_y2, checked=False)
    draw_field_en(c, "Headcount", Box(margin + 120, cb_y2 - 2, 30 * mm, 12), value="")

    cb_y3 = cb_y2 - 16
    draw_checkbox_en(c, "By seats/equipment", margin + 2, cb_y3, checked=False)
    draw_field_en(c, "Qty", Box(margin + 120, cb_y3 - 2, 30 * mm, 12), value="")

    cb_y4 = cb_y3 - 16
    draw_checkbox_en(c, "Independent metering", margin + 2, cb_y4, checked=True)

    cb_y5 = cb_y4 - 16
    draw_checkbox_en(c, "Other", margin + 2, cb_y5, checked=False)
    draw_field_en(c, "Details", Box(margin + 70, cb_y5 - 2, w - 2 * margin - 80, 12), value="")

    y3 = cb_y5 - 30
    draw_label_en(c, "6. Parking / access / deposits (if applicable)", margin, y3 + 10, size=11, bold=True)

    box_h = 130
    draw_box(c, Box(margin, y3 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y3 - 12
    col_w = (w - 2 * margin - 18) / 2
    row_h = 20

    fields = [
        ("Parking spots", d["parking_spots"]),
        ("Parking fee", money(d["parking_fee"])),
        ("Access cards", d["access_cards"]),
        ("Access card deposit", money(d["access_deposit"])),
        ("Other deposit / guarantee", money(d["other_deposit"])),
        ("Refund / deduction this period", money(d["deposit_refund_or_deduction"])),
    ]

    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w + 6)
        by = top - row * row_h
        draw_field_en(c, label, Box(bx, by - row_h + 2, col_w, row_h - 6), value=value)


def page_en_4(c: canvas.Canvas, d: dict) -> None:
    w, h = A4
    margin = 15 * mm
    y = h - margin - 40
    draw_label_en(c, "7. Payments & reconciliation (received / credits / discounts / late fees)", margin, y + 10, size=11, bold=True)

    x = margin
    y_top = y - 5

    col_widths = [
        22 * mm,  # Date
        35 * mm,  # Type
        26 * mm,  # Amount
        34 * mm,  # Channel/Ref
        28 * mm,  # Applied to
        35 * mm,  # Notes
    ]
    header = ["Date", "Type", "Amount", "Channel / ref", "Applied to", "Notes"]

    tx_rows = [
        ["2025-12-05", "Payment received", money(6000.00), "Bank / TRX-88421", "Dec 2025", "Partial payment"],
        ["2025-12-20", "Payment received", money(4000.00), "Bank / TRX-90117", "Dec 2025", "Partial payment"],
        ["2025-11-30", "Carryover credit", money(-500.00), "N/A", "Nov 2025", "Overpayment"],
        ["2025-12-12", "Discount / adjustment", money(-300.00), "Approval#D-118", "Dec 2025", "Goodwill"],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
    ]

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=18, rows=tx_rows, header=header, font_size=7)

    charges_subtotal = 24500.00 + 1500.00 + 320.00 + 260.00 + 180.00
    vat = round(charges_subtotal * 0.06, 2)
    gross = charges_subtotal + vat
    received = 10000.00
    carryover = -500.00
    adjustment = -300.00
    outstanding = gross - received + carryover + adjustment

    y2 = y_bottom - 25
    draw_label_en(c, "Reconciliation result", margin, y2 + 10, size=11, bold=True)

    box_h = 170
    draw_box(c, Box(margin, y2 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y2 - 12
    draw_field_en(c, "Gross due (this period)", Box(left, top - 18, 60 * mm, 14), value=money(gross))
    draw_field_en(c, "Paid / received", Box(left + 66 * mm, top - 18, 55 * mm, 14), value=money(received))
    draw_field_en(c, "Outstanding (payable/refundable)", Box(left + 127 * mm, top - 18, 55 * mm, 14), value=money(outstanding))

    qr = Box(w - margin - 55 * mm, y2 - box_h + 75, 50 * mm, 50 * mm)
    draw_label_en(c, "Payment QR (optional)", qr.x, qr.y + qr.h + 6, size=9, bold=False)
    draw_box(c, qr)
    c.setFont(EN_FONT_BOLD, 10)
    c.drawCentredString(qr.x + qr.w / 2, qr.y + qr.h / 2, "PAY")

    confirm = Box(left, y2 - box_h + 75, w - 2 * margin - 12 - 55 * mm - 8, 80)
    draw_label_en(c, "Explanation (differences, justifications, required documents):", confirm.x, confirm.y + confirm.h + 6, size=9, bold=False)
    draw_box(c, confirm)
    c.setFont(EN_FONT, 8)
    c.drawString(confirm.x + 4, confirm.y + confirm.h - 14, "No discrepancies reported. Discount and credit applied as noted.")

    sig_y = y2 - box_h + 12
    draw_label_en(c, "Sign-off:", left, sig_y + 38, size=9, bold=False)
    draw_field_en(c, "Payee authorized signature", Box(left, sig_y, 75 * mm, 30), value="Lily Chen")
    draw_field_en(c, "Payer authorized signature", Box(left + 83 * mm, sig_y, 75 * mm, 30), value="Michael Brown")
    draw_field_en(c, "Date", Box(left + 166 * mm, sig_y, 30 * mm, 30), value="2025-12-12")


def page_en_5(c: canvas.Canvas, d: dict) -> None:
    w, h = A4
    margin = 15 * mm
    y = h - margin - 40
    draw_label_en(c, "8. Terms, attachments & contacts", margin, y + 10, size=11, bold=True)

    terms_h = 280
    terms = Box(margin, y - terms_h, w - 2 * margin, terms_h)
    draw_box(c, terms, lw=1.0)

    tx = terms.x + 6
    ty = terms.y + terms_h - 14

    draw_label_en(c, "Terms summary (sample — adjust per your lease/legal requirements):", tx, ty, size=9, bold=True)
    lines = [
        "1) This statement is issued under the lease agreement. The lease, addenda and valid supporting documents prevail.",
        "2) Payment shall be made by the due date. Late fees/penalties may apply as stipulated in the lease (if applicable).",
        "3) Billing disputes must be raised in writing within 3 business days of receipt, with supporting evidence; otherwise deemed accepted.",
        "4) Metered utilities are based on readings and the applicable rate; allocated charges follow the published allocation basis and data.",
        "5) For invoicing, please provide complete invoice details (legal name, tax ID, address/phone, bank info) and comply with tax rules.",
        "6) This form contains business/personal information and must be handled confidentially and used only for lease settlement purposes.",
    ]

    text = c.beginText(tx, ty - 16)
    text.setFont(EN_FONT, 8)
    text.setLeading(12)
    for ln in lines:
        text.textLine(ln)
    c.drawText(text)

    att_y = terms.y - 25
    draw_label_en(c, "Attachments checklist (tick what is provided):", margin, att_y + 10, size=11, bold=True)

    box_h = 120
    att = Box(margin, att_y - box_h, w - 2 * margin, box_h)
    draw_box(c, att, lw=1.0)

    x0 = margin + 8
    y0 = att_y - 20
    items = [
        "Lease agreement / addendum (key pages)",
        "Prior bill & reconciliation sign-off",
        "Meter photos / meter log",
        "Allocation detail (published sheet)",
        "Work order & acceptance",
        "Payment receipt / bank slip",
        "Invoice copy (PDF/e-invoice)",
        "Other (specify)",
    ]
    checked = {0, 2, 5}  # sample checked items
    for i, it in enumerate(items):
        col = i % 2
        row = i // 2
        draw_checkbox_en(c, it, x0 + col * 250, y0 - row * 18, checked=i in checked)

    y2 = att.y - 25
    draw_label_en(c, "Contacts", margin, y2 + 10, size=11, bold=True)

    contact_h = 95
    contact = Box(margin, y2 - contact_h, w - 2 * margin, contact_h)
    draw_box(c, contact, lw=1.0)

    left = margin + 6
    top = y2 - 12
    col_w = (w - 2 * margin - 18) / 2
    row_h = 20

    fields = [
        ("Payee contact", d["contacts"]["payee_contact"]),
        ("Payee phone/email", f'{d["contacts"]["payee_phone"]} / {d["contacts"]["payee_email"]}'),
        ("Payer contact", d["contacts"]["payer_contact"]),
        ("Payer phone/email", f'{d["contacts"]["payer_phone"]} / {d["contacts"]["payer_email"]}'),
        (
            "Invoice details (legal name / tax ID / address+phone / bank)",
            f'{d["invoice_info"]["legal_name"]} | {d["invoice_info"]["tax_id"]}',
        ),
        ("Delivery (invoice/receipt)", d["deliver_to"]),
    ]
    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w + 6)
        by = top - row * row_h
        draw_field_en(c, label, Box(bx, by - row_h + 2, col_w, row_h - 6), value=value, value_size=8)

    y3 = contact.y - 35
    draw_label_en(c, "Final confirmation (sign & stamp):", margin, y3 + 10, size=11, bold=True)

    sig_h = 70
    sig = Box(margin, y3 - sig_h, w - 2 * margin, sig_h)
    draw_box(c, sig, lw=1.0)

    left = margin + 6
    top = y3 - 12
    draw_field_en(c, "Payee signature / stamp", Box(left, top - 45, 85 * mm, 40), value="Greenfield PM (stamp)")
    draw_field_en(c, "Payer signature / stamp", Box(left + 95 * mm, top - 45, 85 * mm, 40), value="Acme Robotics (stamp)")
    draw_field_en(c, "Date", Box(left + 190 * mm, top - 45, 20 * mm, 40), value="2025-12-12")


def page_1(c: canvas.Canvas) -> None:
    w, h = A4
    margin = 15 * mm

    y = h - margin - 40

    # Basic info blocks
    draw_label(c, "一、基本信息", margin, y + 10, size=11)

    block_h = 95
    draw_box(c, Box(margin, y - block_h, w - 2 * margin, block_h), lw=1.0)

    left = margin + 6
    top = y - 10

    col_w = (w - 2 * margin - 18) / 2
    row_h = 18

    fields = [
        ("账单编号 / Invoice No.", "TB-2025-001"),
        ("账期 / Billing Period", "2025-12-01 ~ 2025-12-31"),
        ("出具日期 / Issue Date", datetime.now().strftime("%Y-%m-%d")),
        ("币种 / Currency", "CNY"),
        ("收款方（房东/物业）", "（填写）"),
        ("付款方（租户）", "（填写）"),
        ("物业地址 / Property Address", "（填写）"),
        ("房号/铺位 / Unit", "（填写）"),
    ]

    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        x = left + col * (col_w + 6)
        y_field_top = top - row * row_h
        draw_field(c, label, Box(x, y_field_top - row_h + 2, col_w, row_h - 6), value=value)

    y2 = y - block_h - 25

    # Summary
    draw_label(c, "二、金额汇总", margin, y2 + 10, size=11)
    sum_h = 90
    draw_box(c, Box(margin, y2 - sum_h, w - 2 * margin, sum_h), lw=1.0)

    x = margin + 6
    y_top = y2 - 10

    sum_fields = [
        ("本期应收合计", "（自动/填写）"),
        ("税额（如适用）", ""),
        ("本期实收/已收", ""),
        ("上期结转（欠/预）", ""),
        ("本期调整（减免/补收）", ""),
        ("期末结余（应付/应退）", ""),
    ]

    col_w3 = (w - 2 * margin - 18) / 3
    row_h2 = 22

    for i, (label, value) in enumerate(sum_fields):
        col = i % 3
        row = i // 3
        bx = x + col * (col_w3 + 6)
        by = y_top - row * row_h2
        draw_field(c, label, Box(bx, by - row_h2 + 2, col_w3, row_h2 - 6), value=value)

    # Payment info
    y3 = y2 - sum_h - 25
    draw_label(c, "三、付款信息", margin, y3 + 10, size=11)
    pay_h = 140
    draw_box(c, Box(margin, y3 - pay_h, w - 2 * margin, pay_h), lw=1.0)

    left = margin + 6
    top = y3 - 10

    draw_label(c, "付款方式（可多选）：", left, top, size=9)
    cb_y = top - 16
    draw_checkbox(c, "银行转账", left, cb_y)
    draw_checkbox(c, "现金", left + 110, cb_y)
    draw_checkbox(c, "支付宝", left + 190, cb_y)
    draw_checkbox(c, "微信", left + 270, cb_y)
    draw_checkbox(c, "支票", left + 350, cb_y)

    # bank fields
    bank_top = cb_y - 20
    col_w2 = (w - 2 * margin - 18) / 2
    row_h3 = 20
    bank_fields = [
        ("收款账户名", ""),
        ("开户行", ""),
        ("收款账号", ""),
        ("联行号/Swift（如有）", ""),
        ("付款参考/附言（建议填写账单编号）", "TB-2025-001"),
        ("付款截止日", "（填写）"),
    ]

    for i, (label, value) in enumerate(bank_fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w2 + 6)
        by = bank_top - row * row_h3
        draw_field(c, label, Box(bx, by - row_h3 + 2, col_w2, row_h3 - 6), value=value)

    # note
    note_y = y3 - pay_h + 10
    c.setFont(PDF_FONT, 8)
    c.drawString(margin + 8, note_y, "备注：本页仅为汇总与付款信息，明细见第2-4页；条款与附件清单见第5页。")


def page_2(c: canvas.Canvas) -> None:
    w, h = A4
    margin = 15 * mm

    y = h - margin - 40
    draw_label(c, "四、费用明细（房租/管理费/其他）", margin, y + 10, size=11)

    # Table
    x = margin
    y_top = y - 5

    col_widths = [
        18 * mm,  # 日期
        28 * mm,  # 项目
        28 * mm,  # 周期
        14 * mm,  # 数量
        18 * mm,  # 单价
        14 * mm,  # 税率
        20 * mm,  # 金额
        35 * mm,  # 备注
    ]

    header = ["日期", "项目", "计费周期", "数量", "单价", "税率", "金额", "备注"]

    rows: list[list[str]] = []
    for i in range(15):
        rows.append([
            "（填写）",
            "（如：房租）" if i == 0 else "",
            "（如：12月）" if i == 0 else "",
            "",
            "",
            "",
            "",
            "",
        ])

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=16, rows=rows, header=header, font_size=8)

    # Totals section
    y2 = y_bottom - 25
    draw_label(c, "小计与说明", margin, y2 + 10, size=11)

    box_h = 120
    draw_box(c, Box(margin, y2 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y2 - 12

    draw_field(c, "本页费用小计", Box(left, top - 18, 70 * mm, 14), value="")
    draw_field(c, "税额小计", Box(left + 75 * mm, top - 18, 60 * mm, 14), value="")
    draw_field(c, "含税合计", Box(left + 140 * mm, top - 18, 45 * mm, 14), value="")

    # text area
    text_box = Box(left, y2 - box_h + 12, w - 2 * margin - 12, 70)
    draw_label(c, "说明/备注（可写付款原因、减免依据、合同条款号等）：", text_box.x, text_box.y + text_box.h + 6, size=9)
    draw_box(c, text_box)


def page_3(c: canvas.Canvas) -> None:
    w, h = A4
    margin = 15 * mm

    y = h - margin - 40
    draw_label(c, "五、能耗与公用事业费（抄表/分摊）", margin, y + 10, size=11)

    # Meter table
    x = margin
    y_top = y - 5

    col_widths = [
        28 * mm,  # 项目
        22 * mm,  # 表号
        20 * mm,  # 上期读数
        20 * mm,  # 本期读数
        18 * mm,  # 用量
        18 * mm,  # 单价
        20 * mm,  # 金额
        34 * mm,  # 计费规则/备注
    ]
    header = ["项目", "表号", "上期读数", "本期读数", "用量", "单价", "金额", "计费规则/备注"]

    items = [
        "电费（尖峰平谷）",
        "水费",
        "燃气费",
        "供暖/制冷",
        "网络/通信",
        "垃圾清运",
        "公区能耗分摊",
        "其他",
    ]

    rows: list[list[str]] = []
    for it in items:
        rows.append([it, "", "", "", "", "", "", ""])

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=18, rows=rows, header=header, font_size=8)

    # Allocation options
    y2 = y_bottom - 20
    draw_label(c, "分摊方式（如适用，勾选并填写）：", margin, y2 + 6, size=10)

    cb_y = y2 - 14
    draw_checkbox(c, "按面积（㎡）分摊", margin + 2, cb_y)
    draw_field(c, "承租面积", Box(margin + 120, cb_y - 2, 40 * mm, 12), value="")

    cb_y2 = cb_y - 16
    draw_checkbox(c, "按人数分摊", margin + 2, cb_y2)
    draw_field(c, "人数", Box(margin + 120, cb_y2 - 2, 30 * mm, 12), value="")

    cb_y3 = cb_y2 - 16
    draw_checkbox(c, "按工位/设备分摊", margin + 2, cb_y3)
    draw_field(c, "数量", Box(margin + 120, cb_y3 - 2, 30 * mm, 12), value="")

    cb_y4 = cb_y3 - 16
    draw_checkbox(c, "按抄表/独立计量", margin + 2, cb_y4)

    cb_y5 = cb_y4 - 16
    draw_checkbox(c, "其他", margin + 2, cb_y5)
    draw_field(c, "说明", Box(margin + 70, cb_y5 - 2, w - 2 * margin - 80, 12), value="")

    # Parking / access
    y3 = cb_y5 - 30
    draw_label(c, "六、停车/门禁/押金（如适用）", margin, y3 + 10, size=11)

    box_h = 130
    draw_box(c, Box(margin, y3 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y3 - 12

    fields = [
        ("车位数量", ""),
        ("车位费用", ""),
        ("门禁卡数量", ""),
        ("门禁卡押金", ""),
        ("其他押金/保证金", ""),
        ("本期退还/扣除", ""),
    ]
    col_w = (w - 2 * margin - 18) / 2
    row_h = 20
    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w + 6)
        by = top - row * row_h
        draw_field(c, label, Box(bx, by - row_h + 2, col_w, row_h - 6), value=value)


def page_4(c: canvas.Canvas) -> None:
    w, h = A4
    margin = 15 * mm

    y = h - margin - 40
    draw_label(c, "七、收付款与对账（回款/抵扣/减免/滞纳金）", margin, y + 10, size=11)

    # Reconciliation table
    x = margin
    y_top = y - 5

    col_widths = [
        22 * mm,  # 日期
        30 * mm,  # 类型
        24 * mm,  # 金额
        26 * mm,  # 渠道/凭证号
        28 * mm,  # 对应账期
        50 * mm,  # 备注
    ]
    header = ["日期", "类型", "金额", "渠道/凭证号", "对应账期", "备注"]

    rows: list[list[str]] = []
    for i in range(14):
        rows.append(["（填写）", "（收款/退款/抵扣/减免/滞纳）", "", "", "", ""])

    y_bottom = draw_table(c, x, y_top, col_widths, row_h=18, rows=rows, header=header, font_size=8)

    # Summary + confirmation
    y2 = y_bottom - 25
    draw_label(c, "对账结论", margin, y2 + 10, size=11)

    box_h = 170
    draw_box(c, Box(margin, y2 - box_h, w - 2 * margin, box_h), lw=1.0)

    left = margin + 6
    top = y2 - 12

    draw_field(c, "截至本账期：应付金额", Box(left, top - 18, 60 * mm, 14), value="")
    draw_field(c, "已付金额", Box(left + 66 * mm, top - 18, 55 * mm, 14), value="")
    draw_field(c, "未付金额", Box(left + 127 * mm, top - 18, 55 * mm, 14), value="")

    # QR placeholder
    qr = Box(w - margin - 55 * mm, y2 - box_h + 75, 50 * mm, 50 * mm)
    draw_label(c, "收款码/二维码（可选）", qr.x, qr.y + qr.h + 6, size=9)
    draw_box(c, qr)
    c.setFont(PDF_FONT, 7)
    c.drawCentredString(qr.x + qr.w / 2, qr.y + qr.h / 2, "QR")

    # confirmation text area
    confirm = Box(left, y2 - box_h + 75, w - 2 * margin - 12 - 55 * mm - 8, 80)
    draw_label(c, "对账说明（差异原因/调整依据/需补充材料）：", confirm.x, confirm.y + confirm.h + 6, size=9)
    draw_box(c, confirm)

    # signatures
    sig_y = y2 - box_h + 12
    draw_label(c, "对账确认签章：", left, sig_y + 38, size=9)

    draw_field(c, "收款方经办/签章", Box(left, sig_y, 75 * mm, 30), value="")
    draw_field(c, "付款方经办/签章", Box(left + 83 * mm, sig_y, 75 * mm, 30), value="")
    draw_field(c, "确认日期", Box(left + 166 * mm, sig_y, 30 * mm, 30), value="")


def page_5(c: canvas.Canvas) -> None:
    w, h = A4
    margin = 15 * mm

    y = h - margin - 40
    draw_label(c, "八、条款、附件与联系方式", margin, y + 10, size=11)

    # Terms box
    terms_h = 280
    terms = Box(margin, y - terms_h, w - 2 * margin, terms_h)
    draw_box(c, terms, lw=1.0)

    tx = terms.x + 6
    ty = terms.y + terms_h - 14

    c.setFont(PDF_FONT, 9)
    c.drawString(tx, ty, "条款摘要（示例，可按合同/法律要求调整）：")

    lines = [
        "1）本账单为租赁合同项下费用对账与收款通知，最终以双方签署的合同、补充协议及有效凭证为准。",
        "2）租户应在付款截止日前完成付款；逾期将按合同约定计收滞纳金/违约金（如适用）。",
        "3）如对费用有异议，应在收到账单后 3 个工作日内以书面形式提出，并提供相关证明材料；逾期视为认可。",
        "4）抄表类费用以本期读数及计费规则为依据；分摊类费用以公示的分摊口径及数据为依据。",
        "5）涉及开票的，需提供完整开票信息（名称/税号/地址电话/开户行账号），并遵循当地税务规定。",
        "6）本表含个人/企业信息，仅用于租赁结算与对账；双方应妥善保管并遵守数据保护义务。",
    ]

    text = c.beginText(tx, ty - 16)
    text.setFont(PDF_FONT, 8)
    text.setLeading(12)
    for ln in lines:
        text.textLine(ln)
    c.drawText(text)

    # Attachments checklist
    att_y = terms.y - 25
    draw_label(c, "附件清单（勾选已随账单提供的材料）：", margin, att_y + 10, size=11)

    box_h = 120
    att = Box(margin, att_y - box_h, w - 2 * margin, box_h)
    draw_box(c, att, lw=1.0)

    x0 = margin + 8
    y0 = att_y - 20

    items = [
        "租赁合同/补充协议（关键页）",
        "上期账单与对账确认",
        "抄表照片/抄表记录",
        "物业费/能耗分摊明细（公示表）",
        "维修/服务工单与验收单",
        "付款凭证/银行回单",
        "发票（复印件/电子版）",
        "其他材料（请注明）",
    ]

    for i, it in enumerate(items):
        col = i % 2
        row = i // 2
        draw_checkbox(c, it, x0 + col * 250, y0 - row * 18, checked=False)

    # Contacts
    y2 = att.y - 25
    draw_label(c, "联系方式", margin, y2 + 10, size=11)

    contact_h = 95
    contact = Box(margin, y2 - contact_h, w - 2 * margin, contact_h)
    draw_box(c, contact, lw=1.0)

    left = margin + 6
    top = y2 - 12

    fields = [
        ("收款方联系人", ""),
        ("电话/邮箱", ""),
        ("付款方联系人", ""),
        ("电话/邮箱", ""),
        ("开票信息（名称/税号/地址电话/开户行账号）", ""),
        ("收件地址/电子邮箱（用于寄送/发送票据）", ""),
    ]

    col_w = (w - 2 * margin - 18) / 2
    row_h = 20
    for i, (label, value) in enumerate(fields):
        col = i % 2
        row = i // 2
        bx = left + col * (col_w + 6)
        by = top - row * row_h
        draw_field(c, label, Box(bx, by - row_h + 2, col_w, row_h - 6), value=value)

    # Final signatures
    y3 = contact.y - 35
    draw_label(c, "最终确认（双方签字盖章）：", margin, y3 + 10, size=11)

    sig_h = 70
    sig = Box(margin, y3 - sig_h, w - 2 * margin, sig_h)
    draw_box(c, sig, lw=1.0)

    left = margin + 6
    top = y3 - 12

    draw_field(c, "收款方签字/盖章", Box(left, top - 45, 85 * mm, 40), value="")
    draw_field(c, "付款方签字/盖章", Box(left + 95 * mm, top - 45, 85 * mm, 40), value="")
    draw_field(c, "日期", Box(left + 190 * mm, top - 45, 20 * mm, 40), value="")


def generate_pdf(pdf_path: str) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT))

    c = canvas.Canvas(pdf_path, pagesize=A4)
    set_style(c)

    total_pages = 5
    pages = [page_1, page_2, page_3, page_4, page_5]

    for i, fn in enumerate(pages, start=1):
        draw_header(c, i, total_pages)
        fn(c)
        draw_footer(c, i, total_pages)
        if i != total_pages:
            c.showPage()
            set_style(c)

    c.save()


def generate_pdf_filled_en(pdf_path: str) -> None:
    """Generate an English PDF with filled mock data (5 pages)."""

    # Keep CN font registered for safety; EN uses built-in Helvetica.
    pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT))
    c = canvas.Canvas(pdf_path, pagesize=A4)
    set_style(c)

    d = generate_mock_data()
    total_pages = 5
    pages = [page_en_1, page_en_2, page_en_3, page_en_4, page_en_5]

    for i, fn in enumerate(pages, start=1):
        draw_header_en(c, i, total_pages)
        fn(c, d)
        draw_footer_en(c, i, total_pages)
        if i != total_pages:
            c.showPage()
            set_style(c)

    c.save()


def render_first_page_png(pdf_path: str, png_path: str) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(2.0, 2.0)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(png_path)
    doc.close()
    return png_path


def render_pngs(pdf_path: str, out_dir: str) -> list[str]:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    png_paths: list[str] = []

    # ~144 dpi (2x) for readability without huge files
    mat = fitz.Matrix(2.0, 2.0)

    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_path = os.path.join(out_dir, f"tenant-bill-page-{i+1}.png")
        pix.save(png_path)
        png_paths.append(png_path)

    doc.close()
    return png_paths


def main() -> None:
    out_dir = ensure_output_dir()
    pdf_path = os.path.join(out_dir, "tenant-bill-5pages.pdf")

    generate_pdf(pdf_path)
    render_pngs(pdf_path, out_dir)

    en_pdf_path = os.path.join(out_dir, "tenant-bill-filled-en-5pages.pdf")
    generate_pdf_filled_en(en_pdf_path)
    en_png_path = os.path.join(out_dir, "tenant-bill-filled-en-page-1.png")
    render_first_page_png(en_pdf_path, en_png_path)

    print("Generated:")
    print("-", pdf_path)
    for i in range(1, 6):
        print("-", os.path.join(out_dir, f"tenant-bill-page-{i}.png"))
    print("-", en_pdf_path)
    print("-", en_png_path)


if __name__ == "__main__":
    main()
