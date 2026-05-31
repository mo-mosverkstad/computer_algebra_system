#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "engine/eval.h"
#include "modules/series.h"
#include "output/printer.h"

using namespace axion;

TEST(Series, SumIntegers) {
    // sum(k, k, 1, 10) = 55
    Arena a;
    Expr* body = parse(a, "k");
    Expr* result = eval_sum(a, body, "k", 1, 10);
    EXPECT_EQ(result->num, 55);
    EXPECT_EQ(result->den, 1);
}

TEST(Series, SumSquares) {
    // sum(k^2, k, 1, 5) = 1+4+9+16+25 = 55
    Arena a;
    Expr* body = parse(a, "k^2");
    Expr* result = eval_sum(a, body, "k", 1, 5);
    EXPECT_EQ(result->num, 55);
}

TEST(Series, SumConstant) {
    // sum(3, k, 1, 4) = 12
    Arena a;
    Expr* body = parse(a, "3");
    Expr* result = eval_sum(a, body, "k", 1, 4);
    EXPECT_EQ(result->num, 12);
}

TEST(Series, ProdIntegers) {
    // prod(k, k, 1, 5) = 120
    Arena a;
    Expr* body = parse(a, "k");
    Expr* result = eval_prod(a, body, "k", 1, 5);
    EXPECT_EQ(result->num, 120);
}

TEST(Series, ProdExpression) {
    // prod(k+1, k, 0, 3) = 1*2*3*4 = 24
    Arena a;
    Expr* body = parse(a, "k+1");
    Expr* result = eval_prod(a, body, "k", 0, 3);
    EXPECT_EQ(result->num, 24);
}

TEST(Series, CollectSimple) {
    // collect(x^2 + 2*x + 3*x, x) should combine 2*x + 3*x = 5*x
    Arena a;
    Expr* e = parse(a, "x^2 + 2*x + 3*x");
    e = simplify(a, e);
    Expr* result = collect(a, e, "x");
    std::string s = print(result);
    // Should have x^2 and 5*x terms
    // Evaluate at x=2: 4 + 10 = 14
    double val = evaluate(result, {{"x", 2.0}});
    EXPECT_DOUBLE_EQ(val, 14.0);
}
