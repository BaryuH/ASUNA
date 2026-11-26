"""
collect_frames.py - Thu thap anh yoga tu video theo bang ke hoach frames_plan.csv

Cach dung (chay tu thu muc data/ cua repo ASUNA;
    chay tren may ca nhan, KHONG chay tren Kaggle/Colab vi YouTube hay chan IP may chu):
    python collect_frames.py                 # tai va cat tat ca dong da dien
    python collect_frames.py --sheet         # them anh tong hop de kiem tra bang mat
    python collect_frames.py --check-only    # chi kiem tra bang ke hoach, khong tai

Can cai truoc:
    pip install yt-dlp pillow
    ffmpeg (Windows: winget install ffmpeg | macOS: brew install ffmpeg)

Moi dong trong frames_plan.csv sinh ra:
    raw_images/db/P01_01.jpg hoac raw_images/query/Q01.jpg   (frame tai dung moc thoi gian)
    audio/<image_id>.wav                              (10 giay am thanh quanh frame, dung cho ASR/Whisper)
    clips/<image_id>.mp4                              (doan video 10 giay, dung cho temporal)
Sau khi chay xong se tao:
    sources.csv        (thong tin nguon anh - bat buoc nop)
    ground_truth.csv   (ID anh phu hop voi tung truy van - tao TRUOC khi chay cac phuong phap)
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(ROOT, "frames_plan.csv")
WINDOW = 10  # so giay lay truoc va sau moc thoi gian (doan 20 giay, du rong cho ASR)


def parse_time(s):
    """'1:23' -> 83, '01:02:03' -> 3723, '95' -> 95, '1:23.5' -> 83.5"""
    parts = [float(p) for p in s.strip().split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(" ".join(cmd[:3]) + " ... loi:\n" + (r.stderr or r.stdout)[-800:])


def read_plan():
    with open(PLAN, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def video_key(url):
    """Rut ID video YouTube de so sanh (bo qua phan ?si=... thay doi moi lan chia se)."""
    import re
    m = re.search(r"(?:youtu\.be/|shorts/|v=|embed/)([\w-]{11})", url)
    return m.group(1) if m else url.strip()


def check_plan(rows):
    """Kiem tra cac loi hay gap: thieu anh, trung video trong cung tu the, ro ri du lieu."""
    problems = []
    filled = [r for r in rows if r["video_url"].strip() and r["timestamp"].strip()]
    db = [r for r in filled if r["split"] == "db"]
    q = [r for r in filled if r["split"] == "query"]

    by_pose = defaultdict(list)
    for r in db:
        by_pose[r["pose_id"]].append(r)
    for pid, items in sorted(by_pose.items()):
        urls = [video_key(r["video_url"]) for r in items]
        dup = {u for u in urls if urls.count(u) > 1}
        if dup:
            problems.append(f"[{pid}] co nhieu anh trong kho lay tu CUNG mot video: {', '.join(dup)}")

    db_urls = {video_key(r["video_url"]) for r in db}
    for r in q:
        if video_key(r["video_url"]) in db_urls:
            problems.append(f"[{r['image_id']}] video truy van da dung trong kho -> ro ri du lieu")

    print(f"Da dien: {len(db)}/50 anh kho, {len(q)}/10 truy van")
    missing = [r["image_id"] for r in rows if r not in filled]
    if missing:
        print("Chua dien video_url/timestamp:", ", ".join(missing))
    for p in problems:
        print("CANH BAO:", p)
    if not problems:
        print("Khong phat hien trung video hay ro ri du lieu.")
    return filled


def fetch_clip(row, clip_path):
    """Chi tai doan 10 giay quanh moc thoi gian (khong tai ca video)."""
    t = parse_time(row["timestamp"])
    start = max(0.0, t - WINDOW)
    end = t + WINDOW
    src = row["video_url"].strip()

    if os.path.isfile(src):  # video da co san tren may
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-i", src,
             "-t", str(end - start), "-c:v", "libx264", "-c:a", "aac", clip_path])
    else:  # link YouTube
        out_tmpl = clip_path[:-4] + ".%(ext)s"
        run([sys.executable, "-m", "yt_dlp", "-q", "--no-playlist", "--force-overwrites",
             "-f", "bv*[height<=720]+ba/b[height<=720]/b",
             "--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts",
             "--merge-output-format", "mp4", "-o", out_tmpl, src])
    return t - start  # vi tri frame can lay ben trong doan clip


def previous_sources():
    """Doc sources.csv cua lan chay truoc de biet dong nao da doi link/moc thoi gian."""
    p = os.path.join(ROOT, "sources.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8-sig", newline="") as f:
        return {r["image_id"]: r for r in csv.DictReader(f)}


def process(row, prev, redo=False):
    iid = row["image_id"]
    sub = "db" if row["split"] == "db" else "query"
    img_path = os.path.join(ROOT, "raw_images", sub, iid + ".jpg")
    clip_path = os.path.join(ROOT, "clips", iid + ".mp4")
    wav_path = os.path.join(ROOT, "audio", iid + ".wav")
    old = prev.get(iid)
    unchanged = old is not None and old.get("video_url", "").strip() == row["video_url"].strip() \
        and old.get("timestamp", "").strip() == row["timestamp"].strip()
    if not redo and unchanged and os.path.exists(img_path) and os.path.exists(clip_path):
        print(f"  {iid}: da co, bo qua")
        return
    if old is not None and not unchanged:
        print(f"  {iid}: link hoac moc thoi gian da doi -> cat lai")
    offset = fetch_clip(row, clip_path)
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{offset:.2f}", "-i", clip_path,
         "-frames:v", "1", "-q:v", "2", img_path])
    try:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip_path, "-vn", "-ac", "1",
             "-ar", "16000", wav_path])
    except RuntimeError:
        print(f"  {iid}: video khong co am thanh (ASR se khong dung duoc cho anh nay)")
    print(f"  {iid}: OK")


def write_outputs(rows, prev=None, errors=()):
    prev = prev or {}
    done = []
    for r in rows:
        if not os.path.exists(os.path.join(
                ROOT, "raw_images", "db" if r["split"] == "db" else "query", r["image_id"] + ".jpg")):
            continue
        # dong bi loi: giu thong tin cu de lan sau van biet can cat lai
        done.append(prev.get(r["image_id"], r) if r["image_id"] in errors else r)

    cols = ["image_id", "split", "pose_id", "pose_name", "video_url", "channel",
            "timestamp", "license", "view", "people", "notes"]
    with open(os.path.join(ROOT, "sources.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(done)

    db_by_pose = defaultdict(list)
    for r in done:
        if r["split"] == "db":
            db_by_pose[r["pose_id"]].append(r["image_id"])
    with open(os.path.join(ROOT, "ground_truth.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["query_id", "pose_id", "pose_name", "relevant_ids"])
        for r in done:
            if r["split"] == "query":
                w.writerow([r["image_id"], r["pose_id"], r["pose_name"],
                            ";".join(sorted(db_by_pose[r["pose_id"]]))])
    print(f"Da ghi sources.csv ({len(done)} anh) va ground_truth.csv")


def contact_sheets(rows):
    """Moi tu the 1 anh: 5 anh kho + anh truy van, de kiem tra bang mat."""
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(ROOT, "checks"), exist_ok=True)
    by_pose = defaultdict(list)
    for r in rows:
        by_pose[r["pose_id"]].append(r)
    H = 240
    for pid, items in sorted(by_pose.items()):
        thumbs = []
        for r in sorted(items, key=lambda r: (r["split"] != "db", r["image_id"])):
            p = os.path.join(ROOT, "raw_images", "db" if r["split"] == "db" else "query", r["image_id"] + ".jpg")
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGB")
            im = im.resize((int(im.width * H / im.height), H))
            ImageDraw.Draw(im).rectangle([0, 0, 90, 22], fill="black")
            ImageDraw.Draw(im).text((4, 4), r["image_id"], fill="white")
            thumbs.append(im)
        if not thumbs:
            continue
        sheet = Image.new("RGB", (sum(t.width for t in thumbs) + 8 * len(thumbs), H), "white")
        x = 0
        for t in thumbs:
            sheet.paste(t, (x, 0))
            x += t.width + 8
        sheet.save(os.path.join(ROOT, "checks", f"{pid}.jpg"), quality=85)
    print("Da tao anh kiem tra trong thu muc checks/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--redo", action="store_true", help="cat lai tat ca, ke ca anh da co")
    args = ap.parse_args()

    rows = read_plan()
    filled = check_plan(rows)
    if args.check_only:
        return
    if not shutil.which("ffmpeg"):
        sys.exit("Chua cai ffmpeg. Windows: winget install ffmpeg | macOS: brew install ffmpeg")
    for d in ["raw_images/db", "raw_images/query", "clips", "audio"]:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)

    errors = []
    prev = previous_sources()
    for r in filled:
        try:
            process(r, prev, args.redo)
        except Exception as e:  # mot dong loi khong lam dung ca qua trinh
            errors.append(r["image_id"])
            print(f"  {r['image_id']}: LOI - {e}")
    write_outputs(rows, prev, set(errors))
    if args.sheet:
        contact_sheets(rows)
    if errors:
        print("Cac dong bi loi, kiem tra link/moc thoi gian roi chay lai:", ", ".join(errors))


if __name__ == "__main__":
    main()
