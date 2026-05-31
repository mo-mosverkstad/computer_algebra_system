#include "modules/polynomial.h"
#include "engine/simplify.h"
#include <cmath>

namespace axion {

namespace {

Expr* deep_copy(Arena& arena, const Expr* e) {
    if (!e) return nullptr;
    auto* n = arena.create<Expr>();
    n->type = e->type;
    n->num = e->num;
    n->den = e->den;
    n->name = e->name;
    for (auto* c : e->children)
        n->children.push_back(deep_copy(arena, c));
    return n;
}

Expr* mul_expand(Arena& arena, Expr* a, Expr* b) {
    std::vector<Expr*> a_terms, b_terms;
    if (a->is_add()) a_terms = a->children; else a_terms.push_back(a);
    if (b->is_add()) b_terms = b->children; else b_terms.push_back(b);

    std::vector<Expr*> result;
    for (auto* at : a_terms)
        for (auto* bt : b_terms)
            result.push_back(make_mul(arena, {at, bt}));

    if (result.size() == 1) return result[0];
    return make_add(arena, std::move(result));
}

} // anonymous namespace

Expr* expand(Arena& arena, Expr* e) {
    if (!e) return e;

    for (auto& child : e->children)
        child = expand(arena, child);

    if (e->is_pow()) {
        Expr* base = e->children[0];
        Expr* exp = e->children[1];
        if (exp->is_num() && exp->den == 1 && exp->num > 1 && exp->num <= 20
            && (base->is_add() || base->is_mul())) {
            int n = static_cast<int>(exp->num);
            Expr* result = deep_copy(arena, base);
            for (int i = 1; i < n; ++i) {
                result = mul_expand(arena, result, deep_copy(arena, base));
                result = simplify(arena, result);
            }
            return result;
        }
        return e;
    }

    if (e->is_mul()) {
        Expr* result = e->children[0];
        for (size_t i = 1; i < e->children.size(); ++i) {
            result = mul_expand(arena, result, e->children[i]);
            result = simplify(arena, result);
        }
        return result;
    }

    if (e->is_neg() && e->children[0]->is_add()) {
        std::vector<Expr*> terms;
        for (auto* t : e->children[0]->children)
            terms.push_back(make_neg(arena, t));
        return make_add(arena, std::move(terms));
    }

    return e;
}

} // namespace axion
