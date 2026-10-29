"""Scan variants of our own synthetic PDFs (Pillow only): skew, noise, lower DPI.

Test and demo fixtures only. Never used on a real document; the input is always a PDF made by the
repository's synthetic generators.
"""

import io
import random

import pikepdf
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

from satya_ocr.inspect import PDFIUM_LOCK

# The three demo scans (docs/DEMO-NOTES.md): what they are and how they are made. Seeds are fixed.
SCAN_VARIANTS: dict[str, dict[str, object]] = {
    "scan_clean": {"dpi": 150, "skew_deg": 0.4, "noise": 0.0, "blur": 0.0, "seed": 11},
    "scan_noisy": {"dpi": 70, "skew_deg": 2.0, "noise": 0.06, "blur": 1.3, "seed": 12},
    "scan_mixed": {"dpi": 150, "skew_deg": 0.4, "noise": 0.0, "blur": 0.0, "seed": 13},
}


def _noise(img: Image.Image, amount: float, rng: random.Random) -> Image.Image:
    if amount <= 0:
        return img
    px = img.load()
    assert px is not None
    w, h = img.size
    for _ in range(int(w * h * amount)):
        x, y = rng.randrange(w), rng.randrange(h)
        px[x, y] = rng.choice((0, 255))
    return img


def page_images(
    pdf: bytes, *, dpi: int, skew_deg: float, noise: float, blur: float, seed: int
) -> list[Image.Image]:
    rng = random.Random(seed)
    out = []
    with PDFIUM_LOCK:
        doc = pdfium.PdfDocument(pdf)
        try:
            for index in range(len(doc)):
                img = doc[index].render(scale=dpi / 72).to_pil().convert("L")
                angle = skew_deg * (1 if index % 2 == 0 else -1)
                if angle:
                    img = img.rotate(angle, resample=Image.Resampling.BICUBIC, fillcolor=255)
                if blur:
                    img = img.filter(ImageFilter.GaussianBlur(blur))
                out.append(_noise(img, noise, rng))
        finally:
            doc.close()
    return out


def _to_pdf(images: list[Image.Image], dpi: int) -> bytes:
    buf = io.BytesIO()
    images[0].save(buf, "PDF", save_all=True, append_images=images[1:], resolution=float(dpi))
    # Pillow stamps the current time and a random /ID; drop both so the same input gives the same
    # bytes (make synth-check compares them).
    with pikepdf.open(io.BytesIO(buf.getvalue())) as pdf:
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]
        stable = io.BytesIO()
        pdf.save(stable, deterministic_id=True)
        return stable.getvalue()


def rasterise(
    pdf: bytes,
    *,
    dpi: int = 150,
    skew_deg: float = 0.0,
    noise: float = 0.0,
    blur: float = 0.0,
    seed: int = 1,
    only_pages: set[int] | None = None,
) -> bytes:
    """A scan of `pdf`: every page (or only the 1-based `only_pages`, the rest stay native text)
    becomes an image-only page. Digital signatures are lost, as they would be on a real scan."""
    images = page_images(pdf, dpi=dpi, skew_deg=skew_deg, noise=noise, blur=blur, seed=seed)
    scan = _to_pdf(images, dpi)
    if only_pages is None:
        return scan
    # Mixed document: keep the original pages not listed, take the image pages for the others.
    with pikepdf.open(io.BytesIO(pdf)) as original, pikepdf.open(io.BytesIO(scan)) as scanned:
        out = pikepdf.new()
        for number in range(1, len(original.pages) + 1):
            source = scanned if number in only_pages else original
            out.pages.append(source.pages[number - 1])
        for page in out.pages:  # a rebuilt file has no valid signature: drop widgets and fields
            if "/Annots" in page.obj:
                del page.obj["/Annots"]
        buf = io.BytesIO()
        out.save(buf, deterministic_id=True)
        return buf.getvalue()
