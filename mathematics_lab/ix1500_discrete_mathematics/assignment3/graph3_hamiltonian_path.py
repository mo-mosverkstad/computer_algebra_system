import graph_util
import random
import time

from typing import Dict, List, Optional, Set, Tuple

Graph = Dict[int, set]


def hamiltonian_path_from(graph: Graph, start: int) -> Tuple[Optional[List[int]], int]:
    vertices = sorted(graph)
    path = [start]
    visited = {start}
    calls = [0]

    def extend() -> bool:
        calls[0] += 1
        if len(path) == len(vertices):
            return True
        for other in sorted(graph[path[-1]]):
            if other in visited:
                continue
            path.append(other)
            visited.add(other)
            if extend():
                return True
            path.pop()
            visited.remove(other)
        return False

    return (list(path), calls[0]) if extend() else (None, calls[0])


def hamiltonian_path(graph: Graph) -> Tuple[Optional[List[int]], int]:
    total = 0
    for start in sorted(graph, key=lambda vertex: len(graph[vertex])):
        path, calls = hamiltonian_path_from(graph, start)
        total += calls
        if path is not None:
            return path, total
    return None, total


def held_karp_path(graph: Graph) -> Tuple[Optional[List[int]], int]:
    vertices = sorted(graph)
    index_of = {vertex: index for index, vertex in enumerate(vertices)}
    count = len(vertices)
    reachable: Dict[Tuple[int, int], Optional[int]] = {}
    for vertex in vertices:
        reachable[(1 << index_of[vertex], index_of[vertex])] = -1

    states = 0
    for mask in range(1, 1 << count):
        for last in range(count):
            if not mask >> last & 1:
                continue
            if (mask, last) not in reachable:
                continue
            states += 1
            for other in graph[vertices[last]]:
                bit = index_of[other]
                if mask >> bit & 1:
                    continue
                key = (mask | 1 << bit, bit)
                if key not in reachable:
                    reachable[key] = last

    full = (1 << count) - 1
    for last in range(count):
        if (full, last) not in reachable:
            continue
        path: List[int] = []
        mask, current = full, last
        while current != -1:
            path.append(vertices[current])
            previous = reachable[(mask, current)]
            mask ^= 1 << current
            current = previous
        path.reverse()
        return path, states
    return None, states


def is_hamiltonian_path(graph: Graph, path: List[int]) -> bool:
    if path is None or sorted(path) != sorted(graph):
        return False
    return all(path[index + 1] in graph[path[index]] for index in range(len(path) - 1))


def count_hamiltonian_paths(graph: Graph) -> int:
    vertices = sorted(graph)
    total = 0

    def extend(path: List[int], visited: Set[int]) -> None:
        nonlocal total
        if len(path) == len(vertices):
            total += 1
            return
        for other in graph[path[-1]]:
            if other in visited:
                continue
            path.append(other)
            visited.add(other)
            extend(path, visited)
            path.pop()
            visited.remove(other)

    for start in vertices:
        extend([start], {start})
    return total


def worked_example() -> None:
    graph = graph_util.build_graph(6, [(0, 1), (0, 2), (1, 2), (1, 3), (2, 4),
                                       (3, 4), (3, 5)])
    print("--- 3 worked example, 6 vertices ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    print(f"degrees: {graph_util.degrees(graph)}")
    for start in sorted(graph):
        path, calls = hamiltonian_path_from(graph, start)
        shown = ' -> '.join(str(vertex) for vertex in path) if path else "none"
        print(f"  start {start}: {shown} ({calls} partial paths)")
    path, _ = hamiltonian_path(graph)
    print(f"a Hamiltonian path exists: {is_hamiltonian_path(graph, path)}")
    print(f"total number of Hamiltonian paths: {count_hamiltonian_paths(graph)}")
    print()


def path_but_no_cycle() -> None:
    graph = graph_util.path_graph(5)
    print("--- 3 a path can exist where no cycle does ---")
    print(f"path P5 edges: {graph_util.render_edges(graph, 20)}")
    path, _ = hamiltonian_path(graph)
    print(f"Hamiltonian path: {path}")
    print(f"is it a cycle?: {path[0] in graph[path[-1]]}, so P5 has no Hamiltonian cycle")
    print()

    graph = graph_util.petersen_graph()
    path, _ = hamiltonian_path(graph)
    print(f"Petersen graph Hamiltonian path: {path}")
    print("the Petersen graph is hypohamiltonian: a path exists but no cycle")
    print()


def families_table() -> None:
    print("--- 3 Hamiltonian paths across families, compared with cycles ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'path':>5}  {'cycle':>5}  {'paths counted':>13}")
    families: List[Tuple[str, Graph]] = [
        ("K5", graph_util.complete_graph(5)),
        ("path P6", graph_util.path_graph(6)),
        ("C6 cycle", graph_util.cycle_graph(6)),
        ("Petersen", graph_util.petersen_graph()),
        ("K(3,3)", graph_util.complete_bipartite(3, 3)),
        ("K(2,4)", graph_util.complete_bipartite(2, 4)),
        ("K(3,4)", graph_util.complete_bipartite(3, 4)),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("cube Q3", graph_util.hypercube_graph(3)),
        ("wheel W5", graph_util.wheel_graph(5)),
    ]
    for name, graph in families:
        path, _ = hamiltonian_path(graph)
        cycle = has_hamiltonian_cycle(graph)
        print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
              f"  {str(path is not None):>5}  {str(cycle):>5}"
              f"  {count_hamiltonian_paths(graph):>13}")
    print()


