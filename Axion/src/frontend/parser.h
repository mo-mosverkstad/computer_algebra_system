#pragma once
#include <string>
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

Expr* parse(Arena& arena, const std::string& input);

} // namespace axion
