"""Encode images into normalized embeddings.

Run from the repository root, for example:
    python processing/encode_images.py --model dinov2
    python processing/encode_images.py --model pe-core --batch-size 8

Each output .npz contains `embeddings` and corresponding relative `paths`.
Model weights are downloaded on first use.
"""

import argparse
import tempfile
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class ImageDataset(Dataset):
    def __init__(self, paths, preprocess):
        self.paths = paths
        self.preprocess = preprocess

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        with Image.open(self.paths[index]) as image:
            return self.preprocess(image.convert("RGB"))


def load_model(name, device):
    if name == "dinov2":
        model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitg14")
        preprocess = transforms.Compose([
            transforms.Resize(518, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(518),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
    else:
        import open_clip

        model, _, preprocess = open_clip.create_model_and_transforms(
            "hf-hub:timm/PE-Core-bigG-14-448"
        )
    return model.eval().to(device), preprocess


def main():
    parser = argparse.ArgumentParser(description="Encode images with DINOv2 Giant or PE-Core G14 448")
    parser.add_argument("--model", choices=("dinov2", "pe-core"), required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "raw_images")
    parser.add_argument("--output", type=Path, help="Output .npz file")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=0)
    args = parser.parse_args()

    if args.batch_size < 1 or args.num_workers < 0:
        parser.error("--batch-size must be positive and --num-workers must be non-negative")
    if not args.input.is_dir():
        parser.error(f"input directory does not exist: {args.input}")
    paths = sorted(path for path in args.input.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    if not paths:
        parser.error(f"no supported images found in {args.input}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, preprocess = load_model(args.model, device)
    loader_options = {
        "batch_size": args.batch_size,
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
    }
    if args.num_workers > 0:
        loader_options.update(persistent_workers=True, prefetch_factor=2)
    loader = DataLoader(ImageDataset(paths, preprocess), **loader_options)
    output = args.output or ROOT / "data" / "embeddings" / f"{args.model}.npz"
    output.parent.mkdir(parents=True, exist_ok=True)
    use_cuda = device.type == "cuda"
    dtype = torch.bfloat16 if use_cuda and torch.cuda.is_bf16_supported() else torch.float16
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary_dir:
        embeddings = None
        offset = 0
        try:
            with torch.inference_mode():
                for images in tqdm(loader, desc="Encoding images"):
                    images = images.to(device, non_blocking=use_cuda)
                    with torch.autocast(device_type=device.type, dtype=dtype, enabled=use_cuda):
                        features = model.encode_image(images) if args.model == "pe-core" else model(images)
                    features = torch.nn.functional.normalize(features.float(), dim=-1).cpu().numpy()
                    if embeddings is None:
                        embeddings = np.lib.format.open_memmap(
                            Path(temporary_dir) / "embeddings.npy", mode="w+",
                            dtype=np.float32, shape=(len(paths), features.shape[-1]),
                        )
                    next_offset = offset + len(features)
                    embeddings[offset:next_offset] = features
                    offset = next_offset
            embeddings.flush()
            with output.open("wb") as file:
                np.savez(file, embeddings=embeddings, paths=np.array([path.relative_to(args.input).as_posix() for path in paths]))
        finally:
            if embeddings is not None:
                del embeddings
    print(f"Saved {len(paths)} embeddings to {output}")


if __name__ == "__main__":
    main()
