FROM python:3.11-slim AS native-build

RUN apt-get update && apt-get install -y --no-install-recommends cmake g++ \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY native/ ./native/
RUN cmake -S native -B native/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build native/build --config Release

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/asuna/.cache/huggingface \
    TORCH_HOME=/home/asuna/.cache/torch \
    ASUNA_IMAGE_ROOT=/data/raw_images \
    ASUNA_EMBEDDINGS_ROOT=/data/embeddings \
    ASUNA_SEARCH_LIBRARY=/app/native/libasuna_vector_search.so

WORKDIR /app
COPY requirements.txt .
# CUDA-enabled PyTorch wheels also support CPU execution. GPU use requires an NVIDIA driver and container toolkit on the host.
RUN pip install --no-cache-dir torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124 \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 asuna \
    && mkdir -p /home/asuna/.cache && chown asuna:asuna /home/asuna/.cache
COPY --from=native-build /build/native/build/libasuna_vector_search.so /app/native/libasuna_vector_search.so
COPY app/ /app/app/
USER asuna
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
