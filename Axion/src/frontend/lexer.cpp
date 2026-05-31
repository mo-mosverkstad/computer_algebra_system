#include "frontend/lexer.h"
#include <cctype>
#include <stdexcept>
#include <cmath>

namespace axion {

std::vector<Token> tokenize(const std::string& input) {
    std::vector<Token> tokens;
    size_t i = 0;

    while (i < input.size()) {
        char c = input[i];

        if (std::isspace(c)) { ++i; continue; }

        // Numbers (integer or decimal → rational)
        if (std::isdigit(c) || (c == '.' && i + 1 < input.size() && std::isdigit(input[i + 1]))) {
            size_t start = i;
            bool has_dot = false;
            while (i < input.size() && (std::isdigit(input[i]) || input[i] == '.')) {
                if (input[i] == '.') has_dot = true;
                ++i;
            }
            std::string text = input.substr(start, i - start);
            Token tok;
            tok.type = TokenType::NUMBER;
            tok.text = text;
            if (has_dot) {
                tok.is_float = true;
                // Convert to rational: e.g. "3.14" → 314/100
                auto dot_pos = text.find('.');
                std::string digits = text.substr(0, dot_pos) + text.substr(dot_pos + 1);
                int64_t decimals = static_cast<int64_t>(text.size() - dot_pos - 1);
                tok.frac_num = std::stoll(digits);
                tok.frac_den = 1;
                for (int64_t d = 0; d < decimals; ++d) tok.frac_den *= 10;
            } else {
                tok.int_val = std::stoll(text);
                tok.frac_num = tok.int_val;
                tok.frac_den = 1;
            }
            tokens.push_back(tok);
            continue;
        }

        // Identifiers (allow _ for subscripts: x_1, x_(12))
        if (std::isalpha(c) || c == '_') {
            size_t start = i;
            while (i < input.size() && (std::isalnum(input[i]) || input[i] == '_'))
                ++i;
            // Check for subscript with parens: x_(12)
            if (i < input.size() && input[i] == '(' && i > start && input[i - 1] == '_') {
                ++i; // skip (
                while (i < input.size() && input[i] != ')') ++i;
                if (i < input.size()) ++i; // skip )
            }
            tokens.push_back({TokenType::SYMBOL, input.substr(start, i - start), 0, 0, 1, false});
            continue;
        }

        // Two-character operators
        if (i + 1 < input.size()) {
            std::string two = input.substr(i, 2);
            if (two == ":=") { tokens.push_back({TokenType::ASSIGN, ":=", 0, 0, 1, false}); i += 2; continue; }
            if (two == "!=") { tokens.push_back({TokenType::NEQ, "!=", 0, 0, 1, false}); i += 2; continue; }
            if (two == "<=") { tokens.push_back({TokenType::LEQ, "<=", 0, 0, 1, false}); i += 2; continue; }
            if (two == ">=") { tokens.push_back({TokenType::GEQ, ">=", 0, 0, 1, false}); i += 2; continue; }
        }

        // Single-character operators
        switch (c) {
            case '+': tokens.push_back({TokenType::PLUS, "+", 0, 0, 1, false}); break;
            case '-': tokens.push_back({TokenType::MINUS, "-", 0, 0, 1, false}); break;
            case '*': tokens.push_back({TokenType::STAR, "*", 0, 0, 1, false}); break;
            case '/': tokens.push_back({TokenType::SLASH, "/", 0, 0, 1, false}); break;
            case '^': tokens.push_back({TokenType::CARET, "^", 0, 0, 1, false}); break;
            case '(': tokens.push_back({TokenType::LPAREN, "(", 0, 0, 1, false}); break;
            case ')': tokens.push_back({TokenType::RPAREN, ")", 0, 0, 1, false}); break;
            case '[': tokens.push_back({TokenType::LBRACKET, "[", 0, 0, 1, false}); break;
            case ']': tokens.push_back({TokenType::RBRACKET, "]", 0, 0, 1, false}); break;
            case ',': tokens.push_back({TokenType::COMMA, ",", 0, 0, 1, false}); break;
            case '!': tokens.push_back({TokenType::BANG, "!", 0, 0, 1, false}); break;
            case '=': tokens.push_back({TokenType::EQ, "=", 0, 0, 1, false}); break;
            case '<': tokens.push_back({TokenType::LT, "<", 0, 0, 1, false}); break;
            case '>': tokens.push_back({TokenType::GT, ">", 0, 0, 1, false}); break;
            case '%': tokens.push_back({TokenType::SYMBOL, "%", 0, 0, 1, false}); break;
            default:
                throw std::runtime_error(std::string("Unknown character: ") + c);
        }
        ++i;
    }

    tokens.push_back({TokenType::END, "", 0, 0, 1, false});
    return tokens;
}

} // namespace axion
