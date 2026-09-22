from typing import List, Tuple

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
    inverse, _ = gcd_linear_comb(factor, modulo)
    return inverse % modulo


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

def power_modulo(base: int, exponent: int, modulo: int) -> int:
    result = 1
    base = base % modulo
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulo
        base = (base * base) % modulo
        exponent >>= 1
    return result