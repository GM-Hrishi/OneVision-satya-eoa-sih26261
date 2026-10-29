"""Build-time only: download the PP-OCR models once and copy them to OUT/det and OUT/rec.

Run by services/api/Dockerfile when WITH_OCR=1, so the running product never reaches the network.
Not verified in the cloud session (the sandbox cannot reach the model hosts); see
docs/DEMO-CHECKLIST.md for the laptop check.
"""

import shutil
import sys
from pathlib import Path

DET = "PP-OCRv5_mobile_det"
REC = "en_PP-OCRv5_mobile_rec"  # Latin script; English and numerals


def main(out: Path) -> int:
    from paddleocr import PaddleOCR

    PaddleOCR(
        text_detection_model_name=DET,
        text_recognition_model_name=REC,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    cache = Path.home() / ".paddlex" / "official_models"
    for name, target in ((DET, "det"), (REC, "rec")):
        source = cache / name
        if not source.is_dir():
            print(f"model {name} not found under {cache}", file=sys.stderr)
            return 1
        shutil.copytree(source, out / target, dirs_exist_ok=True)
    print(f"models written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/ocr-models")))
