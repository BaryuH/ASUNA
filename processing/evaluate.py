"""Danh gia tim anh tuong tu: 10 truy van x nhieu cach bieu dien, Hit@5.

Chay tu thu muc goc repo (can da co data/embeddings/*.npz va data/ground_truth.csv):
    python processing/evaluate.py
    python processing/evaluate.py --vis      # them anh minh hoa top-5 cho tung truy van

Quy tac (theo de bai):
- Kho tim kiem chi gom 50 anh trong db/. 10 anh query/ khong bao gio nam trong ket qua.
- Neu anh truy van cung co trong kho (cung ID), anh do bi loai khoi danh sach ket qua.
- Moi truy van lay 5 ket qua dau. Hit@5 = so truy van co it nhat 1 anh dung trong top-5 / 10.

Do tuong tu:
- Histogram mau (hsv_hist): histogram intersection, tong cac min(h1, h2), nam trong [0, 1].
- Embedding (dinov2, pe-core): cosine similarity giua hai vector da chuan hoa.

Dau ra trong results/:
- top5_<method>.csv   : 5 ket qua dau cua moi truy van, kem diem va dung/sai.
- summary.csv         : Hit@5, Precision@5, MRR cua moi phuong phap.
- results.md          : bang 10 truy van, ID anh phu hop, ket qua cac phuong phap (dan vao bao cao).
- vis/Qxx.jpg         : (voi --vis) anh truy van + top-5 cua moi phuong phap, vien xanh = dung, do = sai.
"""

import argparse
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
METHODS = {
    # ten file .npz : (ten hien thi, cach do)
    "hsv_hist": ("Histogram HSV", "intersection"),
    "dinov2": ("DINOv2 Giant", "cosine"),
    "pe-core": ("PE-Core bigG", "cosine"),
}
TOP_K = 5


def image_id(path):
    """'db/P01_02.jpg' -> 'P01_02'."""
    return Path(path).stem


def load_ground_truth(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["query_id"]: {"pose_id": r["pose_id"], "pose_name": r["pose_name"],
                            "relevant": r["relevant_ids"].split(";")} for r in rows}


def load_embeddings(path):
    with np.load(path, allow_pickle=False) as archive:
        embeddings = archive["embeddings"].astype(np.float64)
        paths = [str(p) for p in archive["paths"]]
    db = [i for i, p in enumerate(paths) if p.startswith("db/")]
    queries = {image_id(p): i for i, p in enumerate(paths) if p.startswith("query/")}
    return embeddings, paths, db, queries


def similarity(query_vec, db_matrix, kind):
    if kind == "intersection":
        return np.minimum(db_matrix, query_vec).sum(axis=1)
    q = query_vec / np.linalg.norm(query_vec)
    d = db_matrix / np.linalg.norm(db_matrix, axis=1, keepdims=True)
    return d @ q


def evaluate(method, kind, emb_dir, gt):
    embeddings, paths, db, queries = load_embeddings(emb_dir / f"{method}.npz")
    missing = set(gt) - set(queries)
    if missing:
        raise SystemExit(f"{method}.npz thieu anh truy van: {sorted(missing)}")
    db_ids = [image_id(paths[i]) for i in db]
    db_matrix = embeddings[db]

    per_query = {}
    for qid in sorted(gt):
        scores = similarity(embeddings[queries[qid]], db_matrix, kind)
        # Loai chinh anh truy van neu no co trong kho (cung ID).
        candidates = [(s, i) for s, i in zip(scores, db_ids) if i != qid]
        ranked = sorted(candidates, key=lambda x: (-x[0], x[1]))
        relevant = set(gt[qid]["relevant"])
        top = [{"rank": r + 1, "image_id": i, "score": float(s), "correct": i in relevant}
               for r, (s, i) in enumerate(ranked[:TOP_K])]
        first = next((r + 1 for r, (_, i) in enumerate(ranked) if i in relevant), None)
        per_query[qid] = {"top": top, "hit": any(t["correct"] for t in top),
                          "precision": sum(t["correct"] for t in top) / TOP_K,
                          "first_correct_rank": first}
    n = len(per_query)
    summary = {
        "hit@5": sum(q["hit"] for q in per_query.values()) / n,
        "hits": sum(q["hit"] for q in per_query.values()),
        "precision@5": sum(q["precision"] for q in per_query.values()) / n,
        "mrr": sum(1 / q["first_correct_rank"] for q in per_query.values()) / n,
    }
    return per_query, summary


