#pragma once
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

// Fully expand an expression (distribute products, expand powers)
Expr* expand(Arena& arena, Expr* e);

} // namespace axion
