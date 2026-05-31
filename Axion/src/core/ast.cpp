#include "core/ast.h"

namespace axion {

Expr* make_num(Arena& a, double val) {
    auto* e = a.create<Expr>();
    e->type = NodeType::NUM;
    e->num = val;
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

} // namespace axion
