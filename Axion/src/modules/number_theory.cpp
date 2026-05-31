#include "modules/number_theory.h"
#include <cmath>

namespace axion {

int64_t lcm_val(int64_t a, int64_t b) {
    if (a == 0 || b == 0) return 0;
    return std::abs(a / gcd_val(a, b) * b);
}

int64_t factorial_int(int64_t n) {
    if (n < 0) return 0;
    int64_t r = 1;
    for (int64_t i = 2; i <= n; ++i) r *= i;
    return r;
}

int64_t binom_val(int64_t n, int64_t k) {
    if (k < 0 || k > n) return 0;
    if (k == 0 || k == n) return 1;
    if (k > n - k) k = n - k; // optimization
    int64_t r = 1;
    for (int64_t i = 0; i < k; ++i) {
        r = r * (n - i) / (i + 1);
    }
    return r;
}

int64_t perm_val(int64_t n, int64_t k) {
    if (k < 0 || k > n) return 0;
    int64_t r = 1;
    for (int64_t i = 0; i < k; ++i) r *= (n - i);
    return r;
}

std::vector<std::pair<int64_t, int64_t>> prime_factorize(int64_t n) {
    std::vector<std::pair<int64_t, int64_t>> factors;
    if (n <= 1) return factors;
    for (int64_t d = 2; d * d <= n; ++d) {
        if (n % d == 0) {
            int64_t count = 0;
            while (n % d == 0) { n /= d; ++count; }
            factors.push_back({d, count});
        }
    }
    if (n > 1) factors.push_back({n, 1});
    return factors;
}

int64_t mod_val(int64_t a, int64_t m) {
    int64_t r = a % m;
    return r < 0 ? r + m : r;
}

int64_t powmod_val(int64_t base, int64_t exp, int64_t mod) {
    if (mod == 1) return 0;
    int64_t result = 1;
    base = mod_val(base, mod);
    while (exp > 0) {
        if (exp % 2 == 1) result = (result * base) % mod;
        exp /= 2;
        base = (base * base) % mod;
    }
    return result;
}

} // namespace axion
