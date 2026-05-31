#include "frontend/parser.h"
#include "frontend/lexer.h"
#include <stdexcept>
#include <unordered_set>

namespace axion {

namespace {

const std::unordered_set<std::string> KNOWN_FUNCS = {
    "sin", "cos", "tan", "ln", "log", "exp", "sqrt", "abs"
};

class Parser {
    std::vector<Token> tokens_;
    size_t pos_ = 0;
    Arena& arena_;

    const Token& peek() const { return tokens_[pos_]; }
    Token advance() { return tokens_[pos_++]; }

    bool match(TokenType t) {
        if (peek().type == t) { advance(); return true; }
        return false;
    }

    void expect(TokenType t) {
        if (!match(t))
            throw std::runtime_error("Expected token: " + std::to_string(static_cast<int>(t)));
    }

    // Pratt parser: precedence levels
    // 1: + -
    // 2: * /
    // 3: unary -
    // 4: ^  (right-associative)

    Expr* expr(int min_prec = 1) {
        Expr* left = prefix();

        while (true) {
            int prec = infix_prec();
            if (prec < min_prec) break;

            TokenType op = peek().type;
            advance();

            if (op == TokenType::PLUS || op == TokenType::MINUS) {
                Expr* right = expr(prec + 1);
                if (op == TokenType::MINUS)
                    right = make_neg(arena_, right);
                left = make_add(arena_, {left, right});
            } else if (op == TokenType::STAR || op == TokenType::SLASH) {
                Expr* right = expr(prec + 1);
                if (op == TokenType::SLASH)
                    right = make_pow(arena_, right, make_num(arena_, -1));
                left = make_mul(arena_, {left, right});
            } else if (op == TokenType::CARET) {
                Expr* right = expr(prec); // right-associative
                left = make_pow(arena_, left, right);
            }
        }
        return left;
    }

    int infix_prec() {
        switch (peek().type) {
            case TokenType::PLUS: case TokenType::MINUS: return 1;
            case TokenType::STAR: case TokenType::SLASH: return 2;
            case TokenType::CARET: return 4;
            default: return 0;
        }
    }

    Expr* prefix() {
        Token t = peek();

        if (t.type == TokenType::MINUS) {
            advance();
            Expr* operand = expr(3); // unary binds tighter than +- but looser than ^
            return make_neg(arena_, operand);
        }

        if (t.type == TokenType::NUMBER) {
            advance();
            return make_num(arena_, t.num_val);
        }

        if (t.type == TokenType::SYMBOL) {
            advance();
            if (KNOWN_FUNCS.count(t.text) && peek().type == TokenType::LPAREN) {
                expect(TokenType::LPAREN);
                Expr* arg = expr();
                expect(TokenType::RPAREN);
                return make_func(arena_, t.text, arg);
            }
            // Check for implicit multiplication: symbol followed by '('
            return make_sym(arena_, t.text);
        }

        if (t.type == TokenType::LPAREN) {
            advance();
            Expr* inner = expr();
            expect(TokenType::RPAREN);
            return inner;
        }

        throw std::runtime_error("Unexpected token: " + t.text);
    }

public:
    Parser(Arena& arena, std::vector<Token> tokens)
        : tokens_(std::move(tokens)), arena_(arena) {}

    Expr* parse_expr() {
        Expr* result = expr();
        if (peek().type != TokenType::END)
            throw std::runtime_error("Unexpected trailing input: " + peek().text);
        return result;
    }
};

} // anonymous namespace

Expr* parse(Arena& arena, const std::string& input) {
    auto tokens = tokenize(input);
    Parser p(arena, std::move(tokens));
    return p.parse_expr();
}

} // namespace axion
