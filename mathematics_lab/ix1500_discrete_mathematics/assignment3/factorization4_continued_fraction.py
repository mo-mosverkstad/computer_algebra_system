import time
import util

from typing import Dict, List, Optional, Tuple

TEST_NUMBERS = [5959, 8051, 13290059, 1000003 * 2000003, 104729 * 1299709,
                15770708441, 1000000007 * 1000000009]


def continued_fraction_convergents(number: int, count: int) -> List[Tuple[int, int, int, int]]:
    root = util.integer_sqrt(number)
    if root * root == number:
        return []
    numerator_previous, numerator = 1, root
    denominator_previous, denominator = 0, 1
    remainder_numerator, remainder_denominator = root, 1
    terms: List[Tuple[int, int, int, int]] = []
    for _ in range(count):
        remainder_denominator = (number - remainder_numerator * remainder_numerator) \
            // remainder_denominator
        term = (root + remainder_numerator) // remainder_denominator
        remainder_numerator = term * remainder_denominator - remainder_numerator
        numerator_previous, numerator = numerator, term * numerator + numerator_previous
        denominator_previous, denominator = denominator, term * denominator + denominator_previous
        residue = (numerator * numerator - number * denominator * denominator)
        terms.append((term, numerator % number, denominator, residue))
    return terms


