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
    bit_vector = BitVector(0)
    for index, prime in enumerate(factor_base):
        if powers.get(prime, 0) & 1:
            bit_vector = bit_vector.set_bit(index)
    return bit_vector

def gf2_gauss_elimination(vectors: List[BitVector]) -> List[BitVector]:
    '''
    Gauss elimination of a matrix given in ...
    '''
    pivot_rows: Dict[BitVector, Tuple[BitVector, BitVector]] = {}
    lin_comb_vectors: List[BitVector] = []
    for index, vector in enumerate(vectors):
        index_mask = BitVector(1 << index)
        while vector:
            lowest_set_bit_vector = vector.lowest_set_bit()
            if lowest_set_bit_vector not in pivot_rows:
                pivot_rows[lowest_set_bit_vector] = (vector, index_mask)
                break
            pivot_vector, pivot_mask = pivot_rows[lowest_set_bit_vector]
            vector = vector ^ pivot_vector
            index_mask = index_mask ^ pivot_mask
        else:
            lin_comb_vectors.append(index_mask)
    return lin_comb_vectors