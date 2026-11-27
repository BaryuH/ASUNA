"""Exact cosine retrieval using the native image-search kernel."""

import ctypes
from functools import lru_cache
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

import numpy as np


@lru_cache(maxsize=1)
def _native_search():
    name = "asuna_vector_search.dll" if sys.platform == "win32" else "libasuna_vector_search.dylib" if sys.platform == "darwin" else "libasuna_vector_search.so"
    build = Path(__file__).resolve().parents[1] / "native" / "build"
    configured = os.environ.get("ASUNA_SEARCH_LIBRARY")
    candidates = [Path(configured)] if configured else [build / name, build / "Release" / name]
    for path in candidates:
        if path.is_file():
            library = ctypes.CDLL(str(path))
            function = library.asuna_search
            pointer = ctypes.POINTER(ctypes.c_float)
            function.argtypes = [pointer, pointer, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
                                 ctypes.POINTER(ctypes.c_size_t), pointer]
            function.restype = ctypes.c_int
            return function
    raise RuntimeError("Native search library not found; build BE/native with CMake")

def _normalized(values: np.ndarray, axis: int) -> np.ndarray:
    """Normalize without overflowing or underflowing on finite inputs."""
    scale = np.max(np.abs(values), axis=axis, keepdims=True)
    if np.any(scale == 0):
        raise ValueError("embedding vectors must not be zero")
    values = values / scale
    return values / np.sqrt(np.sum(values * values, axis=axis, keepdims=True))


class ImageIndex:
    """Load an NPZ once and rank images by descending cosine similarity.

    Ties are resolved by original archive row order. A nonnegative ``top_k``
    larger than the number of images returns all images; zero returns none.
    """

    def __init__(self, path: Path):
        with np.load(path, allow_pickle=False) as archive:
            if not isinstance(archive, np.lib.npyio.NpzFile):
                raise ValueError("index must be an NPZ archive")
            if "embeddings" not in archive or "paths" not in archive:
                raise ValueError("index must contain embeddings and paths")
            embeddings = archive["embeddings"]
            paths = archive["paths"]

        if embeddings.ndim != 2 or embeddings.shape[1] == 0:
            raise ValueError("embeddings must have shape (images, dimensions) with positive dimensions")
        if embeddings.dtype.kind not in "fiu":
            raise ValueError("embeddings must be real numeric values")
        if paths.ndim != 1 or len(paths) != len(embeddings) or paths.dtype.kind != "U":
            raise ValueError("paths must be a one-dimensional string array matching embeddings")
        for value in paths:
            posix = PurePosixPath(value)
            windows = PureWindowsPath(value)
            if (not value or "\x00" in value or posix.is_absolute() or windows.is_absolute()
                    or windows.drive or ".." in posix.parts or ".." in windows.parts
                    or value in (".", "..")):
                raise ValueError("paths must be nonempty relative image paths")

        dtype = np.float64 if embeddings.dtype.kind == "f" and embeddings.dtype.itemsize > 4 else np.float32
        embeddings = np.asarray(embeddings, dtype=dtype, order="C")
        if not np.isfinite(embeddings).all():
            raise ValueError("embeddings must be finite")
        self._embeddings = np.ascontiguousarray(
            _normalized(embeddings, axis=1) if len(embeddings) else embeddings, dtype=np.float32
        )
        self._paths = paths.tolist()

    def search(self, vector: np.ndarray, top_k: int) -> list[dict]:
        if isinstance(top_k, (bool, np.bool_)) or not isinstance(top_k, (int, np.integer)) or top_k < 0:
            raise ValueError("top_k must be a nonnegative integer")
        vector = np.asarray(vector)
        if vector.ndim != 1 or vector.shape[0] != self._embeddings.shape[1]:
            raise ValueError("query must be a one-dimensional vector matching the index dimension")
        if vector.dtype.kind not in "fiu":
            raise ValueError("query must contain real numeric values")
        vector = np.asarray(vector, dtype=np.float64 if vector.dtype.itemsize > 4 else np.float32)
        if not np.isfinite(vector).all():
            raise ValueError("query must be finite")
        vector = np.ascontiguousarray(_normalized(vector, axis=0), dtype=np.float32)
        count = min(int(top_k), len(self._paths))
        if count == 0:
            return []

        ids = np.empty(count, dtype=np.uintp)
        scores = np.empty(count, dtype=np.float32)
        float_ptr = ctypes.POINTER(ctypes.c_float)
        status = _native_search()(
            self._embeddings.ctypes.data_as(float_ptr), vector.ctypes.data_as(float_ptr),
            len(self._paths), self._embeddings.shape[1], count,
            ids.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)), scores.ctypes.data_as(float_ptr),
        )
        if status:
            raise RuntimeError(f"Native search failed with code {status}")
        return [{"path": self._paths[index], "score": float(score)} for index, score in zip(ids, scores)]
