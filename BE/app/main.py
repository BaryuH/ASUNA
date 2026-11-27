"""HTTP API for text-to-image and image-to-image retrieval."""

from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Literal
from urllib.parse import quote
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from .encoder import ImageEncoder
from .index import ImageIndex

ROOT = Path(__file__).resolve().parents[2]
IMAGE_ROOT = Path(os.environ.get("ASUNA_IMAGE_ROOT", ROOT / "data" / "raw_images")).resolve()
EMBEDDINGS_ROOT = Path(os.environ.get("ASUNA_EMBEDDINGS_ROOT", ROOT / "data" / "embeddings")).resolve()
DEVICE = os.environ.get("ASUNA_DEVICE", "auto")
PUBLIC_BASE_URL = os.environ.get("ASUNA_PUBLIC_BASE_URL", "").strip().rstrip("/")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
Model = Literal["pe-core", "dinov2"]

app = FastAPI(title="ASUNA Image Retrieval")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get("ASUNA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class TextQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    model: Literal["pe-core"] = "pe-core"
    top_k: int = Field(default=20, ge=1, le=1000)


class SearchResult(BaseModel):
    path: str
    score: float
    image_url: str


class SearchResponse(BaseModel):
    model: Model
    results: list[SearchResult]


# Serialize model initialization and inference: GPU memory and OpenCLIP models
# are shared by all requests in this process.
_lock = Lock()
_encoders: dict[str, ImageEncoder] = {}
_indexes: dict[str, ImageIndex] = {}


def _get_index(model: Model) -> ImageIndex:
    if model not in _indexes:
        path = EMBEDDINGS_ROOT / f"{model}.npz"
        if not path.is_file():
            raise HTTPException(status_code=503, detail=f"Embeddings not found for {model}: {path}")
        try:
            _indexes[model] = ImageIndex(path)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=f"Cannot load {model} embeddings: {exc}") from exc
    return _indexes[model]


def _get_encoder(model: Model) -> ImageEncoder:
    if model not in _encoders:
        try:
            _encoders[model] = ImageEncoder(model, device=DEVICE)
        except (OSError, RuntimeError, ImportError) as exc:
            raise HTTPException(status_code=503, detail=f"Cannot load {model} encoder: {exc}") from exc
    return _encoders[model]


def _response(model: Model, index: ImageIndex, vector, top_k: int) -> SearchResponse:
    try:
        matches = index.search(vector, top_k)
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail=f"Search unavailable: {exc}") from exc
    return SearchResponse(model=model, results=[
        SearchResult(path=match["path"], score=match["score"], image_url=f"{PUBLIC_BASE_URL}/images/{quote(match['path'], safe='/')}")
        for match in matches
    ])


@app.get("/health")
def health():
    return {"status": "ok", "available_indexes": [model for model in ("pe-core", "dinov2") if (EMBEDDINGS_ROOT / f"{model}.npz").is_file()]}


@app.post("/search/text", response_model=SearchResponse)
def search_text(request: TextQuery):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query must not be blank")
    with _lock:
        index = _get_index(request.model)
        vector = _get_encoder(request.model).encode_text(query)
        return _response(request.model, index, vector, request.top_k)


@app.post("/search/image", response_model=SearchResponse)
def search_image(file: UploadFile = File(...), model: Model = Form("pe-core"), top_k: int = Form(20, ge=1, le=1000)):
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MiB")
    try:
        with Image.open(BytesIO(data)) as image:
            image = image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc
    with _lock:
        index = _get_index(model)
        vector = _get_encoder(model).encode_image(image)
        return _response(model, index, vector, top_k)


@app.get("/images/{image_path:path}")
def get_image(image_path: str):
    path = (IMAGE_ROOT / image_path).resolve()
    if not path.is_relative_to(IMAGE_ROOT) or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)
