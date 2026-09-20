import time
import util

from typing import List, Tuple

EXPONENTS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 89, 107, 127]


def mersenne(exponent: int) -> int:
    return (1 << exponent) - 1


def modulo_mersenne(value: int, exponent: int) -> int:
    mask = mersenne(exponent)
    while value > mask:
        value = (value & mask) + (value >> exponent)
    return mask if value == mask else value


def lucas_lehmer_sequence(exponent: int) -> List[int]:
    modulo = mersenne(exponent)
    residue = 4 % modulo
    residues = [residue]
    for _ in range(exponent - 2):
        residue = modulo_mersenne(residue * residue - 2, exponent) % modulo
        residues.append(residue)
    return residues


def lucas_lehmer_test(exponent: int) -> bool:
    if exponent == 2:
        return True
    if not util.is_prime(exponent):
        return False
    modulo = mersenne(exponent)
    residue = 4
    for _ in range(exponent - 2):
        residue = modulo_mersenne(residue * residue - 2, exponent) % modulo
    return residue == 0


def worked_example() -> None:
    exponent = 7
    print(f"--- 4 worked example, p = {exponent}, M_p = {mersenne(exponent)} ---")
    residues = lucas_lehmer_sequence(exponent)
    for index, residue in enumerate(residues):
        print(f"  s_{index} = {residue}")
    print(f"  s_(p-2) = {residues[-1]} -> "
          f"{'prime' if residues[-1] == 0 else 'composite'}")
    print()

    exponent = 11
    print(f"--- 4 worked example, p = {exponent}, M_p = {mersenne(exponent)} ---")
    residues = lucas_lehmer_sequence(exponent)
    for index, residue in enumerate(residues):
        print(f"  s_{index} = {residue}")
    factors = ' * '.join(str(prime) for prime in util.factorize(mersenne(exponent)))
    print(f"  s_(p-2) = {residues[-1]} -> "
          f"{'prime' if residues[-1] == 0 else 'composite'}, M_11 = {factors}")
    print()


def mersenne_table() -> None:
    print("--- 4 Mersenne numbers M_p for prime p ---")
    print(f"{'p':>4}  {'bits':>4}  {'M_p':>42}  {'lucas-lehmer':>12}  {'trial division':>14}")
    for exponent in EXPONENTS:
        probable = lucas_lehmer_test(exponent)
        number = mersenne(exponent)
        truth = util.is_prime(number) if number < 10 ** 12 else None
        truth_text = "?" if truth is None else ("prime" if truth else "composite")
        flag = "" if truth is None or probable == truth else "  <- wrong"
        shown = str(number) if number < 10 ** 40 else f"2^{exponent} - 1"
        print(f"{exponent:>4}  {number.bit_length():>4}  {shown:>42}"
              f"  {'prime' if probable else 'composite':>12}  {truth_text:>14}{flag}")
    print()


def composite_factors() -> None:
    print("--- 4 composite M_p and their smallest factors ---")
    print(f"{'p':>4}  {'M_p':>14}  factors")
    for exponent in EXPONENTS:
        number = mersenne(exponent)
        if number >= 10 ** 12 or lucas_lehmer_test(exponent):
            continue
        factors = ' * '.join(str(prime) for prime in util.factorize(number))
        print(f"{exponent:>4}  {number:>14}  {factors}")
    print()


def cost_table() -> None:
    print("--- 4 cost of Lucas-Lehmer against trial division ---")
    print(f"{'p':>4}  {'bits':>4}  {'lucas-lehmer (ms)':>17}  {'trial division (ms)':>19}")
    for exponent in (13, 17, 19, 31, 61, 89, 127):
        number = mersenne(exponent)
        start = time.perf_counter()
        lucas_lehmer_test(exponent)
        lucas_time = (time.perf_counter() - start) * 1000

        if number < 10 ** 10:
            start = time.perf_counter()
            util.is_prime(number)
            trial_time = f"{(time.perf_counter() - start) * 1000:.3f}"
        else:
            trial_time = "not feasible"
        print(f"{exponent:>4}  {number.bit_length():>4}  {lucas_time:>17.3f}  {trial_time:>19}")
    print()


def non_prime_exponent() -> None:
    print("--- 4 M_p is composite whenever p is composite ---")
    print(f"{'p':>4}  {'M_p':>10}  factors")
    for exponent in (4, 6, 8, 9, 10, 12, 15):
        number = mersenne(exponent)
        factors = ' * '.join(str(prime) for prime in util.factorize(number))
        print(f"{exponent:>4}  {number:>10}  {factors}")
    print()


worked_example()
mersenne_table()
composite_factors()
non_prime_exponent()
cost_table()
