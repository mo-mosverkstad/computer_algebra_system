#include "engine/eval.h"
#include <cmath>
#include <stdexcept>

namespace axion {

double evaluate(const Expr* e, const std::unordered_map<std::string, double>& env) {
    if (!e) throw std::runtime_error("null expression");

    switch (e->type) {
        case NodeType::NUM:
            return e->num;

        case NodeType::SYM: {
            auto it = env.find(e->name);
            if (it == env.end())
                throw std::runtime_error("Undefined variable: " + e->name);
            return it->second;
        }

        case NodeType::ADD: {
            double sum = 0.0;
            for (auto* c : e->children) sum += evaluate(c, env);
            return sum;
        }

        case NodeType::MUL: {
            double prod = 1.0;
            for (auto* c : e->children) prod *= evaluate(c, env);
            return prod;
        }

        case NodeType::POW:
            return std::pow(evaluate(e->children[0], env), evaluate(e->children[1], env));

        case NodeType::NEG:
            return -evaluate(e->children[0], env);

        case NodeType::FUNC: {
            double arg = evaluate(e->children[0], env);
            if (e->name == "sin") return std::sin(arg);
            if (e->name == "cos") return std::cos(arg);
            if (e->name == "tan") return std::tan(arg);
            if (e->name == "ln")  return std::log(arg);
            if (e->name == "log") return std::log10(arg);
            if (e->name == "exp") return std::exp(arg);
            if (e->name == "sqrt") return std::sqrt(arg);
            if (e->name == "abs") return std::fabs(arg);
            throw std::runtime_error("Unknown function: " + e->name);
        }
    }
    throw std::runtime_error("Unknown node type");
}

} // namespace axion
