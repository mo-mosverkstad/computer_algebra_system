import random
import time
import util

from typing import Dict, List, Optional, Tuple

TEST_NUMBERS = [5959, 8051, 84923, 13290059, 1000003 * 2000003, 104729 * 1299709,
                15770708441]


def factor_base(bound: int) -> List[int]:
    return util.prime_list(bound)


def smooth_over_base(value: int, base: List[int]) -> Optional[Dict[int, int]]:
    powers: Dict[int, int] = {}
    for prime in base:
        while value % prime == 0:
            powers[prime] = powers.get(prime, 0) + 1
            value = value // prime
    return powers if value == 1 else None


def dixon_relations(number: int, base: List[int], wanted: int,
                    attempts: int) -> List[Tuple[int, int, Dict[int, int]]]:
    relations: List[Tuple[int, int, Dict[int, int]]] = []
    root = util.integer_sqrt(number)
    for _ in range(attempts):
        candidate = random.randrange(root + 1, number)
        residue = (candidate * candidate) % number
        if residue == 0:
            continue
        powers = smooth_over_base(residue, base)
        if powers is None:
            continue
        relations.append((candidate, residue, powers))
        if len(relations) >= wanted:
            break
    return relations


def dixon_factor(number: int, bound: int = 0,
                 attempts: int = 40000) -> Tuple[Optional[int], int, int]:
    if number % 2 == 0:
        return 2, 0, 0
    if bound == 0:
        bound = max(20, util.integer_sqrt(util.integer_sqrt(number)) * 3)
    base = factor_base(bound)
    relations = dixon_relations(number, base, len(base) + 10, attempts)
    if not relations:
        return None, len(base), 0

    vectors = [util.exponent_vector(powers, base) for _, _, powers in relations]
    for mask in util.gf2_dependencies(vectors):
        left = 1
        combined: Dict[int, int] = {}
        for index in util.mask_indices(mask):
            candidate, _, powers = relations[index]
            left = (left * candidate) % number
            for prime, power in powers.items():
                combined[prime] = combined.get(prime, 0) + power
        right = 1
        for prime, power in combined.items():
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        shared = util.gcd(abs(left - right), number)
        if 1 < shared < number:
            return shared, len(base), len(relations)
    return None, len(base), len(relations)


