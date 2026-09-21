import graph_util
import random
import time

from typing import Dict, List, Optional, Set, Tuple

Graph = Dict[int, set]
Multigraph = Dict[int, List[int]]


def to_multigraph(graph: Graph) -> Multigraph:
    return {vertex: sorted(graph[vertex]) for vertex in sorted(graph)}


def odd_degree_vertices(graph: Graph) -> List[int]:
    return [vertex for vertex in sorted(graph) if len(graph[vertex]) % 2 == 1]


def euler_classification(graph: Graph) -> str:
    if not graph_util.is_connected(graph):
        return "disconnected, neither"
    odd = odd_degree_vertices(graph)
    if len(odd) == 0:
        return "circuit"
    if len(odd) == 2:
        return "path only"
    return f"{len(odd)} odd vertices, neither"


def hierholzer(graph: Graph) -> Tuple[Optional[List[int]], str]:
    classification = euler_classification(graph)
    if classification.endswith("neither"):
        return None, classification

    remaining = {vertex: dict.fromkeys(sorted(graph[vertex])) for vertex in sorted(graph)}
    odd = odd_degree_vertices(graph)
    start = odd[0] if odd else next(vertex for vertex in sorted(graph) if graph[vertex])

    stack = [start]
    trail: List[int] = []
    while stack:
        vertex = stack[-1]
        if remaining[vertex]:
            other = next(iter(remaining[vertex]))
            del remaining[vertex][other]
            del remaining[other][vertex]
            stack.append(other)
        else:
            trail.append(stack.pop())
    trail.reverse()
    return trail, classification


def fleury(graph: Graph) -> Optional[List[int]]:
    if euler_classification(graph).endswith("neither"):
        return None
    working = {vertex: set(graph[vertex]) for vertex in graph}
    odd = odd_degree_vertices(graph)
    current = odd[0] if odd else next(vertex for vertex in sorted(graph) if graph[vertex])
    trail = [current]

    def is_bridge(first: int, second: int) -> bool:
        working[first].discard(second)
        working[second].discard(first)
        reachable = reachable_from(working, first)
        working[first].add(second)
        working[second].add(first)
        return second not in reachable

    while any(working[vertex] for vertex in working):
        candidates = sorted(working[current])
        chosen = None
        for other in candidates:
            if len(candidates) == 1 or not is_bridge(current, other):
                chosen = other
                break
        if chosen is None:
            chosen = candidates[0]
        working[current].discard(chosen)
        working[chosen].discard(current)
        current = chosen
        trail.append(current)
    return trail


def reachable_from(graph: Graph, start: int) -> Set[int]:
    seen = {start}
    stack = [start]
    while stack:
        vertex = stack.pop()
        for other in graph[vertex]:
            if other not in seen:
                seen.add(other)
                stack.append(other)
    return seen


def is_euler_trail(graph: Graph, trail: List[int]) -> bool:
    if trail is None:
        return False
    used: Set[Tuple[int, int]] = set()
    for index in range(len(trail) - 1):
        first, second = trail[index], trail[index + 1]
        if second not in graph[first]:
            return False
        edge = (min(first, second), max(first, second))
        if edge in used:
            return False
        used.add(edge)
    return len(used) == graph_util.size(graph)


def worked_example() -> None:
    graph = graph_util.build_graph(5, [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3),
                                       (3, 4), (2, 4)])
    print("--- 4 worked example, 5 vertices, 7 edges ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    print(f"degrees: {graph_util.degrees(graph)}")
    print(f"odd degree vertices: {odd_degree_vertices(graph)}")
    print(f"classification: {euler_classification(graph)}")
    trail, _ = hierholzer(graph)
    print(f"Hierholzer trail: {' -> '.join(str(vertex) for vertex in trail)}")
    print(f"edges used: {len(trail) - 1} of {graph_util.size(graph)}, "
          f"valid?: {is_euler_trail(graph, trail)}")
    print()


def konigsberg() -> None:
    print("--- 4 the seven bridges of Konigsberg ---")
    adjacency: Dict[int, List[int]] = {0: [1, 1, 2, 3], 1: [0, 0, 2, 3], 2: [0, 1, 3], 3: [0, 1, 2]}
    degrees = {vertex: len(neighbours) for vertex, neighbours in adjacency.items()}
    print("land masses: north bank, south bank, island, east island")
    print(f"degrees (counting parallel bridges): {degrees}")
    odd = [vertex for vertex, degree in degrees.items() if degree % 2 == 1]
    print(f"odd degree land masses: {odd}, that is {len(odd)} of them")
    print("Euler's answer: a walk crossing every bridge once needs 0 or 2 odd vertices")
    print("so no such walk exists")
    print()


def classification_table() -> None:
    print("--- 4 classification by counting odd degrees ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'odd':>3}  {'classification':>26}"
          f"  {'trail valid':>11}")
    families: List[Tuple[str, Graph]] = [
        ("C5 cycle", graph_util.cycle_graph(5)),
        ("C6 cycle", graph_util.cycle_graph(6)),
        ("path P5", graph_util.path_graph(5)),
        ("K3 triangle", graph_util.complete_graph(3)),
        ("K4", graph_util.complete_graph(4)),
        ("K5", graph_util.complete_graph(5)),
        ("K6", graph_util.complete_graph(6)),
        ("K7", graph_util.complete_graph(7)),
        ("K(2,3)", graph_util.complete_bipartite(2, 3)),
        ("K(3,3)", graph_util.complete_bipartite(3, 3)),
        ("K(2,4)", graph_util.complete_bipartite(2, 4)),
        ("Petersen", graph_util.petersen_graph()),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("cube Q3", graph_util.hypercube_graph(3)),
    ]
    for name, graph in families:
        trail, classification = hierholzer(graph)
        valid = is_euler_trail(graph, trail) if trail is not None else False
        expected = trail is not None
        print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
              f"  {len(odd_degree_vertices(graph)):>3}  {classification:>26}"
              f"  {str(valid) if expected else '-':>11}")
    print("K_n has an Euler circuit exactly when n is odd, every degree is n-1")
    print()


