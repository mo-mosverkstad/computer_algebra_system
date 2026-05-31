#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>

namespace axion {

Expr* differentiate(Arena& arena, Expr* e, const std::string& var);

} // namespace axion
