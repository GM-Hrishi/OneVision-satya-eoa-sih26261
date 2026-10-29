"""The OCR engine interface and its implementations.

`PaddleOcrEngine` is the real, self-hosted engine (models baked into the image, no network at
runtime). `FakeOcrEngine` returns known text and boxes for tests; it is never used by the product.
"""

import logging
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from PIL import Image

log = logging.getLogger("satya.ocr")


@dataclass(frozen=True)
class OcrWord:
    """One word read from a page image: pixel box (x0, y0, x1, y1), origin top left, 0..1 score."""

    text: str
    box: tuple[float, float, float, float]
    confidence: float


class OcrEngine(Protocol):
    name: str

    def available(self) -> bool:
        """False when the engine or its models are missing (the fallback is OCR_UNAVAILABLE)."""
        ...

    def read(self, image: Image.Image, *, page_number: int = 1) -> list[OcrWord]:
        """Words on one page image. `page_number` is a hint that real engines ignore."""
        ...


class FakeOcrEngine:
    """Test double. `responses` is a list (one entry per page read, in call order) or a callable
    taking the image and the page number."""

    name = "fake"

    def __init__(
        self,
        responses: Sequence[list[OcrWord]] | Callable[[Image.Image, int], list[OcrWord]],
        *,
        is_available: bool = True,
        delay_s: float = 0.0,
        error: Exception | None = None,
    ) -> None:
        self._responses = responses
        self._available = is_available
        self._delay = delay_s
        self._error = error
        self.calls: list[tuple[int, tuple[int, int]]] = []

    def available(self) -> bool:
        return self._available

    def read(self, image: Image.Image, *, page_number: int = 1) -> list[OcrWord]:
        import time

        self.calls.append((page_number, image.size))
        if self._delay:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        if callable(self._responses):
            return self._responses(image, page_number)
        index = len(self.calls) - 1
        return list(self._responses[min(index, len(self._responses) - 1)])


class PaddleOcrEngine:
    """PaddleOCR (Apache-2.0), PP-OCR models read from SATYA_OCR_MODEL_DIR, offline.

    Written against the PaddleOCR 3.x API (`PaddleOCR(...).predict(ndarray)` returning dicts with
    `rec_texts`, `rec_scores`, `rec_polys`); the 2.x call (`.ocr(ndarray, cls=False)`) is handled
    too. Not verified in the cloud session (see docs/progress/OCR-SLICE-PROGRESS.md).
    """

    name = "paddleocr"

    def __init__(self, model_dir: str | None = None, lang: str = "en") -> None:
        self.model_dir = model_dir or os.environ.get("SATYA_OCR_MODEL_DIR", "/opt/ocr-models")
        self.lang = lang
        self._ocr: Any = None
        self._missing: str | None = None

    def available(self) -> bool:
        if self._ocr is not None:
            return True
        if self._missing is not None:
            return False
        try:
            os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
            os.environ["HF_HUB_OFFLINE"] = "1"
            from paddleocr import PaddleOCR  # type: ignore[import-not-found,unused-ignore]

            self._ocr = self._build(PaddleOCR)
        except Exception as exc:  # missing package, missing models, incompatible runtime
            self._missing = f"{type(exc).__name__}"
            log.warning("paddleocr unavailable: %s", exc)
            return False
        return True

    def _build(self, paddle_ocr: Any) -> Any:
        det = os.path.join(self.model_dir, "det")
        rec = os.path.join(self.model_dir, "rec")
        if not (os.path.isdir(det) and os.path.isdir(rec)):
            raise FileNotFoundError("OCR models not found in the model directory")
        try:  # 3.x
            return paddle_ocr(
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_detection_model_dir=det,
                text_recognition_model_name="en_PP-OCRv5_mobile_rec",
                text_recognition_model_dir=rec,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=False,
            )
        except TypeError:  # 2.x
            return paddle_ocr(
                det_model_dir=det, rec_model_dir=rec, use_angle_cls=False, lang=self.lang
            )

    def read(self, image: Image.Image, *, page_number: int = 1) -> list[OcrWord]:
        import numpy as np

        if not self.available():
            raise RuntimeError("OCR engine unavailable")
        array = np.asarray(image.convert("RGB"))
        if hasattr(self._ocr, "predict"):
            out: list[OcrWord] = []
            for res in self._ocr.predict(array):
                data = res.get("res", res) if hasattr(res, "get") else res
                polys = data.get("rec_polys", data.get("dt_polys", []))
                for text, score, poly in zip(
                    data.get("rec_texts", []), data.get("rec_scores", []), polys, strict=False
                ):
                    out += _split_line(str(text), float(score), _bbox(poly))
            return out
        result = self._ocr.ocr(array, cls=False) or [[]]
        return [
            w
            for line in (result[0] or [])
            for w in _split_line(str(line[1][0]), float(line[1][1]), _bbox(line[0]))
        ]


def _bbox(poly: Any) -> tuple[float, float, float, float]:
    xs = [float(p[0]) for p in poly]
    ys = [float(p[1]) for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def _split_line(text: str, score: float, box: tuple[float, float, float, float]) -> list[OcrWord]:
    """PaddleOCR returns text lines; split into words with the box shared out by character count."""
    words = text.split()
    if len(words) <= 1:
        return [OcrWord(text.strip(), box, score)] if text.strip() else []
    x0, y0, x1, y1 = box
    total = sum(len(w) for w in words) + len(words) - 1
    out, cursor = [], 0
    for word in words:
        left = x0 + (x1 - x0) * cursor / total
        cursor += len(word)
        right = x0 + (x1 - x0) * cursor / total
        cursor += 1
        out.append(OcrWord(word, (left, y0, right, y1), score))
    return out
