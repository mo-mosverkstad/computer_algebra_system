from typing import Dict, List, Tuple

class BitVector:
    value: int = 0
    def __init__(self, value: int):
        if value < 0:
            raise ValueError("BitVector value must be non-negative")
        self.value = value

    def __xor__(self, other: BitVector) -> BitVector:
        return BitVector(self.value ^ other.value)

    def __and__(self, other: BitVector) -> BitVector:
        return BitVector(self.value & other.value)

    def __or__(self, other: BitVector) -> BitVector:
        return BitVector(self.value | other.value)

    def __lshift__(self, amount: int) -> BitVector:
        return BitVector(self.value << amount)

    def __rshift__(self, amount: int) -> BitVector:
        return BitVector(self.value >> amount)

    def __bool__(self) -> bool:
        return self.value != 0

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BitVector):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"BitVector({self.value:b})"

    def is_set(self, index: int) -> bool:
        return bool(self.value & (1 << index))

    def set_bit(self, index: int) -> BitVector:
        return BitVector(self.value | (1 << index))

    def lowest_set_bit(self) -> BitVector:
        return BitVector(self.value & -self.value)

    def to_indices(self) -> list[int]:
        indices = []
        value = self.value
        index = 0
        while value:
            if value & 1:
                indices.append(index)
            value >>= 1
            index += 1
        return indices

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
    vector = BitVector(0)
    for index, prime in enumerate(factor_base):
        if powers.get(prime, 0) & 1:
            vector = vector.set_bit(index)
    return vector

def gf2_gauss_elimination(vectors: List[BitVector]) -> List[BitVector]:
    '''
    Gauss elimination of a matrix given in ...
    '''
    pivots: Dict[BitVector, Tuple[BitVector, BitVector]] = {}
    dependencies: List[BitVector] = []
    for index, vector in enumerate(vectors):
        mask = BitVector(1 << index)
        while vector:
            lowest = vector.lowest_set_bit()
            if lowest not in pivots:
                pivots[lowest] = (vector, mask)
                break
            pivot_vector, pivot_mask = pivots[lowest]
            vector = vector ^ pivot_vector
            mask = mask ^ pivot_mask
        else:
            dependencies.append(mask)
    return dependencies