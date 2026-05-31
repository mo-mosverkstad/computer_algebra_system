#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <string>
#include <vector>
#include <unordered_map>

namespace axion {

// A rewrite rule: pattern → replacement
// Wildcards in pattern: any symbol starting with '_' (e.g. _a, _b, _x)
struct RewriteRule {
    Expr* pattern;
    Expr* replacement;
    std::string name; // optional rule name
};

// Match context: provides active variable for _c__const / _v__hasvar constraints
struct MatchContext {
    std::string active_var;  // variable of interest (e.g. "x" for integration)
};

// Pattern matching: try to match expr against pattern, binding wildcards
using Bindings = std::unordered_map<std::string, Expr*>;

bool pattern_match(const Expr* expr, const Expr* pattern, Bindings& bindings);
bool pattern_match(const Expr* expr, const Expr* pattern, Bindings& bindings, const MatchContext& ctx);

// Apply substitution: replace wildcards in template with bound values
Expr* apply_bindings(Arena& arena, const Expr* tmpl, const Bindings& bindings);

// Try to apply a single rule to an expression (top-level only)
Expr* apply_rule(Arena& arena, Expr* expr, const RewriteRule& rule);

// Try to apply a rule recursively (at any subexpression)
Expr* apply_rule_recursive(Arena& arena, Expr* expr, const RewriteRule& rule);

// Apply all rules repeatedly until no more changes
Expr* apply_rules(Arena& arena, Expr* expr, const std::vector<RewriteRule>& rules, int max_iter = 100);

// Recognition function type: given an expression, try to produce a simpler form
// Returns nullptr if no recognition applies
using RecognitionFn = Expr* (*)(Arena& arena, Expr* expr);

// Apply recognition functions to an expression (recursive)
Expr* apply_recognizers(Arena& arena, Expr* expr, const std::vector<RecognitionFn>& fns);

} // namespace axion
