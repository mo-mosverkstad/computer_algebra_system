import time
import util

from typing import List, Optional, Tuple

TEST_NUMBERS = [5959, 8051, 10403, 90581, 2041, 1234577 * 1234567,
                999883 * 999979, 1000003 * 2000003, 104729 * 1299709]


def fermat_trace(number: int, limit: int = 12) -> List[Tuple[int, int, bool, int]]:
    steps: List[Tuple[int, int, bool, int]] = []
    x = util.integer_sqrt(number)
    if x * x < number:
        x += 1
    for _ in range(limit):
        square = x * x - number
        perfect, y = util.is_perfect_square(square)
        steps.append((x, square, perfect, y))
        if perfect:
            break
        x += 1
    return steps


def fermat_factor(number: int, max_steps: int = 10 ** 7) -> Tuple[Optional[Tuple[int, int]], int]:
    if number % 2 == 0:
        return (2, number // 2), 0
    x = util.integer_sqrt(number)
    if x * x < number:
        x += 1
    for steps in range(1, max_steps + 1):
        perfect, y = util.is_perfect_square(x * x - number)
        if perfect:
            return (x - y, x + y), steps
        x += 1
    return None, max_steps


def fermat_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    if number % 2 == 0:
        return [2] + fermat_factorize(number // 2)
    pair, _ = fermat_factor(number)
    if pair is None:
        return [number]
    factor1, factor2 = pair
    if factor1 == 1:
        return [number]
    return sorted(fermat_factorize(factor1) + fermat_factorize(factor2))


def worked_example() -> None:
    number = 5959
    print(f"--- 1 worked example, N = {number} ---")
    root = util.integer_sqrt(number)
    print(f"sqrt(N) = {root}.., smallest x = {root + 1}")
    for x, square, perfect, y in fermat_trace(number):
        note = f"  <- perfect square, y = {y}" if perfect else ""
        print(f"  x = {x}: x^2 - N = {square}{note}")
    pair, steps = fermat_factor(number)
    print(f"N = {pair[0]} * {pair[1]} after {steps} steps")
    print()

    number = 90581
    print(f"--- 1 worked example, N = {number} ---")
    for x, square, perfect, y in fermat_trace(number):
        note = f"  <- perfect square, y = {y}" if perfect else ""
        print(f"  x = {x}: x^2 - N = {square}{note}")
    pair, steps = fermat_factor(number)
    print(f"N = {pair[0]} * {pair[1]} after {steps} steps")
    print()


def factor_table() -> None:
    print("--- 1 Fermat factorisation against trial division ---")
    print(f"{'N':>22}  {'bits':>4}  {'p':>10}  {'q':>10}  {'|q-p|':>12}  "
          f"{'fermat steps':>12}  {'trial steps':>11}")
    for number in TEST_NUMBERS:
        pair, steps = fermat_factor(number)
        if pair is None:
            print(f"{number:>22}  {number.bit_length():>4}  {'gave up':>10}")
            continue
        factor1, factor2 = pair
        trial_steps = (min(factor1, factor2) - 1) // 2
        print(f"{number:>22}  {number.bit_length():>4}  {factor1:>10}  {factor2:>10}"
              f"  {abs(factor2 - factor1):>12}  {steps:>12}  {trial_steps:>11}")
    print()


def gap_experiment() -> None:
    print("--- 1 steps grow with the gap between the two primes ---")
    print(f"{'p':>8}  {'q':>8}  {'N':>14}  {'|q-p|':>8}  {'steps':>8}  {'(q-p)^2/(4*sqrt(N))':>19}")
    primes = util.prime_list(2000)
    anchor = 1009
    for other in (1013, 1039, 1103, 1229, 1499, 1999):
        if other not in primes:
            continue
        number = anchor * other
        _, steps = fermat_factor(number)
        bound = (other - anchor) ** 2 / (4 * util.integer_sqrt(number))
        print(f"{anchor:>8}  {other:>8}  {number:>14}  {other - anchor:>8}  {steps:>8}"
              f"  {bound:>19.1f}")
    print()


def cost_comparison() -> None:
    print("--- 1 wall clock, Fermat vs trial division ---")
    print(f"{'N':>22}  {'|q-p|':>12}  {'fermat (ms)':>11}  {'trial (ms)':>10}  {'winner':>6}")
    for number in (1234577 * 1234567, 999883 * 999979, 1000003 * 2000003, 104729 * 1299709):
        start = time.perf_counter()
        pair, _ = fermat_factor(number)
        fermat_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        util.factorize(number)
        trial_time = (time.perf_counter() - start) * 1000

        gap = abs(pair[1] - pair[0])
        winner = "fermat" if fermat_time < trial_time else "trial"
        print(f"{number:>22}  {gap:>12}  {fermat_time:>11.3f}  {trial_time:>10.3f}  {winner:>6}")
    print()


def full_factorisation() -> None:
    print("--- 1 recursive Fermat gives the complete factorisation ---")
    print(f"{'N':>14}  {'fermat':>28}  {'trial division':>28}  {'agree':>5}")
    for number in (5959, 8051, 90581, 4633, 1729, 2431, 123456789):
        by_fermat = fermat_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>14}  {' * '.join(str(p) for p in by_fermat):>28}"
              f"  {' * '.join(str(p) for p in by_trial):>28}"
              f"  {str(by_fermat == by_trial):>5}")
    print()


def worst_case() -> None:
    print("--- 1 worst case: N = 2*p with a tiny factor ---")
    print(f"{'N':>14}  {'p':>10}  {'q':>10}  {'steps':>10}  {'sqrt(N)/2':>10}")
    for prime in (101, 1009, 10007, 100003):
        number = 3 * prime
        pair, steps = fermat_factor(number)
        print(f"{number:>14}  {pair[0]:>10}  {pair[1]:>10}  {steps:>10}"
              f"  {util.integer_sqrt(number) // 2:>10}")
    print()


worked_example()
factor_table()
gap_experiment()
full_factorisation()
worst_case()
cost_comparison()
