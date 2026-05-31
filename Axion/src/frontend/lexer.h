#pragma once
#include <string>
#include <vector>
#include <cstdint>

namespace axion {

enum class TokenType {
    NUMBER, SYMBOL, PLUS, MINUS, STAR, SLASH, CARET,
    LPAREN, RPAREN, COMMA, BANG, ASSIGN, // := 
    EQ, NEQ, LT, GT, LEQ, GEQ,          // relational
    LBRACKET, RBRACKET,                  // [ ]
    END
};

struct Token {
    TokenType type;
    std::string text;
    int64_t int_val = 0;
    int64_t frac_num = 0;  // for decimal: numerator
    int64_t frac_den = 1;  // for decimal: denominator
    bool is_float = false;
};

std::vector<Token> tokenize(const std::string& input);

} // namespace axion
