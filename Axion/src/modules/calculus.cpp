#include "modules/calculus.h"
#include "engine/simplify.h"

namespace axion {

Expr* differentiate(Arena& arena, Expr* e, const std::string& var) {
    if (!e) return make_num(arena, 0);

    switch (e->type) {
        case NodeType::NUM:
            return make_num(arena, 0);

        case NodeType::SYM:
            return make_num(arena, e->name == var ? 1.0 : 0.0);

        case NodeType::NEG:
            return make_neg(arena, differentiate(arena, e->children[0], var));

        case NodeType::ADD: {
            // d/dx(a + b + ...) = a' + b' + ...
            std::vector<Expr*> terms;
            for (auto* c : e->children)
                terms.push_back(differentiate(arena, c, var));
            return make_add(arena, std::move(terms));
        }

        case NodeType::MUL: {
            // Product rule for n-ary: d/dx(f*g*h) = f'*g*h + f*g'*h + f*g*h'
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

            // Case: constant exponent — power rule + chain rule
            // d/dx(f^n) = n * f^(n-1) * f'
            if (exp->is_num()) {
                Expr* f_prime = differentiate(arena, base, var);
                return make_mul(arena, {
                    make_num(arena, exp->num),
                    make_pow(arena, base, make_num(arena, exp->num - 1)),
                    f_prime
                });
            }

            // General case: d/dx(f^g) = f^g * (g' * ln(f) + g * f'/f)
            Expr* f = base;
            Expr* g = exp;
            Expr* f_prime = differentiate(arena, f, var);
            Expr* g_prime = differentiate(arena, g, var);
            return make_mul(arena, {
                e, // f^g
                make_add(arena, {
                    make_mul(arena, {g_prime, make_func(arena, "ln", f)}),
                    make_mul(arena, {g, f_prime, make_pow(arena, f, make_num(arena, -1))})
                })
            });
        }

        case NodeType::FUNC: {
            // Chain rule: d/dx(func(u)) = func'(u) * u'
            Expr* u = e->children[0];
            Expr* u_prime = differentiate(arena, u, var);
            Expr* outer_deriv = nullptr;

            if (e->name == "sin") {
                outer_deriv = make_func(arena, "cos", u);
            } else if (e->name == "cos") {
                outer_deriv = make_neg(arena, make_func(arena, "sin", u));
            } else if (e->name == "tan") {
                // sec^2(u) = 1/cos^2(u)
                outer_deriv = make_pow(arena, make_func(arena, "cos", u), make_num(arena, -2));
            } else if (e->name == "ln") {
                outer_deriv = make_pow(arena, u, make_num(arena, -1));
            } else if (e->name == "log") {
                // log10(u): 1/(u*ln(10))
                outer_deriv = make_pow(arena,
                    make_mul(arena, {u, make_func(arena, "ln", make_num(arena, 10))}),
                    make_num(arena, -1));
            } else if (e->name == "exp") {
                outer_deriv = e; // d/dx(exp(u)) = exp(u)
            } else if (e->name == "sqrt") {
                // 1/(2*sqrt(u))
                outer_deriv = make_pow(arena,
                    make_mul(arena, {make_num(arena, 2), make_func(arena, "sqrt", u)}),
                    make_num(arena, -1));
            } else {
                // Unknown function — return as-is (cannot differentiate)
                return make_num(arena, 0);
            }

            return make_mul(arena, {outer_deriv, u_prime});
        }
    }

    return make_num(arena, 0);
}

} // namespace axion
