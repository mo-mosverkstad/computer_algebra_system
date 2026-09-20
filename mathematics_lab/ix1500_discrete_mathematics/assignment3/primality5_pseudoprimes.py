import util

from typing import Dict, List, Tuple

BOUND = 30000


def split_even_part(number: int) -> Tuple[int, int]:
    power_of_two = 0
    odd_part = number
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1
    return power_of_two, odd_part


def is_fermat_pseudoprime(candidate: int, base: int) -> bool:
    if util.gcd(base, candidate) != 1:
        return False
    return util.power_modulo(base, candidate - 1, candidate) == 1


def is_euler_pseudoprime(candidate: int, base: int) -> bool:
    if util.gcd(base, candidate) != 1:
        return False
    residue = util.power_modulo(base, (candidate - 1) // 2, candidate)
    return residue == 1 or residue == candidate - 1


def is_strong_pseudoprime(candidate: int, base: int) -> bool:
    if util.gcd(base, candidate) != 1:
        return False
    power_of_two, odd_part = split_even_part(candidate - 1)
    witness = util.power_modulo(base, odd_part, candidate)
    if witness == 1 or witness == candidate - 1:
        return True
    for _ in range(power_of_two - 1):
        witness = (witness * witness) % candidate
        if witness == candidate - 1:
            return True
    return False


def collect(bound: int, base: int) -> Dict[str, List[int]]:
    primes = set(util.prime_list(bound))
    found: Dict[str, List[int]] = {"fermat": [], "euler": [], "strong": []}
    for candidate in range(3, bound, 2):
        if candidate in primes:
            continue
        if not is_fermat_pseudoprime(candidate, base):
            continue
        found["fermat"].append(candidate)
        if is_euler_pseudoprime(candidate, base):
            found["euler"].append(candidate)
        if is_strong_pseudoprime(candidate, base):
            found["strong"].append(candidate)
    return found


def hierarchy(bound: int, base: int) -> None:
    found = collect(bound, base)
    print(f"--- 5 pseudoprimes to base {base} below {bound} ---")
    print(f"fermat pseudoprimes: {len(found['fermat'])}")
    print(f"euler  pseudoprimes: {len(found['euler'])}")
    print(f"strong pseudoprimes: {len(found['strong'])}")
    print(f"first fermat: {found['fermat'][:10]}")
    print(f"first euler : {found['euler'][:10]}")
    print(f"first strong: {found['strong'][:10]}")
    strong_set = set(found["strong"])
    euler_set = set(found["euler"])
    print(f"strong subset of euler?: {strong_set <= euler_set}")
    print(f"euler subset of fermat?: {euler_set <= set(found['fermat'])}")
    print()


def separating_examples(bound: int, base: int) -> None:
    found = collect(bound, base)
    euler_set = set(found["euler"])
    strong_set = set(found["strong"])
    fermat_only = [n for n in found["fermat"] if n not in euler_set]
    euler_only = [n for n in found["euler"] if n not in strong_set]
    print(f"--- 5 where the classes separate, base {base} ---")
    print(f"{'n':>7}  {'factors':>22}  class")
    for candidate in sorted(fermat_only)[:5]:
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>22}  fermat only")
    for candidate in sorted(euler_only)[:5]:
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>22}  euler but not strong")
    for candidate in sorted(strong_set)[:5]:
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>22}  strong")
    print()


def smallest_common_liar(bound: int, bases: List[int]) -> None:
    primes = set(util.prime_list(bound))
    print(f"--- 5 smallest strong pseudoprime to all of {bases} ---")
    for candidate in range(3, bound, 2):
        if candidate in primes:
            continue
        if all(is_strong_pseudoprime(candidate, base) for base in bases):
            factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
            print(f"n = {candidate} = {factors}")
            break
    else:
        print(f"none below {bound}")
    print()


def base_growth(bound: int) -> None:
    print(f"--- 5 how many composites survive, bound {bound} ---")
    print(f"{'base':>5}  {'fermat':>6}  {'euler':>6}  {'strong':>6}")
    for base in (2, 3, 5, 7, 11, 13):
        found = collect(bound, base)
        print(f"{base:>5}  {len(found['fermat']):>6}  {len(found['euler']):>6}"
              f"  {len(found['strong']):>6}")
    print()


def cumulative_bases(bound: int) -> None:
    primes = set(util.prime_list(bound))
    print(f"--- 5 composites surviving the first k prime bases, bound {bound} ---")
    print(f"{'bases':>22}  {'survivors':>9}  first survivors")
    bases: List[int] = []
    for base in (2, 3, 5, 7, 11):
        bases.append(base)
        survivors = [candidate for candidate in range(3, bound, 2)
                     if candidate not in primes
                     and all(is_strong_pseudoprime(candidate, b) for b in bases)]
        print(f"{str(bases):>22}  {len(survivors):>9}  {survivors[:4]}")
    print()


hierarchy(BOUND, 2)
hierarchy(BOUND, 3)
separating_examples(BOUND, 2)
base_growth(BOUND)
cumulative_bases(BOUND)
smallest_common_liar(2 * 10 ** 6, [2, 3])
