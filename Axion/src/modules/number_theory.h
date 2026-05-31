#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <vector>

namespace axion {

// GCD and LCM (already have gcd_val in ast.h for int64_t)
int64_t lcm_val(int64_t a, int64_t b);

// Factorial (already exists in simplifier, but expose for combinatorics)
int64_t factorial_int(int64_t n);

// Binomial coefficient: binom(n, k) = n! / (k! * (n-k)!)
int64_t binom_val(int64_t n, int64_t k);

// Permutations: P(n, k) = n! / (n-k)!
int64_t perm_val(int64_t n, int64_t k);

// Integer factorization: returns list of (prime, exponent) pairs
std::vector<std::pair<int64_t, int64_t>> prime_factorize(int64_t n);

// Modular arithmetic: mod(a, m)
int64_t mod_val(int64_t a, int64_t m);

// Modular exponentiation: powmod(base, exp, mod)
int64_t powmod_val(int64_t base, int64_t exp, int64_t mod);

} // namespace axion
