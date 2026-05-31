#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "engine/simplify.h"
#include "output/printer.h"

using namespace axion;

static std::string simp(const std::string& input) {
    Arena a;
    Expr* e = parse(a, input);
    e = simplify(a, e);
    return print(e);
}

TEST(Simplify, AddZero) { EXPECT_EQ(simp("x + 0"), "x"); }
TEST(Simplify, MulOne) { EXPECT_EQ(simp("x * 1"), "x"); }
TEST(Simplify, MulZero) { EXPECT_EQ(simp("x * 0"), "0"); }
TEST(Simplify, ConstantFold) { EXPECT_EQ(simp("2 + 3"), "5"); EXPECT_EQ(simp("2 * 3"), "6"); }
TEST(Simplify, CombineLikeTerms) { EXPECT_EQ(simp("x + x"), "2*x"); EXPECT_EQ(simp("2*x + 3*x"), "5*x"); }
TEST(Simplify, PowerRules) { EXPECT_EQ(simp("x^0"), "1"); EXPECT_EQ(simp("x^1"), "x"); EXPECT_EQ(simp("2^3"), "8"); }
TEST(Simplify, DoubleNeg) { EXPECT_EQ(simp("--x"), "x"); }
TEST(Simplify, SubtractSelf) { EXPECT_EQ(simp("x - x"), "0"); }
TEST(Simplify, Factorial) { EXPECT_EQ(simp("5!"), "120"); EXPECT_EQ(simp("0!"), "1"); }
TEST(Simplify, RationalAdd) { EXPECT_EQ(simp("1/3 + 1/6"), "1/2"); }
TEST(Simplify, RationalMul) { EXPECT_EQ(simp("(2/3) * (3/4)"), "1/2"); }
