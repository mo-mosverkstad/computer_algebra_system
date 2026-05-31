#pragma once
#include <string>
#include <vector>
#include "core/arena.h"

namespace axion {

enum class NodeType {
    NUM,        // numeric literal (rational: num/den)
    SYM,        // variable symbol
    ADD,        // sum (n-ary)
    MUL,        // product (n-ary)
    POW,        // power (binary: base^exp)
    FUNC,       // function call: sin, cos, ln, etc.
    NEG,        // unary negation
    FACTORIAL,  // postfix factorial
    REL,        // relational: =, !=, <, >, <=, >=
};

struct Expr {
    NodeType type;
    // For NUM: represents num/den (rational)
    int64_t num = 0;
    int64_t den = 1;
    std::string name;                // SYM name, FUNC name, or REL operator
    std::vector<Expr*> children;     // operands

    bool is_num() const { return type == NodeType::NUM; }
    bool is_sym() const { return type == NodeType::SYM; }
    bool is_add() const { return type == NodeType::ADD; }
    bool is_mul() const { return type == NodeType::MUL; }
    bool is_pow() const { return type == NodeType::POW; }
    bool is_func() const { return type == NodeType::FUNC; }
    bool is_neg() const { return type == NodeType::NEG; }
    bool is_factorial() const { return type == NodeType::FACTORIAL; }
    bool is_rel() const { return type == NodeType::REL; }

    // Convenience: get numeric value as double
    double num_val() const { return static_cast<double>(num) / static_cast<double>(den); }
    // Check if integer
    bool is_integer() const { return is_num() && den == 1; }
};

// Factory functions
Expr* make_num(Arena& a, int64_t num, int64_t den = 1);
Expr* make_num_double(Arena& a, double val);
Expr* make_sym(Arena& a, const std::string& name);
Expr* make_add(Arena& a, std::vector<Expr*> terms);
Expr* make_mul(Arena& a, std::vector<Expr*> factors);
Expr* make_pow(Arena& a, Expr* base, Expr* exp);
Expr* make_func(Arena& a, const std::string& name, Expr* arg);
Expr* make_neg(Arena& a, Expr* operand);
Expr* make_factorial(Arena& a, Expr* operand);
Expr* make_rel(Arena& a, const std::string& op, Expr* left, Expr* right);

// Rational arithmetic helpers
int64_t gcd_val(int64_t a, int64_t b);
void reduce_fraction(int64_t& num, int64_t& den);

} // namespace axion
