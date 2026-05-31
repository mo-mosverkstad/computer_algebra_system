#include "modules/rewrite.h"
#include "engine/simplify.h"
#include <algorithm>

namespace axion {

namespace {

bool is_wildcard(const Expr* e) {
    return e->is_sym() && !e->name.empty() && e->name[0] == '_';
}

// Check if wildcard has a type constraint: _name__type
// Returns the type ("num", "const", "") or empty for unconstrained
std::string wildcard_type(const Expr* e) {
    auto pos = e->name.find("__");
    if (pos == std::string::npos) return "";
    return e->name.substr(pos + 2);
}

// Get the binding name (without type suffix)
std::string wildcard_name(const Expr* e) {
    auto pos = e->name.find("__");
    if (pos == std::string::npos) return e->name;
    return e->name.substr(0, pos);
}

// Check if expression is a "rest" wildcard (matches remaining children)
bool is_rest_wildcard(const Expr* e) {
    return is_wildcard(e) && e->name == "_rest";
}

// Check type constraint
bool check_type_constraint(const Expr* expr, const std::string& type) {
    if (type.empty()) return true; // no constraint
    if (type == "num") return expr->is_num();
    if (type == "sym") return expr->is_sym();
    if (type == "func") return expr->is_func();
    // "const" would need variable context — skip for now
    return true;
}

bool expr_equal(const Expr* a, const Expr* b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    if (a->type != b->type) return false;
    if (a->is_num()) return a->num == b->num && a->den == b->den;
    if (a->is_sym()) return a->name == b->name;
    if (a->name != b->name) return false;
    if (a->children.size() != b->children.size()) return false;
    for (size_t i = 0; i < a->children.size(); ++i)
        if (!expr_equal(a->children[i], b->children[i])) return false;
    return true;
}

// Match commutative with support for _rest wildcard
bool match_commutative(Arena& arena, const std::vector<Expr*>& expr_children,
                       const std::vector<Expr*>& pat_children,
                       Bindings& bindings) {
    // Check for _rest wildcard in pattern
    int rest_idx = -1;
    for (size_t i = 0; i < pat_children.size(); ++i) {
        if (is_rest_wildcard(pat_children[i])) { rest_idx = static_cast<int>(i); break; }
    }

    if (rest_idx >= 0) {
        // Pattern has _rest: match non-rest patterns against some children,
        // bind _rest to the remaining children
        std::vector<const Expr*> fixed_pats;
        for (size_t i = 0; i < pat_children.size(); ++i)
            if (static_cast<int>(i) != rest_idx) fixed_pats.push_back(pat_children[i]);

        if (expr_children.size() < fixed_pats.size()) return false;

        size_t n_fixed = fixed_pats.size();
        size_t n_expr = expr_children.size();

        if (n_fixed == 0) {
            // _rest only: bind to entire expression
            Expr* rest_expr;
            if (n_expr == 1) rest_expr = expr_children[0];
            else rest_expr = make_add(const_cast<Arena&>(arena), std::vector<Expr*>(expr_children.begin(), expr_children.end()));
            Bindings trial = bindings;
            trial["_rest"] = rest_expr;
            bindings = trial;
            return true;
        }

        // Try to match fixed patterns against a subset of expr children
        // For 1 fixed pattern (most common): try each child
        if (n_fixed == 1) {
            for (size_t i = 0; i < n_expr; ++i) {
                Bindings trial = bindings;
                if (pattern_match(expr_children[i], fixed_pats[0], trial)) {
                    // Bind _rest to remaining children
                    std::vector<Expr*> rest;
                    for (size_t j = 0; j < n_expr; ++j)
                        if (j != i) rest.push_back(expr_children[j]);
                    Expr* rest_expr;
                    if (rest.empty()) rest_expr = make_num(const_cast<Arena&>(arena), 0);
                    else if (rest.size() == 1) rest_expr = rest[0];
                    else {
                        // Determine if parent is ADD or MUL from context
                        // For now, create ADD (most common for _rest in sums)
                        rest_expr = make_add(const_cast<Arena&>(arena), std::move(rest));
                    }
                    trial["_rest"] = rest_expr;
                    bindings = trial;
                    return true;
                }
            }
            return false;
        }

        // For 2 fixed patterns: try all pairs
        if (n_fixed == 2) {
            for (size_t i = 0; i < n_expr; ++i) {
                for (size_t j = 0; j < n_expr; ++j) {
                    if (i == j) continue;
                    Bindings trial = bindings;
                    bool m1 = pattern_match(expr_children[i], fixed_pats[0], trial);
                    bool m2 = m1 ? pattern_match(expr_children[j], fixed_pats[1], trial) : false;
                    if (m1 && m2) {
                        std::vector<Expr*> rest;
                        for (size_t k = 0; k < n_expr; ++k)
                            if (k != i && k != j) rest.push_back(expr_children[k]);
                        Expr* rest_expr;
                        if (rest.empty()) rest_expr = make_num(const_cast<Arena&>(arena), 0);
                        else if (rest.size() == 1) rest_expr = rest[0];
                        else rest_expr = make_add(const_cast<Arena&>(arena), std::move(rest));
                        trial["_rest"] = rest_expr;
                        bindings = trial;
                        return true;
                    }
                }
            }
            return false;
        }

        // General: 1 fixed (already handled above), fall through for 0 fixed
        return false;
    }

    // No _rest: standard commutative matching
    if (expr_children.size() != pat_children.size()) return false;

    // Try in order first
    Bindings trial = bindings;
    bool ok = true;
    for (size_t i = 0; i < pat_children.size(); ++i) {
        if (!pattern_match(expr_children[i], pat_children[i], trial)) { ok = false; break; }
    }
    if (ok) { bindings = trial; return true; }

    // For 2 children, try swapped
    if (pat_children.size() == 2) {
        trial = bindings;
        if (pattern_match(expr_children[0], pat_children[1], trial) &&
            pattern_match(expr_children[1], pat_children[0], trial)) {
            bindings = trial;
            return true;
        }
    }

    // For 3-4 children, try all permutations
    if (pat_children.size() <= 4) {
        std::vector<size_t> perm(pat_children.size());
        for (size_t i = 0; i < perm.size(); ++i) perm[i] = i;
        do {
            trial = bindings;
            bool all_match = true;
            for (size_t i = 0; i < perm.size(); ++i) {
                if (!pattern_match(expr_children[i], pat_children[perm[i]], trial)) {
                    all_match = false; break;
                }
            }
            if (all_match) { bindings = trial; return true; }
        } while (std::next_permutation(perm.begin(), perm.end()));
    }

    return false;
}

// Global arena reference for rest-matching (set during apply_rules)
static Arena* g_match_arena = nullptr;

} // anonymous namespace

bool pattern_match(const Expr* expr, const Expr* pattern, Bindings& bindings) {
    if (!expr || !pattern) return false;

    if (is_wildcard(pattern)) {
        std::string name = wildcard_name(pattern);
        std::string type = wildcard_type(pattern);

        // Check type constraint
        if (!check_type_constraint(expr, type)) return false;

        auto it = bindings.find(name);
        if (it != bindings.end()) return expr_equal(expr, it->second);
        bindings[name] = const_cast<Expr*>(expr);
        return true;
    }

    if (pattern->is_num())
        return expr->is_num() && expr->num == pattern->num && expr->den == pattern->den;

    if (pattern->is_sym())
        return expr->is_sym() && expr->name == pattern->name;

    if (expr->type != pattern->type) return false;
    if (expr->name != pattern->name) return false;

    if (expr->is_add() || expr->is_mul()) {
        static Arena fallback_arena;
        Arena& arena = g_match_arena ? *g_match_arena : fallback_arena;
        return match_commutative(arena, expr->children, pattern->children, bindings);
    }

    if (expr->children.size() != pattern->children.size()) return false;
    for (size_t i = 0; i < expr->children.size(); ++i) {
        if (!pattern_match(expr->children[i], pattern->children[i], bindings))
            return false;
    }
    return true;
}

Expr* apply_bindings(Arena& arena, const Expr* tmpl, const Bindings& bindings) {
    if (!tmpl) return nullptr;

    if (is_wildcard(tmpl)) {
        std::string name = wildcard_name(tmpl);
        auto it = bindings.find(name);
        if (it != bindings.end()) return it->second;
        return const_cast<Expr*>(tmpl);
    }

    auto* n = arena.create<Expr>();
    n->type = tmpl->type;
    n->num = tmpl->num;
    n->den = tmpl->den;
    n->name = tmpl->name;
    for (auto* c : tmpl->children)
        n->children.push_back(apply_bindings(arena, c, bindings));
    return n;
}

Expr* apply_rule(Arena& arena, Expr* expr, const RewriteRule& rule) {
    Bindings bindings;
    if (pattern_match(expr, rule.pattern, bindings))
        return apply_bindings(arena, rule.replacement, bindings);
    return nullptr;
}

Expr* apply_rule_recursive(Arena& arena, Expr* expr, const RewriteRule& rule) {
    Expr* result = apply_rule(arena, expr, rule);
    if (result) return result;

    bool changed = false;
    for (auto& child : expr->children) {
        Expr* new_child = apply_rule_recursive(arena, child, rule);
        if (new_child) { child = new_child; changed = true; }
    }
    return changed ? expr : nullptr;
}

Expr* apply_rules(Arena& arena, Expr* expr, const std::vector<RewriteRule>& rules, int max_iter) {
    g_match_arena = &arena;
    for (int iter = 0; iter < max_iter; ++iter) {
        bool changed = false;
        for (const auto& rule : rules) {
            Expr* result = apply_rule_recursive(arena, expr, rule);
            if (result) {
                expr = simplify(arena, result);
                changed = true;
                break;
            }
        }
        if (!changed) break;
    }
    g_match_arena = nullptr;
    return expr;
}

} // namespace axion
