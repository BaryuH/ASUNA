"""Model encoders compatible with the precomputed image embeddings."""

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


class ImageEncoder:
    """Encode queries in the same feature space as the image index."""

    def __init__(self, model_name: str, device: str = "auto"):
        if model_name not in {"pe-core", "dinov2"}:
            raise ValueError(f"Unsupported model: {model_name}")

        self.model_name = model_name
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        ) if device == "auto" else torch.device(device)
        self.tokenizer = None

        if model_name == "pe-core":
            import open_clip

            model_id = "hf-hub:timm/PE-Core-bigG-14-448"
            model, _, self.preprocess = open_clip.create_model_and_transforms(model_id)
            self.tokenizer = open_clip.get_tokenizer(model_id)
        else:
            model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitg14")
            self.preprocess = transforms.Compose([
                transforms.Resize(518, interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.CenterCrop(518),
                transforms.ToTensor(),
                transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
            ])

        self.model = model.eval().to(self.device)
        self.use_cuda = self.device.type == "cuda"
        self.dtype = (
            torch.bfloat16
            if self.use_cuda and torch.cuda.is_bf16_supported()
            else torch.float16
        )

    @torch.inference_mode()
    def encode_image(self, image: Image.Image) -> np.ndarray:
        batch = self.preprocess(image.convert("RGB")).unsqueeze(0).to(self.device)
        with torch.autocast(device_type=self.device.type, dtype=self.dtype, enabled=self.use_cuda):
            features = (
                self.model.encode_image(batch)
                if self.model_name == "pe-core"
                else self.model(batch)
            )
        return torch.nn.functional.normalize(features.float(), dim=-1)[0].cpu().numpy()

    @torch.inference_mode()
    def encode_text(self, text: str) -> np.ndarray:
        if self.tokenizer is None:
            raise ValueError("DINOv2 does not support text encoding")
        tokens = self.tokenizer([text], context_length=self.model.context_length).to(self.device)
        with torch.autocast(device_type=self.device.type, dtype=self.dtype, enabled=self.use_cuda):
            features = self.model.encode_text(tokens)
        return torch.nn.functional.normalize(features.float(), dim=-1)[0].cpu().numpy()
