from typing import Optional

import util

def calculate_smallest_i(square: int, prime: int) -> int:
    '''
    Solve smallest i for sqaure^2^i === 1 (mod prime)
    '''
    smallest_i = 0
    while square != 1:
        square = (square * square) % prime
        smallest_i += 1
    return smallest_i

def tonelli_shanks(residue: int, prime: int) -> Optional[int]:
    '''
    Solve x from x^2 === residue (mod prime) using Tonelli-Shanks algorithm
    '''
    residue = residue % prime

    # simple cases
    if residue == 0:
        return 0
    if prime == 2: # prime = 2*k
        return residue

    # Euler's criterion p=[odd_prime], a^((p-1)/2) \= legendre_symbol(a, p) (mod p)
    # help: legendre_symbol(a, p) = cases(1: exist(x, x^2===a (mod p)), 0: a = n*p, -1: non_exist(x, x^2===a (mod p)))
    # if non_exist(x, x^2 === residue (mod prime))
    if util.power_modulo(residue, (prime - 1) // 2, prime) != 1:
        return None
    if prime % 4 == 3: # prime = 3 + 4*k
        # x = a^((p+1)/4)
        # x^2 = (a^((p+1)/4))^2 = a^((p+1)/2) = a*a^((p-1)/2) === a*1 (mod p)
        return util.power_modulo(residue, (prime + 1) // 4, prime)

    # remaining case: prime = 1 + 4*k

    # write as: p - 1 = odd_part * 2^power_of_two
    power_of_two = 0
    odd_part = prime - 1
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1

    non_residue = 2
    while util.power_modulo(non_residue, (prime - 1) // 2, prime) != prime - 1:
        non_residue += 1

    root = util.power_modulo(residue, (odd_part + 1) // 2, prime)
    error_multiplier = util.power_modulo(residue, odd_part, prime)
    shift = util.power_modulo(non_residue, odd_part, prime)
    tracking_exponent = power_of_two

    while error_multiplier != 1:
        smallest_i = calculate_smallest_i(error_multiplier, prime)
        correction = util.power_modulo(shift, 1 << (tracking_exponent - smallest_i - 1), prime)
        root = (root * correction) % prime
        shift = (correction * correction) % prime
        error_multiplier = (error_multiplier * shift) % prime
        tracking_exponent = smallest_i
    return root