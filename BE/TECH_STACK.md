# Backend Technology Stack

| Component | Technology | Role |
| --- | --- | --- |
| Language | Python 3.11.9 | Backend and data processing development |
| API | FastAPI 0.112.1, Uvicorn | HTTP API and interactive documentation at `/docs` |
| Configuration and data | Pydantic, pydantic-settings 2.4.0 | Data schemas and environment-based configuration |
| Deep learning | PyTorch 2.5.0, Hugging Face Transformers >=4.49,<5, OpenCLIP | Run image and text encoding models |
| Vector search | C++ native kernel | Exact cosine similarity and bounded top-k ranking over image embeddings |
| Text search | Elasticsearch 8.7 with a Vietnamese analysis plugin | Index and search OCR and ASR transcript content |
| Data processing | NumPy 1.26.4, Pandas 2.2.3, Pillow 10.4.0 | Process vectors, tabular data, and images |
| AI integration | OpenAI API, HTTPX | Integrate language models and make HTTP requests |
| Deployment | Docker, Docker Compose, Conda | Package and run the backend and Elasticsearch |
| Acceleration | CUDA 12.4 for GPU environments; CPU supported | Run PyTorch on supported hardware |

## Conda Environment

The following environment is CPU-only. A GPU environment requires replacing the CPU-only PyTorch and FAISS packages with compatible GPU builds; CUDA 12.4 is not enabled by this file.

```yaml
name: py311
channels:
  - pytorch
  - conda-forge
  - anaconda
dependencies:
  - python=3.11.9
  - pip=24.2
  - gdown=5.2.0
  - pytorch=2.5.0
  - torchaudio=2.5.0
  - torchvision=0.20.0
  - cpuonly=2.0
  - faiss-cpu=1.8.0
  # - faiss-gpu=1.8.0
  - pandas=2.2.3
  - timm
  - open-clip-torch
  - tqdm=4.66.5
  - numpy=1.26.4
  - pillow=10.4.0
  - transformers>=4.49,<5
  - sentencepiece
  - protobuf
  # - matplotlib
  - fastapi=0.112.1
  - pydantic-settings=2.4.0
  - fuzzywuzzy=0.18.0
  - joblib=1.4.2
  - openai
  - httpx
  - openblas
  - openmp
  - cmake
  - pip:
      # - salesforce-lavis==1.0.2
      # - timm==1.0.9
      - elasticsearch==8.15.0
      # - numpy==1.26.4
```

The Elasticsearch server version above is 8.7; `elasticsearch==8.15.0` is the Python client version. Uvicorn is part of the selected stack but is not listed in the supplied Conda environment.

## Image retrieval API

The C++ flat-search kernel scans normalized image vectors and maintains a bounded top-k heap without materializing a score array. Ties use archive order. It operates on independent images; temporal and prefix search are not included.

Create a Python 3.11 environment, install `BE/requirements.txt`, build the native library with CMake and a C++ compiler, and generate embeddings with `processing/encode_images.py`. Run from the repository root:

```bash
python -m pip install -r BE/requirements.txt
cmake -S BE/native -B BE/native/build -DCMAKE_BUILD_TYPE=Release
cmake --build BE/native/build --config Release
uvicorn app.main:app --app-dir BE --host 127.0.0.1 --port 8000
```

- `POST /search/text`: JSON such as `{"query":"tree pose","model":"pe-core","top_k":5}`.
- `POST /search/image`: multipart form with `file`, optional `model` (`pe-core` or `dinov2`), and `top_k`.
- `GET /images/{path}`: serve an image relative to the configured image root.
- `GET /health`: report available embedding files; `/docs` provides interactive API documentation.

The default input paths are `data/raw_images/` and `data/embeddings/{model}.npz`; set `ASUNA_IMAGE_ROOT` and `ASUNA_EMBEDDINGS_ROOT` to override them. Set `ASUNA_DEVICE` to `auto`, `cpu`, or a PyTorch CUDA device, and `ASUNA_CORS_ORIGINS` to a comma-separated list of allowed browser origins. Models and indexes are loaded on first use; the first request can download large model weights. Run one Uvicorn worker unless there is sufficient memory for a separate model and index per worker.

The C++ library is loaded from `BE/native/build` (or its `Release` subdirectory). Set `ASUNA_SEARCH_LIBRARY` to override its path. It is required; the API returns an error rather than silently switching search engines.

Each `.npz` must be generated with the exact matching encoder and preprocessing, not merely a matching vector dimension. Text search requires PE-Core's text encoder; DINOv2 supports image queries only. The API reports a missing or incompatible index instead of substituting results. Restart the server after changing embeddings or image paths.

## Remote deployment with Docker

Install Docker Engine and Compose on the backend server. Place the generated `.npz` files and their matching image files on that server; they are mounted read-only and are not copied into the image. The default host paths are `data/embeddings/` and `data/raw_images/` at the repository root; both directories must exist before starting Compose.

```bash
docker compose -f BE/docker-compose.yml up -d --build
docker compose -f BE/docker-compose.yml logs -f backend
```

By default the API binds to `127.0.0.1:8000` on the server. For a remote frontend, place it behind an HTTPS reverse proxy and set these environment variables on the server before starting Compose:

```bash
export ASUNA_CORS_ORIGINS=https://frontend.example.com
export ASUNA_PUBLIC_BASE_URL=https://api.example.com
docker compose -f BE/docker-compose.yml up -d --build
```

`ASUNA_PUBLIC_BASE_URL` is the externally reachable API base URL, including any reverse-proxy path prefix. Search responses contain absolute `image_url` values when it is set; otherwise they contain `/images/...` paths that clients resolve against the API origin. Configure the proxy to route `/search`, `/images`, `/health`, and `/docs` to port 8000. `ASUNA_IMAGES_DIR`, `ASUNA_EMBEDDINGS_DIR`, `ASUNA_BIND_HOST`, and `ASUNA_PORT` override host paths and binding.

For NVIDIA GPUs, install the NVIDIA driver and NVIDIA Container Toolkit on the server, and use Docker Compose 2.30 or newer:

```bash
docker compose -f BE/docker-compose.yml -f BE/docker-compose.gpu.yml up -d --build
```

The container caches downloaded model weights in a named Docker volume. The first request loads the selected model and index; `/health` is a process liveness check, not proof that weights and embeddings are ready.

**Security:** the API has no authentication or rate limiting, and `/images/` serves files under the configured image directory. Keep the port private and add authentication, TLS, and access controls at the reverse proxy before exposing it publicly. The frontend must call this backend explicitly; changing the server deployment alone does not connect the current preview UI.
