#include "modules/integration.h"
#include "engine/simplify.h"
#include "engine/rules.h"
#include "frontend/parser.h"
#include <cmath>
#include <functional>

namespace axion {

namespace {

Expr* subst_int(Arena& arena, const Expr* e, const std::string& var, Expr* val) {
    if (!e) return nullptr;
    if (e->is_sym() && e->name == var) return val;
    auto* n = arena.create<Expr>();
    n->type = e->type;
    n->num = e->num;
    n->den = e->den;
    n->name = e->name;
    for (auto* c : e->children)
        n->children.push_back(subst_int(arena, c, var, val));
    return n;
}

bool contains_var(const Expr* e, const std::string& var) {
    if (!e) return false;
    if (e->is_sym() && e->name == var) return true;
    for (auto* c : e->children)
        if (contains_var(c, var)) return true;
    return false;
}

bool is_var(const Expr* e, const std::string& var) {
    return e->is_sym() && e->name == var;
}

// Substitute _u with actual expression in an integration pattern
Expr* subst_u(Arena& arena, const std::string& pattern_str, Expr* u) {
    Expr* pat = parse(arena, pattern_str);
    std::function<Expr*(Expr*)> replace = [&](Expr* e) -> Expr* {
        if (e->is_sym() && e->name == "_u") return u;
        for (auto& c : e->children) c = replace(c);
        return e;
    };
    return replace(pat);
}

} // anonymous namespace

Expr* integrate(Arena& arena, Expr* e, const std::string& var) {
    e = simplify(arena, e);

    // Constant (no var): c → c*x
    if (!contains_var(e, var))
        return make_mul(arena, {e, make_sym(arena, var)});

    // x → x^2/2
    if (is_var(e, var))
        return make_mul(arena, {make_num(arena, 1, 2), make_pow(arena, make_sym(arena, var), make_num(arena, 2))});

    // e^x → e^x
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == "e" && is_var(e->children[1], var))
        return e;

    // e^(a*x) → e^(a*x)/a
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == "e"
        && e->children[1]->is_mul() && contains_var(e->children[1], var)) {
        auto* inner = e->children[1];
        std::vector<Expr*> consts;
        bool has_v = false;
        for (auto* f : inner->children) {
            if (is_var(f, var)) has_v = true;
            else consts.push_back(f);
        }
        if (has_v && !consts.empty()) {
            Expr* a = (consts.size() == 1) ? consts[0] : make_mul(arena, std::move(consts));
            return make_mul(arena, {make_pow(arena, a, make_num(arena, -1)), e});
        }
    }

    // x^n → x^(n+1)/(n+1)
    if (e->is_pow() && is_var(e->children[0], var) && e->children[1]->is_num()
        && !contains_var(e->children[1], var)) {
        int64_t n_num = e->children[1]->num;
        int64_t n_den = e->children[1]->den;
        int64_t new_n = n_num + n_den;
        int64_t new_d = n_den;
        reduce_fraction(new_n, new_d);
        if (new_n == 0)
            return make_func(arena, "ln", make_func(arena, "abs", make_sym(arena, var)));
        return make_mul(arena, {
            make_num(arena, new_d, new_n),
            make_pow(arena, make_sym(arena, var), make_num(arena, new_n, new_d))
        });
    }

    // Linearity: int(a + b) = int(a) + int(b)
    if (e->is_add()) {
        std::vector<Expr*> terms;
        for (auto* c : e->children) {
            Expr* t = integrate(arena, c, var);
            if (!t) return nullptr;
            terms.push_back(t);
        }
        return make_add(arena, std::move(terms));
    }

    // Constant multiple + product patterns
    if (e->is_mul()) {
        std::vector<Expr*> const_factors;
        std::vector<Expr*> var_factors;
        for (auto* f : e->children) {
            if (contains_var(f, var)) var_factors.push_back(f);
            else const_factors.push_back(f);
        }
        if (!const_factors.empty() && !var_factors.empty()) {
            Expr* var_part = (var_factors.size() == 1) ? var_factors[0] : make_mul(arena, std::move(var_factors));
            Expr* integral = integrate(arena, var_part, var);
            if (!integral) return nullptr;
            const_factors.push_back(integral);
            return make_mul(arena, std::move(const_factors));
        }
        // sin(x)*cos(x) pattern
        if (var_factors.size() == 2 || (const_factors.empty() && e->children.size() == 2)) {
            Expr* a = e->children.size() == 2 ? e->children[0] : var_factors[0];
            Expr* b = e->children.size() == 2 ? e->children[1] : var_factors[1];
            if (a->is_func() && b->is_func() && a->children[0]->is_sym() && b->children[0]->is_sym()) {
                bool sin_cos = (a->name == "sin" && b->name == "cos" && a->children[0]->name == b->children[0]->name && a->children[0]->name == var);
                bool cos_sin = (a->name == "cos" && b->name == "sin" && a->children[0]->name == b->children[0]->name && a->children[0]->name == var);
                if (sin_cos || cos_sin)
                    return make_mul(arena, {make_num(arena, 1, 2), make_pow(arena, make_func(arena, "sin", make_sym(arena, var)), make_num(arena, 2))});
            }
        }
    }

    // NEG: int(-f) = -int(f)
    if (e->is_neg()) {
        Expr* inner = integrate(arena, e->children[0], var);
        if (!inner) return nullptr;
        return make_neg(arena, inner);
    }

    // Table-based function integration: f(x) → antideriv from rule table
    if (e->is_func() && is_var(e->children[0], var)) {
        const IntRule* rule = get_rules().find_int(e->name);
        if (rule)
            return subst_u(arena, rule->antideriv, make_sym(arena, var));
    }

    // Linear substitution: f(a*x) → F(a*x)/a from rule table
    if (e->is_func() && e->children[0]->is_mul() && contains_var(e->children[0], var)) {
        auto* inner = e->children[0];
        std::vector<Expr*> consts;
        bool has_v = false;
        for (auto* f : inner->children) {
            if (is_var(f, var)) has_v = true;
            else consts.push_back(f);
        }
        if (has_v && !consts.empty()) {
            const IntRule* rule = get_rules().find_int(e->name);
            if (rule) {
                Expr* a = (consts.size() == 1) ? consts[0] : make_mul(arena, std::move(consts));
                Expr* antideriv = subst_u(arena, rule->antideriv, inner);
                return make_mul(arena, {make_pow(arena, a, make_num(arena, -1)), antideriv});
            }
        }
    }

    return nullptr;
}

Expr* integrate_definite(Arena& arena, Expr* e, const std::string& var, Expr* a, Expr* b) {
    Expr* antideriv = integrate(arena, e, var);
    if (!antideriv) return nullptr;
    antideriv = simplify_full(arena, antideriv);

    Expr* fb = subst_int(arena, antideriv, var, b);
    Expr* fa = subst_int(arena, antideriv, var, a);
    fb = simplify_full(arena, fb);
    fa = simplify_full(arena, fa);

    Expr* result = make_add(arena, {fb, make_neg(arena, fa)});
    return simplify_full(arena, result);
}

} // namespace axion
