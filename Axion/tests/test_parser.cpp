#include <gtest/gtest.h>
#include "core/arena.h"
#include "frontend/parser.h"
#include "output/printer.h"

using namespace axion;

TEST(Parser, SimpleAdd) {
    Arena a;
    Expr* e = parse(a, "x + y");
    EXPECT_EQ(e->type, NodeType::ADD);
    EXPECT_EQ(e->children.size(), 2u);
}

TEST(Parser, Precedence) {
    Arena a;
    // 2 + 3*x should parse as ADD(2, MUL(3, x))
    Expr* e = parse(a, "2 + 3*x");
    EXPECT_EQ(e->type, NodeType::ADD);
    EXPECT_EQ(e->children[1]->type, NodeType::MUL);
}

TEST(Parser, Power) {
    Arena a;
    Expr* e = parse(a, "x^2");
    EXPECT_EQ(e->type, NodeType::POW);
    EXPECT_EQ(e->children[0]->type, NodeType::SYM);
    EXPECT_EQ(e->children[1]->num, 2.0);
}

TEST(Parser, Function) {
    Arena a;
    Expr* e = parse(a, "sin(x)");
    EXPECT_EQ(e->type, NodeType::FUNC);
    EXPECT_EQ(e->name, "sin");
}

TEST(Parser, UnaryMinus) {
    Arena a;
    Expr* e = parse(a, "-x");
    EXPECT_EQ(e->type, NodeType::NEG);
}

TEST(Parser, ComplexExpr) {
    Arena a;
    Expr* e = parse(a, "2*x^2 + 3*x + 1");
    EXPECT_EQ(e->type, NodeType::ADD);
}
