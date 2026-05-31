#include "modules/limits.h"
#include "engine/simplify.h"
#include "modules/calculus.h"
#include <cmath>
#include <unordered_map>

namespace axion {

namespace {

// Deep-copy with variable substitution
Expr* subst(Arena& arena, const Expr* e, const std::string& var, Expr* val) {
    if (!e) return nullptr;
    if (e->is_sym() && e->name == var) return val;
    auto* n = arena.create<Expr>();
    n->type = e->type;
    n->num = e->num;
    n->den = e->den;
    n->name = e->name;
    for (auto* c : e->children)
        n->children.push_back(subst(arena, c, var, val));
    return n;
}

bool is_zero(const Expr* e) {
    return e && e->is_num() && e->num == 0;
}

bool is_inf(const Expr* e) {
    return e && e->is_sym() && e->name == "inf";
}

bool is_neg_inf(const Expr* e) {
    return e && e->is_neg() && e->children[0]->is_sym() && e->children[0]->name == "inf";
}

// Try direct substitution
Expr* try_direct(Arena& arena, Expr* e, const std::string& var, Expr* point) {
    Expr* result = subst(arena, e, var, point);
    result = simplify(arena, result);
    // Valid if result doesn't contain the variable anymore and isn't division by zero
    // Check for den=0 (undefined)
    if (result->is_num() && result->den == 0) return nullptr;
    // If result still contains a 0-denominator somewhere, it's undefined
    // Otherwise accept any simplified result (number, symbol, function of constants)
    return result;
}

// Check if expression evaluates to 0 at point
bool eval_is_zero(Arena& arena, Expr* e, const std::string& var, Expr* point) {
    Expr* val = subst(arena, e, var, point);
    val = simplify(arena, val);
    return is_zero(val);
}

// L'Hôpital: if f/g → 0/0, try f'/g'
Expr* try_lhopital(Arena& arena, Expr* e, const std::string& var, Expr* point, int depth) {
    if (depth > 5) return nullptr; // prevent infinite recursion

    // Check if expression is a quotient: MUL(f, POW(g, -1))
    if (!e->is_mul()) return nullptr;

    Expr* numerator = nullptr;
    Expr* denominator = nullptr;

    // Find numerator and denominator in MUL
    std::vector<Expr*> num_factors, den_factors;
    for (auto* f : e->children) {
        if (f->is_pow() && f->children[1]->is_num() && f->children[1]->num < 0) {
            // This is 1/something
            Expr* base = f->children[0];
            int64_t exp_n = -f->children[1]->num;
            int64_t exp_d = f->children[1]->den;
            if (exp_n == 1 && exp_d == 1)
                den_factors.push_back(base);
            else
                den_factors.push_back(make_pow(arena, base, make_num(arena, exp_n, exp_d)));
        } else {
            num_factors.push_back(f);
        }
    }

    if (den_factors.empty()) return nullptr; // not a quotient

    if (num_factors.empty()) numerator = make_num(arena, 1);
    else if (num_factors.size() == 1) numerator = num_factors[0];
    else numerator = make_mul(arena, std::move(num_factors));

    if (den_factors.size() == 1) denominator = den_factors[0];
    else denominator = make_mul(arena, std::move(den_factors));

    // Check 0/0 form
    bool num_zero = eval_is_zero(arena, numerator, var, point);
    bool den_zero = eval_is_zero(arena, denominator, var, point);

    if (num_zero && den_zero) {
        // Apply L'Hôpital: lim f/g = lim f'/g'
        Expr* f_prime = differentiate(arena, numerator, var);
        f_prime = simplify(arena, f_prime);
        Expr* g_prime = differentiate(arena, denominator, var);
        g_prime = simplify(arena, g_prime);

        // Build f'/g'
        Expr* new_expr = make_mul(arena, {f_prime, make_pow(arena, g_prime, make_num(arena, -1))});
        new_expr = simplify(arena, new_expr);

        // Try direct substitution on the new expression
        Expr* result = try_direct(arena, new_expr, var, point);
        if (result) return result;

        // Recurse (might need L'Hôpital again)
        return try_lhopital(arena, new_expr, var, point, depth + 1);
    }

    return nullptr;
}

} // anonymous namespace

Expr* compute_limit(Arena& arena, Expr* e, const std::string& var, Expr* point, int direction) {
    (void)direction; // TODO: use for one-sided limits

    e = simplify(arena, e);

    // Handle limit at infinity
    if (is_inf(point) || is_neg_inf(point)) {
        return nullptr; // not yet fully implemented for inf
    }

    // Try L'Hôpital first (before direct substitution might give wrong 0)
    Expr* lhop = try_lhopital(arena, e, var, point, 0);
    if (lhop) return lhop;

    // Try direct substitution
    Expr* result = try_direct(arena, e, var, point);
    if (result) return result;

    // Fallback: return unevaluated
    return nullptr;
}

} // namespace axion
