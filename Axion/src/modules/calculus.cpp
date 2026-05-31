#include "modules/calculus.h"
#include "engine/simplify.h"
#include "engine/rules.h"
#include "frontend/parser.h"
#include <functional>

namespace axion {

namespace {

// Substitute _u with actual argument in a derivative pattern
Expr* subst_u(Arena& arena, const std::string& pattern_str, Expr* u) {
    // Parse the pattern, then replace _u with u
    Expr* pat = parse(arena, pattern_str);
    // Walk tree and replace _u
    std::function<Expr*(Expr*)> replace = [&](Expr* e) -> Expr* {
        if (e->is_sym() && e->name == "_u") return u;
        for (auto& c : e->children) c = replace(c);
        return e;
    };
    return replace(pat);
}

} // anonymous namespace

Expr* differentiate(Arena& arena, Expr* e, const std::string& var) {
    if (!e) return make_num(arena, 0);

    switch (e->type) {
        case NodeType::NUM:
            return make_num(arena, 0);

        case NodeType::SYM:
            return make_num(arena, e->name == var ? 1 : 0);

        case NodeType::NEG:
            return make_neg(arena, differentiate(arena, e->children[0], var));

        case NodeType::ADD: {
            std::vector<Expr*> terms;
            for (auto* c : e->children)
                terms.push_back(differentiate(arena, c, var));
            return make_add(arena, std::move(terms));
        }

        case NodeType::MUL: {
            // Product rule (n-ary)
            std::vector<Expr*> sum_terms;
            for (size_t i = 0; i < e->children.size(); ++i) {
                std::vector<Expr*> factors;
                for (size_t j = 0; j < e->children.size(); ++j) {
                    if (j == i)
                        factors.push_back(differentiate(arena, e->children[j], var));
                    else
                        factors.push_back(e->children[j]);
                }
                sum_terms.push_back(make_mul(arena, std::move(factors)));
            }
            return make_add(arena, std::move(sum_terms));
        }

        case NodeType::POW: {
            Expr* base = e->children[0];
            Expr* exp = e->children[1];
            if (exp->is_num()) {
                // Power rule + chain rule: d/dx f^n = n*f^(n-1)*f'
                Expr* f_prime = differentiate(arena, base, var);
                return make_mul(arena, {
                    make_num(arena, exp->num, exp->den),
                    make_pow(arena, base, make_num(arena, exp->num - exp->den, exp->den)),
                    f_prime
                });
            }
            // General: d/dx f^g = f^g * (g'*ln(f) + g*f'/f)
            Expr* f_prime = differentiate(arena, base, var);
            Expr* g_prime = differentiate(arena, exp, var);
            return make_mul(arena, {
                e,
                make_add(arena, {
                    make_mul(arena, {g_prime, make_func(arena, "ln", base)}),
                    make_mul(arena, {exp, f_prime, make_pow(arena, base, make_num(arena, -1))})
                })
            });
        }

        case NodeType::FUNC: {
            // Chain rule: d/dx f(u) = f'(u) * u'
            Expr* u = e->children[0];
            Expr* u_prime = differentiate(arena, u, var);

            // Look up derivative in rule table
            const DiffRule* rule = get_rules().find_diff(e->name);
            if (rule) {
                Expr* outer_deriv = subst_u(arena, rule->derivative, u);
                return make_mul(arena, {outer_deriv, u_prime});
            }

            // Unknown function — treat as constant
            return make_num(arena, 0);
        }

        case NodeType::FACTORIAL:
        case NodeType::REL:
            return make_num(arena, 0);
    }
    return make_num(arena, 0);
}

} // namespace axion
