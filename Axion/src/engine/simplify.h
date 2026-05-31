#pragma once
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

Expr* simplify(Arena& arena, Expr* e);

} // namespace axion
