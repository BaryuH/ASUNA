from io import BytesIO
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app import main


class Encoder:
    def encode_text(self, query):
        return np.array([1.0, 0.0], dtype=np.float32)

    def encode_image(self, image):
        return np.array([0.0, 1.0], dtype=np.float32)


def test_text_and_image_search(tmp_path, monkeypatch):
    images = tmp_path / "images"
    embeddings = tmp_path / "embeddings"
    images.mkdir()
    embeddings.mkdir()
    (images / "one.png").write_bytes(b"sample")
    np.savez(embeddings / "pe-core.npz", embeddings=np.eye(2, dtype=np.float32), paths=np.array(["one.png", "two.png"]))
    monkeypatch.setattr(main, "IMAGE_ROOT", images)
    monkeypatch.setattr(main, "EMBEDDINGS_ROOT", embeddings)
    monkeypatch.setattr(main, "_indexes", {})
    monkeypatch.setattr(main, "_encoders", {"pe-core": Encoder()})
    client = TestClient(main.app)

    text = client.post("/search/text", json={"query": "tree pose", "top_k": 1})
    assert text.status_code == 200
    assert text.json()["results"][0]["path"] == "one.png"
    assert text.json()["results"][0]["image_url"] == "/images/one.png"
    monkeypatch.setattr(main, "PUBLIC_BASE_URL", "https://api.example.com/asuna")
    remote = client.post("/search/text", json={"query": "tree pose", "top_k": 1})
    assert remote.json()["results"][0]["image_url"] == "https://api.example.com/asuna/images/one.png"
    assert client.get("/images/one.png").content == b"sample"

    file = BytesIO()
    Image.new("RGB", (2, 2)).save(file, format="PNG")
    result = client.post("/search/image", files={"file": ("query.png", file.getvalue(), "image/png")}, data={"top_k": "1"})
    assert result.status_code == 200
    assert result.json()["results"][0]["path"] == "two.png"
    assert client.post("/search/text", json={"query": " ", "model": "pe-core"}).status_code == 422
    assert client.post("/search/text", json={"query": "pose", "model": "dinov2"}).status_code == 422
    assert client.post("/search/image", files={"file": ("bad.png", b"invalid", "image/png")}).status_code == 400


def test_missing_embeddings_returns_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "EMBEDDINGS_ROOT", tmp_path)
    monkeypatch.setattr(main, "_indexes", {})
    response = TestClient(main.app).post("/search/text", json={"query": "pose"})
    assert response.status_code == 503
