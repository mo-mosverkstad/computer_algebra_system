#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>
#include <vector>

namespace axion {

// Solve equation for variable. Returns list of solutions.
std::vector<Expr*> solve(Arena& arena, Expr* equation, const std::string& var);

// Solve system of linear equations. Equations as vector of REL nodes, vars as names.
// Returns map-like: vector of (var_name, value) pairs
std::vector<std::pair<std::string, Expr*>> solve_system(Arena& arena, std::vector<Expr*> equations, std::vector<std::string> vars);

// Solve linear inequality. Returns a description string or structured result.
// e.g. solve_ineq(2*x + 1 > 0, x) → x > -1/2
Expr* solve_inequality(Arena& arena, Expr* ineq, const std::string& var);

// Factor a polynomial expression
Expr* factor(Arena& arena, Expr* e, const std::string& var);

} // namespace axion
