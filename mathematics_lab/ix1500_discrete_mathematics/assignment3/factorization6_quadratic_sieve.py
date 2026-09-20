import math
import time
import util

from typing import Dict, List, Optional, Tuple

TEST_NUMBERS = [8051, 84923, 13290059, 1000003 * 2000003, 104729 * 1299709,
                15770708441, 1000000007 * 1000000009, 10000000019 * 10000000033]


def tonelli_shanks(residue: int, prime: int) -> Optional[int]:
    residue = residue % prime
    if residue == 0:
        return 0
    if prime == 2:
        return residue
    if util.power_modulo(residue, (prime - 1) // 2, prime) != 1:
        return None
    if prime % 4 == 3:
        return util.power_modulo(residue, (prime + 1) // 4, prime)

    power_of_two = 0
    odd_part = prime - 1
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1

    non_residue = 2
    while util.power_modulo(non_residue, (prime - 1) // 2, prime) != prime - 1:
        non_residue += 1

    root = util.power_modulo(residue, (odd_part + 1) // 2, prime)
    value = util.power_modulo(residue, odd_part, prime)
    shift = util.power_modulo(non_residue, odd_part, prime)
    order = power_of_two

    while value != 1:
        square = value
        level = 0
        while square != 1:
            square = (square * square) % prime
            level += 1
        correction = util.power_modulo(shift, 1 << (order - level - 1), prime)
        root = (root * correction) % prime
        shift = (correction * correction) % prime
        value = (value * shift) % prime
        order = level
    return root


def sieve_factor_base(number: int, bound: int) -> List[int]:
    base: List[int] = []
    for prime in util.prime_list(bound):
        if prime == 2:
            base.append(prime)
        elif util.power_modulo(number % prime, (prime - 1) // 2, prime) == 1:
            base.append(prime)
    return base


def sieve_interval(number: int, base: List[int],
                   width: int) -> List[Tuple[int, int, Dict[int, int]]]:
    root = util.integer_sqrt(number)
    if root * root < number:
        root += 1
    residues = [(root + offset) * (root + offset) - number for offset in range(width)]
    remaining = list(residues)

    for prime in base:
        target = tonelli_shanks(number, prime)
        if target is None:
            continue
        starts = {(target - root) % prime, (-target - root) % prime}
        for start in starts:
            for index in range(start, width, prime):
                while remaining[index] % prime == 0:
                    remaining[index] //= prime

    relations: List[Tuple[int, int, Dict[int, int]]] = []
    for offset in range(width):
        if residues[offset] == 0 or remaining[offset] != 1:
            continue
        powers: Dict[int, int] = {}
        value = residues[offset]
        for prime in base:
            while value % prime == 0:
                powers[prime] = powers.get(prime, 0) + 1
                value //= prime
        relations.append((root + offset, residues[offset], powers))
    return relations


def natural_log(number: int) -> float:
    shift = number.bit_length() - 53
    if shift > 0:
        return math.log(number >> shift) + shift * math.log(2)
    return math.log(number)


def heuristic_bound(number: int) -> int:
    logarithm = natural_log(number)
    return max(30, int(math.exp(0.5 * math.sqrt(logarithm * math.log(logarithm)))))


def quadratic_sieve_attempt(number: int, bound: int,
                            width: int) -> Tuple[Optional[int], int, int]:
    base = sieve_factor_base(number, bound)
    relations = sieve_interval(number, base, width)
    if len(relations) <= len(base):
        return None, len(base), len(relations)

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


def quadratic_sieve(number: int, bound: int = 0,
                    width: int = 0) -> Tuple[Optional[int], int, int]:
    if number % 2 == 0:
        return 2, 0, 0
    if bound != 0:
        return quadratic_sieve_attempt(number, bound, width or max(3000, bound * 100))
    start = heuristic_bound(number)
    base_size = relations = 0
    for scale in (1, 2, 4, 8, 16, 32):
        bound = start * scale
        factor, base_size, relations = quadratic_sieve_attempt(
            number, bound, max(3000, bound * 100))
        if factor is not None:
            return factor, base_size, relations
    return None, base_size, relations


def sieve_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    for prime in util.prime_list(100):
        if number % prime == 0:
            return sorted([prime] + sieve_factorize(number // prime))
    perfect, root = util.is_perfect_square(number)
    if perfect:
        return sorted(sieve_factorize(root) + sieve_factorize(root))
    factor, _, _ = quadratic_sieve(number)
    if factor is None:
        return [number]
    return sorted(sieve_factorize(factor) + sieve_factorize(number // factor))


def tonelli_check() -> None:
    print("--- 6 Tonelli-Shanks finds the square roots the sieve needs ---")
    print(f"{'N':>10}  {'p':>6}  {'p mod 4':>7}  {'root':>6}  {'root^2 mod p':>12}"
          f"  {'N mod p':>7}")
    number = 13290059
    for prime in (3, 5, 7, 11, 13, 17, 29, 37, 41, 97, 101):
        root = tonelli_shanks(number, prime)
        if root is None:
            print(f"{number:>10}  {prime:>6}  {prime % 4:>7}  {'none':>6}"
                  f"  {'N is not a QR':>12}  {number % prime:>7}")
            continue
        print(f"{number:>10}  {prime:>6}  {prime % 4:>7}  {root:>6}"
              f"  {root * root % prime:>12}  {number % prime:>7}")
    print()


def worked_example() -> None:
    number = 84923
    bound = 100
    width = 3000
    base = sieve_factor_base(number, bound)
    root = util.integer_sqrt(number) + 1
    print(f"--- 6 worked example, N = {number}, base {base} ---")
    print(f"ceil(sqrt(N)) = {root}, sieving Q(x) = x^2 - N")
    relations = sieve_interval(number, base, width)
    print(f"{'x':>6}  {'x - ceil(sqrt(N))':>17}  {'Q(x)':>10}  smooth factorisation")
    for candidate, residue, powers in relations[:10]:
        shown = ' * '.join(f"{prime}^{power}" for prime, power in sorted(powers.items()))
        print(f"{candidate:>6}  {candidate - root:>17}  {residue:>10}  {shown}")
    print(f"smooth values found in {width} offsets: {len(relations)}")
    print()

    factor, base_size, count = quadratic_sieve(number, bound, width)
    print(f"N = {factor} * {number // factor} from {count} relations over a base of {base_size}")
    print()


def sieving_beats_division() -> None:
    number = 13290059
    bound = 100
    base = sieve_factor_base(number, bound)
    width = 20000
    print(f"--- 6 sieving the whole interval at once, N = {number} ---")
    start = time.perf_counter()
    relations = sieve_interval(number, base, width)
    sieve_time = (time.perf_counter() - start) * 1000

    root = util.integer_sqrt(number) + 1
    start = time.perf_counter()
    by_division = 0
    for offset in range(width):
        value = (root + offset) ** 2 - number
        for prime in base:
            while value % prime == 0:
                value //= prime
        if value == 1:
            by_division += 1
    division_time = (time.perf_counter() - start) * 1000

    print(f"base size {len(base)}, interval {width}")
    print(f"sieve:          {len(relations):>5} smooth values in {sieve_time:>8.2f} ms")
    print(f"trial division: {by_division:>5} smooth values in {division_time:>8.2f} ms")
    print()


def base_size_tradeoff() -> None:
    number = 1000003 * 2000003
    print(f"--- 6 factor base size against sieve cost, N = {number} ---")
    print(f"{'bound':>6}  {'base':>5}  {'relations':>9}  {'factor':>10}  {'time (ms)':>9}")
    for bound in (50, 100, 200, 400, 800, 1600, 3200):
        start = time.perf_counter()
        factor, base_size, relations = quadratic_sieve(number, bound, bound * 120)
        elapsed = (time.perf_counter() - start) * 1000
        shown = "none" if factor is None else str(min(factor, number // factor))
        print(f"{bound:>6}  {base_size:>5}  {relations:>9}  {shown:>10}  {elapsed:>9.2f}")
    print()


def factor_table() -> None:
    print("--- 6 quadratic sieve ---")
    print(f"{'N':>24}  {'bits':>4}  {'p':>12}  {'q':>12}  {'base':>5}  {'relations':>9}"
          f"  {'time (ms)':>9}")
    for number in TEST_NUMBERS:
        start = time.perf_counter()
        factor, base_size, relations = quadratic_sieve(number)
        elapsed = (time.perf_counter() - start) * 1000
        if factor is None:
            print(f"{number:>24}  {number.bit_length():>4}  {'gave up':>12}  {'-':>12}"
                  f"  {base_size:>5}  {relations:>9}  {elapsed:>9.2f}")
            continue
        other = number // factor
        print(f"{number:>24}  {number.bit_length():>4}  {min(factor, other):>12}"
              f"  {max(factor, other):>12}  {base_size:>5}  {relations:>9}  {elapsed:>9.2f}")
    print()


def full_factorisation() -> None:
    print("--- 6 recursive quadratic sieve ---")
    print(f"{'N':>22}  {'quadratic sieve':>30}  {'agree':>5}")
    for number in (8051, 1729, 84923, 123456789, 13290059, 41255931679):
        by_sieve = sieve_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>22}  {' * '.join(str(p) for p in by_sieve):>30}"
              f"  {str(by_sieve == by_trial):>5}")
    print()


tonelli_check()
worked_example()
sieving_beats_division()
base_size_tradeoff()
factor_table()
full_factorisation()
