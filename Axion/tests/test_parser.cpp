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
    Expr* e = parse(a, "2 + 3*x");
    EXPECT_EQ(e->type, NodeType::ADD);
    EXPECT_EQ(e->children[1]->type, NodeType::MUL);
}

TEST(Parser, Power) {
    Arena a;
    Expr* e = parse(a, "x^2");
    EXPECT_EQ(e->type, NodeType::POW);
    EXPECT_EQ(e->children[1]->num, 2);
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

TEST(Parser, Factorial) {
    Arena a;
    Expr* e = parse(a, "5!");
    EXPECT_EQ(e->type, NodeType::FACTORIAL);
    EXPECT_EQ(e->children[0]->num, 5);
}

TEST(Parser, Relational) {
    Arena a;
    Expr* e = parse(a, "x = 3");
    EXPECT_EQ(e->type, NodeType::REL);
    EXPECT_EQ(e->name, "=");
}

TEST(Parser, MultiArgFunc) {
    Arena a;
    Expr* e = parse(a, "diff(x^2, x)");
    EXPECT_EQ(e->type, NodeType::FUNC);
    EXPECT_EQ(e->name, "diff");
    EXPECT_EQ(e->children.size(), 2u);
}
