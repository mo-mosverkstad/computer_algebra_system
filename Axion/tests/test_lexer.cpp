#include <gtest/gtest.h>
#include "frontend/lexer.h"

using namespace axion;

TEST(Lexer, BasicTokens) {
    auto tokens = tokenize("2*x + 3");
    ASSERT_EQ(tokens.size(), 6u); // 2 * x + 3 END
    EXPECT_EQ(tokens[0].type, TokenType::NUMBER);
    EXPECT_DOUBLE_EQ(tokens[0].num_val, 2.0);
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

TEST(Lexer, PowerAndParens) {
    auto tokens = tokenize("x^2 + (y - 1)");
    EXPECT_EQ(tokens[0].type, TokenType::SYMBOL);
    EXPECT_EQ(tokens[1].type, TokenType::CARET);
    EXPECT_EQ(tokens[2].type, TokenType::NUMBER);
    EXPECT_EQ(tokens[3].type, TokenType::PLUS);
    EXPECT_EQ(tokens[4].type, TokenType::LPAREN);
}
