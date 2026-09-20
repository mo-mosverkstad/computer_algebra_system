import time
import util

from typing import Dict, List, Optional, Tuple

TEST_NUMBERS = [5959, 10403, 90581, 540143, 1000003 * 2000003, 104729 * 1299709,
                299 * 1009, 15770708441, 48112959837082048697 % (10 ** 12)]


def largest_prime_factor(number: int) -> int:
    return util.factorize(number)[-1]


def smoothness_bound(prime: int) -> int:
    return largest_prime_factor(prime - 1)


def pollard_p_minus_1(number: int, bound: int,
                      base: int = 2) -> Tuple[Optional[int], int]:
    if number % 2 == 0:
        return 2, 0
    shared = util.gcd(base, number)
    if shared > 1:
        return shared, 0
    power = base
    steps = 0
    for prime in util.prime_list(bound):
        exponent = prime
        while exponent <= bound:
            steps += 1
            power = util.power_modulo(power, prime, number)
            shared = util.gcd(power - 1, number)
            if shared > 1:
                return shared, steps
            exponent *= prime
    return None, steps


def pollard_p_minus_1_trace(number: int, bound: int,
                            base: int = 2) -> List[Tuple[int, int, int, int]]:
    steps: List[Tuple[int, int, int, int]] = []
    power = base
    for prime in util.prime_list(bound):
        exponent = prime
        while exponent <= bound:
            power = util.power_modulo(power, prime, number)
            shared = util.gcd(power - 1, number)
            steps.append((prime, exponent, power, shared))
            if shared > 1:
                return steps
            exponent *= prime
    return steps


def pollard_p_minus_1_growing(number: int, extra_bases: Tuple[int, ...] = (3, 5, 7, 10, 21),
                              start: int = 8,
                              limit: int = 10 ** 6) -> Tuple[Optional[int], int, int]:
    bound = start
    while bound <= limit:
        factor, _ = pollard_p_minus_1(number, bound)
        if factor is not None and factor != number:
            return factor, bound, 2
        if factor == number:
            for base in extra_bases:
                factor, _ = pollard_p_minus_1(number, bound, base)
                if factor is not None and factor != number:
                    return factor, bound, base
        bound *= 2
    return None, bound, 2


def p_minus_1_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    if number % 2 == 0:
        return [2] + p_minus_1_factorize(number // 2)
    factor, _, _ = pollard_p_minus_1_growing(number)
    if factor is None:
        return [number]
    return sorted(p_minus_1_factorize(factor) + p_minus_1_factorize(number // factor))


def worked_example() -> None:
    number = 540143
    bound = 17
    print(f"--- 3 worked example, N = {number}, B = {bound}, a = 2 ---")
    print(f"{'q':>4}  {'q^k':>8}  {'a^M mod N':>10}  {'gcd(a^M - 1, N)':>15}")
    for prime, exponent, power, shared in pollard_p_minus_1_trace(number, bound):
        note = "  <- non trivial factor" if shared > 1 else ""
        print(f"{prime:>4}  {exponent:>8}  {power:>10}  {shared:>15}{note}")
    factor, _ = pollard_p_minus_1(number, bound)
    other = number // factor
    print(f"N = {factor} * {other}")
    for prime in (factor, other):
        factors = ' * '.join(str(p) for p in util.factorize(prime - 1))
        print(f"  {prime} - 1 = {factors}, largest prime factor {smoothness_bound(prime)}")
    print()


def why_it_works() -> None:
    print("--- 3 the smooth prime is the one that gets found ---")
    print(f"{'p':>8}  {'p - 1':>26}  {'largest prime factor':>20}")
    for prime in (641, 199, 1009, 104729, 1000003, 2000003):
        factors = ' * '.join(str(f) for f in util.factorize(prime - 1))
        print(f"{prime:>8}  {factors:>26}  {smoothness_bound(prime):>20}")
    print()


def bound_sweep() -> None:
    number = 299 * 1009
    print(f"--- 3 raising B on N = {number} = 299 * 1009 ---")
    print(f"{'B':>6}  {'factor':>8}  {'primes used':>11}")
    for bound in (5, 7, 13, 17, 31, 61, 127):
        factor, steps = pollard_p_minus_1(number, bound)
        shown = "none" if factor is None else str(factor)
        print(f"{bound:>6}  {shown:>8}  {steps:>11}")
    print(f"13 - 1 = {' * '.join(str(f) for f in util.factorize(12))}")
    print(f"23 - 1 = {' * '.join(str(f) for f in util.factorize(22))}")
    print(f"1009 - 1 = {' * '.join(str(f) for f in util.factorize(1008))}")
    print()


def factor_table() -> None:
    print("--- 3 Pollard p-1 with a growing bound ---")
    print(f"{'N':>22}  {'bits':>4}  {'p':>12}  {'q':>12}  {'B needed':>9}  {'base':>4}")
    for number in TEST_NUMBERS:
        factor, bound, base = pollard_p_minus_1_growing(number)
        if factor is None:
            verdict = "prime" if util.is_prime(number) else "gave up"
            print(f"{number:>22}  {number.bit_length():>4}  {verdict:>12}  {'-':>12}"
                  f"  {'-':>9}  {'-':>4}")
            continue
        other = number // factor
        print(f"{number:>22}  {number.bit_length():>4}  {min(factor, other):>12}"
              f"  {max(factor, other):>12}  {bound:>9}  {base:>4}")
    print()


def hard_case() -> None:
    print("--- 3 safe primes defeat the method, p - 1 = 2 * (large prime) ---")
    print(f"{'p':>10}  {'p - 1':>22}  {'safe?':>5}  {'B needed':>9}")
    for prime in (1019, 2039, 10007, 1000003):
        if not util.is_prime(prime):
            continue
        half = (prime - 1) // 2
        safe = util.is_prime(half)
        number = prime * 1000003 if prime != 1000003 else prime * 2000003
        _, bound, _ = pollard_p_minus_1_growing(number, start=32, limit=10 ** 5)
        factors = ' * '.join(str(f) for f in util.factorize(prime - 1))
        print(f"{prime:>10}  {factors:>22}  {str(safe):>5}  {bound:>9}")
    print()


def full_factorisation() -> None:
    print("--- 3 recursive p-1 gives the complete factorisation ---")
    print(f"{'N':>16}  {'p-1 method':>30}  {'agree':>5}")
    for number in (5959, 1729, 123456789, 540143, 2 ** 20 + 1, 90581 * 455459):
        by_method = p_minus_1_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>16}  {' * '.join(str(p) for p in by_method):>30}"
              f"  {str(by_method == by_trial):>5}")
    print()


def cost_comparison() -> None:
    print("--- 3 wall clock, p-1 vs rho style birthday cost vs trial division ---")
    print(f"{'N':>22}  {'p':>12}  {'p-1 smooth to':>13}  {'p-1 (ms)':>9}  {'trial (ms)':>10}")
    for number in (1000003 * 2000003, 104729 * 1299709, 15770708441):
        start = time.perf_counter()
        factor, _, _ = pollard_p_minus_1_growing(number)
        method_time = (time.perf_counter() - start) * 1000

        smaller = min(factor, number // factor)
        start = time.perf_counter()
        util.factorize(number)
        trial_time = (time.perf_counter() - start) * 1000
        print(f"{number:>22}  {smaller:>12}  {smoothness_bound(smaller):>13}"
              f"  {method_time:>9.3f}  {trial_time:>10.3f}")
    print()


worked_example()
why_it_works()
bound_sweep()
factor_table()
hard_case()
full_factorisation()
cost_comparison()
