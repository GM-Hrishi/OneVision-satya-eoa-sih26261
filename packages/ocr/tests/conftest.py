import io

import pikepdf
import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from satya_ocr import OcrSettings
from satya_ocr.engine import OcrWord


def text_pdf(pages: int = 2, text: str = "Demo Institute of Technology 03 affidavit line") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for n in range(pages):
        for row in range(6):
            c.drawString(72, 760 - row * 24, f"{text} page {n + 1} row {row}")
        c.showPage()
    c.save()
    return buf.getvalue()


def image_pdf(pages: int = 1, size: tuple[int, int] = (800, 1100)) -> bytes:
    imgs = []
    for n in range(pages):
        img = Image.new("L", size, 255)
        ImageDraw.Draw(img).text((50, 50 + n), "scan", fill=0)
        imgs.append(img)
    buf = io.BytesIO()
    imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:], resolution=100.0)
    return buf.getvalue()


def blank_pdf(pages: int = 2) -> bytes:
    pdf = pikepdf.new()
    for _ in range(pages):
        pdf.add_blank_page(page_size=(595, 842))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def words(conf: float, n: int = 12) -> list[OcrWord]:
    return [OcrWord(f"word{i}", (10.0 + i * 40, 10.0, 45.0 + i * 40, 30.0), conf) for i in range(n)]


@pytest.fixture
def settings() -> OcrSettings:
    return OcrSettings()
