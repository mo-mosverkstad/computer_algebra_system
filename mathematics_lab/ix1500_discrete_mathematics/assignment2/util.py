from typing import List, Tuple
import random

def gcd(factor1: int, factor2: int) -> int:
    while factor2 != 0:
        factor1, factor2 = factor2, factor1 % factor2
    return factor1

def gcd_expansion(factor1: int, factor2: int) -> List[Tuple[int, int, int, int]]:
    factor_stack: List[Tuple[int, int, int, int]] = []
    while factor2 != 0:
        quotient = factor1 // factor2
        remainder = factor1 % factor2
        factor_stack.append((factor1, factor2, quotient, remainder))
        factor1 = factor2
        factor2 = remainder
    return factor_stack
 
def gcd_linear_comb(factor1: int, factor2: int) -> Tuple[int, int]:
    factor_stack: List[Tuple[int, int, int, int]] = gcd_expansion(factor1, factor2)
    x, y = 1, 0
    for factor1, factor2, quotient, remainder in reversed(factor_stack):
        # (x, y) in (a, b) = x*a + y*b = x*a + y*(c - q*a) 
        # = x*a + y*c - y*q*a = y*c + (x-y*q)*b = (y, x-y*q) in (c, b)
        x, y = y, x - quotient * y
    return x, y
    
def modulo_inverse(factor: int, modulo: int) -> int:
    inverse, other = gcd_linear_comb(factor, modulo)
    return inverse % modulo

def recover_factors(moduli: List[int]) -> List[Tuple[int, int]]:
    """Recover p, q for each modulus.

    Several of the given moduli reuse the same prime, so a pairwise gcd splits
    them immediately and no factoring is needed. Only moduli that share nothing
    with the others fall back to trial division.
    """
    factors: List[Tuple[int, int]] = [(0, 0)] * len(moduli)

    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            shared = gcd(moduli[i], moduli[j])
            if shared > 1:
                factors[i] = (shared, moduli[i] // shared)
                factors[j] = (shared, moduli[j] // shared)

    for i, modulus in enumerate(moduli):
        if factors[i] == (0, 0):
            prime_factors = factorize(modulus)
            factors[i] = (prime_factors[0], prime_factors[1])

    return factors


def factorize(factor_number: int) -> List[int]:
    prime_factors = []
    while factor_number % 2 == 0:
        prime_factors.append(2)
        factor_number = factor_number // 2
        
    i = 3
    while i * i <= factor_number:
        while factor_number % i == 0:
            prime_factors.append(i)
            factor_number = factor_number // i
        i = i + 2
        
    if factor_number > 1:
        prime_factors.append(factor_number)
        
    return prime_factors

def is_probable_prime(candidate: int, rounds: int = 20) -> bool:
    """Miller-Rabin.

    If candidate is prime then for every base a either a^r == 1, or one of the
    repeated squarings of a^r reaches -1 (mod candidate). A base that shows
    neither proves the number composite. Trial division is not usable here
    because the 128 bit keys in 2.2.1 are far too large for it.
    """
    if candidate < 2:
        return False
    for small_prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if candidate == small_prime:
            return True
        if candidate % small_prime == 0:
            return False

    # candidate - 1 = odd_part * 2^power_of_two
    odd_part = candidate - 1
    power_of_two = 0
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1

    for _ in range(rounds):
        base = random.randrange(2, candidate - 1)
        witness = power_modulo(base, odd_part, candidate)
        if witness == 1 or witness == candidate - 1:
            continue
        for _ in range(power_of_two - 1):
            witness = (witness * witness) % candidate
            if witness == candidate - 1:
                break
        else:
            return False
    return True


def random_prime(bits: int) -> int:
    """Draw odd candidates of the requested bit length until one is prime."""
    while True:
        # force the top bit so n = p*q really has the requested size, and the
        # bottom bit so the candidate is odd
        candidate = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate


def power_modulo(base: int, exponent: int, modulo: int) -> int:
    result = 1
    base = base % modulo
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulo
        base = (base * base) % modulo
        exponent >>= 1
    return result