import random
import time
import util

from typing import Callable, Dict, List, Tuple

CARMICHAEL_NUMBERS = [561, 1105, 1729, 2465, 2821, 6601, 8911]
STRONG_PSEUDOPRIMES_BASE2 = [2047, 3277, 4033, 4681, 8321, 15841, 29341]


def split_even_part(number: int) -> Tuple[int, int]:
    power_of_two = 0
    odd_part = number
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1
    return power_of_two, odd_part


def jacobi_symbol(numerator: int, denominator: int) -> int:
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


def fermat_round(candidate: int, base: int) -> bool:
    return util.power_modulo(base, candidate - 1, candidate) == 1


def euler_round(candidate: int, base: int) -> bool:
    if util.gcd(base, candidate) != 1:
        return False
    symbol = jacobi_symbol(base, candidate) % candidate
    return util.power_modulo(base, (candidate - 1) // 2, candidate) == symbol


def strong_round(candidate: int, base: int) -> bool:
    power_of_two, odd_part = split_even_part(candidate - 1)
    witness = util.power_modulo(base, odd_part, candidate)
    if witness == 1 or witness == candidate - 1:
        return True
    for _ in range(power_of_two - 1):
        witness = (witness * witness) % candidate
        if witness == candidate - 1:
            return True
    return False


TESTS: List[Tuple[str, Callable[[int, int], bool]]] = [
    ("fermat", fermat_round),
    ("solovay-strassen", euler_round),
    ("miller-rabin", strong_round),
]


def run_test(round_function: Callable[[int, int], bool], candidate: int,
             bases: List[int]) -> bool:
    if candidate < 2:
        return False
    if candidate == 2:
        return True
    if candidate % 2 == 0:
        return False
    for base in bases:
        if base % candidate == 0:
            continue
        if util.gcd(base, candidate) != 1:
            return False
        if not round_function(candidate, base):
            return False
    return True


def liar_counts(candidate: int) -> Dict[str, Tuple[int, int]]:
    counts: Dict[str, Tuple[int, int]] = {}
    coprime = [base for base in range(2, candidate - 1)
               if util.gcd(base, candidate) == 1]
    for name, round_function in TESTS:
        liars = sum(1 for base in coprime if round_function(candidate, base))
        counts[name] = (liars, len(coprime))
    return counts


def liar_table() -> None:
    print("--- 7 liar rates on hard composites, lower is better ---")
    print(f"{'n':>7}  {'factors':>18}  {'fermat':>15}  {'solovay-strassen':>16}"
          f"  {'miller-rabin':>15}")
    for candidate in (341, 561, 1105, 1729, 2047, 2465, 2821, 6601, 8911, 15841):
        counts = liar_counts(candidate)
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        cells = []
        for name, _ in TESTS:
            liars, total = counts[name]
            cells.append(f"{liars}/{total} = {liars / total:.3f}")
        print(f"{candidate:>7}  {factors:>18}  {cells[0]:>15}  {cells[1]:>16}  {cells[2]:>15}")
    print()


def theoretical_bounds(bound: int) -> None:
    print(f"--- 7 worst case liar rate over all odd composites below {bound} ---")
    primes = set(util.prime_list(bound))
    worst: Dict[str, Tuple[float, int]] = {name: (0.0, 0) for name, _ in TESTS}
    for candidate in range(9, bound, 2):
        if candidate in primes:
            continue
        coprime = [base for base in range(2, candidate - 1)
                   if util.gcd(base, candidate) == 1]
        if not coprime:
            continue
        for name, round_function in TESTS:
            liars = sum(1 for base in coprime if round_function(candidate, base))
            rate = liars / len(coprime)
            if rate > worst[name][0]:
                worst[name] = (rate, candidate)
    print(f"{'test':>17}  {'worst rate':>10}  {'attained at':>11}  {'theory':>8}")
    theory = {"fermat": "1.000", "solovay-strassen": "0.500", "miller-rabin": "0.250"}
    for name, _ in TESTS:
        rate, candidate = worst[name]
        print(f"{name:>17}  {rate:>10.4f}  {candidate:>11}  {theory[name]:>8}")
    print()


def error_after_k_rounds() -> None:
    print("--- 7 error probability bound after k independent random bases ---")
    print(f"{'k':>3}  {'fermat':>12}  {'solovay-strassen':>16}  {'miller-rabin':>14}")
    for rounds in (1, 2, 5, 10, 20, 40):
        print(f"{rounds:>3}  {'no bound':>12}  {0.5 ** rounds:>16.3e}"
              f"  {0.25 ** rounds:>14.3e}")
    print()


def agreement_sweep(bound: int) -> None:
    primes = set(util.prime_list(bound))
    print(f"--- 7 mistakes below {bound} with the fixed bases 2, 3, 5, 7 ---")
    bases = [2, 3, 5, 7]
    print(f"{'test':>17}  {'false primes':>12}  first few")
    for name, round_function in TESTS:
        wrong = [candidate for candidate in range(3, bound, 2)
                 if candidate not in primes and run_test(round_function, candidate, bases)]
        print(f"{name:>17}  {len(wrong):>12}  {wrong[:6]}")
    print()


def cost_table() -> None:
    print("--- 7 cost per round, one base, averaged over repeats ---")
    print(f"{'bits':>5}  {'repeats':>7}  {'fermat (us)':>11}  {'solovay-strassen (us)':>21}"
          f"  {'miller-rabin (us)':>17}")
    for bits in (32, 64, 128, 256, 512):
        candidate = random_odd_prime(bits)
        repeats = max(20, 4000 // bits)
        timings = []
        for _, round_function in TESTS:
            start = time.perf_counter()
            for _ in range(repeats):
                round_function(candidate, 2)
            timings.append((time.perf_counter() - start) / repeats * 1e6)
        print(f"{bits:>5}  {repeats:>7}  {timings[0]:>11.2f}  {timings[1]:>21.2f}"
              f"  {timings[2]:>17.2f}")
    print()


def random_odd_prime(bits: int) -> int:
    while True:
        candidate = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if run_test(strong_round, candidate, [2, 3, 5, 7, 11, 13, 17, 19, 23]):
            return candidate


def practical_recommendation() -> None:
    print("--- 7 what a library actually does: small trial division then Miller-Rabin ---")
    print(f"{'bits':>5}  {'candidates tried':>16}  {'time to find a prime (ms)':>25}")
    small_primes = util.prime_list(100)
    for bits in (32, 64, 128, 256):
        start = time.perf_counter()
        tried = 0
        while True:
            tried += 1
            candidate = random.getrandbits(bits) | (1 << (bits - 1)) | 1
            if any(candidate % prime == 0 for prime in small_primes if prime * prime <= candidate):
                continue
            if run_test(strong_round, candidate, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]):
                break
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{bits:>5}  {tried:>16}  {elapsed:>25.2f}")
    print()


def hard_case_summary() -> None:
    print("--- 7 who is fooled by what, single base 2 ---")
    print(f"{'n':>7}  {'kind':>22}  {'fermat':>9}  {'solovay-strassen':>16}"
          f"  {'miller-rabin':>12}")
    labelled = [(candidate, "Carmichael") for candidate in CARMICHAEL_NUMBERS]
    labelled += [(candidate, "strong pseudoprime 2") for candidate in STRONG_PSEUDOPRIMES_BASE2]
    for candidate, kind in sorted(set(labelled)):
        verdicts = []
        for _, round_function in TESTS:
            verdicts.append("prime" if run_test(round_function, candidate, [2]) else "composite")
        print(f"{candidate:>7}  {kind:>22}  {verdicts[0]:>9}  {verdicts[1]:>16}"
              f"  {verdicts[2]:>12}")
    print()


random.seed(20260920)
liar_table()
theoretical_bounds(8000)
error_after_k_rounds()
agreement_sweep(30000)
hard_case_summary()
cost_table()
practical_recommendation()
