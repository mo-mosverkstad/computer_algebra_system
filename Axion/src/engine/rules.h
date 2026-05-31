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

// Function evaluation at known values: func(arg_num/arg_den) → result
struct FuncEvalRule {
    std::string func_name;
    int64_t arg_num;           // argument numerator (0 for sin(0), 1 for ln(1))
    int64_t arg_den;           // argument denominator
    int64_t res_num;           // result numerator
    int64_t res_den;           // result denominator
    std::string res_sym;       // if non-empty, result is this symbol (e.g. "e" for exp(1))
};

// Function evaluation at symbolic args: func(sym) → result
struct FuncSymRule {
    std::string func_name;
    std::string arg_sym;       // argument symbol name (e.g. "pi", "e")
    int64_t res_num;
    int64_t res_den;
};

struct RuleTables {
    std::vector<RewriteRule> identities;   // simplification identities
    std::vector<DiffRule> diff_rules;      // differentiation table
    std::vector<IntRule> int_rules;        // integration table
    std::vector<RecognitionFn> recognizers; // backward pattern detectors
    std::vector<FuncEvalRule> func_eval;   // f(numeric) → value
    std::vector<FuncSymRule> func_sym;     // f(symbol) → value

    // Lookup helpers
    const DiffRule* find_diff(const std::string& func) const;
    const IntRule* find_int(const std::string& func) const;
};

// Global rule tables — initialized once, read by all modules
RuleTables& get_rules();
void init_rules(Arena& arena);

// Load additional rules from a file (returns number of rules loaded, -1 on error)
int load_rules_file(Arena& arena, const std::string& path);

// Strategy: try recognizers and pick shorter result if beneficial
Expr* simplify_smart(Arena& arena, Expr* expr);

} // namespace axion
