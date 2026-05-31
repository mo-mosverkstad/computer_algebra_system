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
    // (x+1)*(x+2) at x=5 should be 42
    std::string result = expand_and_simplify("(x+1)*(x+2)");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 5.0}});
    EXPECT_DOUBLE_EQ(val, 42.0);
}

TEST(Polynomial, ExpandSquare) {
    // (x+1)^2 at x=3 should be 16
    std::string result = expand_and_simplify("(x+1)^2");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 3.0}});
    EXPECT_DOUBLE_EQ(val, 16.0);
}

TEST(Polynomial, ExpandCube) {
    // (x+1)^3 at x=2 should be 27
    std::string result = expand_and_simplify("(x+1)^3");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 2.0}});
    EXPECT_DOUBLE_EQ(val, 27.0);
}

TEST(Polynomial, ExpandDiffOfSquares) {
    // (x+1)*(x-1) at x=4 should be 15
    std::string result = expand_and_simplify("(x+1)*(x-1)");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 4.0}});
    EXPECT_DOUBLE_EQ(val, 15.0);
}

TEST(Polynomial, ExpandMultivar) {
    // (x+y)*(x-y) at x=3,y=2 should be 5
    std::string result = expand_and_simplify("(x+y)*(x-y)");
    Arena a;
    Expr* e = parse(a, result);
    double val = evaluate(e, {{"x", 3.0}, {"y", 2.0}});
    EXPECT_DOUBLE_EQ(val, 5.0);
}

TEST(Polynomial, NoExpansionNeeded) {
    EXPECT_EQ(expand_and_simplify("x^2 + 1"), "1 + x^2");
}
