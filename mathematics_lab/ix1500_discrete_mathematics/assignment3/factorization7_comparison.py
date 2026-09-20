import math
import random
import time
import util

from typing import Callable, Dict, List, Optional, Tuple

BALANCED = [5959, 84923, 13290059, 15770708441, 136117223861, 2000009000009,
            1000000016000000063]
LOPSIDED = [3 * 100003, 5 * 1000003, 7 * 10000019, 11 * 100000007]
CLOSE_PRIMES = [1234567891 * 1234567907, 999883 * 999979, 10000000019 * 10000000033]
SMOOTH_MINUS_1 = [421 * 1283, 104729 * 1299709, 115979 * 135979]


def trial_division(number: int) -> Optional[int]:
    if number % 2 == 0:
        return 2
    divisor = 3
    while divisor * divisor <= number:
        if number % divisor == 0:
            return divisor
        divisor += 2
    return None


def fermat_factor(number: int, max_steps: int = 2 * 10 ** 6) -> Optional[int]:
    if number % 2 == 0:
        return 2
    x = util.integer_sqrt(number)
    if x * x < number:
        x += 1
    for _ in range(max_steps):
        perfect, y = util.is_perfect_square(x * x - number)
        if perfect and x - y > 1:
            return x - y
        x += 1
    return None


def pollard_rho(number: int, shift: int, batch: int = 128) -> Optional[int]:
    if number % 2 == 0:
        return 2
    tortoise = hare = 2
    while True:
        saved_tortoise, saved_hare = tortoise, hare
        product = 1
        for _ in range(batch):
            tortoise = (tortoise * tortoise + shift) % number
            hare = (hare * hare + shift) % number
            hare = (hare * hare + shift) % number
            product = (product * abs(tortoise - hare)) % number
            if product == 0:
                break
        if util.gcd(product, number) == 1:
            continue
        tortoise, hare = saved_tortoise, saved_hare
        shared = 1
        for _ in range(batch):
            tortoise = (tortoise * tortoise + shift) % number
            hare = (hare * hare + shift) % number
            hare = (hare * hare + shift) % number
            shared = util.gcd(abs(tortoise - hare), number)
            if shared != 1:
                break
        return None if shared == number else shared


def pollard_rho_retry(number: int, attempts: int = 12) -> Optional[int]:
    for shift in range(1, attempts + 1):
        factor = pollard_rho(number, shift)
        if factor is not None:
            return factor
    return None


def pollard_p_minus_1(number: int, bound: int, base: int = 2) -> Optional[int]:
    if number % 2 == 0:
        return 2
    power = base
    for prime in util.prime_list(bound):
        exponent = prime
        while exponent <= bound:
            power = util.power_modulo(power, prime, number)
            shared = util.gcd(power - 1, number)
            if shared > 1:
                return shared
            exponent *= prime
    return None


def pollard_p_minus_1_growing(number: int, limit: int = 10 ** 6) -> Optional[int]:
    bound = 8
    while bound <= limit:
        factor = pollard_p_minus_1(number, bound)
        if factor is not None and factor != number:
            return factor
        if factor == number:
            for base in (3, 5, 7, 10, 21):
                factor = pollard_p_minus_1(number, bound, base)
                if factor is not None and factor != number:
                    return factor
        bound *= 2
    return None


