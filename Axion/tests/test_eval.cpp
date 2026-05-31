#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "engine/eval.h"

using namespace axion;

TEST(Eval, SimpleNum) {
    Arena a;
    Expr* e = parse(a, "42");
    EXPECT_DOUBLE_EQ(evaluate(e, {}), 42.0);
}

TEST(Eval, Variable) {
    Arena a;
    Expr* e = parse(a, "x + 1");
    e = simplify(a, e);
    EXPECT_DOUBLE_EQ(evaluate(e, {{"x", 2.0}}), 3.0);
}

TEST(Eval, Polynomial) {
    Arena a;
    Expr* e = parse(a, "x^2 + 2*x + 1");
    e = simplify(a, e);
    EXPECT_DOUBLE_EQ(evaluate(e, {{"x", 3.0}}), 16.0);
}

TEST(Eval, Factorial) {
    Arena a;
    Expr* e = parse(a, "5!");
    e = simplify(a, e);
    EXPECT_DOUBLE_EQ(evaluate(e, {}), 120.0);
}

TEST(Eval, Rational) {
    Arena a;
    Expr* e = parse(a, "1/3 + 1/6");
    e = simplify(a, e);
    EXPECT_NEAR(evaluate(e, {}), 0.5, 1e-10);
}
