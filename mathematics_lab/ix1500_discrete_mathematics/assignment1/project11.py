from typing import List, Set, Union

# universal_set_lower_bound = 1
# universal_set_upper_bound = 30
# subset_size = 3
# subset_sum = 105
# subset_prod_divisable = 360

universal_set_lower_bound = 1
universal_set_upper_bound = 9
subset_sum = 20
subset_prod_divisable = 24

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



def generate_subsets(
    universal_set_lower_bound: int,
    universal_set_upper_bound: int,
    subset_even_size: int,
    subset_odd_size: int,
    subset_sum: int,
    subset_prod_divisable: int
) -> List[Set[int]]:
    
    result: List[Set[int]] = set()
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
    
    print(f"Bounds: {lower_even_bound} {upper_even_bound} {lower_odd_bound} {upper_odd_bound}")
    print(f"Lower sums: {lower_even_sum}, {lower_odd_sum}, upper sums: {upper_even_sum}, {upper_odd_sum}")
    
    partial_lower_bound = min(lower_even_sum, lower_odd_sum)
    partial_upper_bound = max(upper_even_sum, upper_odd_sum)
    
    for even_term in range(partial_lower_bound, partial_upper_bound + 1, 2):
        odd_term = subset_sum - even_term
        
        print(f"even_term = {even_term}, odd_term = {odd_term}")
    
    
    print("Successfully calculated result")
    return result
    
def generate_subsets_1(
    universal_odd_set: Set[int],
    universal_even_set: Set[int],
    subset_even_size: int,
    subset_odd_size: int,
    subset_sum: int,
    subset_prod_divisable: int
) -> List[Set[int]]:
    
    result: List[Set[int]] = set()
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
    
    print(f"Bounds: {lower_even_bound} {upper_even_bound} {lower_odd_bound} {upper_odd_bound}")
    print(f"Lower sums: {lower_even_sum}, {lower_odd_sum}, upper sums: {upper_even_sum}, {upper_odd_sum}")
    
    partial_lower_bound = min(lower_even_sum, lower_odd_sum)
    partial_upper_bound = max(upper_even_sum, upper_odd_sum)
    
    for even_term in range(partial_lower_bound, partial_upper_bound + 1, 2):
        odd_term = subset_sum - even_term
        print(f"even_term = {even_term}, odd_term = {odd_term}")
    
    
    print("Successfully calculated result")
    return result
    
generate_subsets_1(
    universal_set_lower_bound = universal_set_lower_bound,
    universal_set_upper_bound = universal_set_upper_bound,
    subset_even_size = 2,
    subset_odd_size = 2,
    subset_sum = subset_sum,
    subset_prod_divisable = subset_prod_divisable
)

'''
generate_subsets(
    universal_set_lower_bound = 1,
    universal_set_upper_bound = 4,
    subset_even_size = 2,
    subset_odd_size = 2,
    subset_sum = subset_sum,
    subset_prod_divisable = subset_prod_divisable
)
'''