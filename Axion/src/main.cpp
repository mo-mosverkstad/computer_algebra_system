#include <iostream>
#include <string>
#include <sstream>
#include <iomanip>
#include <unordered_map>
#include <cmath>

extern "C" {
#include "linenoise.h"
}

#include "core/arena.h"
#include "core/ast.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "engine/eval.h"
#include "modules/calculus.h"
#include "modules/polynomial.h"
#include "modules/series.h"
#include "modules/limits.h"
#include "modules/integration.h"
#include "output/printer.h"

using namespace axion;

namespace {

struct Session {
    Arena arena;
    std::unordered_map<std::string, Expr*> vars;        // variable bindings
    std::unordered_map<std::string, Expr*> func_bodies; // f(x) := expr
    std::unordered_map<std::string, std::vector<std::string>> func_params;
    Expr* last_result = nullptr;

    Session() {
        // Constants
        vars["pi"] = make_sym(arena, "pi");
        vars["e"] = make_sym(arena, "e");
    }
};

Expr* substitute(Arena& arena, Expr* e, const std::unordered_map<std::string, Expr*>& vars) {
    if (!e) return e;
    if (e->is_sym()) {
        if (e->name == "%") return nullptr;
        auto it = vars.find(e->name);
        if (it != vars.end()) return it->second;
        return e;
    }
    for (auto& c : e->children)
        c = substitute(arena, c, vars);
    return e;
}

} // anonymous namespace

