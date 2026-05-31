#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>

namespace axion {

// Compute lim(expr, var, point)
// direction: 0 = two-sided, 1 = right, -1 = left
Expr* compute_limit(Arena& arena, Expr* e, const std::string& var, Expr* point, int direction = 0);

} // namespace axion
