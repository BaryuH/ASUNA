"""ASUNA - script chay tren Kaggle (GPU T4, bat Internet) de encode anh bang DINOv2 Giant va PE-Core bigG.

Gan dataset chua thu muc raw_images/ vao notebook, roi chay. Script clone repo va goi
processing/encode_images.py, sau do ma hoa them 10 cau mo ta tu the bang PE-Core (de tim bang chu).
Ket qua nam o /kaggle/working/embeddings/.
"""
import glob, os, subprocess, sys, json, time
import numpy as np

def sh(cmd):
    print("$", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)

t0 = time.time()
sh("pip install -q -U open_clip_torch timm")
sh("git clone --depth 1 https://github.com/BaryuH/ASUNA.git /kaggle/working/ASUNA")

cands = [p for p in glob.glob("/kaggle/input/**/raw_images", recursive=True) if os.path.isdir(p)]
assert cands, "khong tim thay raw_images trong /kaggle/input"
src = cands[0]
n = len(glob.glob(os.path.join(src, "*", "*.jpg")))
print("raw_images:", src, "| so anh:", n, flush=True)
assert n == 60, n

import torch
print("torch", torch.__version__, "| cuda", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "", flush=True)

out = "/kaggle/working/embeddings"
os.makedirs(out, exist_ok=True)
enc = "/kaggle/working/ASUNA/processing/encode_images.py"
sh(f"{sys.executable} {enc} --model dinov2 --input {src} --output {out}/dinov2.npz --batch-size 8")
sh(f"{sys.executable} {enc} --model pe-core --input {src} --output {out}/pe-core.npz --batch-size 4")

# Vector chu cho demo tim bang chu (PE-Core co bo ma hoa chu)
import open_clip
model, _, _ = open_clip.create_model_and_transforms("hf-hub:timm/PE-Core-bigG-14-448")
tok = open_clip.get_tokenizer("hf-hub:timm/PE-Core-bigG-14-448")
poses = {"P01": "warrior one", "P02": "warrior two", "P03": "cobra", "P04": "upward facing dog",
         "P05": "downward facing dog", "P06": "plank", "P07": "tree", "P08": "mountain",
         "P09": "triangle", "P10": "child's"}
prompts = [f"a photo of a person doing the {v} yoga pose" for v in poses.values()]
dev = "cuda" if torch.cuda.is_available() else "cpu"
model = model.eval().to(dev)
with torch.inference_mode(), torch.autocast(device_type=dev, dtype=torch.float16, enabled=dev == "cuda"):
    t = model.encode_text(tok(prompts).to(dev))
t = torch.nn.functional.normalize(t.float(), dim=-1).cpu().numpy()
np.savez(f"{out}/pe-core_text.npz", embeddings=t, pose_ids=np.array(list(poses)), prompts=np.array(prompts))

summary = {}
for f in sorted(glob.glob(f"{out}/*.npz")):
    d = np.load(f)
    summary[os.path.basename(f)] = {k: list(d[k].shape) for k in d.files}
summary["seconds"] = round(time.time() - t0)
json.dump(summary, open(f"{out}/summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
