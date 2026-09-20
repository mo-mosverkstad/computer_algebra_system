import util

from typing import List, Tuple

CARMICHAEL_NUMBERS = [561, 1105, 1729, 2465, 2821, 6601, 8911]
EULER_PSEUDOPRIMES_BASE2 = [561, 1105, 1729, 1905, 2047, 2465, 3277]
TEST_CASES = [341, 561, 1105, 1729, 2047, 2465, 7919, 65537, 1000003]


def jacobi_symbol(numerator: int, denominator: int) -> int:
    if denominator <= 0 or denominator % 2 == 0:
        raise ValueError(f"jacobi needs odd positive denominator, got {denominator}")
    numerator = numerator % denominator
    symbol = 1
    while numerator != 0:
        while numerator % 2 == 0:
            numerator //= 2
            if denominator % 8 in (3, 5):
                symbol = -symbol
        numerator, denominator = denominator, numerator
        if numerator % 4 == 3 and denominator % 4 == 3:
            symbol = -symbol
        numerator = numerator % denominator
    return symbol if denominator == 1 else 0


def jacobi_by_legendre(numerator: int, denominator: int) -> int:
    symbol = 1
    for prime, power in util.factor_powers(denominator).items():
        residue = util.power_modulo(numerator % prime, (prime - 1) // 2, prime)
        legendre = 0 if numerator % prime == 0 else (1 if residue == 1 else -1)
        symbol *= legendre ** power
    return symbol


def solovay_strassen_round(candidate: int, base: int) -> Tuple[bool, int, int]:
    shared = util.gcd(base, candidate)
    if shared > 1:
        return False, 0, shared
    symbol = jacobi_symbol(base, candidate)
    residue = util.power_modulo(base, (candidate - 1) // 2, candidate)
    return residue == symbol % candidate, symbol, residue


def solovay_strassen_test(candidate: int,
                          bases: List[int]) -> Tuple[bool, List[Tuple[int, int, int, bool]]]:
    rounds: List[Tuple[int, int, int, bool]] = []
    if candidate < 2:
        return False, rounds
    if candidate == 2:
        return True, rounds
    if candidate % 2 == 0:
        return False, rounds
    for base in bases:
        if base % candidate == 0:
            continue
        passed, symbol, residue = solovay_strassen_round(candidate, base)
        rounds.append((base, symbol, residue, passed))
        if not passed:
            return False, rounds
    return True, rounds


def euler_liars(candidate: int) -> Tuple[int, int]:
    liars = 0
    total = 0
    for base in range(2, candidate - 1):
        if util.gcd(base, candidate) != 1:
            continue
        total += 1
        passed, _, _ = solovay_strassen_round(candidate, base)
        if passed:
            liars += 1
    return liars, total


def worked_example() -> None:
    candidate = 561
    print("--- 3 worked example, n = 561 ---")
    print(f"(n-1)/2 = {(candidate - 1) // 2}")
    for base in (2, 5, 8):
        passed, symbol, residue = solovay_strassen_round(candidate, base)
        print(f"a = {base}: (a/n) = {symbol:>2}, a^((n-1)/2) = {residue:>4} (mod {candidate})"
              f" -> {'pass' if passed else 'composite'}")
    print(f"561 = {' * '.join(str(prime) for prime in util.factorize(candidate))}")
    print()


def jacobi_check() -> None:
    print("--- 3 Jacobi by quadratic reciprocity vs product of Legendre symbols ---")
    print(f"{'a':>4}  {'n':>6}  {'reciprocity':>11}  {'legendre product':>16}  {'agree':>5}")
    for numerator, denominator in ((2, 561), (5, 561), (8, 561), (1001, 9907),
                                   (19, 45), (30, 59), (7, 15), (6, 561)):
        fast = jacobi_symbol(numerator, denominator)
        slow = jacobi_by_legendre(numerator, denominator)
        print(f"{numerator:>4}  {denominator:>6}  {fast:>11}  {slow:>16}"
              f"  {str(fast == slow):>5}")
    print()


def test_table(bases: List[int]) -> None:
    print(f"--- 3 Solovay-Strassen over bases {bases} ---")
    print(f"{'n':>8}  {'prime?':>6}  {'verdict':>9}  {'rounds':>6}  first witness")
    for candidate in TEST_CASES:
        probable, rounds = solovay_strassen_test(candidate, bases)
        truth = util.is_prime(candidate)
        verdict = "prime" if probable else "composite"
        flag = "" if probable == truth else "  <- wrong"
        if probable:
            reason = "none"
        else:
            base, symbol, residue, _ = rounds[-1]
            reason = f"a = {base}, (a/n) = {symbol}, a^((n-1)/2) = {residue}"
        print(f"{candidate:>8}  {str(truth):>6}  {verdict:>9}  {len(rounds):>6}  {reason}{flag}")
    print()


def euler_liar_density() -> None:
    print("--- 3 Euler liar density, theory says at most 1/2 ---")
    print(f"{'n':>7}  {'factors':>18}  {'coprime':>7}  {'liars':>6}  {'rate':>6}")
    for candidate in (341, 561, 1105, 1729, 2047, 2465, 3277):
        liars, total = euler_liars(candidate)
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}  {total:>7}  {liars:>6}  {liars / total:>6.3f}")
    print()


def against_fermat() -> None:
    print("--- 3 Euler condition is strictly stronger than Fermat ---")
    print(f"{'n':>7}  {'factors':>18}  {'fermat 2':>9}  {'euler 2':>9}")
    candidates = sorted(set([341] + EULER_PSEUDOPRIMES_BASE2 + CARMICHAEL_NUMBERS))
    for candidate in candidates:
        fermat = util.power_modulo(2, candidate - 1, candidate) == 1
        euler, _ = solovay_strassen_test(candidate, [2])
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}"
              f"  {'prime' if fermat else 'composite':>9}"
              f"  {'prime' if euler else 'composite':>9}")
    print()


worked_example()
jacobi_check()
test_table([2])
test_table([2, 3])
test_table([2, 3, 5, 7])
euler_liar_density()
against_fermat()
