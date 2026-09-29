from typing import Dict, List, Tuple

def prime_to_integer_vector(powers: Dict[int, int], factor_base: List[int]) -> int:
    """
    Converts a prime factorization into a bit vector representing exponent parity
    A bit is set to 1 if the prime exponent is odd, and 0 if it is even

    The bit vector constructs from right to left (LSB to MSB):
        Bit 0 (LSB) -> factor_base[0]
        Bit 1       -> factor_base[1]
        ...
        Bit n       -> factor_base[n]
    """
    vector = 0
    for index, prime in enumerate(factor_base):
        if powers.get(prime, 0) & 1:
            vector |= 1 << index
    return vector

def gf2_gauss_elimination(vectors: List[int]) -> List[int]:
    '''
    Gauss elimination of a matrix given in ...
    '''
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
    '''
    Mask indices ...
    '''
    indices: List[int] = []
    index = 0
    while mask:
        if mask & 1:
            indices.append(index)
        mask >>= 1
        index += 1
    return indices
