import graph_util
import itertools
import random
import time

from typing import Dict, List, Optional, Tuple

Graph = Dict[int, set]


def degree_invariant(graph: Graph) -> Tuple[int, int, Tuple[int, ...]]:
    return (graph_util.order(graph), graph_util.size(graph),
            tuple(graph_util.degree_sequence(graph)))


def triangle_count(graph: Graph) -> int:
    total = 0
    for first in graph:
        for second in graph[first]:
            if second <= first:
                continue
            total += len(graph[first] & graph[second])
    return total // 3


def weisfeiler_lehman(graph: Graph, rounds: int = 3) -> Tuple[Tuple[int, ...], ...]:
    labels = {vertex: 0 for vertex in graph}
    history: List[Tuple[int, ...]] = []
    for _ in range(rounds):
        signatures = {vertex: (labels[vertex],
                               tuple(sorted(labels[other] for other in graph[vertex])))
                      for vertex in graph}
        ordered = sorted(set(signatures.values()))
        compressed = {signature: index for index, signature in enumerate(ordered)}
        labels = {vertex: compressed[signatures[vertex]] for vertex in graph}
        history.append(tuple(sorted(labels.values())))
    return tuple(history)


def brute_force_isomorphism(first: Graph, second: Graph) -> Tuple[Optional[Dict[int, int]], int]:
    if degree_invariant(first) != degree_invariant(second):
        return None, 0
    left = sorted(first)
    right = sorted(second)
    tried = 0
    for permutation in itertools.permutations(right):
        tried += 1
        mapping = dict(zip(left, permutation))
        if all((mapping[other] in second[mapping[vertex]])
               for vertex in left for other in first[vertex]):
            return mapping, tried
    return None, tried


def refined_isomorphism(first: Graph, second: Graph) -> Tuple[Optional[Dict[int, int]], int]:
    if degree_invariant(first) != degree_invariant(second):
        return None, 0
    if weisfeiler_lehman(first) != weisfeiler_lehman(second):
        return None, 0

    left = sorted(first, key=lambda vertex: (-len(first[vertex]), vertex))
    right = sorted(second)
    mapping: Dict[int, int] = {}
    used: Dict[int, bool] = {}
    calls = [0]

    def extend(index: int) -> bool:
        calls[0] += 1
        if index == len(left):
            return True
        vertex = left[index]
        for candidate in right:
            if used.get(candidate):
                continue
            if len(second[candidate]) != len(first[vertex]):
                continue
            consistent = True
            for other in first[vertex]:
                if other in mapping and mapping[other] not in second[candidate]:
                    consistent = False
                    break
            if consistent:
                for other in second[candidate]:
                    inverse = next((key for key, value in mapping.items() if value == other), None)
                    if inverse is not None and inverse not in first[vertex]:
                        consistent = False
                        break
            if not consistent:
                continue
            mapping[vertex] = candidate
            used[candidate] = True
            if extend(index + 1):
                return True
            del mapping[vertex]
            used[candidate] = False
        return False

    return (dict(mapping), calls[0]) if extend(0) else (None, calls[0])


def relabel(graph: Graph, permutation: List[int]) -> Graph:
    mapping = {vertex: permutation[index] for index, vertex in enumerate(sorted(graph))}
    edges = [(mapping[first], mapping[second]) for first, second in graph_util.edge_list(graph)]
    return graph_util.build_graph(graph_util.order(graph), edges)


def worked_example() -> None:
    first = graph_util.build_graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    second = graph_util.build_graph(5, [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)])
    print("--- 5 worked example, two drawings of C5 ---")
    print(f"first  edges: {graph_util.render_edges(first, 20)}")
    print(f"second edges: {graph_util.render_edges(second, 20)}")
    print(f"invariants equal?: {degree_invariant(first) == degree_invariant(second)}")
    mapping, tried = brute_force_isomorphism(first, second)
    print(f"brute force tried {tried} of {120} permutations")
    print(f"isomorphism: {mapping}")
    mapping, calls = refined_isomorphism(first, second)
    print(f"refined search needed {calls} calls, mapping {mapping}")
    print()


