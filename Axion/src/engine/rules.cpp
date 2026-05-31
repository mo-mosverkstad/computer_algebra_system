#include "engine/rules.h"
#include "engine/simplify.h"
#include "output/printer.h"
#include "frontend/parser.h"
#include <cmath>
#include <fstream>

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

// Recognize perfect cube: a³+3a²b+3ab²+b³ → (a+b)³
Expr* recognize_perfect_cube(Arena& arena, Expr* expr) {
    if (!expr->is_add() || expr->children.size() != 4) return nullptr;

    // Find cube terms (exponent 3 or numeric perfect cubes)
    struct CubeInfo { Expr* root; size_t idx; };
    std::vector<CubeInfo> cubes;

    for (size_t i = 0; i < 4; ++i) {
        Expr* t = expr->children[i];
        BaseExp be = get_base_exp(t);
        if (be.exp_n == 3 && be.exp_d == 1) {
            cubes.push_back({be.base, i});
        } else if (t->is_num() && t->den == 1) {
            int64_t n = std::abs(t->num);
            int64_t cr = static_cast<int64_t>(std::round(std::cbrt(static_cast<double>(n))));
            if (cr * cr * cr == n) {
                int64_t sign = (t->num > 0) ? cr : -cr;
                cubes.push_back({make_num(arena, sign), i});
            }
        }
    }
    if (cubes.size() != 2) return nullptr;

    // Try both orderings
    for (size_t ord = 0; ord < 2; ++ord) {
        Expr* a = (ord == 0) ? cubes[0].root : cubes[1].root;
        Expr* b = (ord == 0) ? cubes[1].root : cubes[0].root;

        // Expected middle terms: 3a²b and 3ab²
        Expr* t1 = simplify(arena, make_mul(arena, {make_num(arena, 3), make_pow(arena, a, make_num(arena, 2)), b}));
        Expr* t2 = simplify(arena, make_mul(arena, {make_num(arena, 3), a, make_pow(arena, b, make_num(arena, 2))}));

        // Find the two middle terms (not cube terms)
        std::vector<Expr*> middles;
        for (size_t i = 0; i < 4; ++i) {
            if (i != cubes[0].idx && i != cubes[1].idx)
                middles.push_back(expr->children[i]);
        }
        if (middles.size() != 2) continue;

        std::string m0 = print(middles[0]), m1 = print(middles[1]);
        std::string e1 = print(t1), e2 = print(t2);

        if ((m0 == e1 && m1 == e2) || (m0 == e2 && m1 == e1))
            return make_pow(arena, make_add(arena, {a, b}), make_num(arena, 3));

        // Try (a-b)^3 = a³ - 3a²b + 3ab² - b³
        Expr* nt1 = simplify(arena, make_mul(arena, {make_num(arena, -3), make_pow(arena, a, make_num(arena, 2)), b}));
        Expr* nt2 = simplify(arena, make_mul(arena, {make_num(arena, 3), a, make_pow(arena, b, make_num(arena, 2))}));
        std::string ne1 = print(nt1), ne2 = print(nt2);

        if ((m0 == ne1 && m1 == ne2) || (m0 == ne2 && m1 == ne1))
            return make_pow(arena, make_add(arena, {a, make_neg(arena, b)}), make_num(arena, 3));
    }
    return nullptr;
}

