#include "core/ast.h"
#include <cmath>
#include <algorithm>

namespace axion {

int64_t gcd_val(int64_t a, int64_t b) {
    a = std::abs(a); b = std::abs(b);
    while (b) { a %= b; std::swap(a, b); }
    return a;
}

void reduce_fraction(int64_t& num, int64_t& den) {
    if (den < 0) { num = -num; den = -den; }
    if (num == 0) { den = 1; return; }
    int64_t g = gcd_val(num, den);
    num /= g; den /= g;
}

Expr* make_num(Arena& a, int64_t n, int64_t d) {
    auto* e = a.create<Expr>();
    e->type = NodeType::NUM;
    e->num = n; e->den = d;
    reduce_fraction(e->num, e->den);
    return e;
}

Expr* make_num_double(Arena& a, double val) {
    // Try to convert to rational if it's an integer or simple fraction
    if (val == std::floor(val) && std::abs(val) < 1e15) {
        return make_num(a, static_cast<int64_t>(val), 1);
    }
    // For non-integer doubles, store as large fraction approximation
    // Check common fractions
    for (int64_t d = 1; d <= 1000; ++d) {
        double n = val * d;
        if (std::abs(n - std::round(n)) < 1e-9) {
            return make_num(a, static_cast<int64_t>(std::round(n)), d);
        }
    }
    // Fallback: store as integer * 10^-precision
    auto* e = a.create<Expr>();
    e->type = NodeType::NUM;
    e->num = static_cast<int64_t>(val * 1000000);
    e->den = 1000000;
    reduce_fraction(e->num, e->den);
    return e;
}

Expr* make_sym(Arena& a, const std::string& name) {
    auto* e = a.create<Expr>();
    e->type = NodeType::SYM;
    e->name = name;
    return e;
}

Expr* make_add(Arena& a, std::vector<Expr*> terms) {
    auto* e = a.create<Expr>();
    e->type = NodeType::ADD;
    e->children = std::move(terms);
    return e;
}

Expr* make_mul(Arena& a, std::vector<Expr*> factors) {
    auto* e = a.create<Expr>();
    e->type = NodeType::MUL;
    e->children = std::move(factors);
    return e;
}

Expr* make_pow(Arena& a, Expr* base, Expr* exp) {
    auto* e = a.create<Expr>();
    e->type = NodeType::POW;
    e->children = {base, exp};
    return e;
}

Expr* make_func(Arena& a, const std::string& name, Expr* arg) {
    auto* e = a.create<Expr>();
    e->type = NodeType::FUNC;
    e->name = name;
    e->children = {arg};
    return e;
}

Expr* make_neg(Arena& a, Expr* operand) {
    auto* e = a.create<Expr>();
    e->type = NodeType::NEG;
    e->children = {operand};
    return e;
}

Expr* make_factorial(Arena& a, Expr* operand) {
    auto* e = a.create<Expr>();
    e->type = NodeType::FACTORIAL;
    e->children = {operand};
    return e;
}

Expr* make_rel(Arena& a, const std::string& op, Expr* left, Expr* right) {
    auto* e = a.create<Expr>();
    e->type = NodeType::REL;
    e->name = op;
    e->children = {left, right};
    return e;
}

} // namespace axion