def invariants_are_not_enough() -> None:
    first = graph_util.build_graph(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    second = graph_util.cycle_graph(6)
    print("--- 5 same degree sequence, different graphs ---")
    print(f"two triangles:  {graph_util.render_edges(first, 20)}")
    print(f"one hexagon:    {graph_util.render_edges(second, 20)}")
    print(f"order and size:  {degree_invariant(first)[:2]} vs {degree_invariant(second)[:2]}")
    print(f"degree sequence: {graph_util.degree_sequence(first)}"
          f" vs {graph_util.degree_sequence(second)}, identical")
    print(f"triangles:       {triangle_count(first)} vs {triangle_count(second)}")
    print(f"components:      {len(graph_util.connected_components(first))}"
          f" vs {len(graph_util.connected_components(second))}")
    mapping, tried = brute_force_isomorphism(first, second)
    print(f"brute force verdict: {'isomorphic' if mapping else 'not isomorphic'}"
          f" after {tried} permutations")
    print()


def invariant_ladder() -> None:
    print("--- 5 invariants in increasing strength ---")
    pairs: List[Tuple[str, Graph, Graph]] = [
        ("C6 vs two triangles",
         graph_util.cycle_graph(6),
         graph_util.build_graph(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])),
        ("C6 vs K(3,3)", graph_util.cycle_graph(6), graph_util.complete_bipartite(3, 3)),
        ("C5 relabelled", graph_util.cycle_graph(5),
         relabel(graph_util.cycle_graph(5), [2, 4, 1, 3, 0])),
        ("Petersen relabelled", graph_util.petersen_graph(),
         relabel(graph_util.petersen_graph(), [3, 7, 1, 9, 5, 0, 8, 2, 6, 4])),
        ("Q3 vs K(4,4) minus perfect matching", graph_util.hypercube_graph(3),
         graph_util.build_graph(8, [(first, 4 + second)
                                    for first in range(4) for second in range(4)
                                    if first != second])),
    ]
    print(f"{'pair':>36}  {'size ok':>7}  {'degrees ok':>10}  {'triangles ok':>12}"
          f"  {'WL ok':>5}  {'isomorphic':>10}")
    for name, first, second in pairs:
        size_ok = graph_util.size(first) == graph_util.size(second)
        degrees_ok = graph_util.degree_sequence(first) == graph_util.degree_sequence(second)
        triangles_ok = triangle_count(first) == triangle_count(second)
        wl_ok = weisfeiler_lehman(first) == weisfeiler_lehman(second)
        mapping, _ = brute_force_isomorphism(first, second)
        print(f"{name:>36}  {str(size_ok):>7}  {str(degrees_ok):>10}  {str(triangles_ok):>12}"
              f"  {str(wl_ok):>5}  {str(mapping is not None):>10}")
    print()


