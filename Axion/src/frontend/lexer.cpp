#include "frontend/lexer.h"
#include <cctype>
#include <stdexcept>

namespace axion {

std::vector<Token> tokenize(const std::string& input) {
    std::vector<Token> tokens;
    size_t i = 0;

    while (i < input.size()) {
        char c = input[i];

        if (std::isspace(c)) { ++i; continue; }

        if (std::isdigit(c) || c == '.') {
            size_t start = i;
            while (i < input.size() && (std::isdigit(input[i]) || input[i] == '.'))
                ++i;
            std::string text = input.substr(start, i - start);
            tokens.push_back({TokenType::NUMBER, text, std::stod(text)});
            continue;
        }

        if (std::isalpha(c) || c == '_') {
            size_t start = i;
            while (i < input.size() && (std::isalnum(input[i]) || input[i] == '_'))
                ++i;
            tokens.push_back({TokenType::SYMBOL, input.substr(start, i - start), 0.0});
            continue;
        }

        switch (c) {
            case '+': tokens.push_back({TokenType::PLUS, "+", 0}); break;
            case '-': tokens.push_back({TokenType::MINUS, "-", 0}); break;
            case '*': tokens.push_back({TokenType::STAR, "*", 0}); break;
            case '/': tokens.push_back({TokenType::SLASH, "/", 0}); break;
            case '^': tokens.push_back({TokenType::CARET, "^", 0}); break;
            case '(': tokens.push_back({TokenType::LPAREN, "(", 0}); break;
            case ')': tokens.push_back({TokenType::RPAREN, ")", 0}); break;
            case ',': tokens.push_back({TokenType::COMMA, ",", 0}); break;
            default:
                throw std::runtime_error(std::string("Unknown character: ") + c);
        }
        ++i;
    }

    tokens.push_back({TokenType::END, "", 0});
    return tokens;
}

} // namespace axion
