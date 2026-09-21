import graph_util
import random
import time

from typing import Dict, List, Optional, Set, Tuple

Graph = Dict[int, set]


def hamiltonian_cycle(graph: Graph) -> Tuple[Optional[List[int]], int]:
    vertices = sorted(graph)
    if len(vertices) < 3:
        return None, 0
    start = vertices[0]
    path = [start]
    visited = {start}
    calls = [0]

    def extend() -> bool:
        calls[0] += 1
        if len(path) == len(vertices):
            return start in graph[path[-1]]
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


def hamiltonian_cycle_pruned(graph: Graph) -> Tuple[Optional[List[int]], int]:
    vertices = sorted(graph)
    if len(vertices) < 3:
        return None, 0
    if any(len(graph[vertex]) < 2 for vertex in vertices):
        return None, 0
    start = min(vertices, key=lambda vertex: len(graph[vertex]))
    path = [start]
    visited = {start}
    calls = [0]

    def remaining_connected() -> bool:
        free = [vertex for vertex in vertices if vertex not in visited]
        if not free:
            return True
        subgraph = {vertex: {other for other in graph[vertex] if other not in visited}
                    for vertex in free}
        return len(graph_util.connected_components(subgraph)) == 1

    def extend() -> bool:
        calls[0] += 1
        if len(path) == len(vertices):
            return start in graph[path[-1]]
        if not remaining_connected():
            return False
        candidates = sorted((other for other in graph[path[-1]] if other not in visited),
                            key=lambda vertex: len(graph[vertex] - visited))
        for other in candidates:
            path.append(other)
            visited.add(other)
            if extend():
                return True
            path.pop()
            visited.remove(other)
        return False

    return (list(path), calls[0]) if extend() else (None, calls[0])


def is_hamiltonian_cycle(graph: Graph, cycle: List[int]) -> bool:
    if sorted(cycle) != sorted(graph):
        return False
    for index, vertex in enumerate(cycle):
        if cycle[(index + 1) % len(cycle)] not in graph[vertex]:
            return False
    return True


def dirac_condition(graph: Graph) -> bool:
    order = graph_util.order(graph)
    return order >= 3 and all(len(graph[vertex]) >= order / 2 for vertex in graph)


def ore_condition(graph: Graph) -> bool:
    order = graph_util.order(graph)
    if order < 3:
        return False
    for first in graph:
        for second in graph:
            if first < second and second not in graph[first]:
                if len(graph[first]) + len(graph[second]) < order:
                    return False
    return True


def cut_vertices(graph: Graph) -> List[int]:
    found: List[int] = []
    base = len(graph_util.connected_components(graph))
    for vertex in sorted(graph):
        reduced = {other: graph[other] - {vertex}
                   for other in graph if other != vertex}
        if len(graph_util.connected_components(reduced)) > base:
            found.append(vertex)
    return found


def worked_example() -> None:
    graph = graph_util.build_graph(6, [(0, 1), (0, 3), (0, 5), (1, 2), (1, 4),
                                       (2, 3), (2, 5), (3, 4), (4, 5)])
    print("--- 2 worked example, 6 vertices ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    print(f"degrees: {graph_util.degrees(graph)}")
    cycle, calls = hamiltonian_cycle(graph)
    print(f"search visited {calls} partial paths")
    print(f"cycle found: {cycle}")
    print(f"valid?: {is_hamiltonian_cycle(graph, cycle)}")
    print(f"Dirac (every degree >= n/2 = 3)?: {dirac_condition(graph)}")
    print(f"Ore?: {ore_condition(graph)}")
    print()


def no_cycle_example() -> None:
    graph = graph_util.build_graph(7, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4),
                                       (4, 5), (5, 3), (3, 6)])
    print("--- 2 a graph with no Hamiltonian cycle ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    cycle, calls = hamiltonian_cycle(graph)
    print(f"search visited {calls} partial paths, result {cycle}")
    print(f"vertex 6 has degree {len(graph[6])}, so it cannot sit on a cycle")
    print(f"cut vertices: {cut_vertices(graph)}")
    print()


def sufficient_conditions() -> None:
    print("--- 2 Dirac and Ore are sufficient but not necessary ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'dirac':>5}  {'ore':>5}  {'hamiltonian':>11}")
    families: List[Tuple[str, Graph]] = [
        ("K5", graph_util.complete_graph(5)),
        ("C6 cycle", graph_util.cycle_graph(6)),
        ("path P6", graph_util.path_graph(6)),
        ("Petersen", graph_util.petersen_graph()),
        ("K(3,3)", graph_util.complete_bipartite(3, 3)),
        ("K(2,3)", graph_util.complete_bipartite(2, 3)),
        ("wheel W6", graph_util.wheel_graph(6)),
        ("grid 3x4", graph_util.grid_graph(3, 4)),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("cube Q3", graph_util.hypercube_graph(3)),
    ]
    for name, graph in families:
        cycle, _ = hamiltonian_cycle_pruned(graph)
        print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
              f"  {str(dirac_condition(graph)):>5}  {str(ore_condition(graph)):>5}"
              f"  {str(cycle is not None):>11}")
    print("C6 and Petersen show a graph can be Hamiltonian, or not, with Dirac failing")
    print()


