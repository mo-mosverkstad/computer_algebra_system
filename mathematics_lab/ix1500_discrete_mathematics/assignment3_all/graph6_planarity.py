import graph_util
import itertools
import random
import time

from typing import Dict, List, Optional, Set, Tuple

Graph = Dict[int, set]


def is_bipartite(graph: Graph) -> bool:
    colour: Dict[int, int] = {}
    for start in sorted(graph):
        if start in colour:
            continue
        colour[start] = 0
        stack = [start]
        while stack:
            vertex = stack.pop()
            for other in graph[vertex]:
                if other not in colour:
                    colour[other] = 1 - colour[vertex]
                    stack.append(other)
                elif colour[other] == colour[vertex]:
                    return False
    return True


def euler_edge_bound(order: int, bipartite: bool) -> int:
    if order < 3:
        return order * (order - 1) // 2
    return 2 * order - 4 if bipartite else 3 * order - 6


def violates_euler(graph: Graph) -> bool:
    order = graph_util.order(graph)
    if order < 5:
        return False
    return graph_util.size(graph) > euler_edge_bound(order, is_bipartite(graph))


def faces_from_euler(graph: Graph) -> int:
    components = len(graph_util.connected_components(graph))
    return graph_util.size(graph) - graph_util.order(graph) + 1 + components


def suppress_degree_two(graph: Graph) -> Graph:
    working = {vertex: set(neighbours) for vertex, neighbours in graph.items()}
    changed = True
    while changed:
        changed = False
        for vertex in list(working):
            if vertex not in working:
                continue
            neighbours = working[vertex]
            if len(neighbours) <= 1:
                for other in neighbours:
                    working[other].discard(vertex)
                del working[vertex]
                changed = True
            elif len(neighbours) == 2:
                first, second = sorted(neighbours)
                if second in working[first]:
                    continue
                working[first].discard(vertex)
                working[second].discard(vertex)
                working[first].add(second)
                working[second].add(first)
                del working[vertex]
                changed = True
    return working


def all_simple_paths(graph: Graph, start: int, end: int,
                     forbidden: Set[int]) -> List[List[int]]:
    results: List[List[int]] = []

    def walk(path: List[int], visited: Set[int]) -> None:
        vertex = path[-1]
        if vertex == end and len(path) >= 2:
            results.append(list(path))
            return
        for other in sorted(graph[vertex]):
            if other in visited:
                continue
            if other != end and other in forbidden:
                continue
            path.append(other)
            visited.add(other)
            walk(path, visited)
            path.pop()
            visited.remove(other)

    walk([start], {start})
    return results


def route_disjoint(graph: Graph, pairs: List[Tuple[int, int]],
                   branch: Set[int]) -> Optional[List[List[int]]]:
    chosen: List[List[int]] = []
    blocked: Set[int] = set()

    def step(index: int) -> bool:
        if index == len(pairs):
            return True
        start, end = pairs[index]
        for path in all_simple_paths(graph, start, end, branch | blocked):
            interior = set(path[1:-1])
            if interior & blocked:
                continue
            chosen.append(path)
            blocked.update(interior)
            if step(index + 1):
                return True
            blocked.difference_update(interior)
            chosen.pop()
        return False

    return [list(path) for path in chosen] if step(0) else None


def contains_subdivision(graph: Graph,
                         target: Graph) -> Optional[Tuple[Dict[int, int], List[List[int]]]]:
    reduced = suppress_degree_two(graph)
    nodes = sorted(target)
    needed = max(len(target[node]) for node in target)
    candidates = sorted(vertex for vertex in reduced if len(reduced[vertex]) >= needed)
    for selection in itertools.combinations(candidates, len(nodes)):
        for assignment in itertools.permutations(selection):
            mapping = {node: assignment[index] for index, node in enumerate(nodes)}
            branch = set(assignment)
            pairs = [(mapping[first], mapping[second])
                     for first in nodes for second in sorted(target[first])
                     if first < second]
            routes = route_disjoint(reduced, pairs, branch)
            if routes is not None:
                return mapping, routes
    return None


def contains_k5(graph: Graph) -> Optional[Tuple[Dict[int, int], List[List[int]]]]:
    return contains_subdivision(graph, graph_util.complete_graph(5))


