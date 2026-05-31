#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "engine/eval.h"
#include "modules/polynomial.h"
#include "output/printer.h"

using namespace axion;

static std::string expand_and_simplify(const std::string& input) {
    Arena a;
    Expr* e = parse(a, input);
    e = expand(a, e);
    e = simplify(a, e);
    return print(e);
}

TEST(Polynomial, ExpandSimpleProduct) {
    std::string result = expand_and_simplify("(x+1)*(x+2)");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 5.0}});
    EXPECT_DOUBLE_EQ(val, 42.0);
}

TEST(Polynomial, ExpandSquare) {
    std::string result = expand_and_simplify("(x+1)^2");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 3.0}});
    EXPECT_DOUBLE_EQ(val, 16.0);
}

TEST(Polynomial, ExpandCube) {
    std::string result = expand_and_simplify("(x+1)^3");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 2.0}});
    EXPECT_DOUBLE_EQ(val, 27.0);
}

TEST(Polynomial, ExpandDiffOfSquares) {
    std::string result = expand_and_simplify("(x+1)*(x-1)");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 4.0}});
    EXPECT_DOUBLE_EQ(val, 15.0);
}
