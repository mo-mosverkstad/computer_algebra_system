#include <cstdint>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

std::vector<uint64_t> factorize(uint64_t factor_number) {
    std::vector<uint64_t> factors;

    while (factor_number % 2 == 0) {
        factors.push_back(2);
        factor_number /= 2;
    }

    for (uint64_t i = 3; i <= factor_number / i; i += 2) {
        while (factor_number % i == 0) {
            factors.push_back(i);
            factor_number /= i;
        }
    }

    if (factor_number > 1) {
        factors.push_back(factor_number);
    }

    return factors;
}

PYBIND11_MODULE(factor, m) {
    m.def("factorize", &factorize);
}