def write_outputs(out_dir, gt, results):
    out_dir.mkdir(parents=True, exist_ok=True)
    for method, (per_query, _) in results.items():
        with open(out_dir / f"top5_{method}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "pose_id", "rank", "image_id", "score", "correct"])
            for qid, q in per_query.items():
                for t in q["top"]:
                    w.writerow([qid, gt[qid]["pose_id"], t["rank"], t["image_id"], f"{t['score']:.4f}",
                                int(t["correct"])])

    with open(out_dir / "summary.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "similarity", "hits", "hit@5", "precision@5", "mrr"])
        for method, (_, s) in results.items():
            w.writerow([method, METHODS[method][1], f"{s['hits']}/10", f"{s['hit@5']:.2f}",
                        f"{s['precision@5']:.2f}", f"{s['mrr']:.3f}"])

    lines = ["# Kết quả tìm kiếm trên 10 truy vấn", "",
             "Kho tìm kiếm: 50 ảnh `db/`. Mỗi ô kết quả liệt kê top-5 theo thứ tự; ✓ là ảnh đúng tư thế, ✗ là sai.", "",
             "## Tổng hợp", "", "| Phương pháp | Độ tương tự | Hit@5 | Precision@5 | MRR |", "|---|---|---|---|---|"]
    for method, (_, s) in results.items():
        name, kind = METHODS[method]
        lines.append(f"| {name} | {kind} | {s['hits']}/10 = {s['hit@5']:.2f} | {s['precision@5']:.2f} | {s['mrr']:.3f} |")
    header = "| Truy vấn | Tư thế | Ảnh phù hợp | " + " | ".join(METHODS[m][0] for m in results) + " |"
    lines += ["", "## Chi tiết từng truy vấn", "", header, "|" + "---|" * (3 + len(results))]
    for qid in sorted(gt):
        cells = []
        for method, (per_query, _) in results.items():
            q = per_query[qid]
            top = ", ".join(f"{t['image_id']}{'✓' if t['correct'] else '✗'}" for t in q["top"])
            cells.append(f"{'**HIT**' if q['hit'] else '**MISS**'}: {top}")
        relevant = ", ".join(gt[qid]["relevant"])
        lines.append(f"| {qid} | {gt[qid]['pose_name']} | {relevant} | " + " | ".join(cells) + " |")
    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_font(size=14):
    """Font co dau tieng Viet: Arial (Windows), DejaVu (Linux), Helvetica (macOS)."""
    from PIL import ImageFont
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def write_visuals(out_dir, image_root, gt, results, thumb=150):
    from PIL import Image, ImageDraw, ImageOps

    vis = out_dir / "vis"
    vis.mkdir(parents=True, exist_ok=True)
    pad, label_w = 8, 140

    def tile(path, color=None):
        with Image.open(path) as im:
            im = ImageOps.fit(im.convert("RGB"), (thumb, thumb))
        if color:
            im = ImageOps.expand(im.crop((4, 4, thumb - 4, thumb - 4)), border=4, fill=color)
        return im

    for qid in sorted(gt):
        rows = len(results)
        canvas = Image.new("RGB", (label_w + thumb + pad * 3 + (thumb + pad) * TOP_K,
                                   pad + rows * (thumb + 24 + pad)), "white")
        draw = ImageDraw.Draw(canvas)
        font = load_font(13)
        canvas.paste(tile(image_root / "query" / f"{qid}.jpg", (40, 90, 200)), (label_w, pad + 18))
        draw.text((label_w, pad + 2), f"{qid} (truy van)", font=font, fill="black")
        draw.text((4, pad + 2), gt[qid]["pose_name"].split(" (")[0], font=font, fill="black")
        for r, (method, (per_query, _)) in enumerate(results.items()):
            y = pad + r * (thumb + 24 + pad)
            q = per_query[qid]
            draw.text((4, y + 30), METHODS[method][0], font=font, fill="black")
            draw.text((4, y + 46), "HIT" if q["hit"] else "MISS", font=font, fill=(0, 140, 0) if q["hit"] else (200, 0, 0))
            for k, t in enumerate(q["top"]):
                x = label_w + thumb + pad * 3 + k * (thumb + pad)
                color = (0, 170, 0) if t["correct"] else (220, 0, 0)
                canvas.paste(tile(image_root / "db" / f"{t['image_id']}.jpg", color), (x, y + 18))
                draw.text((x, y + 2), f"#{k + 1} {t['image_id']} {t['score']:.2f}", font=font, fill="black")
        canvas.save(vis / f"{qid}.jpg", quality=88)


def main():
    parser = argparse.ArgumentParser(description="Evaluate image retrieval with Hit@5")
    parser.add_argument("--embeddings", type=Path, default=ROOT / "data" / "embeddings")
    parser.add_argument("--ground-truth", type=Path, default=ROOT / "data" / "ground_truth.csv")
    parser.add_argument("--images", type=Path, default=ROOT / "data" / "raw_images")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--methods", nargs="+", default=list(METHODS), choices=list(METHODS))
    parser.add_argument("--vis", action="store_true", help="ve anh minh hoa top-5 (can thu muc anh)")
    args = parser.parse_args()

    gt = load_ground_truth(args.ground_truth)
    results = {}
    for method in args.methods:
        if not (args.embeddings / f"{method}.npz").is_file():
            print(f"Bo qua {method}: khong thay {method}.npz")
            continue
        results[method] = evaluate(method, METHODS[method][1], args.embeddings, gt)
    if not results:
        raise SystemExit("Khong co file embedding nao de danh gia")

    write_outputs(args.output, gt, results)
    if args.vis:
        write_visuals(args.output, args.images, gt, results)

    print(f"{'Phuong phap':<16}{'Hit@5':>10}{'P@5':>8}{'MRR':>8}")
    for method, (per_query, s) in results.items():
        print(f"{METHODS[method][0]:<16}{s['hits']:>6}/10{s['precision@5']:>8.2f}{s['mrr']:>8.3f}")
        misses = [q for q, v in per_query.items() if not v["hit"]]
        if misses:
            print(f"{'':<16}truot: {', '.join(misses)}")
    print(f"Da ghi ket qua vao {args.output}")


if __name__ == "__main__":
    main()