def petersen_detail() -> None:
    graph = graph_util.petersen_graph()
    print("--- 2 the Petersen graph is the classic non-Hamiltonian example ---")
    print(f"vertices {graph_util.order(graph)}, edges {graph_util.size(graph)}, "
          f"every degree {len(graph[0])}")
    cycle, calls = hamiltonian_cycle_pruned(graph)
    print(f"Hamiltonian cycle: {cycle} after {calls} partial paths")
    print(f"it is however vertex transitive and 3-connected, cut vertices {cut_vertices(graph)}")
    print()


def bipartite_parity() -> None:
    print("--- 2 a bipartite graph needs equal sides for a Hamiltonian cycle ---")
    print(f"{'graph':>10}  {'left':>4}  {'right':>5}  {'hamiltonian':>11}  reason")
    for left, right in ((2, 2), (2, 3), (3, 3), (3, 4), (4, 4)):
        graph = graph_util.complete_bipartite(left, right)
        cycle, _ = hamiltonian_cycle_pruned(graph)
        reason = "sides equal" if left == right else "sides differ, cycle must alternate"
        print(f"{'K(' + str(left) + ',' + str(right) + ')':>10}  {left:>4}  {right:>5}"
              f"  {str(cycle is not None):>11}  {reason}")
    print()


def pruning_effect() -> None:
    print("--- 2 pruning on connectivity cuts the search dramatically ---")
    print(f"{'graph':>14}  {'n':>3}  {'plain calls':>11}  {'pruned calls':>12}"
          f"  {'plain (ms)':>10}  {'pruned (ms)':>11}")
    for rows, columns in ((3, 3), (3, 4), (4, 4), (4, 5)):
        graph = graph_util.grid_graph(rows, columns)
        start = time.perf_counter()
        _, plain_calls = hamiltonian_cycle(graph)
        plain_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        _, pruned_calls = hamiltonian_cycle_pruned(graph)
        pruned_time = (time.perf_counter() - start) * 1000
        print(f"{'grid ' + str(rows) + 'x' + str(columns):>14}  {graph_util.order(graph):>3}"
              f"  {plain_calls:>11}  {pruned_calls:>12}  {plain_time:>10.2f}"
              f"  {pruned_time:>11.2f}")
    print()


def cost_growth() -> None:
    print("--- 2 exponential growth on random graphs with every degree at least 2 ---")
    print(f"{'n':>3}  {'m':>5}  {'hamiltonian':>11}  {'calls':>9}  {'time (ms)':>9}")
    random.seed(20260920)
    for order_value in (10, 14, 18, 22, 26, 30, 34):
        while True:
            edges = [(first, second)
                     for first in range(order_value)
                     for second in range(first + 1, order_value)
                     if random.random() < 0.18]
            graph = graph_util.build_graph(order_value, edges)
            if all(len(graph[vertex]) >= 2 for vertex in graph):
                break
        start = time.perf_counter()
        cycle, calls = hamiltonian_cycle_pruned(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{order_value:>3}  {len(edges):>5}  {str(cycle is not None):>11}"
              f"  {calls:>9}  {elapsed:>9.2f}")
    print()


def two_cliques(clique_order: int) -> Graph:
    edges = [(first, second)
             for first in range(clique_order)
             for second in range(first + 1, clique_order)]
    edges += [(clique_order - 1 + first, clique_order - 1 + second)
              for first in range(clique_order)
              for second in range(first + 1, clique_order)]
    return graph_util.build_graph(2 * clique_order - 1, edges)


def worst_case() -> None:
    print("--- 2 hard instances: every degree at least 2 but no cycle exists ---")
    print(f"{'n':>3}  {'graph':>24}  {'hamiltonian':>11}  {'calls':>10}  {'time (ms)':>9}")
    for clique_order in (4, 5, 6, 7):
        graph = two_cliques(clique_order)
        start = time.perf_counter()
        cycle, calls = hamiltonian_cycle_pruned(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{graph_util.order(graph):>3}  {'two K' + str(clique_order) + ' sharing a vertex':>24}"
              f"  {str(cycle is not None):>11}  {calls:>10}  {elapsed:>9.2f}")
    for order_value in (6, 10, 14, 18, 22):
        graph = graph_util.complete_graph(order_value)
        start = time.perf_counter()
        cycle, calls = hamiltonian_cycle_pruned(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{order_value:>3}  {'complete graph':>24}  {str(cycle is not None):>11}"
              f"  {calls:>10}  {elapsed:>9.2f}")
    print("a single cut vertex kills the cycle, but the search still explores both cliques")
    print()


worked_example()
no_cycle_example()
sufficient_conditions()
petersen_detail()
bipartite_parity()
pruning_effect()
cost_growth()
worst_case()
