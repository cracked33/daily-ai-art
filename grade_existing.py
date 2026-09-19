"""
grade_existing.py
-----------------
One-off helper: tones down the saturation of images that are already in
generated_images/ and writes the results to generated_images_graded/.
Originals are never modified or deleted.

Usage (from the repo root, after `pip install Pillow`):
    python grade_existing.py                # default saturation 0.85
    python grade_existing.py 0.80            # stronger effect
"""

import sys
from pathlib import Path

from PIL import Image, ImageEnhance

SRC = Path("generated_images")
DST = Path("generated_images_graded")


def main():
    saturation = float(sys.argv[1]) if len(sys.argv) > 1 else 0.85
    DST.mkdir(exist_ok=True)

    files = sorted(p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not files:
        print(f"No images found in {SRC}/")
        return

    for p in files:
        try:
            im = Image.open(p).convert("RGB")
            im = ImageEnhance.Color(im).enhance(saturation)
            out = DST / (p.stem + ".jpg")
            im.save(out, format="JPEG", quality=92)
            print(f"graded {p.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"skipped {p.name}: {exc}")

    print(f"Done. {len(files)} files processed -> {DST}/")


if __name__ == "__main__":
    main()
