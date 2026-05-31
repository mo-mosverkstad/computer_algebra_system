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
    // Reject if result contains division by zero
    if (result->is_num() && result->den == 0) return nullptr;
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
    e = simplify(arena, e);

    // Handle limit at infinity: substitute increasingly large values and detect trend
    if (is_inf(point) || is_neg_inf(point)) {
        // Evaluate at large values to detect: converges to constant, diverges to ±inf, or oscillates
        double sign = is_neg_inf(point) ? -1.0 : 1.0;
        double vals[3];
        double test_points[] = {1000.0, 10000.0, 100000.0};
        bool all_valid = true;

        for (int i = 0; i < 3; ++i) {
            Expr* big = make_num(arena, static_cast<int64_t>(sign * test_points[i]));
            Expr* substituted = subst(arena, e, var, big);
            substituted = simplify(arena, substituted);
            if (!substituted->is_num()) { all_valid = false; break; }
            vals[i] = substituted->num_val();
        }

        if (all_valid) {
            // Check convergence
            double diff1 = std::abs(vals[1] - vals[0]);
            double diff2 = std::abs(vals[2] - vals[1]);
            double abs_val = std::abs(vals[2]);
            // Converging if differences are shrinking and value is bounded
            if (diff2 < diff1 * 0.5 && abs_val < 1e10) {
                // Converging — try to get exact rational
                Expr* big = make_num(arena, static_cast<int64_t>(sign * 1000000));
                Expr* result = subst(arena, e, var, big);
                result = simplify(arena, result);
                if (result->is_num()) {
                    // Round to nearest simple fraction if close
                    double v = result->num_val();
                    // Check if it's close to a simple integer or fraction
                    for (int64_t d = 1; d <= 100; ++d) {
                        double n = v * d;
                        if (std::abs(n - std::round(n)) < 1e-4) {
                            return make_num(arena, static_cast<int64_t>(std::round(n)), d);
                        }
                    }
                }
                return result;
            }
            // Check divergence to +inf or -inf
            if (vals[2] > vals[1] && vals[1] > vals[0] && std::abs(vals[2]) > 1e8) {
                return make_sym(arena, "inf");
            }
            if (vals[2] < vals[1] && vals[1] < vals[0] && vals[2] < -1e8) {
                return make_neg(arena, make_sym(arena, "inf"));
            }
        }
        return nullptr;
    }

    // Finite point: try L'Hôpital first (for 0/0 forms)
    Expr* lhop = try_lhopital(arena, e, var, point, 0);
    if (lhop) return lhop;

    // Try direct substitution
    Expr* result = try_direct(arena, e, var, point);
    if (result) return result;

    // Direct substitution failed (likely division by zero)
    // For one-sided limits, probe to determine sign of divergence
    if (direction != 0 && point->is_num()) {
        double pt_val = point->num_val();
        double probe_offset = (direction > 0) ? 0.001 : -0.001;
        int64_t probe_n = static_cast<int64_t>((pt_val + probe_offset) * 1000);
        Expr* probe = make_num(arena, probe_n, 1000);
        Expr* probed = subst(arena, e, var, probe);
        probed = simplify(arena, probed);
        if (probed->is_num() && probed->den != 0) {
            if (probed->num > 0) return make_sym(arena, "inf");
            if (probed->num < 0) return make_neg(arena, make_sym(arena, "inf"));
        }
    }

    return nullptr;
}

} // namespace axion
