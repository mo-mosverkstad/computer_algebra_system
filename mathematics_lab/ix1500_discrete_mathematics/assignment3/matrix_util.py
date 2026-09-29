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
