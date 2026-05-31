#include "modules/matrix.h"
#include "engine/simplify.h"
#include "output/printer.h"
#include <sstream>
#include <stdexcept>

namespace axion {

Expr* make_matrix(Arena& arena, int rows, int cols, std::vector<Expr*> elements) {
    auto* e = arena.create<Expr>();
    e->type = NodeType::FUNC;
    e->name = "__matrix__" + std::to_string(rows) + "x" + std::to_string(cols);
    e->children = std::move(elements);
    return e;
}

bool is_matrix(const Expr* e) {
    return e && e->is_func() && e->name.substr(0, 10) == "__matrix__";
}

int matrix_rows(const Expr* e) {
    auto x = e->name.find('x', 10);
    return std::stoi(e->name.substr(10, x - 10));
}

int matrix_cols(const Expr* e) {
    auto x = e->name.find('x', 10);
    return std::stoi(e->name.substr(x + 1));
}

Expr* matrix_at(const Expr* e, int r, int c) {
    int cols = matrix_cols(e);
    return e->children[static_cast<size_t>(r * cols + c)];
}

Expr* matrix_add(Arena& arena, Expr* a, Expr* b) {
    int ra = matrix_rows(a), ca = matrix_cols(a);
    int rb = matrix_rows(b), cb = matrix_cols(b);
    if (ra != rb || ca != cb) return nullptr;

    std::vector<Expr*> elems;
    for (int i = 0; i < ra * ca; ++i) {
        Expr* sum = make_add(arena, {a->children[i], b->children[i]});
        elems.push_back(simplify(arena, sum));
    }
    return make_matrix(arena, ra, ca, std::move(elems));
}

Expr* matrix_mul(Arena& arena, Expr* a, Expr* b) {
    int ra = matrix_rows(a), ca = matrix_cols(a);
    int rb = matrix_rows(b), cb = matrix_cols(b);
    if (ca != rb) return nullptr;

    std::vector<Expr*> elems;
    for (int i = 0; i < ra; ++i) {
        for (int j = 0; j < cb; ++j) {
            std::vector<Expr*> terms;
            for (int k = 0; k < ca; ++k) {
                terms.push_back(make_mul(arena, {matrix_at(a, i, k), matrix_at(b, k, j)}));
            }
            Expr* sum = make_add(arena, std::move(terms));
            elems.push_back(simplify(arena, sum));
        }
    }
    return make_matrix(arena, ra, cb, std::move(elems));
}

Expr* matrix_scalar_mul(Arena& arena, Expr* scalar, Expr* mat) {
    int r = matrix_rows(mat), c = matrix_cols(mat);
    std::vector<Expr*> elems;
    for (int i = 0; i < r * c; ++i) {
        Expr* prod = make_mul(arena, {scalar, mat->children[i]});
        elems.push_back(simplify(arena, prod));
    }
    return make_matrix(arena, r, c, std::move(elems));
}

Expr* matrix_transpose(Arena& arena, Expr* m) {
    int r = matrix_rows(m), c = matrix_cols(m);
    std::vector<Expr*> elems;
    for (int j = 0; j < c; ++j)
        for (int i = 0; i < r; ++i)
            elems.push_back(matrix_at(m, i, j));
    return make_matrix(arena, c, r, std::move(elems));
}

Expr* matrix_det(Arena& arena, Expr* m) {
    int n = matrix_rows(m);
    if (n != matrix_cols(m)) return nullptr;

    if (n == 1) return matrix_at(m, 0, 0);

    if (n == 2) {
        // ad - bc
        Expr* ad = make_mul(arena, {matrix_at(m, 0, 0), matrix_at(m, 1, 1)});
        Expr* bc = make_mul(arena, {matrix_at(m, 0, 1), matrix_at(m, 1, 0)});
        return simplify(arena, make_add(arena, {ad, make_neg(arena, bc)}));
    }

    if (n == 3) {
        // Cofactor expansion along first row
        std::vector<Expr*> terms;
        for (int j = 0; j < 3; ++j) {
            // Build 2x2 minor
            std::vector<Expr*> minor_elems;
            for (int r = 1; r < 3; ++r)
                for (int c = 0; c < 3; ++c)
                    if (c != j) minor_elems.push_back(matrix_at(m, r, c));
            Expr* minor = make_matrix(arena, 2, 2, std::move(minor_elems));
            Expr* cofactor = make_mul(arena, {matrix_at(m, 0, j), matrix_det(arena, minor)});
            if (j % 2 == 1) cofactor = make_neg(arena, cofactor);
            terms.push_back(cofactor);
        }
        return simplify(arena, make_add(arena, std::move(terms)));
    }

    // General cofactor expansion for n > 3
    std::vector<Expr*> terms;
    for (int j = 0; j < n; ++j) {
        std::vector<Expr*> minor_elems;
        for (int r = 1; r < n; ++r)
            for (int c = 0; c < n; ++c)
                if (c != j) minor_elems.push_back(matrix_at(m, r, c));
        Expr* minor = make_matrix(arena, n - 1, n - 1, std::move(minor_elems));
        Expr* cofactor = make_mul(arena, {matrix_at(m, 0, j), matrix_det(arena, minor)});
        if (j % 2 == 1) cofactor = make_neg(arena, cofactor);
        terms.push_back(cofactor);
    }
    return simplify(arena, make_add(arena, std::move(terms)));
}

Expr* matrix_inverse(Arena& arena, Expr* m) {
    int n = matrix_rows(m);
    if (n != matrix_cols(m)) return nullptr;
    Expr* det = matrix_det(arena, m);
    if (!det || (det->is_num() && det->num == 0)) return nullptr;

    if (n == 2) {
        // [[d, -b], [-c, a]] / det
        Expr* inv_det = make_pow(arena, det, make_num(arena, -1));
        std::vector<Expr*> elems = {
            matrix_at(m, 1, 1),
            make_neg(arena, matrix_at(m, 0, 1)),
            make_neg(arena, matrix_at(m, 1, 0)),
            matrix_at(m, 0, 0)
        };
        Expr* adj = make_matrix(arena, 2, 2, std::move(elems));
        return matrix_scalar_mul(arena, simplify(arena, inv_det), adj);
    }

    return nullptr; // Only 2x2 inverse for now
}

Expr* vector_dot(Arena& arena, Expr* a, Expr* b) {
    if (!is_matrix(a) || !is_matrix(b)) return nullptr;
    int na = static_cast<int>(a->children.size());
    int nb = static_cast<int>(b->children.size());
    if (na != nb) return nullptr;

    std::vector<Expr*> terms;
    for (int i = 0; i < na; ++i)
        terms.push_back(make_mul(arena, {a->children[i], b->children[i]}));
    return simplify(arena, make_add(arena, std::move(terms)));
}

Expr* vector_cross(Arena& arena, Expr* a, Expr* b) {
    if (!is_matrix(a) || !is_matrix(b)) return nullptr;
    if (a->children.size() != 3 || b->children.size() != 3) return nullptr;

    // [a1,a2,a3] x [b1,b2,b3] = [a2*b3-a3*b2, a3*b1-a1*b3, a1*b2-a2*b1]
    std::vector<Expr*> elems = {
        simplify(arena, make_add(arena, {make_mul(arena, {a->children[1], b->children[2]}), make_neg(arena, make_mul(arena, {a->children[2], b->children[1]}))})),
        simplify(arena, make_add(arena, {make_mul(arena, {a->children[2], b->children[0]}), make_neg(arena, make_mul(arena, {a->children[0], b->children[2]}))})),
        simplify(arena, make_add(arena, {make_mul(arena, {a->children[0], b->children[1]}), make_neg(arena, make_mul(arena, {a->children[1], b->children[0]}))})),
    };
    return make_matrix(arena, 1, 3, std::move(elems));
}

std::string print_matrix(const Expr* e) {
    int r = matrix_rows(e), c = matrix_cols(e);
    std::ostringstream os;
    os << "[";
    for (int i = 0; i < r; ++i) {
        if (r > 1) os << "[";
        for (int j = 0; j < c; ++j) {
            if (j > 0) os << ", ";
            os << print(matrix_at(e, i, j));
        }
        if (r > 1) os << "]";
        if (i < r - 1) os << ", ";
    }
    os << "]";
    return os.str();
}

} // namespace axion
