#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>

namespace axion {

// Indefinite integral: integrate(expr, var)
Expr* integrate(Arena& arena, Expr* e, const std::string& var);

// Definite integral: integrate(expr, var, a, b) = F(b) - F(a)
Expr* integrate_definite(Arena& arena, Expr* e, const std::string& var, Expr* a, Expr* b);

} // namespace axion
