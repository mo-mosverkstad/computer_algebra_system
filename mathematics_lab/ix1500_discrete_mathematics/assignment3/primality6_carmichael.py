import util

from typing import List, Tuple

BOUND = 100000


def is_squarefree(number: int) -> bool:
    return all(power == 1 for power in util.factor_powers(number).values())


def korselt_criterion(candidate: int) -> Tuple[bool, List[int], List[Tuple[int, bool]]]:
    if candidate < 3 or candidate % 2 == 0:
        return False, [], []
    primes = util.factorize(candidate)
    if len(set(primes)) != len(primes) or len(primes) < 3:
        return False, primes, []
    divides = [(prime, (candidate - 1) % (prime - 1) == 0) for prime in primes]
    return all(ok for _, ok in divides), primes, divides


def is_carmichael(candidate: int) -> bool:
    if util.is_prime(candidate):
        return False
    passed, _, _ = korselt_criterion(candidate)
    return passed


def carmichael_by_definition(candidate: int) -> bool:
    if candidate < 2 or util.is_prime(candidate):
        return False
    for base in range(2, candidate):
        if util.gcd(base, candidate) != 1:
            continue
        if util.power_modulo(base, candidate - 1, candidate) != 1:
            return False
    return True


def carmichael_list(bound: int) -> List[int]:
    return [candidate for candidate in range(3, bound, 2) if is_carmichael(candidate)]


def worked_example() -> None:
    print("--- 6 Korselt's criterion on n = 561 ---")
    passed, primes, divides = korselt_criterion(561)
    print(f"561 = {' * '.join(str(prime) for prime in primes)}, squarefree")
    for prime, ok in divides:
        print(f"  (n-1) / (p-1) = 560 / {prime - 1} = {560 / (prime - 1):.4f}"
              f" -> {'divides' if ok else 'does not divide'}")
    print(f"-> {'Carmichael' if passed else 'not Carmichael'}")
    print()

    print("--- 6 Korselt fails on n = 341 ---")
    passed, primes, divides = korselt_criterion(341)
    print(f"341 = {' * '.join(str(prime) for prime in primes)}")
    print(f"only {len(primes)} prime factors, Carmichael needs at least 3"
          f" -> {'Carmichael' if passed else 'not Carmichael'}")
    print()


def korselt_against_definition() -> None:
    print("--- 6 Korselt vs brute force over all coprime bases ---")
    print(f"{'n':>6}  {'korselt':>7}  {'definition':>10}  {'agree':>5}")
    for candidate in range(3, 3000, 2):
        korselt = is_carmichael(candidate)
        definition = carmichael_by_definition(candidate)
        if korselt or definition:
            print(f"{candidate:>6}  {str(korselt):>7}  {str(definition):>10}"
                  f"  {str(korselt == definition):>5}")
    print()


def carmichael_table(bound: int) -> None:
    numbers = carmichael_list(bound)
    print(f"--- 6 Carmichael numbers below {bound} ---")
    print(f"count: {len(numbers)}")
    print(f"{'n':>7}  {'factors':>26}  {'prime factors':>13}  {'fermat base 2':>13}")
    for candidate in numbers:
        primes = util.factorize(candidate)
        fermat = util.power_modulo(2, candidate - 1, candidate) == 1
        print(f"{candidate:>7}  {' * '.join(str(p) for p in primes):>26}  {len(primes):>13}"
              f"  {'prime' if fermat else 'composite':>13}")
    print()


def density(bound: int) -> None:
    print(f"--- 6 Carmichael density up to {bound} ---")
    print(f"{'limit':>7}  {'primes':>7}  {'carmichael':>10}  {'ratio':>10}")
    numbers = carmichael_list(bound)
    for limit in (1000, 10000, 50000, bound):
        count = sum(1 for candidate in numbers if candidate <= limit)
        primes = len(util.prime_list(limit))
        print(f"{limit:>7}  {primes:>7}  {count:>10}  {count / primes:>10.6f}")
    print()


def three_factor_family() -> None:
    print("--- 6 Chernick family (6k+1)(12k+1)(18k+1) ---")
    print(f"{'k':>3}  {'6k+1':>6}  {'12k+1':>6}  {'18k+1':>6}  {'n':>12}  {'all prime':>9}"
          f"  {'carmichael':>10}")
    for k in range(1, 16):
        factor1, factor2, factor3 = 6 * k + 1, 12 * k + 1, 18 * k + 1
        all_prime = all(util.is_prime(factor) for factor in (factor1, factor2, factor3))
        number = factor1 * factor2 * factor3
        print(f"{k:>3}  {factor1:>6}  {factor2:>6}  {factor3:>6}  {number:>12}"
              f"  {str(all_prime):>9}  {str(is_carmichael(number)):>10}")
    print()


def miller_rabin_beats_them() -> None:
    print("--- 6 Miller-Rabin base 2 on the smallest Carmichael numbers ---")
    print(f"{'n':>7}  {'fermat 2':>9}  {'miller-rabin 2':>14}")
    for candidate in carmichael_list(10000):
        fermat = util.power_modulo(2, candidate - 1, candidate) == 1
        odd_part = candidate - 1
        power_of_two = 0
        while odd_part % 2 == 0:
            odd_part //= 2
            power_of_two += 1
        witness = util.power_modulo(2, odd_part, candidate)
        strong = witness == 1 or witness == candidate - 1
        for _ in range(power_of_two - 1):
            if strong:
                break
            witness = (witness * witness) % candidate
            if witness == candidate - 1:
                strong = True
        print(f"{candidate:>7}  {'prime' if fermat else 'composite':>9}"
              f"  {'prime' if strong else 'composite':>14}")
    print()


worked_example()
korselt_against_definition()
carmichael_table(BOUND)
density(BOUND)
three_factor_family()
miller_rabin_beats_them()
