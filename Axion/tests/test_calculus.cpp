#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "modules/calculus.h"
#include "output/printer.h"

using namespace axion;

static std::string diff_and_simplify(const std::string& input, const std::string& var) {
    Arena a;
    Expr* e = parse(a, input);
    e = simplify(a, e);
    e = differentiate(a, e, var);
    e = simplify(a, e);
    return print(e);
}

TEST(Calculus, ConstantDerivative) {
    EXPECT_EQ(diff_and_simplify("5", "x"), "0");
}

TEST(Calculus, VariableDerivative) {
    EXPECT_EQ(diff_and_simplify("x", "x"), "1");
}

TEST(Calculus, OtherVariable) {
    EXPECT_EQ(diff_and_simplify("y", "x"), "0");
}

TEST(Calculus, LinearTerm) {
    EXPECT_EQ(diff_and_simplify("3*x", "x"), "3");
}

TEST(Calculus, PowerRule) {
    EXPECT_EQ(diff_and_simplify("x^3", "x"), "3*x^2");
}

TEST(Calculus, SumRule) {
    EXPECT_EQ(diff_and_simplify("x^2 + x", "x"), "1 + 2*x");
}

TEST(Calculus, ProductRule) {
    // d/dx(x*x) = x + x = 2*x
    EXPECT_EQ(diff_and_simplify("x*x", "x"), "2*x");
}

TEST(Calculus, SinDerivative) {
    EXPECT_EQ(diff_and_simplify("sin(x)", "x"), "cos(x)");
}

TEST(Calculus, CosDerivative) {
    EXPECT_EQ(diff_and_simplify("cos(x)", "x"), "-sin(x)");
}

TEST(Calculus, ChainRule) {
    // d/dx(sin(x^2)) = cos(x^2) * 2*x = 2*x*cos(x^2)
    EXPECT_EQ(diff_and_simplify("sin(x^2)", "x"), "2*x*cos(x^2)");
}

TEST(Calculus, ExpDerivative) {
    EXPECT_EQ(diff_and_simplify("exp(x)", "x"), "exp(x)");
}

TEST(Calculus, LnDerivative) {
    // d/dx(ln(x)) = 1/x = x^(-1)
    EXPECT_EQ(diff_and_simplify("ln(x)", "x"), "x^-1");
}
