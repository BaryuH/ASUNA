from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.index import ImageIndex


def make_index(tmp_path, embeddings, paths):
    path = tmp_path / "index.npz"
    np.savez(path, embeddings=np.asarray(embeddings), paths=np.asarray(paths))
    return ImageIndex(path)


def test_cosine_ranking_and_scores(tmp_path):
    index = make_index(tmp_path, [[0, 10], [-2, 0], [3, 0], [1, 1]],
                       ["b.jpg", "c.jpg", "a.jpg", "d.jpg"])
    results = index.search(np.array([5, 0]), 4)
    assert [result["path"] for result in results] == ["a.jpg", "d.jpg", "b.jpg", "c.jpg"]
    assert [result["score"] for result in results] == pytest.approx([1, 2 ** -0.5, 0, -1])


def test_ties_across_top_k_boundary_follow_archive_order(tmp_path):
    index = make_index(tmp_path, [[1, 0], [0, 1], [1, 0], [1, 0]],
                       ["z.jpg", "other.jpg", "a.jpg", "b.jpg"])
    assert [r["path"] for r in index.search(np.array([1, 0]), 2)] == ["z.jpg", "a.jpg"]


def test_top_k_bounds_and_empty_index(tmp_path):
    index = make_index(tmp_path, [[1, 0]], ["one.jpg"])
    assert index.search(np.array([1, 0]), 0) == []
    assert len(index.search(np.array([1, 0]), 100)) == 1
    for value in (-1, 1.5, True, "1"):
        with pytest.raises(ValueError):
            index.search(np.array([1, 0]), value)
    empty = make_index(tmp_path, np.empty((0, 2)), np.array([], dtype="U1"))
    assert empty.search(np.array([1, 0]), 10) == []


@pytest.mark.parametrize("embeddings,paths", [
    ([1, 2], ["a.jpg"]),
    (np.empty((1, 0)), ["a.jpg"]),
    ([[1, 2]], ["a.jpg", "b.jpg"]),
    ([[1, 2]], [["a.jpg"]]),
    ([[1, 2]], [""]),
    ([[1, 2]], ["../a.jpg"]),
    ([[1, 2]], ["/a.jpg"]),
    ([[1, 2]], ["C:\\a.jpg"]),
    ([[1, 2]], ["dir\\..\\a.jpg"]),
    ([[0, 0]], ["a.jpg"]),
    ([[np.nan, 1]], ["a.jpg"]),
    ([[np.inf, 1]], ["a.jpg"]),
    ([[1 + 1j, 1]], ["a.jpg"]),
])
def test_invalid_archives(tmp_path, embeddings, paths):
    with pytest.raises(ValueError):
        make_index(tmp_path, embeddings, paths)


def test_pickle_paths_and_missing_keys_are_rejected(tmp_path):
    path = tmp_path / "index.npz"
    np.savez(path, embeddings=[[1, 0]], paths=np.array(["a.jpg"], dtype=object))
    with pytest.raises(ValueError):
        ImageIndex(path)
    np.savez(path, embeddings=[[1, 0]])
    with pytest.raises(ValueError):
        ImageIndex(path)


@pytest.mark.parametrize("vector", [
    [0, 0], [np.nan, 1], [np.inf, 1], [1], [1, 2, 3], [[1, 2]],
    [1 + 1j, 2], ["1", "2"],
])
def test_invalid_queries(tmp_path, vector):
    index = make_index(tmp_path, [[1, 0]], ["a.jpg"])
    with pytest.raises(ValueError):
        index.search(np.asarray(vector), 1)


def test_normalization_handles_extreme_finite_values(tmp_path):
    index = make_index(tmp_path, [[1e308, 1e308], [1e-300, 0]], ["large", "small"])
    results = index.search(np.array([1e308, 1e308]), 2)
    assert [r["path"] for r in results] == ["large", "small"]
    assert [r["score"] for r in results] == pytest.approx([1, 2 ** -0.5])
