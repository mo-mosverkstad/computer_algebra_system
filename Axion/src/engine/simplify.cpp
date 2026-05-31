#include "engine/simplify.h"
#include <algorithm>
#include <cmath>

namespace axion {

namespace {

int type_order(const Expr* e) {
    switch (e->type) {
        case NodeType::NUM: return 0;
        case NodeType::SYM: return 1;
        case NodeType::FUNC: return 2;
        case NodeType::POW: return 3;
        case NodeType::MUL: return 4;
        case NodeType::ADD: return 5;
        case NodeType::NEG: return 6;
        case NodeType::FACTORIAL: return 7;
        case NodeType::REL: return 8;
    }
    return 9;
}

bool expr_less(const Expr* a, const Expr* b) {
    int oa = type_order(a), ob = type_order(b);
    if (oa != ob) return oa < ob;
    if (a->is_num()) return a->num_val() < b->num_val();
    if (a->is_sym()) return a->name < b->name;
    return false;
}

std::string expr_key(const Expr* e) {
    if (!e) return "";
    switch (e->type) {
        case NodeType::NUM: return "N" + std::to_string(e->num) + "/" + std::to_string(e->den);
        case NodeType::SYM: return "S" + e->name;
        case NodeType::POW:
            return "P(" + expr_key(e->children[0]) + "," + expr_key(e->children[1]) + ")";
        case NodeType::FUNC: {
            std::string s = "F" + e->name + "(";
            for (size_t i = 0; i < e->children.size(); ++i) {
                if (i) s += ",";
                s += expr_key(e->children[i]);
            }
            return s + ")";
        }
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
        case NodeType::NEG: return "NEG(" + expr_key(e->children[0]) + ")";
        case NodeType::FACTORIAL: return "FACT(" + expr_key(e->children[0]) + ")";
        case NodeType::REL: return "REL(" + e->name + "," + expr_key(e->children[0]) + "," + expr_key(e->children[1]) + ")";
    }
    return "?";
}

struct CoeffTerm { int64_t coeff_num; int64_t coeff_den; Expr* base; };

CoeffTerm extract_coeff(Expr* e) {
    if (e->is_neg()) {
        auto inner = extract_coeff(e->children[0]);
        return {-inner.coeff_num, inner.coeff_den, inner.base};
    }
    if (e->is_mul() && !e->children.empty() && e->children[0]->is_num()) {
        int64_t cn = e->children[0]->num;
        int64_t cd = e->children[0]->den;
        if (e->children.size() == 2) {
            return {cn, cd, e->children[1]};
        }
        e->children.erase(e->children.begin());
        if (e->children.size() == 1) return {cn, cd, e->children[0]};
        return {cn, cd, e};
    }
    if (e->is_num()) {
        return {e->num, e->den, nullptr};
    }
    return {1, 1, e};
}

int64_t factorial_val(int64_t n) {
    if (n < 0) return 0;
    int64_t r = 1;
    for (int64_t i = 2; i <= n; ++i) r *= i;
    return r;
}

} // anonymous namespace

Expr* simplify(Arena& arena, Expr* e) {
    if (!e) return e;

    for (auto& child : e->children)
        child = simplify(arena, child);

    // NEG
    if (e->is_neg()) {
        Expr* inner = e->children[0];
        if (inner->is_num()) return make_num(arena, -inner->num, inner->den);
        if (inner->is_neg()) return inner->children[0];
        return e;
    }

    // FACTORIAL
    if (e->is_factorial()) {
        Expr* inner = e->children[0];
        if (inner->is_num() && inner->den == 1 && inner->num >= 0 && inner->num <= 20) {
            return make_num(arena, factorial_val(inner->num));
        }
        return e;
    }

    // REL — simplify both sides but keep structure
    if (e->is_rel()) return e;

    // ADD
    if (e->is_add()) {
        std::vector<Expr*> terms;
        for (auto* child : e->children) {
            if (child->is_add()) {
                for (auto* gc : child->children) terms.push_back(gc);
            } else {
                terms.push_back(child);
            }
        }

        struct Group { int64_t cn; int64_t cd; Expr* base; };
        std::vector<Group> groups;
        int64_t num_n = 0, num_d = 1;

        for (auto* t : terms) {
            CoeffTerm ct = extract_coeff(t);
            if (!ct.base) {
                // Add fractions: num_n/num_d + ct.coeff_num/ct.coeff_den
                num_n = num_n * ct.coeff_den + ct.coeff_num * num_d;
                num_d = num_d * ct.coeff_den;
                reduce_fraction(num_n, num_d);
            } else {
                std::string key = expr_key(ct.base);
                bool found = false;
                for (auto& g : groups) {
                    if (expr_key(g.base) == key) {
                        g.cn = g.cn * ct.coeff_den + ct.coeff_num * g.cd;
                        g.cd = g.cd * ct.coeff_den;
                        reduce_fraction(g.cn, g.cd);
                        found = true;
                        break;
                    }
                }
                if (!found) groups.push_back({ct.coeff_num, ct.coeff_den, ct.base});
            }
        }

        std::vector<Expr*> result;
        for (auto& g : groups) {
            if (g.cn == 0) continue;
            if (g.cn == 1 && g.cd == 1) result.push_back(g.base);
            else if (g.cn == -1 && g.cd == 1) result.push_back(make_neg(arena, g.base));
            else result.push_back(make_mul(arena, {make_num(arena, g.cn, g.cd), g.base}));
        }
        if (num_n != 0 || result.empty())
            result.insert(result.begin(), make_num(arena, num_n, num_d));

        std::sort(result.begin(), result.end(), expr_less);
        if (result.size() == 1) return result[0];
        return make_add(arena, std::move(result));
    }

    // MUL
    if (e->is_mul()) {
        std::vector<Expr*> factors;
        for (auto* child : e->children) {
            if (child->is_mul()) {
                for (auto* gc : child->children) factors.push_back(gc);
            } else {
                factors.push_back(child);
            }
        }

        int64_t num_n = 1, num_d = 1;
        std::vector<Expr*> non_num;
        for (auto* f : factors) {
            if (f->is_num()) {
                num_n *= f->num; num_d *= f->den;
                reduce_fraction(num_n, num_d);
            } else if (f->is_neg()) {
                num_n = -num_n;
                non_num.push_back(f->children[0]);
            } else {
                non_num.push_back(f);
            }
        }

        if (num_n == 0) return make_num(arena, 0);

        // Collect like bases into powers
        struct BasePow { Expr* base; int64_t exp_n; int64_t exp_d; };
        std::vector<BasePow> collected;
        for (auto* f : non_num) {
            Expr* b = f;
            int64_t en = 1, ed = 1;
            if (f->is_pow() && f->children[1]->is_num()) {
                b = f->children[0];
                en = f->children[1]->num;
                ed = f->children[1]->den;
            }
            std::string k = expr_key(b);
            bool found = false;
            for (auto& bp : collected) {
                if (expr_key(bp.base) == k) {
                    bp.exp_n = bp.exp_n * ed + en * bp.exp_d;
                    bp.exp_d = bp.exp_d * ed;
                    reduce_fraction(bp.exp_n, bp.exp_d);
                    found = true;
                    break;
                }
            }
            if (!found) collected.push_back({b, en, ed});
        }

        non_num.clear();
        for (auto& bp : collected) {
            if (bp.exp_n == 0) continue;
            if (bp.exp_n == 1 && bp.exp_d == 1) non_num.push_back(bp.base);
            else non_num.push_back(make_pow(arena, bp.base, make_num(arena, bp.exp_n, bp.exp_d)));
        }

        std::vector<Expr*> result;
        if ((num_n != 1 || num_d != 1) || non_num.empty())
            result.push_back(make_num(arena, num_n, num_d));
        for (auto* f : non_num) result.push_back(f);

        std::sort(result.begin() + (result.empty() || !result[0]->is_num() ? 0 : 1),
                  result.end(), expr_less);

        if (result.size() == 1) return result[0];
        if (result.size() == 2 && result[0]->is_num() && result[0]->num == -1 && result[0]->den == 1)
            return make_neg(arena, result[1]);
        return make_mul(arena, std::move(result));
    }

    // POW
    if (e->is_pow()) {
        Expr* base = e->children[0];
        Expr* exp = e->children[1];
        if (exp->is_num()) {
            if (exp->num == 0) return make_num(arena, 1);
            if (exp->num == 1 && exp->den == 1) return base;
            if (base->is_num() && exp->den == 1 && exp->num > 0 && exp->num <= 20) {
                int64_t rn = 1, rd = 1;
                for (int64_t i = 0; i < exp->num; ++i) {
                    rn *= base->num; rd *= base->den;
                    reduce_fraction(rn, rd);
                }
                return make_num(arena, rn, rd);
            }
            if (base->is_num() && exp->den == 1 && exp->num < 0 && exp->num >= -20) {
                int64_t rn = 1, rd = 1;
                for (int64_t i = 0; i < -exp->num; ++i) {
                    rn *= base->den; rd *= base->num;
                }
                reduce_fraction(rn, rd);
                return make_num(arena, rn, rd);
            }
        }
        return e;
    }

    // FUNC with numeric args
    if (e->is_func() && e->children.size() == 1 && e->children[0]->is_num()) {
        if (e->name == "abs") return make_num(arena, std::abs(e->children[0]->num), e->children[0]->den);
    }

    return e;
}

} // namespace axion
