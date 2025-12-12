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


def draw_checkbox(c: canvas.Canvas, label: str, x: float, y: float, checked: bool = False) -> None:
    size = 9
    box = Box(x, y, 10, 10)
    draw_box(c, box, lw=0.8)
    if checked:
        c.setLineWidth(1.2)
        c.line(x + 2, y + 5, x + 4, y + 2)
        c.line(x + 4, y + 2, x + 8, y + 9)
    draw_label(c, label, x + 14, y + 2, size=size)


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

    print("Generated:")
    print("-", pdf_path)
    for i in range(1, 6):
        print("-", os.path.join(out_dir, f"tenant-bill-page-{i}.png"))


if __name__ == "__main__":
    main()
