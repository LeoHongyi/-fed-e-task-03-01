#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Render a multi-page PDF into ONE stitched PNG (vertical).

Input:
- tenant-bill-complex-form/output/tenant-bill-filled-en-5pages.pdf

Output:
- tenant-bill-complex-form/output/tenant-bill-filled-en-5pages.png

Requires:
- PyMuPDF (fitz)
- Pillow
"""

from __future__ import annotations

import os

import fitz  # PyMuPDF
from PIL import Image


def render_pdf_pages(pdf_path: str, zoom: float = 2.0) -> list[Image.Image]:
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(zoom, zoom)

    images: list[Image.Image] = []
    try:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            mode = "RGB"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            images.append(img)
    finally:
        doc.close()

    return images


def stitch_vertical(images: list[Image.Image], bg: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    if not images:
        raise ValueError("No pages to stitch")

    width = max(im.width for im in images)
    height = sum(im.height for im in images)

    out = Image.new("RGB", (width, height), bg)

    y = 0
    for im in images:
        # center horizontally
        x = (width - im.width) // 2
        out.paste(im, (x, y))
        y += im.height

    return out


def main() -> None:
    base_dir = os.path.dirname(__file__)
    out_dir = os.path.join(base_dir, "output")

    pdf_path = os.path.join(out_dir, "tenant-bill-filled-en-5pages.pdf")
    png_path = os.path.join(out_dir, "tenant-bill-filled-en-5pages.png")

    pages = render_pdf_pages(pdf_path, zoom=2.0)
    stitched = stitch_vertical(pages)
    stitched.save(png_path)

    print(png_path)


if __name__ == "__main__":
    main()