def has_hamiltonian_cycle(graph: Graph) -> bool:
    vertices = sorted(graph)
    if len(vertices) < 3:
        return False
    start = vertices[0]

    def extend(path: List[int], visited: Set[int]) -> bool:
        if len(path) == len(vertices):
            return start in graph[path[-1]]
        for other in sorted(graph[path[-1]]):
            if other in visited:
                continue
            path.append(other)
            visited.add(other)
            if extend(path, visited):
                return True
            path.pop()
            visited.remove(other)
        return False

    return extend([start], {start})


def bipartite_bound() -> None:
    print("--- 3 bipartite sides may differ by at most one for a path ---")
    print(f"{'graph':>10}  {'left':>4}  {'right':>5}  {'difference':>10}  {'path':>5}")
    for left, right in ((3, 3), (3, 4), (3, 5), (4, 5), (2, 4), (2, 3)):
        graph = graph_util.complete_bipartite(left, right)
        path, _ = hamiltonian_path(graph)
        print(f"{'K(' + str(left) + ',' + str(right) + ')':>10}  {left:>4}  {right:>5}"
              f"  {abs(left - right):>10}  {str(path is not None):>5}")
    print()


def held_karp_check() -> None:
    print("--- 3 backtracking against the Held-Karp dynamic program ---")
    print(f"{'graph':>18}  {'n':>3}  {'backtrack':>9}  {'held-karp':>9}  {'agree':>5}"
          f"  {'DP states':>9}  {'2^n * n':>9}")
    families: List[Tuple[str, Graph]] = [
        ("path P6", graph_util.path_graph(6)),
        ("C7 cycle", graph_util.cycle_graph(7)),
        ("Petersen", graph_util.petersen_graph()),
        ("K(3,4)", graph_util.complete_bipartite(3, 4)),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("cube Q3", graph_util.hypercube_graph(3)),
        ("cube Q4", graph_util.hypercube_graph(4)),
    ]
    for name, graph in families:
        backtrack, _ = hamiltonian_path(graph)
        dynamic, states = held_karp_path(graph)
        order = graph_util.order(graph)
        print(f"{name:>18}  {order:>3}  {str(backtrack is not None):>9}"
              f"  {str(dynamic is not None):>9}"
              f"  {str((backtrack is None) == (dynamic is None)):>5}"
              f"  {states:>9}  {(1 << order) * order:>9}")
    print()


def cost_growth() -> None:
    print("--- 3 backtracking against Held-Karp as n grows ---")
    print(f"{'n':>3}  {'m':>5}  {'path':>5}  {'backtrack (ms)':>14}  {'held-karp (ms)':>14}")
    random.seed(20260920)
    for order_value in (8, 10, 12, 14, 16, 18):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.2]
        graph = graph_util.build_graph(order_value, edges)
        start = time.perf_counter()
        path, _ = hamiltonian_path(graph)
        backtrack_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        held_karp_path(graph)
        dynamic_time = (time.perf_counter() - start) * 1000
        print(f"{order_value:>3}  {len(edges):>5}  {str(path is not None):>5}"
              f"  {backtrack_time:>14.2f}  {dynamic_time:>14.2f}")
    print("backtracking is fast when a path exists, Held-Karp is steady at O(2^n * n^2)")
    print()


def hard_instances() -> None:
    print("--- 3 hard instances for backtracking: no path but degrees look fine ---")
    print(f"{'n':>3}  {'graph':>26}  {'path':>5}  {'calls':>10}  {'time (ms)':>9}")
    for arms in (3, 4, 5, 6):
        edges: List[Tuple[int, int]] = []
        for arm in range(arms):
            base = 1 + arm * 3
            edges.append((0, base))
            edges.append((base, base + 1))
            edges.append((base + 1, base + 2))
        graph = graph_util.build_graph(1 + 3 * arms, edges)
        start = time.perf_counter()
        path, calls = hamiltonian_path(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{graph_util.order(graph):>3}  {'spider with ' + str(arms) + ' arms':>26}"
              f"  {str(path is not None):>5}  {calls:>10}  {elapsed:>9.2f}")
    for clique_order in (4, 5, 6):
        edges = [(first, second)
                 for first in range(clique_order)
                 for second in range(first + 1, clique_order)]
        centre = clique_order
        edges += [(centre, vertex) for vertex in range(clique_order)]
        edges += [(centre + 1 + first, centre + 1 + second)
                  for first in range(clique_order)
                  for second in range(first + 1, clique_order)]
        edges += [(centre, centre + 1 + vertex) for vertex in range(clique_order)]
        edges += [(centre + clique_order + 1 + first, centre + clique_order + 1 + second)
                  for first in range(clique_order)
                  for second in range(first + 1, clique_order)]
        edges += [(centre, centre + clique_order + 1 + vertex)
                  for vertex in range(clique_order)]
        graph = graph_util.build_graph(1 + 3 * clique_order, edges)
        start = time.perf_counter()
        path, calls = hamiltonian_path(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{graph_util.order(graph):>3}"
              f"  {'three K' + str(clique_order) + ' around a hub':>26}"
              f"  {str(path is not None):>5}  {calls:>10}  {elapsed:>9.2f}")
    print("three branches at one vertex cannot all be traversed by a single path")
    print()


worked_example()
path_but_no_cycle()
families_table()
bipartite_bound()
held_karp_check()
cost_growth()
hard_instances()