int main() {
    std::cout << "Axion CAS v0.4 (Phase 4)\n";
    std::cout << "Commands: diff, expand, eval, approx, quit | := for assignment\n\n";

    Session session;
    linenoiseSetMultiLine(1);
    linenoiseHistorySetMaxLen(100);

    while (true) {
        char* line = linenoise("axion> ");
        if (!line) break;

        std::string input(line);
        free(line);

        while (!input.empty() && input.front() == ' ') input.erase(input.begin());
        while (!input.empty() && input.back() == ' ') input.pop_back();

        if (input.empty()) continue;
        linenoiseHistoryAdd(input.c_str());

        if (input == "quit" || input == "exit") break;

        try {
            // Assignment: name := expr or f(x) := expr
            if (has_assignment(input)) {
                auto a = parse_assignment(session.arena, input);
                Expr* val = simplify(session.arena, a.value);
                if (a.params.empty()) {
                    session.vars[a.name] = val;
                    std::cout << a.name << " := " << print(val) << "\n";
                } else {
                    session.func_bodies[a.name] = val;
                    session.func_params[a.name] = a.params;
                    std::cout << a.name << "(";
                    for (size_t i = 0; i < a.params.size(); ++i) {
                        if (i) std::cout << ", ";
                        std::cout << a.params[i];
                    }
                    std::cout << ") := " << print(val) << "\n";
                }
                continue;
            }

            // Parse
            Expr* e = parse(session.arena, input);

            // Replace % with last result
            if (session.last_result) {
                // Simple substitution for %
                std::unordered_map<std::string, Expr*> subs = session.vars;
                subs["%"] = session.last_result;
                e = substitute(session.arena, e, subs);
            } else {
                e = substitute(session.arena, e, session.vars);
            }

            // Handle commands
            if (e->is_func()) {
                const std::string& fname = e->name;

                // diff(expr, var) or diff(expr, var, order)
                if (fname == "diff" && e->children.size() >= 2) {
                    Expr* expr = simplify(session.arena, e->children[0]);
                    std::string var = e->children[1]->name;
                    int order = 1;
                    if (e->children.size() >= 3 && e->children[2]->is_num())
                        order = static_cast<int>(e->children[2]->num);
                    for (int i = 0; i < order; ++i) {
                        expr = differentiate(session.arena, expr, var);
                        expr = simplify(session.arena, expr);
                    }
                    session.last_result = expr;
                    std::cout << print(expr) << "\n";
                    continue;
                }

                // expand(expr)
                if (fname == "expand" && e->children.size() >= 1) {
                    Expr* expr = e->children[0];
                    expr = expand(session.arena, expr);
                    expr = simplify(session.arena, expr);
                    session.last_result = expr;
                    std::cout << print(expr) << "\n";
                    continue;
                }

                // sum(expr, var, lo, hi)
                if (fname == "sum" && e->children.size() == 4) {
                    Expr* body = e->children[0];
                    std::string var = e->children[1]->name;
                    Expr* lo_e = simplify(session.arena, e->children[2]);
                    Expr* hi_e = simplify(session.arena, e->children[3]);
                    if (lo_e->is_num() && lo_e->den == 1 && hi_e->is_num() && hi_e->den == 1) {
                        Expr* result = eval_sum(session.arena, body, var, lo_e->num, hi_e->num);
                        if (result) {
                            session.last_result = result;
                            std::cout << print(result) << "\n";
                            continue;
                        }
                    }
                    std::cerr << "Error: sum requires integer bounds\n";
                    continue;
                }

                // prod(expr, var, lo, hi)
                if (fname == "prod" && e->children.size() == 4) {
                    Expr* body = e->children[0];
                    std::string var = e->children[1]->name;
                    Expr* lo_e = simplify(session.arena, e->children[2]);
                    Expr* hi_e = simplify(session.arena, e->children[3]);
                    if (lo_e->is_num() && lo_e->den == 1 && hi_e->is_num() && hi_e->den == 1) {
                        Expr* result = eval_prod(session.arena, body, var, lo_e->num, hi_e->num);
                        if (result) {
                            session.last_result = result;
                            std::cout << print(result) << "\n";
                            continue;
                        }
                    }
                    std::cerr << "Error: prod requires integer bounds\n";
                    continue;
                }

                // collect(expr, var)
                if (fname == "collect" && e->children.size() == 2) {
                    Expr* expr = e->children[0];
                    std::string var = e->children[1]->name;
                    expr = collect(session.arena, expr, var);
                    session.last_result = expr;
                    std::cout << print(expr) << "\n";
                    continue;
                }

                // lim(expr, var, point) or lim(expr, var, point, direction)
                if (fname == "lim" && e->children.size() >= 3) {
                    Expr* expr = e->children[0];
                    std::string var = e->children[1]->name;
                    Expr* point = simplify(session.arena, e->children[2]);
                    int dir = 0;
                    if (e->children.size() >= 4 && e->children[3]->is_sym()) {
                        if (e->children[3]->name == "right") dir = 1;
                        else if (e->children[3]->name == "left") dir = -1;
                    }
                    Expr* result = compute_limit(session.arena, expr, var, point, dir);
                    if (result) {
                        session.last_result = result;
                        std::cout << print(result) << "\n";
                    } else {
                        std::cout << "undefined (limit could not be computed)\n";
                    }
                    continue;
                }

                // integrate(expr, var) or integrate(expr, var, a, b) or int(...)
                if ((fname == "integrate" || fname == "int") && e->children.size() >= 2) {
                    Expr* body = e->children[0];
                    std::string var = e->children[1]->name;
                    if (e->children.size() == 2) {
                        Expr* result = integrate(session.arena, body, var);
                        if (result) {
                            result = simplify(session.arena, result);
                            session.last_result = result;
                            std::cout << print(result) << "\n";
                        } else {
                            std::cout << "cannot integrate\n";
                        }
                    } else if (e->children.size() == 4) {
                        Expr* a = simplify(session.arena, e->children[2]);
                        Expr* b = simplify(session.arena, e->children[3]);
                        Expr* result = integrate_definite(session.arena, body, var, a, b);
                        if (result) {
                            result = simplify(session.arena, result);
                            session.last_result = result;
                            std::cout << print(result) << "\n";
                        } else {
                            std::cout << "cannot integrate\n";
                        }
                    }
                    continue;
                }

                // eval(expr, x=val, ...)
                if (fname == "eval" && e->children.size() >= 2) {
                    Expr* expr = simplify(session.arena, e->children[0]);
                    std::unordered_map<std::string, double> env;
                    env["pi"] = M_PI;
                    env["e"] = M_E;
                    for (size_t i = 1; i < e->children.size(); ++i) {
                        if (e->children[i]->is_rel() && e->children[i]->name == "=") {
                            std::string vname = e->children[i]->children[0]->name;
                            double vval = evaluate(e->children[i]->children[1], env);
                            env[vname] = vval;
                        }
                    }
                    double result = evaluate(expr, env);
                    std::cout << result << "\n";
                    continue;
                }

                // approx(expr) or approx(expr, digits)
                if (fname == "approx") {
                    Expr* expr = simplify(session.arena, e->children[0]);
                    std::unordered_map<std::string, double> env;
                    env["pi"] = M_PI;
                    env["e"] = M_E;
                    try {
                        double result = evaluate(expr, env);
                        std::cout << std::setprecision(15) << result << "\n";
                    } catch (...) {
                        std::cout << print(expr) << " (cannot evaluate numerically)\n";
                    }
                    continue;
                }

                // User-defined function call
                if (session.func_bodies.count(fname)) {
                    Expr* body = session.func_bodies[fname];
                    auto& params = session.func_params[fname];
                    std::unordered_map<std::string, Expr*> local_vars = session.vars;
                    for (size_t i = 0; i < params.size() && i < e->children.size(); ++i) {
                        local_vars[params[i]] = simplify(session.arena, e->children[i]);
                    }
                    Expr* result = substitute(session.arena, body, local_vars);
                    result = simplify(session.arena, result);
                    session.last_result = result;
                    std::cout << print(result) << "\n";
                    continue;
                }
            }

            // Default: simplify and print
            e = simplify(session.arena, e);
            session.last_result = e;
            std::cout << print(e) << "\n";

        } catch (const std::exception& ex) {
            std::cerr << "Error: " << ex.what() << "\n";
        }
    }

    return 0;
}
