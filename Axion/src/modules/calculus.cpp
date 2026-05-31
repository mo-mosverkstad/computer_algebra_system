#include "modules/calculus.h"
#include "engine/simplify.h"

namespace axion {

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
                Expr* f_prime = differentiate(arena, base, var);
                return make_mul(arena, {
                    make_num(arena, exp->num, exp->den),
                    make_pow(arena, base, make_num(arena, exp->num - exp->den, exp->den)),
                    f_prime
                });
            }
            Expr* f = base;
            Expr* g = exp;
            Expr* f_prime = differentiate(arena, f, var);
            Expr* g_prime = differentiate(arena, g, var);
            return make_mul(arena, {
                e,
                make_add(arena, {
                    make_mul(arena, {g_prime, make_func(arena, "ln", f)}),
                    make_mul(arena, {g, f_prime, make_pow(arena, f, make_num(arena, -1))})
                })
            });
        }

        case NodeType::FUNC: {
            Expr* u = e->children[0];
            Expr* u_prime = differentiate(arena, u, var);
            Expr* outer_deriv = nullptr;

            if (e->name == "sin") outer_deriv = make_func(arena, "cos", u);
            else if (e->name == "cos") outer_deriv = make_neg(arena, make_func(arena, "sin", u));
            else if (e->name == "tan") outer_deriv = make_pow(arena, make_func(arena, "cos", u), make_num(arena, -2));
            else if (e->name == "ln") outer_deriv = make_pow(arena, u, make_num(arena, -1));
            else if (e->name == "exp") outer_deriv = e;
            else if (e->name == "sqrt") outer_deriv = make_pow(arena, make_mul(arena, {make_num(arena, 2), make_func(arena, "sqrt", u)}), make_num(arena, -1));
            else return make_num(arena, 0);

            return make_mul(arena, {outer_deriv, u_prime});
        }

        case NodeType::FACTORIAL:
        case NodeType::REL:
            return make_num(arena, 0);
    }
    return make_num(arena, 0);
}

} // namespace axion
