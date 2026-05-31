#include <iostream>
#include <string>
#include <sstream>

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
#include "output/printer.h"

using namespace axion;

namespace {

std::unordered_map<std::string, double> parse_env(const std::string& s) {
    std::unordered_map<std::string, double> env;
    std::istringstream iss(s);
    std::string pair;
    while (std::getline(iss, pair, ',')) {
        auto eq = pair.find('=');
        if (eq == std::string::npos) continue;
        std::string var = pair.substr(0, eq);
        while (!var.empty() && var.front() == ' ') var.erase(var.begin());
        while (!var.empty() && var.back() == ' ') var.pop_back();
        double val = std::stod(pair.substr(eq + 1));
        env[var] = val;
    }
    return env;
}

} // anonymous namespace

int main() {
    std::cout << "Axion CAS v0.3 (Phase 3)\n";
    std::cout << "Commands: diff(expr, var), expand(expr), eval(expr, x=val), quit\n\n";

    Arena arena;
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
            if (input.substr(0, 5) == "diff(") {
                auto close = input.rfind(')');
                std::string inner = input.substr(5, close - 5);
                auto comma = inner.rfind(',');
                if (comma == std::string::npos) {
                    std::cerr << "Error: diff requires variable, e.g. diff(x^2, x)\n";
                    continue;
                }
                std::string expr_str = inner.substr(0, comma);
                std::string var = inner.substr(comma + 1);
                while (!var.empty() && var.front() == ' ') var.erase(var.begin());
                while (!var.empty() && var.back() == ' ') var.pop_back();

                Expr* e = parse(arena, expr_str);
                e = simplify(arena, e);
                e = differentiate(arena, e, var);
                e = simplify(arena, e);
                std::cout << print(e) << "\n";
            } else if (input.substr(0, 7) == "expand(") {
                auto close = input.rfind(')');
                std::string expr_str = input.substr(7, close - 7);
                Expr* e = parse(arena, expr_str);
                e = expand(arena, e);
                e = simplify(arena, e);
                std::cout << print(e) << "\n";
            } else if (input.substr(0, 5) == "eval(") {
                auto close = input.rfind(')');
                std::string inner = input.substr(5, close - 5);

                size_t split = std::string::npos;
                for (size_t i = 0; i < inner.size(); ++i) {
                    if (inner[i] == '=') {
                        for (size_t j = i; j > 0; --j) {
                            if (inner[j] == ',') { split = j; break; }
                        }
                        break;
                    }
                }

                if (split == std::string::npos) {
                    std::cerr << "Error: eval requires variable assignments, e.g. eval(x^2, x=3)\n";
                    continue;
                }

                std::string expr_str = inner.substr(0, split);
                std::string env_str = inner.substr(split + 1);

                Expr* e = parse(arena, expr_str);
                e = simplify(arena, e);
                auto env = parse_env(env_str);
                double result = evaluate(e, env);
                std::cout << result << "\n";
            } else {
                Expr* e = parse(arena, input);
                e = simplify(arena, e);
                std::cout << print(e) << "\n";
            }
        } catch (const std::exception& ex) {
            std::cerr << "Error: " << ex.what() << "\n";
        }
    }

    return 0;
}