def contains_k33(graph: Graph) -> Optional[Tuple[Dict[int, int], List[List[int]]]]:
    return contains_subdivision(graph, graph_util.complete_bipartite(3, 3))


def is_planar(graph: Graph) -> Tuple[bool, str]:
    if violates_euler(graph):
        return False, "Euler's edge bound exceeded"
    if contains_k5(graph) is not None:
        return False, "contains a K5 subdivision"
    if contains_k33(graph) is not None:
        return False, "contains a K(3,3) subdivision"
    return True, "no Kuratowski subgraph"


def worked_example() -> None:
    print("--- 6 Euler's formula on planar graphs: v - e + f = 2 ---")
    for name, graph in (("triangle K3", graph_util.complete_graph(3)),
                        ("K4", graph_util.complete_graph(4)),
                        ("cube Q3", graph_util.hypercube_graph(3)),
                        ("grid 3x3", graph_util.grid_graph(3, 3)),
                        ("wheel W5", graph_util.wheel_graph(5))):
        vertices = graph_util.order(graph)
        edges = graph_util.size(graph)
        faces = faces_from_euler(graph)
        print(f"{name:>12}: v = {vertices:>2}, e = {edges:>2}, f = {faces:>2}, "
              f"v - e + f = {vertices - edges + faces}")
    print()


def kuratowski_graphs() -> None:
    print("--- 6 the two forbidden graphs ---")
    for name, graph in (("K5", graph_util.complete_graph(5)),
                        ("K(3,3)", graph_util.complete_bipartite(3, 3))):
        vertices = graph_util.order(graph)
        edges = graph_util.size(graph)
        bound = euler_edge_bound(vertices, is_bipartite(graph))
        planar, reason = is_planar(graph)
        print(f"{name:>8}: v = {vertices}, e = {edges}, Euler allows at most {bound}"
              f", planar?: {planar} ({reason})")
    print("K5: 10 > 3*5 - 6 = 9")
    print("K(3,3) is bipartite so triangle free, 9 > 2*6 - 4 = 8")
    print()


def verdict_table() -> None:
    print("--- 6 Euler's bound first, then the Kuratowski search ---")
    print(f"{'graph':>18}  {'v':>3}  {'e':>4}  {'bound':>5}  {'euler':>10}  {'K5 sub':>6}"
          f"  {'K(3,3) sub':>10}  {'planar':>6}")
    families: List[Tuple[str, Graph]] = [
        ("K4", graph_util.complete_graph(4)),
        ("K5", graph_util.complete_graph(5)),
        ("K6", graph_util.complete_graph(6)),
        ("K(2,3)", graph_util.complete_bipartite(2, 3)),
        ("K(3,3)", graph_util.complete_bipartite(3, 3)),
        ("K(3,4)", graph_util.complete_bipartite(3, 4)),
        ("Petersen", graph_util.petersen_graph()),
        ("cube Q3", graph_util.hypercube_graph(3)),
        ("grid 3x3", graph_util.grid_graph(3, 3)),
        ("wheel W6", graph_util.wheel_graph(6)),
        ("C10 cycle", graph_util.cycle_graph(10)),
    ]
    for name, graph in families:
        vertices = graph_util.order(graph)
        edges = graph_util.size(graph)
        bound = euler_edge_bound(vertices, is_bipartite(graph))
        euler_says = "not planar" if violates_euler(graph) else "no verdict"
        k5 = contains_k5(graph) is not None
        k33 = contains_k33(graph) is not None
        planar, _ = is_planar(graph)
        print(f"{name:>18}  {vertices:>3}  {edges:>4}  {bound:>5}  {euler_says:>10}"
              f"  {str(k5):>6}  {str(k33):>10}  {str(planar):>6}")
    print("Kuratowski: planar exactly when no subdivision of K5 or K(3,3) is present")
    print()


