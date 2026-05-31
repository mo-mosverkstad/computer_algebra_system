#include "engine/rules.h"
#include "engine/simplify.h"
#include "output/printer.h"
#include "frontend/parser.h"
#include <cmath>

namespace axion {

static RuleTables g_rules;
static bool g_initialized = false;
static Arena g_rule_arena; // dedicated arena for rule storage

RuleTables& get_rules() {
    if (!g_initialized) init_rules(g_rule_arena);
    return g_rules;
}

const DiffRule* RuleTables::find_diff(const std::string& func) const {
    for (auto& r : diff_rules)
        if (r.func_name == func) return &r;
    return nullptr;
}

const IntRule* RuleTables::find_int(const std::string& func) const {
    for (auto& r : int_rules)
        if (r.func_name == func) return &r;
    return nullptr;
}

// =========================================================
// RECOGNITION FUNCTIONS (backward pattern detectors)
// =========================================================

namespace {

// Helper: get string key for expression comparison
std::string rkey(const Expr* e) {
    if (!e) return "";
    if (e->is_num()) return "N" + std::to_string(e->num) + "/" + std::to_string(e->den);
    if (e->is_sym()) return "S" + e->name;
    if (e->is_pow()) return "P(" + rkey(e->children[0]) + "," + rkey(e->children[1]) + ")";
    if (e->is_func()) {
        std::string s = "F" + e->name + "(";
        for (size_t i = 0; i < e->children.size(); ++i) { if (i) s += ","; s += rkey(e->children[i]); }
        return s + ")";
    }
    if (e->is_mul()) {
        std::string s = "M(";
        for (size_t i = 0; i < e->children.size(); ++i) { if (i) s += ","; s += rkey(e->children[i]); }
        return s + ")";
    }
    if (e->is_neg()) return "NEG(" + rkey(e->children[0]) + ")";
    return "?";
}

// Extract base and exponent from a term: x^2 → {x, 2}, x → {x, 1}, 3 → {3, 1}
struct BaseExp { Expr* base; int64_t exp_n; int64_t exp_d; };
BaseExp get_base_exp(Expr* e) {
    if (e->is_pow() && e->children[1]->is_num())
        return {e->children[0], e->children[1]->num, e->children[1]->den};
    return {e, 1, 1};
}

// Extract coefficient and base from a MUL term
struct CoeffBase { int64_t cn; int64_t cd; Expr* base; };
CoeffBase get_coeff_base(Expr* e) {
    if (e->is_num()) return {e->num, e->den, nullptr};
    if (e->is_neg()) {
        auto inner = get_coeff_base(e->children[0]);
        return {-inner.cn, inner.cd, inner.base};
    }
    if (e->is_mul() && !e->children.empty() && e->children[0]->is_num()) {
        int64_t cn = e->children[0]->num, cd = e->children[0]->den;
        if (e->children.size() == 2) return {cn, cd, e->children[1]};
        // Rebuild MUL without the coefficient
        std::vector<Expr*> rest(e->children.begin() + 1, e->children.end());
        if (rest.size() == 1) return {cn, cd, rest[0]};
        return {cn, cd, make_mul(g_rule_arena, std::move(rest))};
    }
    return {1, 1, e};
}

} // anonymous namespace

// Recognize perfect square trinomial: a² + 2ab + b² → (a+b)²
// Also: a² - 2ab + b² → (a-b)²
Expr* recognize_perfect_square(Arena& arena, Expr* expr) {
    if (!expr->is_add() || expr->children.size() != 3) return nullptr;

    // Find square terms: x^2, or numeric perfect squares (4, 9, 16...)
    struct SquareInfo { Expr* root; size_t idx; };
    std::vector<SquareInfo> squares;

    for (size_t i = 0; i < 3; ++i) {
        Expr* t = expr->children[i];
        BaseExp be = get_base_exp(t);
        if (be.exp_n == 2 && be.exp_d == 1) {
            squares.push_back({be.base, i});
        } else if (t->is_num() && t->num > 0 && t->den == 1) {
            int64_t sq = static_cast<int64_t>(std::sqrt(static_cast<double>(t->num)));
            if (sq * sq == t->num)
                squares.push_back({make_num(arena, sq), i});
        }
    }
    if (squares.size() != 2) return nullptr;

    size_t mid_idx = 3 - squares[0].idx - squares[1].idx;
    Expr* mid = expr->children[mid_idx];

    // Check if middle term = ±2*a*b (try both orderings of squares)
    for (size_t ord = 0; ord < 2; ++ord) {
        Expr* sa = (ord == 0) ? squares[0].root : squares[1].root;
        Expr* sb = (ord == 0) ? squares[1].root : squares[0].root;
        Expr* pos_mid = simplify(arena, make_mul(arena, {make_num(arena, 2), sa, sb}));
        Expr* neg_mid = simplify(arena, make_mul(arena, {make_num(arena, -2), sa, sb}));

        if (print(mid) == print(pos_mid))
            return make_pow(arena, make_add(arena, {sa, sb}), make_num(arena, 2));
        if (print(mid) == print(neg_mid))
            return make_pow(arena, make_add(arena, {sa, make_neg(arena, sb)}), make_num(arena, 2));
    }

    return nullptr;
}

void init_rules(Arena& arena) {
    if (g_initialized) return;
    g_initialized = true;
    (void)arena; // use internal arena instead for consistency

    auto add_id = [&](const char* pattern, const char* replacement) {
        g_rules.identities.push_back({
            simplify(g_rule_arena, parse(g_rule_arena, pattern)),
            parse(g_rule_arena, replacement), ""
        });
    };

    // =========================================================
    // IDENTITY RULES (applied during simplify_full)
    // These are declarative transformations that the algorithmic
    // simplifier cannot express (pattern-based, not structural).
    // =========================================================

    // Trig at pi/2
    add_id("sin(pi/2)", "1");
    add_id("cos(pi/2)", "0");

    // Inverse function pairs
    add_id("exp(ln(_x))", "_x");
    add_id("ln(exp(_x))", "_x");

    // Pythagorean identity
    add_id("sin(_x)^2 + cos(_x)^2", "1");
    add_id("cos(_x)^2 + sin(_x)^2", "1");

    // Hyperbolic identity: cosh²-sinh²=1
    add_id("cosh(_x)^2 - sinh(_x)^2", "1");

    // Logarithm rules
    add_id("ln(_x) + ln(_y)", "ln(_x * _y)");
    add_id("_n__num * ln(_x)", "ln(_x^_n__num)");

    // =========================================================
    // DIFFERENTIATION RULES: d/dx f(u) = derivative * u'
    // The derivative pattern uses _u as placeholder for the argument
    // =========================================================

    g_rules.diff_rules = {
        {"sin",   "cos(_u)"},
        {"cos",   "-sin(_u)"},
        {"tan",   "cos(_u)^(-2)"},
        {"exp",   "exp(_u)"},
        {"ln",    "_u^(-1)"},
        {"log",   "(_u * ln(10))^(-1)"},
        {"sqrt",  "(2 * sqrt(_u))^(-1)"},
        {"abs",   "_u * abs(_u)^(-1)"},   // sign(u) approximation
        {"asin",  "(1 - _u^2)^(-1/2)"},
        {"acos",  "-(1 - _u^2)^(-1/2)"},
        {"atan",  "(1 + _u^2)^(-1)"},
        {"sinh",  "cosh(_u)"},
        {"cosh",  "sinh(_u)"},
        {"tanh",  "cosh(_u)^(-2)"},
    };

    // =========================================================
    // INTEGRATION RULES: ∫f(u) du = antiderivative
    // Pattern uses _u as the integration variable
    // =========================================================

    g_rules.int_rules = {
        {"sin",   "-cos(_u)"},
        {"cos",   "sin(_u)"},
        {"exp",   "exp(_u)"},
        {"tan",   "-ln(cos(_u))"},
        {"sinh",  "cosh(_u)"},
        {"cosh",  "sinh(_u)"},
    };

    // =========================================================
    // RECOGNITION FUNCTIONS (backward pattern detectors)
    // Used by factor() and simplify_full() for pattern recognition
    // =========================================================

    g_rules.recognizers = {
        recognize_perfect_square,
    };
}

} // namespace axion
