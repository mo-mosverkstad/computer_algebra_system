#pragma once
#include <string>
#include <vector>
#include "core/ast.h"
#include "core/arena.h"

namespace axion {

Expr* parse(Arena& arena, const std::string& input);
bool has_assignment(const std::string& input);

struct AssignResult {
    std::string name;
    std::vector<std::string> params;
    Expr* value;
};

AssignResult parse_assignment(Arena& arena, const std::string& input);

} // namespace axion