def factor_base(number: int, bound: int) -> List[int]:
    base = [-1]
    for prime in util.prime_list(bound):
        if prime == 2:
            base.append(prime)
            continue
        if util.power_modulo(number % prime, (prime - 1) // 2, prime) == 1:
            base.append(prime)
    return base


def smooth_over_base(value: int, base: List[int]) -> Optional[Dict[int, int]]:
    powers: Dict[int, int] = {}
    if value < 0:
        powers[-1] = 1
        value = -value
    for prime in base:
        if prime == -1:
            continue
        while value % prime == 0:
            powers[prime] = powers.get(prime, 0) + 1
            value = value // prime
    return powers if value == 1 else None


def continued_fraction_relations(number: int, base: List[int],
                                 wanted: int,
                                 attempts: int) -> List[Tuple[int, int, Dict[int, int]]]:
    relations: List[Tuple[int, int, Dict[int, int]]] = []
    for _, numerator, _, residue in continued_fraction_convergents(number, attempts):
        powers = smooth_over_base(residue, base)
        if powers is None:
            continue
        relations.append((numerator, residue, powers))
        if len(relations) >= wanted:
            break
    return relations


def continued_fraction_attempt(number: int, bound: int,
                               attempts: int) -> Tuple[Optional[int], int, int]:
    base = factor_base(number, bound)
    relations = continued_fraction_relations(number, base, len(base) + 20, attempts)
    if not relations:
        return None, len(base), 0

    vectors = [util.exponent_vector(powers, base) for _, _, powers in relations]
    for mask in util.gf2_dependencies(vectors):
        indices = util.mask_indices(mask)
        left = 1
        combined: Dict[int, int] = {}
        for index in indices:
            numerator, _, powers = relations[index]
            left = (left * numerator) % number
            for prime, power in powers.items():
                combined[prime] = combined.get(prime, 0) + power
        right = 1
        for prime, power in combined.items():
            if prime == -1:
                continue
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        shared = util.gcd(abs(left - right), number)
        if 1 < shared < number:
            return shared, len(base), len(relations)
    return None, len(base), len(relations)


def continued_fraction_factor(number: int, bound: int = 0,
                              attempts: int = 4000) -> Tuple[Optional[int], int, int]:
    if number % 2 == 0:
        return 2, 0, 0
    if bound != 0:
        return continued_fraction_attempt(number, bound, attempts)
    start = max(20, util.integer_sqrt(util.integer_sqrt(number)) * 2)
    for scale in (1, 2, 4, 8):
        factor, base_size, relations = continued_fraction_attempt(
            number, start * scale, attempts)
        if factor is not None:
            return factor, base_size, relations
    return None, base_size, relations


def cfrac_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    for prime in util.prime_list(100):
        if number % prime == 0:
            return sorted([prime] + cfrac_factorize(number // prime))
    perfect, root = util.is_perfect_square(number)
    if perfect:
        return sorted(cfrac_factorize(root) + cfrac_factorize(root))
    factor, _, _ = continued_fraction_factor(number)
    if factor is None:
        return [number]
    return sorted(cfrac_factorize(factor) + cfrac_factorize(number // factor))


def worked_example() -> None:
    number = 13290059
    print(f"--- 4 expansion of sqrt({number}) ---")
    print(f"sqrt(N) = {util.integer_sqrt(number)}..")
    print(f"{'term':>6}  {'A_i mod N':>12}  {'Q_i = A_i^2 - N*B_i^2':>22}")
    for term, numerator, _, residue in continued_fraction_convergents(number, 10):
        print(f"{term:>6}  {numerator:>12}  {residue:>22}")
    print(f"every |Q_i| < 2*sqrt(N) = {2 * util.integer_sqrt(number)}")
    print()


def relation_example() -> None:
    number = 13290059
    bound = 40
    base = factor_base(number, bound)
    print(f"--- 4 smooth relations for N = {number}, factor base {base} ---")
    relations = continued_fraction_relations(number, base, 8, 600)
    print(f"{'A_i mod N':>12}  {'Q_i':>10}  factorisation of Q_i")
    for numerator, residue, powers in relations:
        shown = ' * '.join(f"{prime}^{power}" for prime, power in sorted(powers.items()))
        print(f"{numerator:>12}  {residue:>10}  {shown}")
    print()

    factor, base_size, count = continued_fraction_factor(number, bound)
    print(f"combining relations gave the factor {factor}")
    print(f"N = {factor} * {number // factor}")
    print()


def congruence_detail() -> None:
    number = 5959
    bound = 30
    base = factor_base(number, bound)
    relations = continued_fraction_relations(number, base, len(base) + 6, 2000)
    vectors = [util.exponent_vector(powers, base) for _, _, powers in relations]
    print(f"--- 4 exponent vectors mod 2 for N = {number}, base {base} ---")
    print(f"{'Q_i':>10}  {'vector':>12}")
    for (_, residue, _), vector in zip(relations, vectors):
        bits = ''.join('1' if vector >> index & 1 else '0' for index in range(len(base)))
        print(f"{residue:>10}  {bits:>12}")
    dependencies = util.gf2_dependencies(vectors)
    print(f"dependencies found: {len(dependencies)}")
    for mask in dependencies[:3]:
        print(f"  subset {util.mask_indices(mask)}")
    print()


def factor_table() -> None:
    print("--- 4 continued fraction factorisation ---")
    print(f"{'N':>22}  {'bits':>4}  {'p':>12}  {'q':>12}  {'base':>5}  {'relations':>9}")
    for number in TEST_NUMBERS:
        factor, base_size, relations = continued_fraction_factor(number)
        if factor is None:
            print(f"{number:>22}  {number.bit_length():>4}  {'gave up':>12}  {'-':>12}"
                  f"  {base_size:>5}  {relations:>9}")
            continue
        other = number // factor
        print(f"{number:>22}  {number.bit_length():>4}  {min(factor, other):>12}"
              f"  {max(factor, other):>12}  {base_size:>5}  {relations:>9}")
    print()


def base_size_effect() -> None:
    number = 1000003 * 2000003
    print(f"--- 4 factor base size against work, N = {number} ---")
    print(f"{'bound':>6}  {'base':>5}  {'factor':>12}  {'time (ms)':>9}")
    for bound in (50, 100, 200, 400, 800, 1600):
        start = time.perf_counter()
        factor, base_size, _ = continued_fraction_factor(number, bound)
        elapsed = (time.perf_counter() - start) * 1000
        shown = "none" if factor is None else str(min(factor, number // factor))
        print(f"{bound:>6}  {base_size:>5}  {shown:>12}  {elapsed:>9.2f}")
    print()


def full_factorisation() -> None:
    print("--- 4 recursive continued fraction factorisation ---")
    print(f"{'N':>22}  {'cfrac':>30}  {'agree':>5}")
    for number in (5959, 8051, 1729, 123456789, 13290059, 41255931679):
        by_cfrac = cfrac_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>22}  {' * '.join(str(p) for p in by_cfrac):>30}"
              f"  {str(by_cfrac == by_trial):>5}")
    print()


def cost_comparison() -> None:
    print("--- 4 wall clock against trial division ---")
    print(f"{'N':>22}  {'p':>12}  {'cfrac (ms)':>11}  {'trial (ms)':>10}")
    for number in (1000003 * 2000003, 104729 * 1299709, 1000000007 * 1000000009):
        start = time.perf_counter()
        factor, _, _ = continued_fraction_factor(number)
        cfrac_time = (time.perf_counter() - start) * 1000
        smaller = "none" if factor is None else str(min(factor, number // factor))

        if factor is not None and min(factor, number // factor) < 10 ** 7:
            start = time.perf_counter()
            util.factorize(number)
            trial_text = f"{(time.perf_counter() - start) * 1000:.3f}"
        else:
            trial_text = "too slow"
        print(f"{number:>22}  {smaller:>12}  {cfrac_time:>11.3f}  {trial_text:>10}")
    print()


worked_example()
relation_example()
congruence_detail()
factor_table()
base_size_effect()
full_factorisation()
cost_comparison()
