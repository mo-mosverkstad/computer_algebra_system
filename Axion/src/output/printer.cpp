#include "output/printer.h"
#include <sstream>
#include <cmath>

namespace axion {

namespace {

std::string print_impl(const Expr* e, int parent_prec, bool is_right_of_minus) {
    if (!e) return "?";

    std::ostringstream os;

    switch (e->type) {
        case NodeType::NUM: {
            double v = e->num;
            if (v == static_cast<int64_t>(v))
                os << static_cast<int64_t>(v);
            else
                os << v;
            break;
        }
        case NodeType::SYM:
            os << e->name;
            break;

        case NodeType::ADD: {
            bool need_parens = parent_prec > 1 || is_right_of_minus;
            if (need_parens) os << "(";
            for (size_t i = 0; i < e->children.size(); ++i) {
                Expr* child = e->children[i];
                if (i > 0) {
                    // Check if child is NEG — print as " - X" instead of " + -X"
                    if (child->is_neg()) {
                        os << " - " << print_impl(child->children[0], 1, true);
                        continue;
                    }
                    os << " + ";
                }
                if (i == 0 && child->is_neg()) {
                    os << "-" << print_impl(child->children[0], 3, false);
                    continue;
                }
                os << print_impl(child, 1, false);
            }
            if (need_parens) os << ")";
            break;
        }

        case NodeType::MUL: {
            bool need_parens = parent_prec > 2;
            if (need_parens) os << "(";
            for (size_t i = 0; i < e->children.size(); ++i) {
                if (i > 0) os << "*";
                os << print_impl(e->children[i], 2, false);
            }
            if (need_parens) os << ")";
            break;
        }

        case NodeType::POW: {
            os << print_impl(e->children[0], 5, false);
            os << "^";
            os << print_impl(e->children[1], 4, false);
            break;
        }

        case NodeType::FUNC:
            os << e->name << "(" << print_impl(e->children[0], 0, false) << ")";
            break;

        case NodeType::NEG:
            os << "-" << print_impl(e->children[0], 3, false);
            break;
    }

    return os.str();
}

} // anonymous namespace

std::string print(const Expr* e) {
    return print_impl(e, 0, false);
}

} // namespace axion