def petersen_detail() -> None:
    graph = graph_util.petersen_graph()
    print("--- 6 the Petersen graph passes Euler's bound yet is not planar ---")
    vertices = graph_util.order(graph)
    edges = graph_util.size(graph)
    print(f"v = {vertices}, e = {edges}, bound 3v - 6 = {3 * vertices - 6}, Euler says nothing")
    print(f"bipartite?: {is_bipartite(graph)}, girth 5 so the bipartite bound does not apply")
    found = contains_k33(graph)
    mapping, routes = found
    print(f"branch vertices: {mapping}")
    for path in routes:
        print(f"  path {' - '.join(str(vertex) for vertex in path)}")
    planar, reason = is_planar(graph)
    print(f"verdict: planar?: {planar}, {reason}")
    print()


def subdivision_example() -> None:
    graph = graph_util.complete_graph(5)
    graph[0].discard(1)
    graph[1].discard(0)
    graph[5] = {0, 1}
    graph[0].add(5)
    graph[1].add(5)
    print("--- 6 a subdivision of K5 is still not planar ---")
    print(f"K5 with edge 0-1 replaced by 0-5-1: v = {graph_util.order(graph)}, "
          f"e = {graph_util.size(graph)}")
    print(f"Euler bound 3v - 6 = {3 * graph_util.order(graph) - 6}, so the bound is satisfied")
    print(f"suppressing the degree 2 vertex recovers: "
          f"{graph_util.edge_list(suppress_degree_two(graph))}")
    planar, reason = is_planar(graph)
    print(f"verdict: planar?: {planar}, {reason}")
    print()


def planar_families() -> None:
    print("--- 6 planar families and their face counts ---")
    print(f"{'graph':>18}  {'v':>3}  {'e':>4}  {'f':>3}  {'v-e+f':>5}  {'e <= 3v-6':>9}"
          f"  {'planar':>6}")
    families: List[Tuple[str, Graph]] = [
        ("path P6", graph_util.path_graph(6)),
        ("C8 cycle", graph_util.cycle_graph(8)),
        ("K4", graph_util.complete_graph(4)),
        ("wheel W7", graph_util.wheel_graph(7)),
        ("grid 3x4", graph_util.grid_graph(3, 4)),
        ("cube Q3", graph_util.hypercube_graph(3)),
    ]
    for name, graph in families:
        vertices = graph_util.order(graph)
        edges = graph_util.size(graph)
        faces = faces_from_euler(graph)
        planar, _ = is_planar(graph)
        print(f"{name:>18}  {vertices:>3}  {edges:>4}  {faces:>3}"
              f"  {vertices - edges + faces:>5}"
              f"  {str(edges <= 3 * vertices - 6):>9}  {str(planar):>6}")
    print()


def consequences() -> None:
    print("--- 6 consequences of Euler's formula ---")
    print(f"{'v':>4}  {'max edges 3v-6':>14}  {'K_v edges':>9}  {'K_v planar?':>11}")
    for vertices in range(3, 8):
        complete_edges = vertices * (vertices - 1) // 2
        bound = euler_edge_bound(vertices, False)
        planar, _ = is_planar(graph_util.complete_graph(vertices))
        print(f"{vertices:>4}  {bound:>14}  {complete_edges:>9}  {str(planar):>11}")
    print("every planar graph has a vertex of degree at most 5, hence the five colour theorem")
    print()


def cost_growth() -> None:
    print("--- 6 Euler's bound is instant, the subdivision search is not ---")
    print(f"{'v':>4}  {'e':>5}  {'planar':>6}  {'euler (ms)':>10}  {'kuratowski (ms)':>15}"
          f"  {'decided by':>26}")
    random.seed(20260920)
    for order_value in (6, 8, 10, 11, 12):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.3]
        graph = graph_util.build_graph(order_value, edges)
        start = time.perf_counter()
        violates_euler(graph)
        euler_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        planar, reason = is_planar(graph)
        kuratowski_time = (time.perf_counter() - start) * 1000
        print(f"{order_value:>4}  {len(edges):>5}  {str(planar):>6}  {euler_time:>10.4f}"
              f"  {kuratowski_time:>15.2f}  {reason:>26}")
    print("Hopcroft and Tarjan reduced planarity testing to linear time in the vertex count")
    print()


worked_example()
kuratowski_graphs()
verdict_table()
petersen_detail()
subdivision_example()
planar_families()
consequences()
cost_growth()
