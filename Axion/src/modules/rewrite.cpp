#include "modules/rewrite.h"
#include "engine/simplify.h"
#include <algorithm>

namespace axion {

namespace {

bool is_wildcard(const Expr* e) {
    return e->is_sym() && !e->name.empty() && e->name[0] == '_';
}

// Deep structural equality check
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

// Match within commutative operations (ADD, MUL)
// Try all permutations of pattern children against expr children
bool match_commutative(const std::vector<Expr*>& expr_children,
                       const std::vector<Expr*>& pat_children,
                       Bindings& bindings) {
    if (expr_children.size() != pat_children.size()) return false;

    // Simple case: try matching in order first
    Bindings trial = bindings;
    bool ok = true;
    for (size_t i = 0; i < pat_children.size(); ++i) {
        if (!pattern_match(expr_children[i], pat_children[i], trial)) {
            ok = false;
            break;
        }
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

    // For 3+ children, try all permutations (expensive but correct)
    if (pat_children.size() <= 4) {
        std::vector<size_t> perm(pat_children.size());
        for (size_t i = 0; i < perm.size(); ++i) perm[i] = i;
        do {
            trial = bindings;
            bool all_match = true;
            for (size_t i = 0; i < perm.size(); ++i) {
                if (!pattern_match(expr_children[i], pat_children[perm[i]], trial)) {
                    all_match = false;
                    break;
                }
            }
            if (all_match) { bindings = trial; return true; }
        } while (std::next_permutation(perm.begin(), perm.end()));
    }

    return false;
}

} // anonymous namespace

bool pattern_match(const Expr* expr, const Expr* pattern, Bindings& bindings) {
    if (!expr || !pattern) return false;

    // Wildcard: matches anything
    if (is_wildcard(pattern)) {
        auto it = bindings.find(pattern->name);
        if (it != bindings.end()) {
            // Already bound: must match same expression
            return expr_equal(expr, it->second);
        }
        bindings[pattern->name] = const_cast<Expr*>(expr);
        return true;
    }

    // Number: exact match
    if (pattern->is_num()) {
        return expr->is_num() && expr->num == pattern->num && expr->den == pattern->den;
    }

    // Symbol: exact name match
    if (pattern->is_sym()) {
        return expr->is_sym() && expr->name == pattern->name;
    }

    // Must be same node type
    if (expr->type != pattern->type) return false;
    if (expr->name != pattern->name) return false;

    // ADD and MUL are commutative
    if (expr->is_add() || expr->is_mul()) {
        return match_commutative(expr->children, pattern->children, bindings);
    }

    // Other nodes: match children in order
    if (expr->children.size() != pattern->children.size()) return false;
    for (size_t i = 0; i < expr->children.size(); ++i) {
        if (!pattern_match(expr->children[i], pattern->children[i], bindings))
            return false;
    }
    return true;
}

Expr* apply_bindings(Arena& arena, const Expr* tmpl, const Bindings& bindings) {
    if (!tmpl) return nullptr;

    // If template is a wildcard, substitute
    if (is_wildcard(tmpl)) {
        auto it = bindings.find(tmpl->name);
        if (it != bindings.end()) return it->second;
        return const_cast<Expr*>(tmpl);
    }

    // Deep copy with substitution
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
    if (pattern_match(expr, rule.pattern, bindings)) {
        return apply_bindings(arena, rule.replacement, bindings);
    }
    return nullptr;
}

Expr* apply_rule_recursive(Arena& arena, Expr* expr, const RewriteRule& rule) {
    // Try at current node
    Expr* result = apply_rule(arena, expr, rule);
    if (result) return result;

    // Try in children
    bool changed = false;
    for (auto& child : expr->children) {
        Expr* new_child = apply_rule_recursive(arena, child, rule);
        if (new_child) {
            child = new_child;
            changed = true;
        }
    }
    return changed ? expr : nullptr;
}

Expr* apply_rules(Arena& arena, Expr* expr, const std::vector<RewriteRule>& rules, int max_iter) {
    for (int iter = 0; iter < max_iter; ++iter) {
        bool changed = false;
        for (const auto& rule : rules) {
            Expr* result = apply_rule_recursive(arena, expr, rule);
            if (result) {
                expr = simplify(arena, result);
                changed = true;
                break; // restart from first rule
            }
        }
        if (!changed) break;
    }
    return expr;
}

} // namespace axion
