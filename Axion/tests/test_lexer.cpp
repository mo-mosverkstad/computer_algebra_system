#include <gtest/gtest.h>
#include "frontend/lexer.h"

using namespace axion;

TEST(Lexer, BasicTokens) {
    auto tokens = tokenize("2*x + 3");
    ASSERT_EQ(tokens.size(), 6u);
    EXPECT_EQ(tokens[0].type, TokenType::NUMBER);
    EXPECT_EQ(tokens[0].frac_num, 2);
    EXPECT_EQ(tokens[1].type, TokenType::STAR);
    EXPECT_EQ(tokens[2].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[2].text, "x");
    EXPECT_EQ(tokens[3].type, TokenType::PLUS);
    EXPECT_EQ(tokens[4].type, TokenType::NUMBER);
    EXPECT_EQ(tokens[5].type, TokenType::END);
}

TEST(Lexer, FunctionToken) {
    auto tokens = tokenize("sin(x)");
    EXPECT_EQ(tokens[0].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[0].text, "sin");
    EXPECT_EQ(tokens[1].type, TokenType::LPAREN);
}

TEST(Lexer, Factorial) {
    auto tokens = tokenize("5!");
    EXPECT_EQ(tokens[0].type, TokenType::NUMBER);
    EXPECT_EQ(tokens[1].type, TokenType::BANG);
}

TEST(Lexer, Relational) {
    auto tokens = tokenize("x <= 3");
    EXPECT_EQ(tokens[0].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[1].type, TokenType::LEQ);
    EXPECT_EQ(tokens[2].type, TokenType::NUMBER);
}

TEST(Lexer, Assignment) {
    auto tokens = tokenize("a := 5");
    EXPECT_EQ(tokens[0].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[1].type, TokenType::ASSIGN);
    EXPECT_EQ(tokens[2].type, TokenType::NUMBER);
}

TEST(Lexer, Subscript) {
    auto tokens = tokenize("x_1 + x_(12)");
    EXPECT_EQ(tokens[0].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[0].text, "x_1");
    EXPECT_EQ(tokens[2].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[2].text, "x_(12)");
}
