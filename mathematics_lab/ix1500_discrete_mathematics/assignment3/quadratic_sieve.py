from typing import List, Tuple, Dict, Optional
from tonelli_shanks import tonelli_shanks
import util
import matrix_util

def sieve_factor_base(number: int, bound: int) -> List[int]:
    base: List[int] = []
    for prime in util.prime_list(bound):
        if prime == 2:
            base.append(prime)
        # Euler's criterion
        elif util.power_modulo(number % prime, (prime - 1) // 2, prime) == 1:
            base.append(prime)
    return base

def sieve_interval(number: int, base: List[int], width: int) -> List[Tuple[int, int, Dict[int, int]]]:
    root = util.integer_sqrt(number)
    if root * root < number:
        root += 1
    residues = [(root + offset) * (root + offset) - number for offset in range(width)]
    remaining = list(residues)

    # Sieve using Tonelli-Shanks algorithm
    for prime in base:
        base_root = tonelli_shanks(number, prime) # base_root^2 === number (mod prime)
        if base_root is None: continue
        root1 = (base_root - root) % prime
        root2 = (-base_root - root) % prime
        for index in range(root1, width, prime):
            while remaining[index] % prime == 0:
                remaining[index] //= prime
        if root1 == root2: continue
        for index in range(root2, width, prime):
            while remaining[index] % prime == 0:
                remaining[index] //= prime

    # Create the smooth interval
    smooth_interval: List[Tuple[int, int, Dict[int, int]]] = []
    for offset in range(width):
        if residues[offset] == 0 or remaining[offset] != 1:
            continue
        powers: Dict[int, int] = {}
        value = residues[offset]
        for prime in base:
            while value % prime == 0:
                powers[prime] = powers.get(prime, 0) + 1
                value //= prime
        smooth_interval.append((root + offset, residues[offset], powers))
    return smooth_interval

def quadratic_sieve(number: int, bound: int, width: int) -> Tuple[Optional[int], int, int]:
    base = sieve_factor_base(number, bound)
    sieving_interval = sieve_interval(number, base, width)
    if len(sieving_interval) <= len(base):
        return None, len(base), len(sieving_interval)

    # Unpack vectors and calculate x^2 === y (mod p), where y is perfect square
    # x is considered as left, and y is considered as right
    vectors = [matrix_util.prime_to_integer_vector(powers, base) for _, _, powers in sieving_interval]
    for lin_comb_vector in matrix_util.gf2_gauss_elimination(vectors):
        left = 1
        right_prime_exp: Dict[int, int] = {}
        for index in lin_comb_vector.to_indices():
            left_factor, _, powers = sieving_interval[index]
            left = (left * left_factor) % number
            for prime, power in powers.items():
                right_prime_exp[prime] = right_prime_exp.get(prime, 0) + power
        right = 1
        for prime, power in right_prime_exp.items():
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        result_factor = util.gcd(abs(left - right), number)
        if 1 < result_factor < number:
            return result_factor, len(base), len(sieving_interval)
    return None, len(base), len(sieving_interval)


number = 8051
factor, base_size, relation_count = quadratic_sieve(number, bound=30, width=3000)
print(f"Number: {number}")
print(f"Factor: {factor}")
print(f"Factor base size: {base_size}")
print(f"Relations found: {relation_count}")