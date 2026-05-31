#pragma once
#include "core/ast.h"
#include "core/arena.h"
#include <vector>

namespace axion {

// Matrix is stored as FUNC("__matrix__") with children = flattened elements
// name encodes dimensions as "__matrix__RxC" (e.g. "__matrix__2x3")

Expr* make_matrix(Arena& arena, int rows, int cols, std::vector<Expr*> elements);
bool is_matrix(const Expr* e);
int matrix_rows(const Expr* e);
int matrix_cols(const Expr* e);
Expr* matrix_at(const Expr* e, int r, int c);

// Operations
Expr* matrix_add(Arena& arena, Expr* a, Expr* b);
Expr* matrix_mul(Arena& arena, Expr* a, Expr* b);
Expr* matrix_scalar_mul(Arena& arena, Expr* scalar, Expr* mat);
Expr* matrix_transpose(Arena& arena, Expr* m);
Expr* matrix_det(Arena& arena, Expr* m);
Expr* matrix_inverse(Arena& arena, Expr* m);
Expr* vector_dot(Arena& arena, Expr* a, Expr* b);
Expr* vector_cross(Arena& arena, Expr* a, Expr* b);

// Print matrix
std::string print_matrix(const Expr* e);

} // namespace axion
