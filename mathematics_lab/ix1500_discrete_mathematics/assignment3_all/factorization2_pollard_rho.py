import random
import time
import util

from typing import Dict, List, Optional, Tuple

TEST_NUMBERS = [8051, 10403, 90581, 455459, 1000003 * 2000003, 104729 * 1299709,
                1000003, 3215031751, 1000000007 * 1000000009]


def report_pair(number: int, factor: Optional[int]) -> Tuple[str, str]:
    if factor is None:
        return ("prime", "-") if util.is_prime(number) else ("gave up", "-")
    other = number // factor
    return str(min(factor, other)), str(max(factor, other))


def rho_polynomial(value: int, shift: int, modulo: int) -> int:
    return (value * value + shift) % modulo


def pollard_rho_trace(number: int, shift: int = 1, start: int = 2,
                      limit: int = 12) -> List[Tuple[int, int, int, int]]:
    steps: List[Tuple[int, int, int, int]] = []
    tortoise = hare = start
    for step in range(1, limit + 1):
        tortoise = rho_polynomial(tortoise, shift, number)
        hare = rho_polynomial(rho_polynomial(hare, shift, number), shift, number)
        shared = util.gcd(abs(tortoise - hare), number)
        steps.append((step, tortoise, hare, shared))
        if shared != 1:
            break
    return steps


def pollard_rho(number: int, shift: int = 1, start: int = 2) -> Tuple[Optional[int], int]:
    if number % 2 == 0:
        return 2, 0
    tortoise = hare = start
    shared = 1
    steps = 0
    while shared == 1:
        steps += 1
        tortoise = rho_polynomial(tortoise, shift, number)
        hare = rho_polynomial(rho_polynomial(hare, shift, number), shift, number)
        shared = util.gcd(abs(tortoise - hare), number)
    if shared == number:
        return None, steps
    return shared, steps


def pollard_rho_batched(number: int, shift: int = 1, start: int = 2,
                        batch: int = 128) -> Tuple[Optional[int], int]:
    if number % 2 == 0:
        return 2, 0
    tortoise = hare = start
    steps = 0
    while True:
        saved_tortoise, saved_hare = tortoise, hare
        product = 1
        for _ in range(batch):
            steps += 1
            tortoise = rho_polynomial(tortoise, shift, number)
            hare = rho_polynomial(rho_polynomial(hare, shift, number), shift, number)
            product = (product * abs(tortoise - hare)) % number
            if product == 0:
                break
        shared = util.gcd(product, number)
        if shared == 1:
            continue
        tortoise, hare = saved_tortoise, saved_hare
        for _ in range(batch):
            tortoise = rho_polynomial(tortoise, shift, number)
            hare = rho_polynomial(rho_polynomial(hare, shift, number), shift, number)
            shared = util.gcd(abs(tortoise - hare), number)
            if shared != 1:
                break
        if shared == number:
            return None, steps
        return shared, steps


def pollard_rho_retry(number: int, attempts: int = 12) -> Tuple[Optional[int], int, int]:
    total_steps = 0
    for shift in range(1, attempts + 1):
        factor, steps = pollard_rho_batched(number, shift)
        total_steps += steps
        if factor is not None:
            return factor, total_steps, shift
    return None, total_steps, attempts