def dixon_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    for prime in util.prime_list(100):
        if number % prime == 0:
            return sorted([prime] + dixon_factorize(number // prime))
    perfect, root = util.is_perfect_square(number)
    if perfect:
        return sorted(dixon_factorize(root) + dixon_factorize(root))
    factor, _, _ = dixon_factor(number)
    if factor is None:
        return [number]
    return sorted(dixon_factorize(factor) + dixon_factorize(number // factor))


def worked_example() -> None:
    number = 84923
    bound = 20
    base = factor_base(bound)
    print(f"--- 5 worked example, N = {number}, factor base {base} ---")
    relations = dixon_relations(number, base, 8, 200000)
    print(f"{'x':>8}  {'x^2 mod N':>10}  smooth factorisation")
    for candidate, residue, powers in relations:
        shown = ' * '.join(f"{prime}^{power}" for prime, power in sorted(powers.items()))
        print(f"{candidate:>8}  {residue:>10}  {shown}")
    print()

    vectors = [util.exponent_vector(powers, base) for _, _, powers in relations]
    print(f"{'x^2 mod N':>10}  {'vector mod 2':>12}")
    for (_, residue, _), vector in zip(relations, vectors):
        bits = ''.join('1' if vector >> index & 1 else '0' for index in range(len(base)))
        print(f"{residue:>10}  {bits:>12}")
    print()

    factor, _, count = dixon_factor(number, bound)
    print(f"a dependency gave gcd -> {factor}")
    print(f"N = {factor} * {number // factor}")
    print()


def congruence_detail() -> None:
    number = 5959
    bound = 20
    base = factor_base(bound)
    relations = dixon_relations(number, base, len(base) + 6, 200000)
    vectors = [util.exponent_vector(powers, base) for _, _, powers in relations]
    dependencies = util.gf2_dependencies(vectors)
    print(f"--- 5 building x^2 = y^2 (mod {number}) ---")
    for mask in dependencies[:4]:
        indices = util.mask_indices(mask)
        left = 1
        combined: Dict[int, int] = {}
        for index in indices:
            candidate, _, powers = relations[index]
            left = (left * candidate) % number
            for prime, power in powers.items():
                combined[prime] = combined.get(prime, 0) + power
        right = 1
        for prime, power in combined.items():
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        shared = util.gcd(abs(left - right), number)
        outcome = "trivial" if shared in (1, number) else f"factor {shared}"
        print(f"subset {indices}: x = {left}, y = {right}, gcd(x-y, N) = {shared}  {outcome}")
    print()


def smooth_probability() -> None:
    number = 13290059
    print(f"--- 5 how rare smooth residues are, N = {number} ---")
    print(f"{'bound':>6}  {'base':>5}  {'trials':>7}  {'smooth':>7}  {'rate':>8}")
    root = util.integer_sqrt(number)
    for bound in (20, 50, 100, 200, 500, 1000):
        base = factor_base(bound)
        trials = 20000
        smooth = 0
        for _ in range(trials):
            candidate = random.randrange(root + 1, number)
            if smooth_over_base((candidate * candidate) % number, base) is not None:
                smooth += 1
        print(f"{bound:>6}  {len(base):>5}  {trials:>7}  {smooth:>7}  {smooth / trials:>8.5f}")
    print()


def factor_table() -> None:
    print("--- 5 Dixon's method ---")
    print(f"{'N':>22}  {'bits':>4}  {'p':>12}  {'q':>12}  {'base':>5}  {'relations':>9}")
    for number in TEST_NUMBERS:
        factor, base_size, relations = dixon_factor(number)
        if factor is None:
            print(f"{number:>22}  {number.bit_length():>4}  {'gave up':>12}  {'-':>12}"
                  f"  {base_size:>5}  {relations:>9}")
            continue
        other = number // factor
        print(f"{number:>22}  {number.bit_length():>4}  {min(factor, other):>12}"
              f"  {max(factor, other):>12}  {base_size:>5}  {relations:>9}")
    print()


def base_size_tradeoff() -> None:
    number = 13290059
    print(f"--- 5 the factor base tradeoff, N = {number} ---")
    print(f"{'bound':>6}  {'base':>5}  {'factor':>8}  {'time (ms)':>9}")
    for bound in (10, 20, 50, 100, 300, 1000, 3000):
        start = time.perf_counter()
        factor, base_size, _ = dixon_factor(number, bound, 200000)
        elapsed = (time.perf_counter() - start) * 1000
        shown = "none" if factor is None else str(min(factor, number // factor))
        print(f"{bound:>6}  {base_size:>5}  {shown:>8}  {elapsed:>9.2f}")
    print()


def against_continued_fraction() -> None:
    number = 13290059
    root = util.integer_sqrt(number)
    print("--- 5 why random x is weaker than the continued fraction choice ---")
    residues = [(random.randrange(root + 1, number) ** 2) % number for _ in range(6)]
    print(f"random x^2 mod N: {residues}")
    print(f"typical size ~ N = {number}, so smoothness is unlikely")
    print(f"continued fraction residues stay below 2*sqrt(N) = {2 * root}")
    print()


def full_factorisation() -> None:
    print("--- 5 recursive Dixon ---")
    print(f"{'N':>16}  {'dixon':>30}  {'agree':>5}")
    for number in (5959, 8051, 1729, 84923, 123456789, 13290059):
        by_dixon = dixon_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>16}  {' * '.join(str(p) for p in by_dixon):>30}"
              f"  {str(by_dixon == by_trial):>5}")
    print()


random.seed(20260920)
worked_example()
congruence_detail()
smooth_probability()
factor_table()
base_size_tradeoff()
against_continued_fraction()
full_factorisation()
