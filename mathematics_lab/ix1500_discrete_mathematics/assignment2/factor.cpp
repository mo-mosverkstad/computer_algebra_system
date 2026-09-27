#include <cstdint>
#include <cstddef>
#include <vector>

extern "C" {

// naive trial division
std::vector<uint64_t> factorize(uint64_t n) {
    std::vector<uint64_t> factors;
    while (n % 2 == 0) {
        factors.push_back(2);
        n /= 2;
    }
    for (uint64_t i = 3; i <= n / i; i += 2) {
        while (n % i == 0) {
            factors.push_back(i);
            n /= i;
        }
    }
    if (n > 1) {
        factors.push_back(n);
    }
    return factors;
}

}