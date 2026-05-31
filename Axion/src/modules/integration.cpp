#include "modules/integration.h"
#include "engine/simplify.h"
#include <cmath>

namespace axion {

namespace {

// Deep-copy with variable substitution
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

// Check if expression contains variable
bool contains_var(const Expr* e, const std::string& var) {
    if (!e) return false;
    if (e->is_sym() && e->name == var) return true;
    for (auto* c : e->children)
        if (contains_var(c, var)) return true;
    return false;
}

// Check if expression is just the variable
bool is_var(const Expr* e, const std::string& var) {
    return e->is_sym() && e->name == var;
}

} // anonymous namespace

Expr* integrate(Arena& arena, Expr* e, const std::string& var) {
    e = simplify(arena, e);

    // Constant (no var): c → c*x
    if (!contains_var(e, var)) {
        return make_mul(arena, {e, make_sym(arena, var)});
    }

    // x → x^2/2
    if (is_var(e, var)) {
        return make_mul(arena, {make_num(arena, 1, 2), make_pow(arena, make_sym(arena, var), make_num(arena, 2))});
    }

    // e^x → e^x (same as exp(x))
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == "e"
        && is_var(e->children[1], var)) {
        return e;
    }

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

    // x^n → x^(n+1)/(n+1) for n != -1
    if (e->is_pow() && is_var(e->children[0], var) && e->children[1]->is_num()
        && !contains_var(e->children[1], var)) {
        int64_t n_num = e->children[1]->num;
        int64_t n_den = e->children[1]->den;
        // n+1
        int64_t new_n = n_num + n_den;
        int64_t new_d = n_den;
        reduce_fraction(new_n, new_d);
        if (new_n == 0) {
            // n = -1: integral of x^-1 = ln|x|
            return make_func(arena, "ln", make_func(arena, "abs", make_sym(arena, var)));
        }
        // x^(n+1) / (n+1)
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
            if (!t) return nullptr; // can't integrate a term
            terms.push_back(t);
        }
        return make_add(arena, std::move(terms));
    }

    // Constant multiple: int(c*f) = c*int(f)
    if (e->is_mul()) {
        std::vector<Expr*> const_factors;
        std::vector<Expr*> var_factors;
        for (auto* f : e->children) {
            if (contains_var(f, var))
                var_factors.push_back(f);
            else
                const_factors.push_back(f);
        }
        if (!const_factors.empty() && !var_factors.empty()) {
            Expr* var_part;
            if (var_factors.size() == 1) var_part = var_factors[0];
            else var_part = make_mul(arena, std::move(var_factors));

            Expr* integral = integrate(arena, var_part, var);
            if (!integral) return nullptr;

            const_factors.push_back(integral);
            return make_mul(arena, std::move(const_factors));
        }
        // Product of var-dependent factors: try known patterns
        if (var_factors.size() == 2 || (const_factors.empty() && e->children.size() == 2)) {
            Expr* a = e->children.size() == 2 ? e->children[0] : var_factors[0];
            Expr* b = e->children.size() == 2 ? e->children[1] : var_factors[1];
            // sin(u)*cos(u) → sin(u)^2 / 2
            if (a->is_func() && b->is_func() && a->children[0]->is_sym() && b->children[0]->is_sym()) {
                bool sin_cos = (a->name == "sin" && b->name == "cos"
                    && a->children[0]->name == b->children[0]->name
                    && a->children[0]->name == var);
                bool cos_sin = (a->name == "cos" && b->name == "sin"
                    && a->children[0]->name == b->children[0]->name
                    && a->children[0]->name == var);
                if (sin_cos || cos_sin) {
                    // ∫sin(x)cos(x)dx = sin(x)^2 / 2
                    return make_mul(arena, {
                        make_num(arena, 1, 2),
                        make_pow(arena, make_func(arena, "sin", make_sym(arena, var)), make_num(arena, 2))
                    });
                }
            }
        }
    }

    // NEG: int(-f) = -int(f)
    if (e->is_neg()) {
        Expr* inner = integrate(arena, e->children[0], var);
        if (!inner) return nullptr;
        return make_neg(arena, inner);
    }

    // sin(x) → -cos(x)
    if (e->is_func() && e->name == "sin" && is_var(e->children[0], var)) {
        return make_neg(arena, make_func(arena, "cos", make_sym(arena, var)));
    }

    // cos(x) → sin(x)
    if (e->is_func() && e->name == "cos" && is_var(e->children[0], var)) {
        return make_func(arena, "sin", make_sym(arena, var));
    }

    // exp(x) → exp(x)
    if (e->is_func() && e->name == "exp" && is_var(e->children[0], var)) {
        return make_func(arena, "exp", make_sym(arena, var));
    }

    // 1/x = x^-1 → ln|x| (handled by power rule above)

    // sin(a*x) → -cos(a*x)/a (linear substitution)
    if (e->is_func() && e->name == "sin" && e->children[0]->is_mul()) {
        auto* inner = e->children[0];
        std::vector<Expr*> consts;
        bool has_var = false;
        for (auto* f : inner->children) {
            if (is_var(f, var)) has_var = true;
            else consts.push_back(f);
        }
        if (has_var && !consts.empty()) {
            Expr* a = (consts.size() == 1) ? consts[0] : make_mul(arena, std::move(consts));
            return make_mul(arena, {
                make_pow(arena, a, make_num(arena, -1)),
                make_neg(arena, make_func(arena, "cos", inner))
            });
        }
    }

    // cos(a*x) → sin(a*x)/a
    if (e->is_func() && e->name == "cos" && e->children[0]->is_mul()) {
        auto* inner = e->children[0];
        std::vector<Expr*> consts;
        bool has_var = false;
        for (auto* f : inner->children) {
            if (is_var(f, var)) has_var = true;
            else consts.push_back(f);
        }
        if (has_var && !consts.empty()) {
            Expr* a = (consts.size() == 1) ? consts[0] : make_mul(arena, std::move(consts));
            return make_mul(arena, {
                make_pow(arena, a, make_num(arena, -1)),
                make_func(arena, "sin", inner)
            });
        }
    }

    // exp(a*x) → exp(a*x)/a
    if (e->is_func() && e->name == "exp" && e->children[0]->is_mul()) {
        auto* inner = e->children[0];
        std::vector<Expr*> consts;
        bool has_var = false;
        for (auto* f : inner->children) {
            if (is_var(f, var)) has_var = true;
            else consts.push_back(f);
        }
        if (has_var && !consts.empty()) {
            Expr* a = (consts.size() == 1) ? consts[0] : make_mul(arena, std::move(consts));
            return make_mul(arena, {
                make_pow(arena, a, make_num(arena, -1)),
                make_func(arena, "exp", inner)
            });
        }
    }

    // Cannot integrate
    return nullptr;
}

Expr* integrate_definite(Arena& arena, Expr* e, const std::string& var, Expr* a, Expr* b) {
    Expr* antideriv = integrate(arena, e, var);
    if (!antideriv) return nullptr;
    antideriv = simplify(arena, antideriv);

    // F(b) - F(a)
    Expr* fb = subst_int(arena, antideriv, var, b);
    Expr* fa = subst_int(arena, antideriv, var, a);
    fb = simplify(arena, fb);
    fa = simplify(arena, fa);

    Expr* result = make_add(arena, {fb, make_neg(arena, fa)});
    return simplify(arena, result);
}

} // namespace axion
