#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>
#include <vector>

namespace axion {

// Solve equation for variable. Returns list of solutions.
// Input: equation (REL node with "=") and variable name
std::vector<Expr*> solve(Arena& arena, Expr* equation, const std::string& var);

// Factor a polynomial expression
Expr* factor(Arena& arena, Expr* e, const std::string& var);

} // namespace axion
