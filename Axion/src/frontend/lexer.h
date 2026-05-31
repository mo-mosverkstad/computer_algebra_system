#pragma once
#include <string>
#include <vector>

namespace axion {

enum class TokenType {
    NUMBER, SYMBOL, PLUS, MINUS, STAR, SLASH, CARET,
    LPAREN, RPAREN, COMMA, END
};

struct Token {
    TokenType type;
    std::string text;
    double num_val = 0.0;
};

std::vector<Token> tokenize(const std::string& input);

} // namespace axion
