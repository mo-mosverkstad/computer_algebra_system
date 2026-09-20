import util

from typing import List, Tuple

CARMICHAEL_NUMBERS = [561, 1105, 1729, 2465, 2821, 6601, 8911]
FERMAT_TEST_CASES = [341, 561, 645, 1105, 1387, 1729, 2047, 2465, 7919, 65537]


def fermat_round(candidate: int, base: int) -> Tuple[bool, int]:
    witness = util.power_modulo(base, candidate - 1, candidate)
    return witness == 1, witness


def fermat_test(candidate: int, bases: List[int]) -> Tuple[bool, List[Tuple[int, int, bool]]]:
    rounds: List[Tuple[int, int, bool]] = []
    if candidate < 2:
        return False, rounds
    for base in bases:
        if base % candidate == 0:
            continue
        shared = util.gcd(base, candidate)
        if shared > 1:
            rounds.append((base, 0, False))
            return False, rounds
        passed, witness = fermat_round(candidate, base)
        rounds.append((base, witness, passed))
        if not passed:
            return False, rounds
    return True, rounds


def fermat_liars(candidate: int) -> List[int]:
    liars: List[int] = []
    for base in range(2, candidate - 1):
        if util.gcd(base, candidate) != 1:
            continue
        if util.power_modulo(base, candidate - 1, candidate) == 1:
            liars.append(base)
    return liars


def worked_example() -> None:
    candidate = 561
    print("--- 1 worked example, n = 561 ---")
    print(f"n - 1 = {candidate - 1}")
    for base in (2, 3, 5, 50):
        passed, witness = fermat_round(candidate, base)
        print(f"a = {base:>3}: a^(n-1) = {witness:>4} (mod {candidate})"
              f" -> {'pass' if passed else 'composite'}")
    print(f"561 = {' * '.join(str(prime) for prime in util.factorize(candidate))}")
    print()


def test_table(bases: List[int]) -> None:
    print(f"--- 1 Fermat test over bases {bases} ---")
    print(f"{'n':>7}  {'prime?':>6}  {'fermat':>9}  {'rounds':>6}  witness")
    for candidate in FERMAT_TEST_CASES:
        probable, rounds = fermat_test(candidate, bases)
        truth = util.is_prime(candidate)
        verdict = "prime" if probable else "composite"
        flag = "" if probable == truth else "  <- wrong"
        if probable:
            reason = "every base gave 1"
        else:
            base, witness, _ = rounds[-1]
            shared = util.gcd(base, candidate)
            reason = (f"gcd({base}, n) = {shared}" if shared > 1
                      else f"{base}^(n-1) = {witness}")
        print(f"{candidate:>7}  {str(truth):>6}  {verdict:>9}  {len(rounds):>6}"
              f"  {reason}{flag}")
    print()


def carmichael_table() -> None:
    print("--- 1 Carmichael numbers defeat every coprime base ---")
    print(f"{'n':>7}  {'factors':>22}  {'coprime bases':>13}  {'liars':>6}  {'liar rate':>9}")
    for candidate in CARMICHAEL_NUMBERS:
        liars = fermat_liars(candidate)
        coprime = sum(1 for base in range(2, candidate - 1)
                      if util.gcd(base, candidate) == 1)
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>22}  {coprime:>13}  {len(liars):>6}"
              f"  {len(liars) / coprime:>9.3f}")
    print()


def liar_density() -> None:
    print("--- 1 liar density for ordinary composites ---")
    print(f"{'n':>7}  {'factors':>18}  {'coprime bases':>13}  {'liars':>6}  {'liar rate':>9}")
    for candidate in (341, 645, 1387, 2047, 3277):
        liars = fermat_liars(candidate)
        coprime = sum(1 for base in range(2, candidate - 1)
                      if util.gcd(base, candidate) == 1)
        factors = ' * '.join(str(prime) for prime in util.factorize(candidate))
        print(f"{candidate:>7}  {factors:>18}  {coprime:>13}  {len(liars):>6}"
              f"  {len(liars) / coprime:>9.3f}")
    print()


worked_example()
test_table([2])
test_table([2, 3])
test_table([2, 3, 5, 7])
carmichael_table()
liar_density()