def complete_graph_rule() -> None:
    print("--- 4 K_n: circuit when n is odd, nothing when n is even and above 2 ---")
    print(f"{'n':>3}  {'degree':>6}  {'m':>4}  {'classification':>26}")
    for order_value in range(3, 10):
        graph = graph_util.complete_graph(order_value)
        print(f"{order_value:>3}  {order_value - 1:>6}  {graph_util.size(graph):>4}"
              f"  {euler_classification(graph):>26}")
    print()


def bipartite_rule() -> None:
    print("--- 4 K(a,b): circuit when both sides are even ---")
    print(f"{'graph':>10}  {'left deg':>8}  {'right deg':>9}  {'classification':>26}")
    for left, right in ((2, 2), (2, 3), (3, 3), (2, 4), (4, 4), (3, 4), (4, 6)):
        graph = graph_util.complete_bipartite(left, right)
        print(f"{'K(' + str(left) + ',' + str(right) + ')':>10}  {right:>8}  {left:>9}"
              f"  {euler_classification(graph):>26}")
    print("left vertices have degree b and right vertices have degree a")
    print()


def disconnected_case() -> None:
    graph = graph_util.build_graph(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    print("--- 4 all degrees even is not enough, the graph must be connected ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    print(f"degrees: {graph_util.degrees(graph)}, all even")
    print(f"components: {graph_util.connected_components(graph)}")
    trail, classification = hierholzer(graph)
    print(f"classification: {classification}, trail {trail}")
    print()


def two_algorithms() -> None:
    print("--- 4 Hierholzer against Fleury, both give valid trails ---")
    print(f"{'graph':>18}  {'m':>4}  {'hierholzer (ms)':>15}  {'fleury (ms)':>11}"
          f"  {'both valid':>10}")
    for name, graph in (("K5", graph_util.complete_graph(5)),
                        ("K7", graph_util.complete_graph(7)),
                        ("K9", graph_util.complete_graph(9)),
                        ("K11", graph_util.complete_graph(11)),
                        ("C20 cycle", graph_util.cycle_graph(20)),
                        ("K(4,4)", graph_util.complete_bipartite(4, 4))):
        start = time.perf_counter()
        trail, _ = hierholzer(graph)
        hierholzer_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        other = fleury(graph)
        fleury_time = (time.perf_counter() - start) * 1000
        both = is_euler_trail(graph, trail) and is_euler_trail(graph, other)
        print(f"{name:>18}  {graph_util.size(graph):>4}  {hierholzer_time:>15.3f}"
              f"  {fleury_time:>11.3f}  {str(both):>10}")
    print("Hierholzer is linear in the number of edges, Fleury pays for a bridge test per step")
    print()


def cost_growth() -> None:
    print("--- 4 Euler trails are polynomial, unlike Hamiltonian ones ---")
    print(f"{'n':>4}  {'m':>6}  {'hierholzer (ms)':>15}  {'us per edge':>11}")
    for order_value in (11, 21, 41, 81, 161, 321):
        graph = graph_util.cycle_graph(order_value)
        for vertex in range(0, order_value - 2, 2):
            graph[vertex].add(vertex + 2)
            graph[vertex + 2].add(vertex)
        if odd_degree_vertices(graph) and len(odd_degree_vertices(graph)) > 2:
            continue
        start = time.perf_counter()
        trail, _ = hierholzer(graph)
        elapsed = (time.perf_counter() - start) * 1000
        edges = graph_util.size(graph)
        valid = is_euler_trail(graph, trail)
        print(f"{order_value:>4}  {edges:>6}  {elapsed:>15.3f}  {elapsed * 1000 / edges:>11.2f}"
              f"{'' if valid else '  invalid'}")
    print()


def random_graphs() -> None:
    print("--- 4 random connected graphs, then fixed up to be Eulerian ---")
    print(f"{'n':>4}  {'m':>6}  {'odd before':>10}  {'m after':>7}  {'circuit':>7}"
          f"  {'time (ms)':>9}")
    random.seed(20260920)
    for order_value in (10, 20, 40, 80, 160):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.3]
        graph = graph_util.build_graph(order_value, edges)
        before = len(odd_degree_vertices(graph))
        odd = odd_degree_vertices(graph)
        for index in range(0, len(odd) - 1, 2):
            first, second = odd[index], odd[index + 1]
            if second in graph[first]:
                graph[first].discard(second)
                graph[second].discard(first)
            else:
                graph[first].add(second)
                graph[second].add(first)
        if not graph_util.is_connected(graph) or odd_degree_vertices(graph):
            print(f"{order_value:>4}  {graph_util.size(graph):>6}  {before:>10}"
                  f"  {graph_util.size(graph):>7}  {'no':>7}  {'-':>9}")
            continue
        start = time.perf_counter()
        trail, _ = hierholzer(graph)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{order_value:>4}  {len(edges):>6}  {before:>10}  {graph_util.size(graph):>7}"
              f"  {str(is_euler_trail(graph, trail)):>7}  {elapsed:>9.3f}")
    print()


worked_example()
konigsberg()
classification_table()
complete_graph_rule()
bipartite_rule()
disconnected_case()
two_algorithms()
cost_growth()
random_graphs()
