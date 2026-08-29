from typing import List, Set, Union

# universal_set_lower_bound = 1
# universal_set_upper_bound = 30
# subset_size = 3
# subset_sum = 105
# subset_prod_divisable = 360

def arithmetic_sum(
    start: Union[int, float],
    stop: Union[int, float],
    step: Union[int, float],
) -> Union[int, float]:
    if step == 0: return 0
    if stop < start: return 0
    
    n = int((stop - start) // step) + 1
    last = start + (n - 1) * step
    return n * (start + last) / 2


# TODO: The function combinations_with_sum can be optimized with a better n-sums problem algorithm
def combinations_with_sum(
    lower_bound: int,
    upper_bound: int,
    size: int,
    target_sum: int,
) -> List[List[int]]:
    if size == 0: return [[]] if target_sum == 0 else []
    
    result: List[List[int]] = []
    for value in range(lower_bound, upper_bound + 1, 2):
        if value * size > target_sum: break
        for rest in combinations_with_sum(value + 2, upper_bound, size - 1, target_sum - value):
            result.append([value] + rest)
    return result


def product(values: List[int]) -> int:
    result = 1
    for value in values: result *= value
    return result


def generate_subsets(
    universal_set_lower_bound: int,
    universal_set_upper_bound: int,
    subset_even_size: int,
    subset_odd_size: int,
    subset_sum: int,
    subset_prod_divisable: int
) -> List[Set[int]]:
    
    result: List[Set[int]] = []
    lower_even_bound: int
    upper_even_bound: int
    lower_odd_bound: int
    upper_odd_bound: int
    
    if universal_set_lower_bound % 2 == 0:
        lower_even_bound = universal_set_lower_bound
        lower_odd_bound = universal_set_lower_bound + 1
    else:
        lower_even_bound = universal_set_lower_bound + 1
        lower_odd_bound = universal_set_lower_bound
    if universal_set_upper_bound % 2 == 0:
        upper_even_bound = universal_set_upper_bound
        upper_odd_bound = universal_set_upper_bound - 1
    else:
        upper_even_bound = universal_set_upper_bound - 1
        upper_odd_bound = universal_set_upper_bound
    
    if lower_even_bound + 2*(subset_even_size - 1) > upper_even_bound:
        print("Cannot fulfill subset_even_size constraint")
        return
    if lower_odd_bound + 2*(subset_odd_size - 1) > upper_odd_bound:
        print("Cannot fulfill subset_odd_size constraint")
        return
    
    lower_even_sum = int(arithmetic_sum(lower_even_bound, lower_even_bound + 2*(subset_even_size - 1), 2))
    lower_odd_sum = int(arithmetic_sum(lower_odd_bound, lower_odd_bound + 2*(subset_odd_size - 1), 2))
    upper_even_sum = int(arithmetic_sum(upper_even_bound - 2*(subset_even_size - 1), upper_even_bound, 2))
    upper_odd_sum = int(arithmetic_sum(upper_odd_bound - 2*(subset_odd_size - 1), upper_odd_bound, 2))
    
    # print(f"Bounds: {lower_even_bound} {upper_even_bound} {lower_odd_bound} {upper_odd_bound}")
    # print(f"Lower sums: {lower_even_sum}, {lower_odd_sum}, upper sums: {upper_even_sum}, {upper_odd_sum}")
    
    partial_lower_bound = max(lower_even_sum, subset_sum - upper_odd_sum)
    partial_upper_bound = min(upper_even_sum, subset_sum - lower_odd_sum)
    if partial_lower_bound % 2 != 0: partial_lower_bound += 1
    
    for even_term_sum in range(partial_lower_bound, partial_upper_bound + 1, 2):
        odd_term_sum = subset_sum - even_term_sum
        
        print(f"even_term_sum: {even_term_sum}, odd_term_sum: {odd_term_sum}")
        
        
        even_parts = combinations_with_sum(lower_even_bound, upper_even_bound, subset_even_size, even_term_sum)
        odd_parts = combinations_with_sum(lower_odd_bound, upper_odd_bound, subset_odd_size, odd_term_sum)
        even_products = [product(part) for part in even_parts]
        odd_products = [product(part) for part in odd_parts]
        
        '''
        # print(f"even_term_sum = {even_term_sum} -> {even_parts}, odd_term_sum = {odd_term_sum} -> {odd_parts}")
        
        # TODO: May be improved here using better algorithm than checking each divisability (using prime factors)
        for even_part, even_prod in zip(even_parts, even_products):
            for odd_part, odd_prod in zip(odd_parts, odd_products):
                if even_prod * odd_prod % subset_prod_divisable != 0: continue
                result.append(set(even_part + odd_part))
        '''
    
    
    print("Successfully calculated result")
    return result

print(" --------------- ASSIGNMENT 1.2 --------------- ")

result = generate_subsets(
    universal_set_lower_bound = 1,
    universal_set_upper_bound = 60,
    subset_even_size = 5,
    subset_odd_size = 6,
    subset_sum = 330,
    subset_prod_divisable = 2**6*3**3*5**2*7
)
print(f"result length: {len(result)}, result: {result[:20]}...<truncated at 20>")