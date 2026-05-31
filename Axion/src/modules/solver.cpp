#include "modules/solver.h"
#include "engine/simplify.h"
#include "modules/polynomial.h"
#include <cmath>
#include <algorithm>

namespace axion {

namespace {

// Move everything to LHS: lhs - rhs = 0
Expr* to_lhs(Arena& arena, Expr* eq) {
    if (!eq->is_rel() || eq->name != "=") return nullptr;
    Expr* lhs = eq->children[0];
    Expr* rhs = eq->children[1];
    // lhs - rhs
    Expr* result = make_add(arena, {lhs, make_neg(arena, rhs)});
    return simplify(arena, result);
}

// Extract polynomial coefficients: expr in terms of var
// Returns coefficients[i] for var^i (constant, linear, quadratic...)
// Returns empty if not a polynomial in var
struct PolyCoeffs {
    std::vector<Expr*> coeffs; // coeffs[0] = constant, coeffs[1] = linear, etc.
    int degree;
};

bool contains_var(const Expr* e, const std::string& var) {
    if (!e) return false;
    if (e->is_sym() && e->name == var) return true;
    for (auto* c : e->children)
        if (contains_var(c, var)) return true;
    return false;
}

// Get the power of var in a simple term
// Returns -1 if term is not a simple power of var
int get_power(const Expr* e, const std::string& var) {
    if (e->is_sym() && e->name == var) return 1;
    if (e->is_pow() && e->children[0]->is_sym() && e->children[0]->name == var
        && e->children[1]->is_num() && e->children[1]->den == 1 && e->children[1]->num >= 0)
        return static_cast<int>(e->children[1]->num);
    return -1;
}

// Extract coefficient and power from a term
// e.g. 3*x^2 → (3, 2), -x → (-1, 1), 5 → (5, 0)
struct TermInfo { Expr* coeff; int power; };

TermInfo analyze_term(Arena& arena, Expr* e, const std::string& var) {
    if (!contains_var(e, var)) return {e, 0};

    if (e->is_sym() && e->name == var) return {make_num(arena, 1), 1};

    int p = get_power(e, var);
    if (p >= 0) return {make_num(arena, 1), p};

    if (e->is_neg()) {
        auto inner = analyze_term(arena, e->children[0], var);
        if (inner.power >= 0)
            return {simplify(arena, make_neg(arena, inner.coeff)), inner.power};
    }

    if (e->is_mul()) {
        std::vector<Expr*> const_parts;
        int var_power = 0;
        bool found_var = false;
        for (auto* f : e->children) {
            int fp = get_power(f, var);
            if (fp > 0) { var_power = fp; found_var = true; }
            else if (f->is_sym() && f->name == var) { var_power = 1; found_var = true; }
            else const_parts.push_back(f);
        }
        if (found_var) {
            Expr* coeff;
            if (const_parts.empty()) coeff = make_num(arena, 1);
            else if (const_parts.size() == 1) coeff = const_parts[0];
            else coeff = make_mul(arena, std::move(const_parts));
            return {simplify(arena, coeff), var_power};
        }
    }

    return {e, -1}; // can't analyze
}

PolyCoeffs extract_poly(Arena& arena, Expr* e, const std::string& var) {
    PolyCoeffs result;
    result.degree = -1;

    std::vector<Expr*> terms;
    if (e->is_add()) terms = e->children;
    else terms.push_back(e);

    // Find max degree
    int max_deg = 0;
    std::vector<TermInfo> infos;
    for (auto* t : terms) {
        TermInfo ti = analyze_term(arena, t, var);
        if (ti.power < 0) return result; // not a polynomial
        infos.push_back(ti);
        max_deg = std::max(max_deg, ti.power);
    }

    if (max_deg > 4) return result; // too high degree

    result.coeffs.resize(max_deg + 1, make_num(arena, 0));
    for (auto& ti : infos) {
        Expr* cur = result.coeffs[ti.power];
        result.coeffs[ti.power] = simplify(arena, make_add(arena, {cur, ti.coeff}));
    }
    result.degree = max_deg;
    return result;
}

} // anonymous namespace

std::vector<Expr*> solve(Arena& arena, Expr* equation, const std::string& var) {
    Expr* lhs = to_lhs(arena, equation);
    if (!lhs) return {};

    lhs = simplify(arena, lhs);
    // Expand to get polynomial form
    lhs = expand(arena, lhs);
    lhs = simplify(arena, lhs);

    PolyCoeffs poly = extract_poly(arena, lhs, var);
    if (poly.degree < 0) return {};

    // Linear: a*x + b = 0 → x = -b/a
    if (poly.degree == 1) {
        Expr* a = poly.coeffs[1];
        Expr* b = poly.coeffs[0];
        // x = -b/a
        Expr* sol = make_mul(arena, {make_neg(arena, b), make_pow(arena, a, make_num(arena, -1))});
        return {simplify(arena, sol)};
    }

    // Quadratic: a*x^2 + b*x + c = 0
    if (poly.degree == 2) {
        Expr* a = poly.coeffs[2];
        Expr* b = poly.coeffs[1];
        Expr* c = poly.coeffs[0];

        // Discriminant: b^2 - 4ac
        Expr* disc = make_add(arena, {
            make_pow(arena, b, make_num(arena, 2)),
            make_neg(arena, make_mul(arena, {make_num(arena, 4), a, c}))
        });
        disc = simplify(arena, disc);

        // Check if discriminant is a perfect square (for rational roots)
        if (disc->is_num() && disc->num >= 0 && disc->den == 1) {
            int64_t d = disc->num;
            int64_t sq = static_cast<int64_t>(std::sqrt(static_cast<double>(d)));
            if (sq * sq == d) {
                // Rational roots: (-b ± sqrt(disc)) / (2a)
                Expr* two_a = make_mul(arena, {make_num(arena, 2), a});
                Expr* neg_b = make_neg(arena, b);
                Expr* sqrt_d = make_num(arena, sq);

                Expr* sol1 = make_mul(arena, {
                    make_add(arena, {neg_b, sqrt_d}),
                    make_pow(arena, two_a, make_num(arena, -1))
                });
                Expr* sol2 = make_mul(arena, {
                    make_add(arena, {neg_b, make_neg(arena, sqrt_d)}),
                    make_pow(arena, two_a, make_num(arena, -1))
                });

                sol1 = simplify(arena, sol1);
                sol2 = simplify(arena, sol2);

                if (sq == 0) return {sol1}; // double root
                return {sol1, sol2};
            }
        }

        // Non-rational roots: return symbolic (-b ± sqrt(disc)) / (2a)
        Expr* two_a = make_mul(arena, {make_num(arena, 2), a});
        Expr* neg_b = make_neg(arena, b);
        Expr* sqrt_d = make_func(arena, "sqrt", disc);

        Expr* sol1 = make_mul(arena, {
            make_add(arena, {neg_b, sqrt_d}),
            make_pow(arena, two_a, make_num(arena, -1))
        });
        Expr* sol2 = make_mul(arena, {
            make_add(arena, {neg_b, make_neg(arena, sqrt_d)}),
            make_pow(arena, two_a, make_num(arena, -1))
        });
        return {simplify(arena, sol1), simplify(arena, sol2)};
    }

    // Degree 3+: Rational Root Theorem
    // Try all ±(factors of constant term) / (factors of leading coefficient)
    if (poly.degree >= 3) {
        Expr* leading = poly.coeffs[poly.degree];
        Expr* constant = poly.coeffs[0];

        // Only works if leading and constant are integers
        if (leading->is_num() && leading->den == 1 && constant->is_num() && constant->den == 1) {
            int64_t lead_val = std::abs(leading->num);
            int64_t const_val = std::abs(constant->num);

            // Get factors
            std::vector<int64_t> const_factors, lead_factors;
            for (int64_t i = 1; i <= const_val; ++i)
                if (const_val % i == 0) const_factors.push_back(i);
            if (const_factors.empty()) const_factors.push_back(0); // constant = 0 means x=0 is a root
            for (int64_t i = 1; i <= lead_val; ++i)
                if (lead_val % i == 0) lead_factors.push_back(i);

            // Try each candidate rational root p/q
            std::vector<Expr*> found_roots;
            std::vector<int64_t> current_coeffs(poly.degree + 1);
            for (int i = 0; i <= poly.degree; ++i) {
                if (poly.coeffs[i]->is_num() && poly.coeffs[i]->den == 1)
                    current_coeffs[i] = poly.coeffs[i]->num;
                else
                    goto not_all_integer; // can't use rational root theorem
            }

            {
                int current_degree = poly.degree;

                // Also try x=0 if constant is 0
                if (current_coeffs[0] == 0) {
                    found_roots.push_back(make_num(arena, 0));
                    // Divide out x: shift coefficients down
                    for (int i = 0; i < current_degree; ++i)
                        current_coeffs[i] = current_coeffs[i + 1];
                    current_degree--;
                }

                for (int64_t p : const_factors) {
                    for (int64_t q : lead_factors) {
                        if (p == 0 && q != 1) continue;
                        // Try +p/q and -p/q
                        for (int sign : {1, -1}) {
                            int64_t num = sign * p;
                            int64_t den = q;
                            // Evaluate polynomial at num/den using Horner's method
                            // To avoid fractions: multiply through by den^degree
                            // P(p/q) = 0 iff sum(coeff[i] * p^i * q^(n-i)) = 0
                            int64_t val = 0;
                            int64_t p_pow = 1;
                            int64_t q_pow = 1;
                            for (int i = 0; i < current_degree; ++i) q_pow *= den;
                            for (int i = 0; i <= current_degree; ++i) {
                                val += current_coeffs[i] * p_pow * q_pow;
                                p_pow *= num;
                                if (i < current_degree) q_pow /= den;
                            }
                            if (val == 0) {
                                found_roots.push_back(make_num(arena, num, den));
                                // Synthetic division: divide by (x - num/den)
                                // Equivalent to dividing by (den*x - num)
                                // Using Horner: new_coeffs[i] from top down
                                std::vector<int64_t> new_coeffs(current_degree);
                                new_coeffs[current_degree - 1] = current_coeffs[current_degree];
                                for (int i = current_degree - 2; i >= 0; --i) {
                                    // new_coeffs[i] = current_coeffs[i+1] + (num/den)*new_coeffs[i+1]
                                    // To stay integer: work with den*x - num division
                                    // Simpler: use rational synthetic division
                                    new_coeffs[i] = current_coeffs[i + 1] + new_coeffs[i + 1] * num / den;
                                }
                                // Verify: remainder should be 0
                                current_coeffs = new_coeffs;
                                current_degree--;
                                // Reset search for remaining polynomial
                                break;
                            }
                        }
                        if (static_cast<int>(found_roots.size()) > poly.degree - current_degree)
                            break; // found a root in this iteration
                    }
                    if (current_degree <= 2) break;
                }

                // Solve remaining quadratic/linear
                if (current_degree == 2) {
                    // Build quadratic from current_coeffs and solve
                    PolyCoeffs remaining;
                    remaining.degree = 2;
                    remaining.coeffs.resize(3);
                    for (int i = 0; i <= 2; ++i)
                        remaining.coeffs[i] = make_num(arena, current_coeffs[i]);

                    Expr* a2 = remaining.coeffs[2];
                    Expr* b2 = remaining.coeffs[1];
                    Expr* c2 = remaining.coeffs[0];
                    Expr* disc = simplify(arena, make_add(arena, {
                        make_pow(arena, b2, make_num(arena, 2)),
                        make_neg(arena, make_mul(arena, {make_num(arena, 4), a2, c2}))
                    }));
                    if (disc->is_num() && disc->num >= 0 && disc->den == 1) {
                        int64_t sq = static_cast<int64_t>(std::sqrt(static_cast<double>(disc->num)));
                        if (sq * sq == disc->num) {
                            int64_t b_val = current_coeffs[1];
                            int64_t a_val = current_coeffs[2];
                            found_roots.push_back(simplify(arena, make_num(arena, -b_val + sq, 2 * a_val)));
                            if (sq != 0)
                                found_roots.push_back(simplify(arena, make_num(arena, -b_val - sq, 2 * a_val)));
                        }
                    }
                } else if (current_degree == 1) {
                    found_roots.push_back(simplify(arena, make_num(arena, -current_coeffs[0], current_coeffs[1])));
                }
            }

            if (!found_roots.empty()) return found_roots;
        }
    }
    not_all_integer:

    return {};
}

Expr* factor(Arena& arena, Expr* e, const std::string& var) {
    e = expand(arena, e);
    e = simplify(arena, e);

    PolyCoeffs poly = extract_poly(arena, e, var);
    if (poly.degree < 2) return e;

    // Find all rational roots
    Expr* eq = make_rel(arena, "=", e, make_num(arena, 0));
    auto roots = solve(arena, eq, var);
    if (roots.empty()) return e;

    // Build factored form: leading_coeff * (x - r1) * (x - r2) * ...
    Expr* leading = poly.coeffs[poly.degree];
    std::vector<Expr*> factors;
    if (!(leading->is_num() && leading->num == 1 && leading->den == 1))
        factors.push_back(leading);

    for (auto* root : roots) {
        Expr* f = make_add(arena, {make_sym(arena, var), make_neg(arena, root)});
        factors.push_back(f);
    }

    // If we didn't find all roots, there's a remaining irreducible factor
    if (static_cast<int>(roots.size()) < poly.degree) {
        // Compute remaining factor by dividing original by found factors
        // For now, just return partial factoring
    }

    if (factors.size() == 1) return factors[0];
    return simplify(arena, make_mul(arena, std::move(factors)));
}

} // namespace axion