// Recognize common factor: a*X + b*X + c*X → (a+b+c)*X
// Finds the largest common symbolic factor across all terms of an ADD.
Expr* recognize_common_factor(Arena& arena, Expr* expr) {
    if (!expr->is_add() || expr->children.size() < 2) return nullptr;

    // Extract factors from each term
    // For MUL(a, b, c): factors are {a, b, c}
    // For single expr X: factors are {X}
    auto get_factors = [](Expr* e) -> std::vector<Expr*> {
        if (e->is_mul()) return e->children;
        if (e->is_neg() && e->children[0]->is_mul()) return e->children[0]->children;
        return {e};
    };

    // Get factors of first term
    std::vector<Expr*> first_factors = get_factors(expr->children[0]);

    // For each factor of the first term, check if it appears in ALL other terms
    for (auto* candidate : first_factors) {
        if (candidate->is_num()) continue; // skip numeric coefficients

        std::string cand_str = print(candidate);
        bool common = true;

        for (size_t i = 1; i < expr->children.size(); ++i) {
            std::vector<Expr*> term_factors = get_factors(expr->children[i]);
            bool found = false;
            for (auto* f : term_factors) {
                if (print(f) == cand_str) { found = true; break; }
                // Also check if term contains candidate as a power base
                if (f->is_pow() && print(f->children[0]) == cand_str) { found = true; break; }
            }
            if (!found) { common = false; break; }
        }

        if (common) {
            // Factor out: divide each term by candidate
            std::vector<Expr*> quotients;
            for (auto* term : expr->children) {
                std::vector<Expr*> factors = get_factors(term);
                std::vector<Expr*> remaining;
                bool removed = false;
                int sign = 1;
                if (term->is_neg()) { sign = -1; factors = get_factors(term->children[0]); }

                for (auto* f : factors) {
                    if (!removed && print(f) == cand_str) { removed = true; continue; }
                    remaining.push_back(f);
                }
                Expr* q;
                if (remaining.empty()) q = make_num(arena, sign);
                else if (remaining.size() == 1) q = remaining[0];
                else q = make_mul(arena, std::move(remaining));
                if (sign == -1 && !remaining.empty()) q = make_neg(arena, q);
                quotients.push_back(q);
            }
            Expr* sum = simplify(arena, make_add(arena, std::move(quotients)));
            return simplify(arena, make_mul(arena, {candidate, sum}));
        }
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
        {"cot",   "-sin(_u)^(-2)"},
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
        recognize_perfect_cube,
        recognize_common_factor,
    };

    // =========================================================
    // FUNCTION EVALUATION RULES: f(numeric) → value
    // Used by simplify() for computational evaluation
    // =========================================================

    g_rules.func_eval = {
        // f(0) rules
        {"sin",  0, 1, 0, 1, ""},
        {"cos",  0, 1, 1, 1, ""},
        {"tan",  0, 1, 0, 1, ""},
        {"exp",  0, 1, 1, 1, ""},
        {"sinh", 0, 1, 0, 1, ""},
        {"cosh", 0, 1, 1, 1, ""},
        {"tanh", 0, 1, 0, 1, ""},
        // f(1) rules
        {"ln",   1, 1, 0, 1, ""},
        {"exp",  1, 1, 0, 0, "e"},  // exp(1) → symbol "e"
    };

    // =========================================================
    // FUNCTION SYMBOLIC EVALUATION: f(symbol) → value
    // Used by simplify() for known symbolic arguments
    // =========================================================

    g_rules.func_sym = {
        {"sin",  "pi", 0, 1},
        {"cos",  "pi", -1, 1},
        {"tan",  "pi", 0, 1},
        {"ln",   "e",  1, 1},
    };
}

Expr* simplify_smart(Arena& arena, Expr* expr) {
    expr = simplify_full(arena, expr);

    // Try recognizers — if result is shorter or equal, prefer factored form
    Expr* recognized = apply_recognizers(arena, expr, get_rules().recognizers);
    if (recognized) {
        Expr* r = simplify(arena, recognized);
        if (print(r).size() <= print(expr).size())
            return r;
    }
    return expr;
}

int load_rules_file(Arena& arena, const std::string& path) {
    (void)arena;
    std::ifstream file(path);
    if (!file.is_open()) return -1;

    init_rules(g_rule_arena);
    int count = 0;
    std::string line;

    while (std::getline(file, line)) {
        // Strip whitespace
        size_t start = line.find_first_not_of(" \t");
        if (start == std::string::npos) continue;
        line = line.substr(start);

        // Skip comments and empty lines
        if (line.empty() || line[0] == '#') continue;

        // Find arrow separator: → or ->
        size_t arrow = line.find("→");
        if (arrow == std::string::npos) arrow = line.find("->");
        if (arrow == std::string::npos) continue;

        size_t arrow_len = (line[arrow] == '-') ? 2 : 3; // "->" is 2, "→" is 3 bytes UTF-8
        std::string lhs = line.substr(0, arrow);
        std::string rhs = line.substr(arrow + arrow_len);

        // Trim
        while (!lhs.empty() && (lhs.back() == ' ' || lhs.back() == '\t')) lhs.pop_back();
        while (!rhs.empty() && (rhs.front() == ' ' || rhs.front() == '\t')) rhs.erase(rhs.begin());

        if (lhs.empty() || rhs.empty()) continue;

        // Check for @diff / @int prefixes
        if (lhs.substr(0, 5) == "@diff") {
            std::string func_pattern = lhs.substr(5);
            while (!func_pattern.empty() && func_pattern[0] == ' ') func_pattern.erase(func_pattern.begin());
            // Extract function name from "func(_u)"
            size_t paren = func_pattern.find('(');
            if (paren != std::string::npos) {
                std::string fname = func_pattern.substr(0, paren);
                g_rules.diff_rules.push_back({fname, rhs});
                ++count;
            }
        } else if (lhs.substr(0, 4) == "@int") {
            std::string func_pattern = lhs.substr(4);
            while (!func_pattern.empty() && func_pattern[0] == ' ') func_pattern.erase(func_pattern.begin());
            size_t paren = func_pattern.find('(');
            if (paren != std::string::npos) {
                std::string fname = func_pattern.substr(0, paren);
                g_rules.int_rules.push_back({fname, rhs});
                ++count;
            }
        } else {
            // Identity rule
            Expr* pattern = simplify(g_rule_arena, parse(g_rule_arena, lhs));
            Expr* replacement = parse(g_rule_arena, rhs);
            g_rules.identities.push_back({pattern, replacement, ""});
            ++count;
        }
    }
    return count;
}

} // namespace axion