def quadratic_factor_base(number: int, bound: int, allow_minus_one: bool) -> List[int]:
    base: List[int] = [-1] if allow_minus_one else []
    for prime in util.prime_list(bound):
        if prime == 2 or util.power_modulo(number % prime, (prime - 1) // 2, prime) == 1:
            base.append(prime)
    return base


def smooth_over_base(value: int, base: List[int]) -> Optional[Dict[int, int]]:
    powers: Dict[int, int] = {}
    if value < 0:
        if -1 not in base:
            return None
        powers[-1] = 1
        value = -value
    for prime in base:
        if prime == -1:
            continue
        while value % prime == 0:
            powers[prime] = powers.get(prime, 0) + 1
            value //= prime
    return powers if value == 1 else None


def combine_relations(number: int, base: List[int],
                      relations: List[Tuple[int, Dict[int, int]]]) -> Optional[int]:
    vectors = [util.exponent_vector(powers, base) for _, powers in relations]
    for mask in util.gf2_dependencies(vectors):
        left = 1
        combined: Dict[int, int] = {}
        for index in util.mask_indices(mask):
            candidate, powers = relations[index]
            left = (left * candidate) % number
            for prime, power in powers.items():
                combined[prime] = combined.get(prime, 0) + power
        right = 1
        for prime, power in combined.items():
            if prime == -1:
                continue
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        shared = util.gcd(abs(left - right), number)
        if 1 < shared < number:
            return shared
    return None


def continued_fraction_factor(number: int, attempts: int = 4000) -> Optional[int]:
    if number % 2 == 0:
        return 2
    root = util.integer_sqrt(number)
    if root * root == number:
        return root
    start = max(20, util.integer_sqrt(root) * 2)
    for scale in (1, 2, 4, 8):
        base = quadratic_factor_base(number, start * scale, True)
        relations: List[Tuple[int, Dict[int, int]]] = []
        numerator_previous, numerator = 1, root
        remainder_numerator, remainder_denominator = root, 1
        denominator_previous, denominator = 0, 1
        for _ in range(attempts):
            remainder_denominator = (number - remainder_numerator * remainder_numerator) \
                // remainder_denominator
            term = (root + remainder_numerator) // remainder_denominator
            remainder_numerator = term * remainder_denominator - remainder_numerator
            numerator_previous, numerator = numerator, term * numerator + numerator_previous
            denominator_previous, denominator = \
                denominator, term * denominator + denominator_previous
            residue = numerator * numerator - number * denominator * denominator
            powers = smooth_over_base(residue, base)
            if powers is not None:
                relations.append((numerator % number, powers))
                if len(relations) > len(base) + 20:
                    break
        if len(relations) > len(base):
            factor = combine_relations(number, base, relations)
            if factor is not None:
                return factor
    return None


def dixon_factor(number: int, attempts: int = 40000) -> Optional[int]:
    if number % 2 == 0:
        return 2
    root = util.integer_sqrt(number)
    start = max(20, util.integer_sqrt(root) * 3)
    for scale in (1, 2, 4):
        base = util.prime_list(start * scale)
        relations: List[Tuple[int, Dict[int, int]]] = []
        for _ in range(attempts):
            candidate = random.randrange(root + 1, number)
            residue = (candidate * candidate) % number
            if residue == 0:
                continue
            powers = smooth_over_base(residue, base)
            if powers is None:
                continue
            relations.append((candidate, powers))
            if len(relations) > len(base) + 10:
                break
        if len(relations) > len(base):
            factor = combine_relations(number, base, relations)
            if factor is not None:
                return factor
    return None


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


def natural_log(number: int) -> float:
    shift = number.bit_length() - 53
    if shift > 0:
        return math.log(number >> shift) + shift * math.log(2)
    return math.log(number)


def heuristic_bound(number: int) -> int:
    logarithm = natural_log(number)
    return max(30, int(math.exp(0.5 * math.sqrt(logarithm * math.log(logarithm)))))


def quadratic_sieve(number: int) -> Optional[int]:
    if number % 2 == 0:
        return 2
    start = heuristic_bound(number)
    for scale in (1, 2, 4, 8, 16, 32):
        bound = start * scale
        width = max(3000, bound * 100)
        base = quadratic_factor_base(number, bound, False)
        root = util.integer_sqrt(number)
        if root * root < number:
            root += 1
        residues = [(root + offset) * (root + offset) - number for offset in range(width)]
        remaining = list(residues)
        for prime in base:
            target = tonelli_shanks(number, prime)
            if target is None:
                continue
            for begin in {(target - root) % prime, (-target - root) % prime}:
                for index in range(begin, width, prime):
                    while remaining[index] % prime == 0:
                        remaining[index] //= prime
        relations: List[Tuple[int, Dict[int, int]]] = []
        for offset in range(width):
            if residues[offset] == 0 or remaining[offset] != 1:
                continue
            powers = smooth_over_base(residues[offset], base)
            if powers is not None:
                relations.append((root + offset, powers))
        if len(relations) > len(base):
            factor = combine_relations(number, base, relations)
            if factor is not None:
                return factor
    return None


METHODS: List[Tuple[str, Callable[[int], Optional[int]]]] = [
    ("trial division", trial_division),
    ("fermat", fermat_factor),
    ("pollard rho", pollard_rho_retry),
    ("pollard p-1", pollard_p_minus_1_growing),
    ("cfrac", continued_fraction_factor),
    ("dixon", dixon_factor),
    ("quadratic sieve", quadratic_sieve),
]


def timed_attempt(method: Callable[[int], Optional[int]],
                  number: int) -> Tuple[Optional[int], float]:
    start = time.perf_counter()
    factor = method(number)
    return factor, (time.perf_counter() - start) * 1000


def verify(number: int, factor: Optional[int]) -> bool:
    return factor is not None and 1 < factor < number and number % factor == 0


def skip_reason(name: str, number: int, smallest: int) -> str:
    if name == "trial division" and smallest > 5 * 10 ** 6:
        return "too slow"
    if name == "fermat" and abs(number // smallest - smallest) > 4 * 10 ** 6:
        return "too slow"
    if name == "dixon" and number > 10 ** 13:
        return "too slow"
    if name == "cfrac" and number > 10 ** 17:
        return "too slow"
    return ""


def smallest_prime_factor(number: int) -> int:
    if number % 2 == 0:
        return 2
    for prime in util.prime_list(1000):
        if number % prime == 0:
            return prime
    if util.is_probable_prime(number):
        return number
    factor = pollard_rho_retry(number)
    if factor is None:
        return number
    return min(smallest_prime_factor(factor), smallest_prime_factor(number // factor))


def run_family(title: str, numbers: List[int]) -> None:
    print(f"--- 7 {title} ---")
    header = f"{'N':>22}  {'bits':>4}  {'p':>12}"
    for name, _ in METHODS:
        header += f"  {name:>15}"
    print(header)
    for number in numbers:
        smallest = smallest_prime_factor(number)
        row = f"{number:>22}  {number.bit_length():>4}  {smallest:>12}"
        for name, method in METHODS:
            reason = skip_reason(name, number, smallest)
            if reason:
                row += f"  {reason:>15}"
                continue
            factor, elapsed = timed_attempt(method, number)
            row += f"  {elapsed:>15.2f}" if verify(number, factor) else f"  {'failed':>15}"
        print(row)
    print("times in milliseconds, 'too slow' means skipped to keep the run short")
    print()


def complexity_summary() -> None:
    print("--- 7 asymptotic cost, p is the smallest prime factor ---")
    print(f"{'method':>17}  {'complexity':>34}  {'wins when':>44}")
    rows = [
        ("trial division", "O(p), O(sqrt(N)) worst case", "p is tiny"),
        ("fermat", "O((q-p)^2 / sqrt(N)) steps", "p and q are almost equal"),
        ("pollard rho", "O(sqrt(p)) = O(N^(1/4)) expected", "p is much smaller than sqrt(N)"),
        ("pollard p-1", "O(B log B) for B-smooth p-1", "p-1 has only small prime factors"),
        ("cfrac", "L(N)^sqrt(2), subexponential", "general N, residues near sqrt(N)"),
        ("dixon", "L(N)^sqrt(2), worse constants", "provable bound, not practical"),
        ("quadratic sieve", "L(N)^1, subexponential", "general N of 40 to 100 digits"),
    ]
    for name, complexity, note in rows:
        print(f"{name:>17}  {complexity:>34}  {note:>44}")
    print("L(N) = exp(sqrt(log N * log log N))")
    print()


def subexponential_growth() -> None:
    print("--- 7 predicted operation counts, why subexponential matters ---")
    print(f"{'digits':>7}  {'bits':>5}  {'sqrt(N)':>12}  {'N^(1/4)':>12}  {'L(N)':>12}")
    for digits in (10, 20, 30, 40, 60, 80, 100):
        logarithm = digits * math.log(10)
        print(f"{digits:>7}  {int(digits * 3.32):>5}  {math.exp(logarithm / 2):>12.2e}"
              f"  {math.exp(logarithm / 4):>12.2e}"
              f"  {math.exp(math.sqrt(logarithm * math.log(logarithm))):>12.2e}")
    print()


def crossover() -> None:
    print("--- 7 measured crossover on balanced semiprimes ---")
    print(f"{'bits':>5}  {'N':>24}  {'rho (ms)':>9}  {'cfrac (ms)':>11}  {'qs (ms)':>9}"
          f"  {'fastest':>15}")
    for prime1, prime2 in ((59, 101), (3119, 4261), (115979, 135979), (1000003, 2000003),
                           (1000000007, 1000000009), (10000000019, 10000000033)):
        number = prime1 * prime2
        _, rho_time = timed_attempt(pollard_rho_retry, number)
        cfrac_time = float('inf')
        if number < 10 ** 17:
            _, cfrac_time = timed_attempt(continued_fraction_factor, number)
        _, sieve_time = timed_attempt(quadratic_sieve, number)
        timings = {"pollard rho": rho_time, "cfrac": cfrac_time, "quadratic sieve": sieve_time}
        best = min(timings, key=lambda name: timings[name])
        cfrac_text = "skipped" if cfrac_time == float('inf') else f"{cfrac_time:.2f}"
        print(f"{number.bit_length():>5}  {number:>24}  {rho_time:>9.2f}  {cfrac_text:>11}"
              f"  {sieve_time:>9.2f}  {best:>15}")
    print()


def rsa_relevance() -> None:
    print("--- 7 what this means for RSA key generation ---")
    print(f"{'weakness':>28}  {'exploited by':>17}  {'countermeasure':>42}")
    for weakness, method, fix in (
            ("p and q too close", "fermat", "require a large gap between p and q"),
            ("p much smaller than q", "pollard rho", "use primes of equal bit length"),
            ("p-1 only small factors", "pollard p-1", "use safe primes, p - 1 = 2 * p'"),
            ("p+1 only small factors", "williams p+1", "check p + 1 as well"),
            ("shared prime across keys", "pairwise gcd", "use a proper entropy source"),
            ("modulus simply too small", "quadratic sieve", "use at least 2048 bit moduli")):
        print(f"{weakness:>28}  {method:>17}  {fix:>42}")
    print()


random.seed(20260920)
complexity_summary()
subexponential_growth()
run_family("balanced semiprimes, the general case", BALANCED)
run_family("one tiny factor, trial division territory", LOPSIDED)
run_family("p and q almost equal, Fermat territory", CLOSE_PRIMES)
run_family("p-1 smooth, Pollard p-1 territory", SMOOTH_MINUS_1)
crossover()
rsa_relevance()
