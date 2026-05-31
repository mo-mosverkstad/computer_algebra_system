#include "engine/simplify.h"
#include <algorithm>
#include <cmath>
#include <unordered_map>

namespace axion {

namespace {

// Canonical ordering key for sorting children
int type_order(const Expr* e) {
    switch (e->type) {
        case NodeType::NUM: return 0;
        case NodeType::SYM: return 1;
        case NodeType::FUNC: return 2;
        case NodeType::POW: return 3;
        case NodeType::MUL: return 4;
        case NodeType::ADD: return 5;
        case NodeType::NEG: return 6;
    }
    return 9;
}

bool expr_less(const Expr* a, const Expr* b) {
    int oa = type_order(a), ob = type_order(b);
    if (oa != ob) return oa < ob;
    if (a->type == NodeType::NUM) return a->num < b->num;
    if (a->type == NodeType::SYM) return a->name < b->name;
    return false; // don't reorder complex expressions beyond type
}

// Get the "base" and "exponent" of a term for combining like terms
// x -> (x, 1), x^2 -> (x, 2), 3*x -> base is x
struct TermKey {
    std::string repr; // simplified key for grouping
};

// For like-term combination in ADD: extract coefficient and base
// e.g. 3*x -> coeff=3, base=x
//      x   -> coeff=1, base=x
//      -x  -> coeff=-1, base=x
//      2*x^2 -> coeff=2, base=x^2
struct CoeffTerm {
    double coeff;
    Expr* base; // the non-numeric part
};

// Simple string key for an expression (for grouping like terms)
std::string expr_key(const Expr* e) {
    if (!e) return "";
    switch (e->type) {
        case NodeType::NUM: return "N" + std::to_string(e->num);
        case NodeType::SYM: return "S" + e->name;
        case NodeType::POW:
            return "P(" + expr_key(e->children[0]) + "," + expr_key(e->children[1]) + ")";
        case NodeType::FUNC:
            return "F" + e->name + "(" + expr_key(e->children[0]) + ")";
        case NodeType::MUL: {
            std::string s = "M(";
            for (size_t i = 0; i < e->children.size(); ++i) {
                if (i) s += ",";
                s += expr_key(e->children[i]);
            }
            return s + ")";
        }
        case NodeType::ADD: {
            std::string s = "A(";
            for (size_t i = 0; i < e->children.size(); ++i) {
                if (i) s += ",";
                s += expr_key(e->children[i]);
            }
            return s + ")";
        }
        case NodeType::NEG:
            return "NEG(" + expr_key(e->children[0]) + ")";
    }
    return "?";
}

CoeffTerm extract_coeff(Expr* e) {
    if (e->is_neg()) {
        auto inner = extract_coeff(e->children[0]);
        return {-inner.coeff, inner.base};
    }
    if (e->is_mul() && !e->children.empty() && e->children[0]->is_num()) {
        double c = e->children[0]->num;
        if (e->children.size() == 2) {
            return {c, e->children[1]};
        }
        // Multiple non-numeric factors: base is a MUL of children[1:]
        // Reuse the existing node but shift children
        // We build a fake Expr on the arena would be ideal but we don't have arena here
        // Instead, modify in place: remove the numeric child, return coeff separately
        // Safe because simplify owns this tree
        Expr* base = e;
        base->children.erase(base->children.begin());
        if (base->children.size() == 1) return {c, base->children[0]};
        return {c, base};
    }
    if (e->is_num()) {
        return {e->num, nullptr}; // pure number
    }
    return {1.0, e};
}

} // anonymous namespace

Expr* simplify(Arena& arena, Expr* e) {
    if (!e) return e;

    // Recursively simplify children first
    for (auto& child : e->children) {
        child = simplify(arena, child);
    }

    // NEG simplification
    if (e->is_neg()) {
        Expr* inner = e->children[0];
        if (inner->is_num()) return make_num(arena, -inner->num);
        if (inner->is_neg()) return inner->children[0]; // --x = x
        // Keep as NEG for clean output
        return e;
    }

    // ADD simplification
    if (e->is_add()) {
        // Flatten nested ADDs
        std::vector<Expr*> terms;
        for (auto* child : e->children) {
            if (child->is_add()) {
                for (auto* gc : child->children)
                    terms.push_back(gc);
            } else {
                terms.push_back(child);
            }
        }

        // Combine like terms
        // Group by base expression, sum coefficients
        struct Group { double coeff; Expr* base; };
        std::vector<Group> groups;
        double num_sum = 0.0;

        for (auto* t : terms) {
            CoeffTerm ct = extract_coeff(t);
            if (!ct.base) {
                num_sum += ct.coeff;
            } else {
                // Find existing group
                bool found = false;
                std::string key = expr_key(ct.base);
                for (auto& g : groups) {
                    if (expr_key(g.base) == key) {
                        g.coeff += ct.coeff;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    groups.push_back({ct.coeff, ct.base});
                }
            }
        }

        // Rebuild terms
        std::vector<Expr*> result;
        for (auto& g : groups) {
            if (g.coeff == 0.0) continue;
            if (g.coeff == 1.0) {
                result.push_back(g.base);
            } else if (g.coeff == -1.0) {
                result.push_back(make_neg(arena, g.base));
            } else {
                result.push_back(make_mul(arena, {make_num(arena, g.coeff), g.base}));
            }
        }
        if (num_sum != 0.0 || result.empty()) {
            result.insert(result.begin(), make_num(arena, num_sum));
        }

        // Sort canonically
        std::sort(result.begin(), result.end(), expr_less);

        if (result.size() == 1) return result[0];
        return make_add(arena, std::move(result));
    }

    // MUL simplification
    if (e->is_mul()) {
        // Flatten nested MULs
        std::vector<Expr*> factors;
        for (auto* child : e->children) {
            if (child->is_mul()) {
                for (auto* gc : child->children)
                    factors.push_back(gc);
            } else {
                factors.push_back(child);
            }
        }

        // Combine numeric factors
        double num_prod = 1.0;
        std::vector<Expr*> non_num;
        for (auto* f : factors) {
            if (f->is_num()) {
                num_prod *= f->num;
            } else if (f->is_neg()) {
                // Flatten NEG inside MUL: x * (-y) = -(x*y)
                num_prod *= -1.0;
                non_num.push_back(f->children[0]);
            } else {
                non_num.push_back(f);
            }
        }

        // x * 0 = 0
        if (num_prod == 0.0) return make_num(arena, 0.0);

        // Collect like bases into powers: x*x -> x^2, x*x^2 -> x^3
        struct BasePow { Expr* base; double exp; };
        std::vector<BasePow> collected;
        for (auto* f : non_num) {
            Expr* b = f;
            double e_val = 1.0;
            if (f->is_pow() && f->children[1]->is_num()) {
                b = f->children[0];
                e_val = f->children[1]->num;
            }
            std::string k = expr_key(b);
            bool found = false;
            for (auto& bp : collected) {
                if (expr_key(bp.base) == k) {
                    bp.exp += e_val;
                    found = true;
                    break;
                }
            }
            if (!found) {
                collected.push_back({b, e_val});
            }
        }

        // Rebuild non-numeric factors from collected powers
        non_num.clear();
        for (auto& bp : collected) {
            if (bp.exp == 0.0) continue;
            if (bp.exp == 1.0) {
                non_num.push_back(bp.base);
            } else {
                non_num.push_back(make_pow(arena, bp.base, make_num(arena, bp.exp)));
            }
        }

        // Rebuild
        std::vector<Expr*> result;
        if (num_prod != 1.0 || non_num.empty()) {
            result.push_back(make_num(arena, num_prod));
        }
        for (auto* f : non_num) result.push_back(f);

        // Sort non-numeric factors
        std::sort(result.begin() + (result.empty() || !result[0]->is_num() ? 0 : 1),
                  result.end(), expr_less);

        if (result.size() == 1) return result[0];

        // Convert MUL(-1, x) to NEG(x)
        if (result.size() == 2 && result[0]->is_num() && result[0]->num == -1.0) {
            return make_neg(arena, result[1]);
        }

        return make_mul(arena, std::move(result));
    }

    // POW simplification
    if (e->is_pow()) {
        Expr* base = e->children[0];
        Expr* exp = e->children[1];
        if (exp->is_num()) {
            if (exp->num == 0.0) return make_num(arena, 1.0);
            if (exp->num == 1.0) return base;
            if (base->is_num()) return make_num(arena, std::pow(base->num, exp->num));
        }
        return e;
    }

    // FUNC with numeric arg
    if (e->is_func() && e->children[0]->is_num()) {
        double v = e->children[0]->num;
        if (e->name == "sin") return make_num(arena, std::sin(v));
        if (e->name == "cos") return make_num(arena, std::cos(v));
        if (e->name == "tan") return make_num(arena, std::tan(v));
        if (e->name == "ln")  return make_num(arena, std::log(v));
        if (e->name == "log") return make_num(arena, std::log10(v));
        if (e->name == "exp") return make_num(arena, std::exp(v));
        if (e->name == "sqrt") return make_num(arena, std::sqrt(v));
        if (e->name == "abs") return make_num(arena, std::fabs(v));
    }

    return e;
}

} // namespace axion
