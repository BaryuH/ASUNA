# Backend Technology Stack

| Component | Technology | Role |
| --- | --- | --- |
| Language | Python 3.11.9 | Backend and data processing development |
| API | FastAPI 0.112.1, Uvicorn | HTTP API and interactive documentation at `/docs` |
| Configuration and data | Pydantic, pydantic-settings 2.4.0 | Data schemas and environment-based configuration |
| Deep learning | PyTorch 2.5.0, Hugging Face Transformers >=4.49,<5, OpenCLIP | Run image and text encoding models |
| Vector search | FAISS CPU 1.8.0 | Find similar embedding vectors |
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