def weisfeiler_lehman_failure() -> None:
    first = graph_util.build_graph(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    second = graph_util.cycle_graph(6)
    print("--- 5 the Weisfeiler-Lehman test is not complete ---")
    print(f"two triangles labels: {weisfeiler_lehman(first)}")
    print(f"hexagon labels:       {weisfeiler_lehman(second)}")
    print("both are 2-regular so every round produces the same multiset of labels")
    print("yet the graphs are not isomorphic, one is connected and the other is not")
    print()


def relabelling_test() -> None:
    print("--- 5 a graph is always isomorphic to a relabelling of itself ---")
    print(f"{'graph':>18}  {'n':>3}  {'brute force calls':>17}  {'refined calls':>13}"
          f"  {'found':>5}")
    random.seed(20260920)
    families: List[Tuple[str, Graph]] = [
        ("C6", graph_util.cycle_graph(6)),
        ("K5", graph_util.complete_graph(5)),
        ("Petersen", graph_util.petersen_graph()),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("cube Q3", graph_util.hypercube_graph(3)),
        ("K(3,4)", graph_util.complete_bipartite(3, 4)),
    ]
    for name, graph in families:
        permutation = list(range(graph_util.order(graph)))
        random.shuffle(permutation)
        shuffled = relabel(graph, permutation)
        brute_calls = "skipped"
        if graph_util.order(graph) <= 8:
            _, tried = brute_force_isomorphism(graph, shuffled)
            brute_calls = str(tried)
        mapping, calls = refined_isomorphism(graph, shuffled)
        print(f"{name:>18}  {graph_util.order(graph):>3}  {brute_calls:>17}  {calls:>13}"
              f"  {str(mapping is not None):>5}")
    print()


def cost_growth() -> None:
    print("--- 5 n! permutations against pruned search ---")
    print(f"{'n':>3}  {'n!':>12}  {'brute force (ms)':>16}  {'refined (ms)':>12}")
    random.seed(20260920)
    for order_value in (5, 6, 7, 8, 9):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.5]
        graph = graph_util.build_graph(order_value, edges)
        permutation = list(range(order_value))
        random.shuffle(permutation)
        shuffled = relabel(graph, permutation)

        start = time.perf_counter()
        brute_force_isomorphism(graph, shuffled)
        brute_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        refined_isomorphism(graph, shuffled)
        refined_time = (time.perf_counter() - start) * 1000
        factorial = 1
        for value in range(2, order_value + 1):
            factorial *= value
        print(f"{order_value:>3}  {factorial:>12}  {brute_time:>16.3f}  {refined_time:>12.3f}")
    for order_value in (12, 16, 20, 24, 30):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.3]
        graph = graph_util.build_graph(order_value, edges)
        permutation = list(range(order_value))
        random.shuffle(permutation)
        shuffled = relabel(graph, permutation)
        start = time.perf_counter()
        mapping, _ = refined_isomorphism(graph, shuffled)
        refined_time = (time.perf_counter() - start) * 1000
        factorial = 1
        for value in range(2, order_value + 1):
            factorial *= value
        print(f"{order_value:>3}  {factorial:>12.3e}  {'not feasible':>16}"
              f"  {refined_time:>12.3f}")
    print()


def hard_case() -> None:
    print("--- 5 regular graphs are the hard case, every cheap invariant agrees ---")
    print(f"{'pair':>34}  {'n':>3}  {'degree':>6}  {'WL ok':>5}  {'isomorphic':>10}"
          f"  {'calls':>8}")
    chorded = graph_util.cycle_graph(6)
    for vertex in range(3):
        chorded[vertex].add(vertex + 3)
        chorded[vertex + 3].add(vertex)
    for name, left, right in (("K(3,3) vs C6 plus long chords",
                               graph_util.complete_bipartite(3, 3), chorded),
                              ("Petersen vs itself relabelled", graph_util.petersen_graph(),
                               relabel(graph_util.petersen_graph(),
                                       [5, 6, 7, 8, 9, 0, 1, 2, 3, 4])),
                              ("Q3 vs C8 plus long chords", graph_util.hypercube_graph(3),
                               add_diagonals(graph_util.cycle_graph(8)))):
        wl_ok = weisfeiler_lehman(left) == weisfeiler_lehman(right)
        mapping, calls = refined_isomorphism(left, right)
        print(f"{name:>34}  {graph_util.order(left):>3}  {len(left[0]):>6}  {str(wl_ok):>5}"
              f"  {str(mapping is not None):>10}  {calls:>8}")
    print("the last pair passes every invariant but the search still proves them different")
    print()


def add_diagonals(graph: Graph) -> Graph:
    order = graph_util.order(graph)
    edges = graph_util.edge_list(graph)
    edges += [(vertex, (vertex + order // 2) % order) for vertex in range(order // 2)]
    return graph_util.build_graph(order, edges)


worked_example()
invariants_are_not_enough()
invariant_ladder()
weisfeiler_lehman_failure()
relabelling_test()
hard_case()
cost_growth()
