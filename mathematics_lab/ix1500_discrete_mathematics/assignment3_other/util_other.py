from typing import Dict, List, Tuple


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
    factor_stack = gcd_expansion(factor1, factor2)
    x, y = 1, 0
    for factor1, factor2, quotient, remainder in reversed(factor_stack):
        x, y = y, x - quotient * y
    return x, y


def modulo_inverse(factor: int, modulo: int) -> int:
    inverse, _ = gcd_linear_comb(factor, modulo)
    return inverse % modulo


def power_modulo(base: int, exponent: int, modulo: int) -> int:
    result = 1
    base = base % modulo
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulo
        base = (base * base) % modulo
        exponent >>= 1
    return result


def integer_sqrt(number: int) -> int:
    if number < 0:
        raise ValueError(f"integer_sqrt of negative number {number}")
    if number < 2:
        return number
    root = 1 << ((number.bit_length() + 1) // 2)
    while True:
        next_root = (root + number // root) // 2
        if next_root >= root:
            return root
        root = next_root


def is_perfect_square(number: int) -> Tuple[bool, int]:
    root = integer_sqrt(number)
    return root * root == number, root


def prime_list(bound: int) -> List[int]:
    if bound < 2:
        return []
    composite = bytearray(bound + 1)
    composite[0] = composite[1] = 1
    for number in range(2, integer_sqrt(bound) + 1):
        if not composite[number]:
            marks = len(range(number * number, bound + 1, number))
            composite[number * number::number] = b'\x01' * marks
    return [number for number in range(2, bound + 1) if not composite[number]]


def factorize(factor_number: int) -> List[int]:
    prime_factors: List[int] = []
    while factor_number % 2 == 0:
        prime_factors.append(2)
        factor_number = factor_number // 2

    divisor = 3
    while divisor * divisor <= factor_number:
        while factor_number % divisor == 0:
            prime_factors.append(divisor)
            factor_number = factor_number // divisor
        divisor += 2

    if factor_number > 1:
        prime_factors.append(factor_number)

    return prime_factors


def factor_powers(factor_number: int) -> Dict[int, int]:
    powers: Dict[int, int] = {}
    for prime in factorize(factor_number):
        powers[prime] = powers.get(prime, 0) + 1
    return powers


def is_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    if candidate < 4:
        return True
    if candidate % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= candidate:
        if candidate % divisor == 0:
            return False
        divisor += 2
    return True


def is_probable_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if candidate == prime:
            return True
        if candidate % prime == 0:
            return False

    odd_part = candidate - 1
    power_of_two = 0
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1

    for base in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
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


def smooth_part(number: int, factor_base: List[int]) -> Tuple[int, Dict[int, int]]:
    powers: Dict[int, int] = {}
    for prime in factor_base:
        while number % prime == 0:
            powers[prime] = powers.get(prime, 0) + 1
            number = number // prime
    return number, powers


def exponent_vector(powers: Dict[int, int], factor_base: List[int]) -> int:
    vector = 0
    for index, prime in enumerate(factor_base):
        if powers.get(prime, 0) & 1:
            vector |= 1 << index
    return vector


def gf2_dependencies(vectors: List[int]) -> List[int]:
    pivots: Dict[int, Tuple[int, int]] = {}
    dependencies: List[int] = []
    for index, vector in enumerate(vectors):
        mask = 1 << index
        while vector:
            lowest = vector & -vector
            if lowest not in pivots:
                pivots[lowest] = (vector, mask)
                break
            pivot_vector, pivot_mask = pivots[lowest]
            vector ^= pivot_vector
            mask ^= pivot_mask
        else:
            dependencies.append(mask)
    return dependencies


def mask_indices(mask: int) -> List[int]:
    indices: List[int] = []
    index = 0
    while mask:
        if mask & 1:
            indices.append(index)
        mask >>= 1
        index += 1
    return indices
