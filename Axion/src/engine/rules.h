#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include "modules/rewrite.h"
#include <vector>
#include <string>
#include <unordered_map>

namespace axion {

// === Centralized Mathematical Knowledge ===
// All declarative rules live here. Modules read from these tables.

struct DiffRule {
    std::string func_name;     // "sin", "cos", "exp", "ln", "tan", "sqrt"
    std::string derivative;    // pattern for outer derivative: "cos(_u)", "-sin(_u)"
};

struct IntRule {
    std::string func_name;     // "sin", "cos", "exp"
    std::string antideriv;     // "-cos(_u)", "sin(_u)", "exp(_u)"
};

struct RuleTables {
    std::vector<RewriteRule> identities;   // simplification identities
    std::vector<DiffRule> diff_rules;      // differentiation table
    std::vector<IntRule> int_rules;        // integration table

    // Lookup helpers
    const DiffRule* find_diff(const std::string& func) const;
    const IntRule* find_int(const std::string& func) const;
};

// Global rule tables — initialized once, read by all modules
RuleTables& get_rules();
void init_rules(Arena& arena);

} // namespace axion
