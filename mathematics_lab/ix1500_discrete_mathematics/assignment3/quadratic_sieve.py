from typing import List, Tuple, Dict, Optional
from tonelli_shanks import tonelli_shanks
import util
import matrix_util
import math

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

    for prime in base:
        target = tonelli_shanks(number, prime) # target^2 === number (mod prime)
        if target is None:
            continue
        starts = {(target - root) % prime, (-target - root) % prime}
        for start in starts:
            for index in range(start, width, prime):
                while remaining[index] % prime == 0:
                    remaining[index] //= prime

    relations: List[Tuple[int, int, Dict[int, int]]] = []
    for offset in range(width):
        if residues[offset] == 0 or remaining[offset] != 1:
            continue
        powers: Dict[int, int] = {}
        value = residues[offset]
        for prime in base:
            while value % prime == 0:
                powers[prime] = powers.get(prime, 0) + 1
                value //= prime
        relations.append((root + offset, residues[offset], powers))
    return relations

def quadratic_sieve(number: int, bound: int, width: int) -> Tuple[Optional[int], int, int]:
    base = sieve_factor_base(number, bound)
    relations = sieve_interval(number, base, width)
    if len(relations) <= len(base):
        return None, len(base), len(relations)

    vectors = [matrix_util.prime_to_integer_vector(powers, base) for _, _, powers in relations]
    for mask in matrix_util.gf2_gauss_elimination(vectors):
        left = 1
        combined: Dict[int, int] = {}
        for index in matrix_util.mask_indices(mask):
            candidate, _, powers = relations[index]
            left = (left * candidate) % number
            for prime, power in powers.items():
                combined[prime] = combined.get(prime, 0) + power
        right = 1
        for prime, power in combined.items():
            right = (right * util.power_modulo(prime, power // 2, number)) % number
        shared = util.gcd(abs(left - right), number)
        if 1 < shared < number:
            return shared, len(base), len(relations)
    return None, len(base), len(relations)


number = 8051
factor, base_size, relation_count = quadratic_sieve(number, bound=30, width=3000)
print(f"Number: {number}")
print(f"Factor: {factor}")
print(f"Factor base size: {base_size}")
print(f"Relations found: {relation_count}")