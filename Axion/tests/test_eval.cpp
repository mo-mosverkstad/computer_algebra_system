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
    // (3)^2 + 2*3 + 1 = 16
    EXPECT_DOUBLE_EQ(evaluate(e, {{"x", 3.0}}), 16.0);
}

TEST(Eval, Function) {
    Arena a;
    Expr* e = parse(a, "sin(0)");
    e = simplify(a, e);
    EXPECT_NEAR(evaluate(e, {}), 0.0, 1e-10);
}

TEST(Eval, UndefinedVar) {
    Arena a;
    Expr* e = parse(a, "x + y");
    EXPECT_THROW(evaluate(e, {{"x", 1.0}}), std::runtime_error);
}
