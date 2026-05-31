#include <iostream>
#include <string>
#include <sstream>
#include <readline/readline.h>
#include <readline/history.h>

#include "core/arena.h"
#include "core/ast.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "engine/eval.h"
#include "output/printer.h"

using namespace axion;

namespace {

// Parse "x=2, y=3" into env map
std::unordered_map<std::string, double> parse_env(const std::string& s) {
    std::unordered_map<std::string, double> env;
    std::istringstream iss(s);
    std::string pair;
    while (std::getline(iss, pair, ',')) {
        auto eq = pair.find('=');
        if (eq == std::string::npos) continue;
        std::string var = pair.substr(0, eq);
        // trim
        while (!var.empty() && var.front() == ' ') var.erase(var.begin());
        while (!var.empty() && var.back() == ' ') var.pop_back();
        double val = std::stod(pair.substr(eq + 1));
        env[var] = val;
    }
    return env;
}

} // anonymous namespace

int main() {
    std::cout << "Axion CAS v0.1 (Phase 1)\n";
    std::cout << "Type expressions to simplify. Commands: eval(expr, x=val), quit\n\n";

    Arena arena;

    while (true) {
        char* line = readline("axion> ");
        if (!line) break; // EOF

        std::string input(line);
        free(line);

        // Trim
        while (!input.empty() && input.front() == ' ') input.erase(input.begin());
        while (!input.empty() && input.back() == ' ') input.pop_back();

        if (input.empty()) continue;
        add_history(input.c_str());

        if (input == "quit" || input == "exit") break;

        try {
            // Check for eval command: eval(expr, x=val, ...)
            if (input.substr(0, 5) == "eval(") {
                // Find the split between expression and assignments
                // Format: eval(expr, x=2, y=3)
                auto close = input.rfind(')');
                std::string inner = input.substr(5, close - 5);

                // Find first assignment (contains '=')
                // Split at first comma that precedes an '='
                size_t split = std::string::npos;
                for (size_t i = 0; i < inner.size(); ++i) {
                    if (inner[i] == '=') {
                        // Walk back to find the comma before this var
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
