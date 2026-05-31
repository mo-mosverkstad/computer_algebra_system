#pragma once
#include "core/ast.h"
#include <string>
#include <unordered_map>

namespace axion {

double evaluate(const Expr* e, const std::unordered_map<std::string, double>& env);

} // namespace axion
