// Exact image-vector search using a bounded top-k heap.
// A single query is scored row by row without materializing similarities.
#include <algorithm>
#include <cstddef>
#include <limits>
#include <vector>

#if defined(_WIN32)
#define ASUNA_EXPORT extern "C" __declspec(dllexport)
#else
#define ASUNA_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {
struct Item {
    std::size_t id;
    float score;
};

// Better items compare before worse ones, so the heap root is the worst.
struct Better {
    bool operator()(const Item& a, const Item& b) const noexcept {
        if (a.score != b.score) return a.score > b.score;
        return a.id < b.id;
    }
};

float dot_product(const float* a, const float* b, std::size_t dims) noexcept {
    float sum = 0.0f;
    for (std::size_t i = 0; i < dims; ++i) sum += a[i] * b[i];
    return sum;
}
}

// Inputs are contiguous normalized float32 values. Returns 0 on success and
// -1 on invalid arguments or allocation failure; no exception crosses the ABI.
ASUNA_EXPORT int asuna_search(const float* matrix, const float* query,
                              std::size_t rows, std::size_t dims, std::size_t k,
                              std::size_t* ids, float* scores) noexcept {
    if (k > rows) return -1;
    if (k == 0) return 0;
    if (!ids || !scores || (dims && (!matrix || !query)) ||
        (dims && rows > std::numeric_limits<std::size_t>::max() / dims)) return -1;

    try {
        std::vector<Item> heap;
        heap.reserve(k);
        const Better better;
        for (std::size_t row = 0; row < rows; ++row) {
            const float score = dims ? dot_product(matrix + row * dims, query, dims) : 0.0f;
            const Item item{row, score};
            if (heap.size() < k) {
                heap.push_back(item);
                std::push_heap(heap.begin(), heap.end(), better);
            } else if (better(item, heap.front())) {
                std::pop_heap(heap.begin(), heap.end(), better);
                heap.back() = item;
                std::push_heap(heap.begin(), heap.end(), better);
            }
        }
        // Pop worst first and write backwards for descending score / ascending id.
        for (std::size_t i = k; i > 0; --i) {
            std::pop_heap(heap.begin(), heap.end(), better);
            ids[i - 1] = heap.back().id;
            scores[i - 1] = heap.back().score;
            heap.pop_back();
        }
        return 0;
    } catch (...) {
        return -1;
    }
}
