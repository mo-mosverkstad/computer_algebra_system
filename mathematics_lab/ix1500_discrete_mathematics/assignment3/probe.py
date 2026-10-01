from typing import List, Dict, Tuple
import math

# N = 12620903
N=1057
base = math.ceil(math.sqrt(N))


def Q(x):
    return x ** 2 - N


def prime_list(bound: int) -> list[int]:
    """
    Generate a prime list up to a given integer bound.
    """
    if bound < 2:
        return []

    composite = [False] * (bound + 1)
    composite[0] = composite[1] = True

    for number in range(2, int(math.sqrt(bound)) + 1):
        if not composite[number]:
            marks = len(range(number * number, bound + 1, number))
            composite[number * number::number] = [True] * marks

    return [
        number for number in range(2, bound + 1)
        if not composite[number]
    ]


def sieve_factor_base(number: int, bound: int) -> list[int]:
    factor_base: list[int] = []

    for prime in prime_list(bound):
        if prime == 2:
            factor_base.append(prime)

        # Euler's criterion
        elif pow(number % prime, (prime - 1) // 2, prime) == 1:
            factor_base.append(prime)

    return factor_base


def prime_factorization(n: int) -> dict[int, int]:
    factors = {}
    divisor = 2

    while divisor * divisor <= n:
        while n % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            n //= divisor

        divisor += 1

    if n > 1:
        factors[n] = factors.get(n, 0) + 1

    return factors


def factors_to_latex(factors: dict[int, int]) -> str:
    """
    Convert a factor dictionary into a LaTeX multiplication expression.

    Example:
        {2: 1, 5: 3, 11: 1}
        -> 2\\times5^3\\times11
    """
    terms = []

    for prime, exponent in factors.items():
        if exponent == 1:
            terms.append(str(prime))
        else:
            terms.append(f"{prime}^{{{exponent}}}")

    return r"\times".join(terms)


def factorization_to_latex(
    x: int,
    q_x: int,
    factors: dict[int, int],
) -> str:
    """
    Produce one row in the requested LaTeX aligned format.
    """
    factor_expression = factors_to_latex(factors)

    return (
        rf"x&={x}, & Q(x)&={q_x}, "
        rf"& \operatorname{{factor}}(Q(x))&={factor_expression}\\"
    )

def matrix_to_latex(matrix: List[List[int]]) -> str:
    latex_rows = []
    for row in matrix:
        latex_rows.append(" & ".join(str(i) for i in row) + " \\\\")
    return (
        f"\\begin{{array}}{{*{{{len(matrix[0])}}}{{c}}}}\n"
        f"{"\n".join(latex_rows)}\n"
        "\\end{array}"
    )

def matrix_transpose(matrix: List[List[int]]) -> List[List[int]]:
    return [list(row) for row in zip(*matrix)]

def matrix_f2(matrix: List[List[int]]) -> List[List[int]]:
    return [[i % 2 for i in row] for row in matrix]

def pack_vectors(matrix: List[List[int]]) -> List[int]:
    packed_matrix = []
    for row in matrix:
        value = 0
        for i in row:
            value = value << 1 | i
        packed_matrix.append(value)
    return packed_matrix

def unpack_vectors(
    vectors: List[int],
    width: int,
) -> List[List[int]]:
    matrix = []

    for value in vectors:
        row = [(value >> i) & 1 for i in range(width - 1, -1, -1)]
        matrix.append(row)

    return matrix


def gf2_gauss_elimination(vectors: List[int]) -> List[int]:
    '''
    Gauss elimination of a matrix given in ...
    '''
    pivots: Dict[int, Tuple[int, int]] = {}
    dependencies: List[int] = []
    for index, vector in enumerate(vectors):
        mask = 1 << index
        while vector:
            lowest = vector & -vector
            if lowest not in pivots:
                pivots[lowest] = (vector, mask)
                break
            pivot_vector, pivot_mask = pivots[lowest]
            vector ^= pivot_vector
            mask ^= pivot_mask
        else:
            dependencies.append(mask)
    return dependencies

def is_smooth(
    factors: dict[int, int],
    factor_base: list[int],
) -> bool:
    """
    Return True if all prime factors belong to the factor base.
    """
    return all(prime in factor_base for prime in factors)


factor_base = sieve_factor_base(N, 18)
matrix: List[List[int]] = []

print("factor base:", factor_base)
print(r"\begin{aligned}")

for x in range(base, base + 20):
    q_x = Q(x)
    factors = prime_factorization(q_x)

    if is_smooth(factors, factor_base):
        print(
            factorization_to_latex(
                x,
                q_x,
                factors
            )
        )
        matrix.append([factors.get(prime_factor, 0) for prime_factor in factor_base])

print(r"\end{aligned}")

print("\n")
print("matrix:")
for row in matrix:
    print(row)

print("matrix to LaTeX")
print(matrix_to_latex(matrix))

matrix_field_2 = matrix_f2(matrix)
print("matrix over f2 to LaTeX")
print(matrix_to_latex(matrix_field_2))
print("matrix over f2")
print(matrix_field_2)

print("\n")
print("Gauss elimination")
print([bin(i)[2:] for i in gf2_gauss_elimination(pack_vectors(matrix_field_2))])
