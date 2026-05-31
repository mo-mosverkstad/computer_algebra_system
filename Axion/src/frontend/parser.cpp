#include "frontend/parser.h"
#include "frontend/lexer.h"
#include <stdexcept>
#include <unordered_set>

namespace axion {

namespace {

const std::unordered_set<std::string> KNOWN_FUNCS = {
    "sin", "cos", "tan", "ln", "log", "exp", "sqrt", "abs",
    "diff", "expand", "eval", "sum", "prod", "lim",
    "integrate", "int", "solve", "factor", "collect",
    "taylor", "approx", "binom", "gcd", "lcm",
    "det", "transpose", "dot", "cross", "simp",
    "inverse", "inv", "rule", "rules", "taylor", "trigsimp", "tsimp",
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

    // Precedence levels:
    // 0: relational (=, !=, <, >, <=, >=)
    // 1: + -
    // 2: * /
    // 3: unary -
    // 4: ^ (right-associative)
    // 5: postfix (!)

    Expr* expr(int min_prec = 0) {
        Expr* left = prefix();

        // Postfix: factorial
        while (peek().type == TokenType::BANG) {
            advance();
            left = make_factorial(arena_, left);
        }

        while (true) {
            int prec = infix_prec();
            if (prec < min_prec) break;

            TokenType op = peek().type;

            // Relational operators
            if (prec == 0) {
                std::string rel_op = peek().text;
                advance();
                Expr* right = expr(1);
                left = make_rel(arena_, rel_op, left, right);
                continue;
            }

            advance();

            if (op == TokenType::PLUS || op == TokenType::MINUS) {
                Expr* right = expr(prec + 1);
                if (op == TokenType::MINUS)
                    right = make_neg(arena_, right);
                left = make_add(arena_, {left, right});
            } else if (op == TokenType::STAR) {
                Expr* right = expr(prec + 1);
                left = make_mul(arena_, {left, right});
            } else if (op == TokenType::SLASH) {
                Expr* right = expr(prec + 1);
                left = make_mul(arena_, {left, make_pow(arena_, right, make_num(arena_, -1))});
            } else if (op == TokenType::CARET) {
                Expr* right = expr(prec); // right-associative
                left = make_pow(arena_, left, right);
            }
        }
        return left;
    }

    int infix_prec() {
        switch (peek().type) {
            case TokenType::EQ: case TokenType::NEQ:
            case TokenType::LT: case TokenType::GT:
            case TokenType::LEQ: case TokenType::GEQ:
                return 0;
            case TokenType::PLUS: case TokenType::MINUS: return 1;
            case TokenType::STAR: case TokenType::SLASH: return 2;
            case TokenType::CARET: return 4;
            default: return -1;
        }
    }

    Expr* prefix() {
        Token t = peek();

        if (t.type == TokenType::MINUS) {
            advance();
            Expr* operand = expr(3);
            return make_neg(arena_, operand);
        }

        if (t.type == TokenType::NUMBER) {
            advance();
            return make_num(arena_, t.frac_num, t.frac_den);
        }

        if (t.type == TokenType::SYMBOL) {
            advance();
            // Check for function call
            if (KNOWN_FUNCS.count(t.text) && peek().type == TokenType::LPAREN) {
                return parse_func_call(t.text);
            }
            // Check for user function call: any symbol followed by (
            if (peek().type == TokenType::LPAREN && !KNOWN_FUNCS.count(t.text)) {
                // Could be user-defined function call
                return parse_func_call(t.text);
            }
            return make_sym(arena_, t.text);
        }

        if (t.type == TokenType::LPAREN) {
            advance();
            Expr* inner = expr();
            expect(TokenType::RPAREN);
            return inner;
        }

        // Matrix/vector literal: [...]
        if (t.type == TokenType::LBRACKET) {
            advance();
            return parse_bracket();
        }

        throw std::runtime_error("Unexpected token: " + t.text);
    }

    Expr* parse_bracket() {
        // Check if first element is another bracket → matrix [[...],[...]]
        if (peek().type == TokenType::LBRACKET) {
            // Matrix: [[a,b],[c,d]]
            std::vector<Expr*> all_elems;
            int rows = 0, cols = -1;
            while (true) {
                expect(TokenType::LBRACKET);
                int this_cols = 0;
                while (true) {
                    all_elems.push_back(expr());
                    this_cols++;
                    if (!match(TokenType::COMMA)) break;
                }
                expect(TokenType::RBRACKET);
                if (cols == -1) cols = this_cols;
                rows++;
                if (!match(TokenType::COMMA)) break;
            }
            expect(TokenType::RBRACKET);
            // Build matrix FUNC node
            auto* e = arena_.create<Expr>();
            e->type = NodeType::FUNC;
            e->name = "__matrix__" + std::to_string(rows) + "x" + std::to_string(cols);
            e->children = std::move(all_elems);
            return e;
        }
        // Vector: [a, b, c]
        std::vector<Expr*> elems;
        while (true) {
            elems.push_back(expr());
            if (!match(TokenType::COMMA)) break;
        }
        expect(TokenType::RBRACKET);
        int n = static_cast<int>(elems.size());
        auto* e = arena_.create<Expr>();
        e->type = NodeType::FUNC;
        e->name = "__matrix__1x" + std::to_string(n);
        e->children = std::move(elems);
        return e;
    }

    Expr* parse_func_call(const std::string& name) {
        expect(TokenType::LPAREN);
        // For single-arg functions, parse as before
        // For multi-arg, collect comma-separated args
        if (peek().type == TokenType::RPAREN) {
            advance();
            return make_func(arena_, name, make_num(arena_, 0));
        }
        Expr* first_arg = expr();
        if (peek().type == TokenType::RPAREN) {
            advance();
            return make_func(arena_, name, first_arg);
        }
        // Multi-arg: store as FUNC with multiple children
        auto* e = arena_.create<Expr>();
        e->type = NodeType::FUNC;
        e->name = name;
        e->children.push_back(first_arg);
        while (match(TokenType::COMMA)) {
            e->children.push_back(expr());
        }
        expect(TokenType::RPAREN);
        return e;
    }

public:
    Parser(Arena& arena, std::vector<Token> tokens)
        : tokens_(std::move(tokens)), arena_(arena) {}

    Expr* parse_expr() {
        Expr* result = expr();
        if (peek().type != TokenType::END && peek().type != TokenType::ASSIGN)
            throw std::runtime_error("Unexpected trailing input: " + peek().text);
        return result;
    }

    bool has_assign() const {
        for (const auto& t : tokens_)
            if (t.type == TokenType::ASSIGN) return true;
        return false;
    }

    // Parse "name := expr" or "name(args) := expr"
    struct Assignment { std::string name; std::vector<std::string> params; Expr* value; };

    Assignment parse_assignment() {
        Assignment a;
        Token name_tok = advance(); // symbol
        a.name = name_tok.text;
        if (peek().type == TokenType::LPAREN) {
            advance();
            while (peek().type != TokenType::RPAREN) {
                a.params.push_back(advance().text);
                if (peek().type == TokenType::COMMA) advance();
            }
            advance(); // )
        }
        expect(TokenType::ASSIGN);
        a.value = expr();
        return a;
    }
};

} // anonymous namespace

Expr* parse(Arena& arena, const std::string& input) {
    auto tokens = tokenize(input);
    Parser p(arena, std::move(tokens));
    return p.parse_expr();
}

// Check if input contains :=
bool has_assignment(const std::string& input) {
    auto tokens = tokenize(input);
    for (const auto& t : tokens)
        if (t.type == TokenType::ASSIGN) return true;
    return false;
}

AssignResult parse_assignment(Arena& arena, const std::string& input) {
    auto tokens = tokenize(input);
    Parser p(arena, std::move(tokens));
    auto a = p.parse_assignment();
    return {a.name, a.params, a.value};
}

} // namespace axion
