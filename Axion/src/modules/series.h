#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>

namespace axion {

// Evaluate sum(expr, var, lower, upper)
Expr* eval_sum(Arena& arena, Expr* body, const std::string& var, int64_t lo, int64_t hi);

// Evaluate prod(expr, var, lower, upper)
Expr* eval_prod(Arena& arena, Expr* body, const std::string& var, int64_t lo, int64_t hi);

// Collect terms by powers of var: collect(expr, var)
Expr* collect(Arena& arena, Expr* e, const std::string& var);

} // namespace axion
