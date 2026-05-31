#pragma once
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

// Core algorithmic simplification (flattening, constant folding, like-term combination)
Expr* simplify(Arena& arena, Expr* e);

// Full simplification: algorithmic pass + builtin identity rules
Expr* simplify_full(Arena& arena, Expr* e);

} // namespace axion
