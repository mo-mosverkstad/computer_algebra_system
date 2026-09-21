import util

from typing import List, Tuple

CARMICHAEL_NUMBERS = [561, 1105, 1729, 2465, 2821, 6601, 8911]
STRONG_PSEUDOPRIMES_BASE2 = [2047, 3277, 4033, 4681, 8321, 15841, 29341]
TEST_CASES = [341, 561, 1105, 1729, 2047, 2465, 3215031751, 7919, 65537, 1000003]


def split_even_part(number: int) -> Tuple[int, int]:
    power_of_two = 0
    odd_part = number
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1
    return power_of_two, odd_part


def miller_rabin_round(candidate: int, base: int) -> Tuple[bool, List[int]]:
    power_of_two, odd_part = split_even_part(candidate - 1)
    witness = util.power_modulo(base, odd_part, candidate)
    squares = [witness]
    if witness == 1 or witness == candidate - 1:
        return True, squares
    for _ in range(power_of_two - 1):
        witness = (witness * witness) % candidate
        squares.append(witness)
        if witness == candidate - 1:
            return True, squares
        if witness == 1:
            return False, squares
    return False, squares


def miller_rabin_test(candidate: int, bases: List[int]) -> Tuple[bool, List[Tuple[int, bool]]]:
    rounds: List[Tuple[int, bool]] = []
    if candidate < 2:
        return False, rounds
    if candidate == 2:
        return True, rounds
    if candidate % 2 == 0:
        return False, rounds
    for base in bases:
        if base % candidate == 0:
            continue
        passed, _ = miller_rabin_round(candidate, base)
        rounds.append((base, passed))
        if not passed:
            return False, rounds
    return True, rounds


def strong_witnesses(candidate: int) -> Tuple[int, int]:
    witnesses = 0
    total = 0
    for base in range(2, candidate - 1):
        total += 1
        passed, _ = miller_rabin_round(candidate, base)
        if not passed:
            witnesses += 1
    return witnesses, total


def worked_example() -> None:
    candidate = 561
    power_of_two, odd_part = split_even_part(candidate - 1)
    print("--- 2 worked example, n = 561 ---")
    print(f"n - 1 = {candidate - 1} = 2^{power_of_two} * {odd_part}")
    for base in (2, 3):
        passed, squares = miller_rabin_round(candidate, base)
        print(f"a = {base}")
        print(f"  a^d        = {squares[0]} (mod {candidate})")
        for index, square in enumerate(squares[1:], start=1):
            note = ""
            if square == candidate - 1:
                note = "  <- -1, round passes"
            elif square == 1:
                note = "  <- 1 without -1 first, composite"
            print(f"  a^(2^{index}*d) = {square} (mod {candidate}){note}")
        print(f"  -> {'pass' if passed else 'composite'}")
    print()


def test_table(bases: List[int]) -> None:
    print(f"--- 2 Miller-Rabin over bases {bases} ---")
    print(f"{'n':>12}  {'prime?':>6}  {'verdict':>9}  {'rounds':>6}  first witness")
    for candidate in TEST_CASES:
        probable, rounds = miller_rabin_test(candidate, bases)
        truth = util.is_prime(candidate) if candidate < 10 ** 7 else None
        failing = [base for base, passed in rounds if not passed]
        verdict = "prime" if probable else "composite"
        truth_text = "?" if truth is None else str(truth)
        flag = "" if truth is None or probable == truth else "  <- wrong"
        witness = str(failing[0]) if failing else "none"
        print(f"{candidate:>12}  {truth_text:>6}  {verdict:>9}  {len(rounds):>6}"
              f"  a = {witness}{flag}")
    print()


def carmichael_table() -> None:
    print("--- 2 Carmichael numbers do not fool Miller-Rabin ---")
    print(f"{'n':>7}  {'factors':>18}  {'base 2':>9}  {'bases 2,3':>9}")
    for candidate in CARMICHAEL_NUMBERS:
        base2, _ = miller_rabin_test(candidate, [2])
        base23, _ = miller_rabin_test(candidate, [2, 3])
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}"
              f"  {'prime' if base2 else 'composite':>9}"
              f"  {'prime' if base23 else 'composite':>9}")
    print()


def witness_density() -> None:
    print("--- 2 witness density, theory says at least 3/4 ---")
    print(f"{'n':>7}  {'factors':>18}  {'bases':>7}  {'witnesses':>9}  {'rate':>6}")
    for candidate in (341, 561, 1105, 2047, 3277, 4033):
        witnesses, total = strong_witnesses(candidate)
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}  {total:>7}  {witnesses:>9}"
              f"  {witnesses / total:>6.3f}")
    print()


def strong_pseudoprime_table() -> None:
    print("--- 2 strong pseudoprimes to base 2 need a second base ---")
    print(f"{'n':>7}  {'factors':>18}  {'base 2':>9}  {'base 3':>9}")
    for candidate in STRONG_PSEUDOPRIMES_BASE2:
        base2, _ = miller_rabin_test(candidate, [2])
        base3, _ = miller_rabin_test(candidate, [3])
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}"
              f"  {'prime' if base2 else 'composite':>9}"
              f"  {'prime' if base3 else 'composite':>9}")
    print()


worked_example()
test_table([2])
test_table([2, 3])
test_table([2, 3, 5, 7, 11, 13])
carmichael_table()
witness_density()
strong_pseudoprime_table()
