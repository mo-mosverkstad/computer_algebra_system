// factor_shim.cpp -- pybind11 bindings for the factorizer in factor.cpp.
#include <cstdint>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // converts std::vector<uint64_t> <-> Python list

namespace py = pybind11;

// Provided by factor.cpp, compiled as-is.
extern "C" std::vector<uint64_t> factorize(uint64_t n);

static std::vector<uint64_t> factorize_guarded(uint64_t n) {
    // 0 and 1 have no prime factors; guarding here keeps n == 0 from looping
    // forever inside the trial division in factor.cpp.
    if (n < 2) {
        return {};
    }
    return factorize(n);
}

PYBIND11_MODULE(factor_ext, m) {
    m.doc() = "naive trial division factorization implemented in C++";
    m.def("factorize", &factorize_guarded, py::arg("n"),
          "Return the prime factors of n (must fit in uint64) in ascending order.");
}
