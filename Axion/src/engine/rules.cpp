#include "engine/rules.h"
#include "engine/simplify.h"
#include "frontend/parser.h"

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
        // Note: ln(x) integration requires integration by parts (not table-based)
    };
}

} // namespace axion
