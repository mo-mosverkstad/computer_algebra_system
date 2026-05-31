#pragma once
#include <string>
#include <vector>
#include "core/arena.h"

namespace axion {

enum class NodeType {
    NUM,    // numeric literal
    SYM,    // variable symbol
    ADD,    // sum (n-ary)
    MUL,    // product (n-ary)
    POW,    // power (binary: base^exp)
    FUNC,   // function call: sin, cos, ln, etc.
    NEG,    // unary negation
};

struct Expr {
    NodeType type;
    double num = 0.0;
    std::string name;                // SYM name or FUNC name
    std::vector<Expr*> children;     // operands

    bool is_num() const { return type == NodeType::NUM; }
    bool is_sym() const { return type == NodeType::SYM; }
    bool is_add() const { return type == NodeType::ADD; }
    bool is_mul() const { return type == NodeType::MUL; }
    bool is_pow() const { return type == NodeType::POW; }
    bool is_func() const { return type == NodeType::FUNC; }
    bool is_neg() const { return type == NodeType::NEG; }
};

// Factory functions (allocate on arena)
Expr* make_num(Arena& a, double val);
Expr* make_sym(Arena& a, const std::string& name);
Expr* make_add(Arena& a, std::vector<Expr*> terms);
Expr* make_mul(Arena& a, std::vector<Expr*> factors);
Expr* make_pow(Arena& a, Expr* base, Expr* exp);
Expr* make_func(Arena& a, const std::string& name, Expr* arg);
Expr* make_neg(Arena& a, Expr* operand);

} // namespace axion