def rho_factorize(number: int) -> List[int]:
    if number < 2:
        return []
    if util.is_prime(number):
        return [number]
    if number % 2 == 0:
        return [2] + rho_factorize(number // 2)
    factor, _, _ = pollard_rho_retry(number)
    if factor is None:
        return [number]
    return sorted(rho_factorize(factor) + rho_factorize(number // factor))


def cycle_shape(number: int, shift: int, start: int) -> Tuple[int, int]:
    seen: Dict[int, int] = {}
    value = start
    index = 0
    while value not in seen:
        seen[value] = index
        value = rho_polynomial(value, shift, number)
        index += 1
    return seen[value], index - seen[value]


def worked_example() -> None:
    number = 8051
    print(f"--- 2 worked example, N = {number}, f(x) = x^2 + 1, x_0 = 2 ---")
    print(f"{'step':>4}  {'tortoise':>8}  {'hare':>8}  {'gcd(|t-h|, N)':>13}")
    for step, tortoise, hare, shared in pollard_rho_trace(number):
        note = "  <- non trivial factor" if shared not in (1, number) else ""
        print(f"{step:>4}  {tortoise:>8}  {hare:>8}  {shared:>13}{note}")
    factor, steps = pollard_rho(number)
    print(f"N = {factor} * {number // factor} after {steps} steps")
    print()

    number = 455459
    print(f"--- 2 worked example, N = {number} ---")
    print(f"{'step':>4}  {'tortoise':>8}  {'hare':>8}  {'gcd(|t-h|, N)':>13}")
    for step, tortoise, hare, shared in pollard_rho_trace(number, 1, 2, 20):
        note = "  <- non trivial factor" if shared not in (1, number) else ""
        print(f"{step:>4}  {tortoise:>8}  {hare:>8}  {shared:>13}{note}")
    factor, steps = pollard_rho(number)
    print(f"N = {factor} * {number // factor} after {steps} steps")
    print()


def failure_and_retry() -> None:
    number = 25
    print(f"--- 2 the polynomial can fail, N = {number} ---")
    print(f"{'shift':>5}  {'start':>5}  {'factor':>8}  {'steps':>5}")
    for shift in (1, 2, 3):
        for start in (2, 3):
            factor, steps = pollard_rho(number, shift, start)
            shown = "collapse" if factor is None else str(factor)
            print(f"{shift:>5}  {start:>5}  {shown:>8}  {steps:>5}")
    factor, steps, shift = pollard_rho_retry(number)
    print(f"retrying shifts until success: factor {factor} with shift {shift}")
    print()


def cycle_table() -> None:
    print("--- 2 rho shape, tail and cycle lengths, birthday bound is ~sqrt(p) ---")
    print(f"{'N':>8}  {'p':>6}  {'shift':>5}  {'tail':>5}  {'cycle':>5}  {'tail+cycle':>10}"
          f"  {'sqrt(N)':>8}")
    for number in (8051, 10403, 90581, 455459):
        smallest = util.factorize(number)[0]
        for shift in (1, 2):
            tail, cycle = cycle_shape(number, shift, 2)
            print(f"{number:>8}  {smallest:>6}  {shift:>5}  {tail:>5}  {cycle:>5}"
                  f"  {tail + cycle:>10}  {util.integer_sqrt(number):>8}")
    print()


def factor_table() -> None:
    print("--- 2 Pollard rho on larger inputs ---")
    print(f"{'N':>22}  {'bits':>4}  {'p':>12}  {'q':>12}  {'steps':>9}  {'sqrt(p)':>8}")
    for number in TEST_NUMBERS:
        factor, steps, _ = pollard_rho_retry(number)
        smaller, larger = report_pair(number, factor)
        root = util.integer_sqrt(int(smaller)) if factor is not None else 0
        root_text = str(root) if factor is not None else "-"
        print(f"{number:>22}  {number.bit_length():>4}  {smaller:>12}"
              f"  {larger:>12}  {steps:>9}  {root_text:>8}")
    print()


def full_factorisation() -> None:
    print("--- 2 recursive rho gives the complete factorisation ---")
    print(f"{'N':>20}  {'pollard rho':>34}  {'agree with trial division':>25}")
    for number in (8051, 1729, 123456789, 600851475143, 2 ** 20 + 1, 9 * 5959):
        by_rho = rho_factorize(number)
        by_trial = util.factorize(number)
        print(f"{number:>20}  {' * '.join(str(p) for p in by_rho):>34}"
              f"  {str(by_rho == by_trial):>25}")
    print()


def cost_comparison() -> None:
    print("--- 2 wall clock against trial division ---")
    print(f"{'N':>22}  {'p':>12}  {'rho (ms)':>9}  {'trial (ms)':>10}  {'speedup':>8}")
    for number in (1000003 * 2000003, 104729 * 1299709, 455459 * 90581,
                   1000000007 * 1000000009):
        start = time.perf_counter()
        factor, _, _ = pollard_rho_retry(number)
        rho_time = (time.perf_counter() - start) * 1000

        smaller = min(factor, number // factor)
        if smaller < 10 ** 7:
            start = time.perf_counter()
            util.factorize(number)
            trial_time = (time.perf_counter() - start) * 1000
            speedup = f"{trial_time / rho_time:.2f}x"
            trial_text = f"{trial_time:.3f}"
        else:
            trial_text = "too slow"
            speedup = "-"
        print(f"{number:>22}  {smaller:>12}  {rho_time:>9.3f}  {trial_text:>10}  {speedup:>8}")
    print()


random.seed(20260920)
worked_example()
failure_and_retry()
cycle_table()
factor_table()
full_factorisation()
cost_comparison()
