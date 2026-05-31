#pragma once
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

// Core algorithmic simplification (flattening, constant folding, like-term combination).
// Use for intermediate steps within tight loops where performance matters.
Expr* simplify(Arena& arena, Expr* e);

// Full simplification: algorithmic pass + declarative identity rules from rule table.
// Use at module boundaries and for user-facing results.
Expr* simplify_full(Arena& arena, Expr* e);

} // namespace axion
