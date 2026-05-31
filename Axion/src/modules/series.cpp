#include "modules/series.h"
#include "engine/simplify.h"
#include <unordered_map>
#include <map>

namespace axion {

namespace {

// Substitute var=val in expression (deep copy with replacement)
Expr* subst_var(Arena& arena, const Expr* e, const std::string& var, Expr* val) {
    if (!e) return nullptr;
    if (e->is_sym() && e->name == var) return val;
    auto* n = arena.create<Expr>();
    n->type = e->type;
    n->num = e->num;
    n->den = e->den;
    n->name = e->name;
    for (auto* c : e->children)
        n->children.push_back(subst_var(arena, c, var, val));
    return n;
}

// Get power of var in a term (returns exponent, or -1 if not a power of var)
// x -> 1, x^2 -> 2, 3*x^2 -> 2, 5 -> 0, y -> -1 (different var)
int64_t get_var_power(const Expr* e, const std::string& var) {
    if (e->is_sym()) return (e->name == var) ? 1 : -1;
    if (e->is_num()) return 0;
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == var
        && e->children[1]->is_num() && e->children[1]->den == 1)
        return e->children[1]->num;
    if (e->is_mul()) {
        // Find the factor that is var or var^n
        for (auto* f : e->children) {
            int64_t p = get_var_power(f, var);
            if (p > 0) return p;
        }
        // All factors are constants or other vars
        bool has_var = false;
        for (auto* f : e->children) {
            if (f->is_sym() && f->name == var) { has_var = true; break; }
            if (f->is_pow() && f->children[0]->is_sym() && f->children[0]->name == var) { has_var = true; break; }
        }
        return has_var ? -1 : 0; // 0 means no var present
    }
    if (e->is_neg()) return get_var_power(e->children[0], var);
    return -1;
}

// Remove var^power factor from a term, returning the coefficient part
Expr* remove_var_factor(Arena& arena, Expr* e, const std::string& var) {
    if (e->is_sym() && e->name == var) return make_num(arena, 1);
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == var)
        return make_num(arena, 1);
    if (e->is_neg()) {
        Expr* inner = remove_var_factor(arena, e->children[0], var);
        return make_neg(arena, inner);
    }
    if (e->is_mul()) {
        std::vector<Expr*> remaining;
        bool removed = false;
        for (auto* f : e->children) {
            if (!removed && (
                (f->is_sym() && f->name == var) ||
                (f->is_pow() && f->children[0]->is_sym() && f->children[0]->name == var))) {
                removed = true;
                continue;
            }
            remaining.push_back(f);
        }
        if (remaining.empty()) return make_num(arena, 1);
        if (remaining.size() == 1) return remaining[0];
        return make_mul(arena, std::move(remaining));
    }
    return e;
}

} // anonymous namespace

Expr* eval_sum(Arena& arena, Expr* body, const std::string& var, int64_t lo, int64_t hi) {
    if (hi - lo > 10000) return nullptr; // safety limit

    std::vector<Expr*> terms;
    for (int64_t k = lo; k <= hi; ++k) {
        Expr* val = make_num(arena, k);
        Expr* term = subst_var(arena, body, var, val);
        term = simplify(arena, term);
        terms.push_back(term);
    }

    if (terms.empty()) return make_num(arena, 0);
    if (terms.size() == 1) return terms[0];

    Expr* result = make_add(arena, std::move(terms));
    return simplify(arena, result);
}

Expr* eval_prod(Arena& arena, Expr* body, const std::string& var, int64_t lo, int64_t hi) {
    if (hi - lo > 10000) return nullptr; // safety limit

    std::vector<Expr*> factors;
    for (int64_t k = lo; k <= hi; ++k) {
        Expr* val = make_num(arena, k);
        Expr* term = subst_var(arena, body, var, val);
        term = simplify(arena, term);
        factors.push_back(term);
    }

    if (factors.empty()) return make_num(arena, 1);
    if (factors.size() == 1) return factors[0];

    Expr* result = make_mul(arena, std::move(factors));
    return simplify(arena, result);
}

Expr* collect(Arena& arena, Expr* e, const std::string& var) {
    e = simplify(arena, e);
    if (!e->is_add()) return e;

    // Group terms by power of var
    // power -> list of coefficient expressions
    std::map<int64_t, std::vector<Expr*>> groups;

    for (auto* term : e->children) {
        int64_t p = get_var_power(term, var);
        if (p < 0) p = 0; // treat unknown structure as power 0
        if (p == 0) {
            groups[0].push_back(term);
        } else {
            Expr* coeff = remove_var_factor(arena, term, var);
            groups[p].push_back(coeff);
        }
    }

    // Rebuild: for each power, sum coefficients * var^power
    std::vector<Expr*> result_terms;
    for (auto& [power, coeffs] : groups) {
        Expr* coeff_sum;
        if (coeffs.size() == 1) coeff_sum = coeffs[0];
        else coeff_sum = simplify(arena, make_add(arena, std::move(coeffs)));

        if (power == 0) {
            result_terms.push_back(coeff_sum);
        } else {
            Expr* var_part;
            if (power == 1) var_part = make_sym(arena, var);
            else var_part = make_pow(arena, make_sym(arena, var), make_num(arena, power));

            if (coeff_sum->is_num() && coeff_sum->num == 1 && coeff_sum->den == 1)
                result_terms.push_back(var_part);
            else
                result_terms.push_back(make_mul(arena, {coeff_sum, var_part}));
        }
    }

    if (result_terms.empty()) return make_num(arena, 0);
    if (result_terms.size() == 1) return result_terms[0];
    return make_add(arena, std::move(result_terms));
}

} // namespace axion
