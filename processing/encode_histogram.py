"""Baseline: histogram mau HSV cho moi anh (khong dung AI).

Chay tu thu muc goc repo:
    python processing/encode_histogram.py

Dau ra data/embeddings/hsv_hist.npz cung dinh dang voi encode_images.py:
`embeddings` (moi dong la histogram 8x8x8 = 512 o, da chuan hoa tong = 1) va `paths`.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def hsv_histogram(path, bins=(8, 8, 8), max_side=256):
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((max_side, max_side))
        hsv = np.asarray(image.convert("HSV")).reshape(-1, 3)
    hist, _ = np.histogramdd(hsv, bins=bins, range=((0, 256), (0, 256), (0, 256)))
    hist = hist.flatten().astype(np.float32)
    return hist / hist.sum()


def main():
    parser = argparse.ArgumentParser(description="Encode images as HSV color histograms")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "raw_images")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "embeddings" / "hsv_hist.npz")
    args = parser.parse_args()

    paths = sorted(p for p in args.input.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if not paths:
        parser.error(f"no supported images found in {args.input}")
    embeddings = np.stack([hsv_histogram(p) for p in paths])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.output, embeddings=embeddings,
             paths=np.array([p.relative_to(args.input).as_posix() for p in paths]))
    print(f"Saved {len(paths)} histograms {embeddings.shape} to {args.output}")


if __name__ == "__main__":
    main()
