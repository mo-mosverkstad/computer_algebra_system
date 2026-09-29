from typing import Dict, List, Tuple


def gcd(factor1: int, factor2: int) -> int:
    while factor2 != 0:
        factor1, factor2 = factor2, factor1 % factor2
    return factor1

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