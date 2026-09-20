import graph_util
import heapq
import random
import time

from typing import Dict, List, Optional, Set, Tuple

WeightedGraph = Dict[int, Dict[int, Tuple[int, int]]]

INFINITY = float('inf')


def build_weighted(order: int,
                   edges: List[Tuple[int, int, int, int]]) -> WeightedGraph:
    graph: WeightedGraph = {vertex: {} for vertex in range(order)}
    for first, second, cost, resource in edges:
        graph[first][second] = (cost, resource)
        graph[second][first] = (cost, resource)
    return graph


def dijkstra(graph: WeightedGraph, source: int) -> Tuple[Dict[int, float], Dict[int, int]]:
    distance: Dict[int, float] = {vertex: INFINITY for vertex in graph}
    parent: Dict[int, Optional[int]] = {vertex: None for vertex in graph}
    distance[source] = 0
    queue: List[Tuple[float, int]] = [(0, source)]
    while queue:
        current, vertex = heapq.heappop(queue)
        if current > distance[vertex]:
            continue
        for other, (cost, _) in graph[vertex].items():
            candidate = current + cost
            if candidate < distance[other]:
                distance[other] = candidate
                parent[other] = vertex
                heapq.heappush(queue, (candidate, other))
    return distance, parent


def rebuild(parent: Dict[int, Optional[int]], target: int) -> List[int]:
    path = [target]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def constrained_dijkstra(graph: WeightedGraph, source: int, target: int,
                         budget: int) -> Tuple[float, Optional[List[int]], int]:
    best: Dict[Tuple[int, int], float] = {(source, 0): 0}
    queue: List[Tuple[float, int, int, List[int]]] = [(0, 0, source, [source])]
    expanded = 0
    while queue:
        cost, resource, vertex, path = heapq.heappop(queue)
        expanded += 1
        if vertex == target:
            return cost, path, expanded
        if best.get((vertex, resource), INFINITY) < cost:
            continue
        for other, (edge_cost, edge_resource) in graph[vertex].items():
            if other in path:
                continue
            next_resource = resource + edge_resource
            if next_resource > budget:
                continue
            next_cost = cost + edge_cost
            key = (other, next_resource)
            if next_cost < best.get(key, INFINITY):
                best[key] = next_cost
                heapq.heappush(queue, (next_cost, next_resource, other, path + [other]))
    return INFINITY, None, expanded


def bounded_hops(graph: WeightedGraph, source: int,
                 hops: int) -> List[Dict[int, float]]:
    layers: List[Dict[int, float]] = [{vertex: INFINITY for vertex in graph}]
    layers[0][source] = 0
    for _ in range(hops):
        previous = layers[-1]
        current = dict(previous)
        for vertex in graph:
            if previous[vertex] == INFINITY:
                continue
            for other, (cost, _) in graph[vertex].items():
                if previous[vertex] + cost < current[other]:
                    current[other] = previous[vertex] + cost
        layers.append(current)
    return layers


def forbidden_vertices(graph: WeightedGraph, source: int, target: int,
                       banned: Set[int]) -> Tuple[float, Optional[List[int]]]:
    reduced = {vertex: {other: weight for other, weight in graph[vertex].items()
                        if other not in banned}
               for vertex in graph if vertex not in banned}
    if source in banned or target in banned:
        return INFINITY, None
    distance, parent = dijkstra(reduced, source)
    if distance[target] == INFINITY:
        return INFINITY, None
    return distance[target], rebuild(parent, target)


def must_visit(graph: WeightedGraph, source: int, target: int,
               required: List[int]) -> Tuple[float, Optional[List[int]]]:
    distance_from: Dict[int, Dict[int, float]] = {}
    parents: Dict[int, Dict[int, Optional[int]]] = {}
    for vertex in [source, target] + required:
        if vertex in distance_from:
            continue
        distance_from[vertex], parents[vertex] = dijkstra(graph, vertex)

    best_cost = INFINITY
    best_order: Optional[List[int]] = None
    for permutation in permutations(required):
        chain = [source] + list(permutation) + [target]
        total = 0.0
        feasible = True
        for index in range(len(chain) - 1):
            step = distance_from[chain[index]][chain[index + 1]]
            if step == INFINITY:
                feasible = False
                break
            total += step
        if feasible and total < best_cost:
            best_cost = total
            best_order = chain
    if best_order is None:
        return INFINITY, None

    full: List[int] = [best_order[0]]
    for index in range(len(best_order) - 1):
        segment = rebuild(parents[best_order[index]], best_order[index + 1])
        full.extend(segment[1:])
    return best_cost, full


def permutations(items: List[int]):
    if not items:
        yield []
        return
    for index, item in enumerate(items):
        for rest in permutations(items[:index] + items[index + 1:]):
            yield [item] + rest


def sample_network() -> WeightedGraph:
    return build_weighted(7, [
        (0, 1, 4, 1), (0, 2, 2, 3), (1, 2, 1, 1), (1, 3, 5, 1),
        (2, 3, 8, 1), (2, 4, 10, 2), (3, 4, 2, 5), (3, 5, 6, 1),
        (4, 5, 3, 1), (4, 6, 5, 1), (5, 6, 1, 4),
    ])


def worked_example() -> None:
    graph = sample_network()
    print("--- 8 worked example, 7 nodes, each edge has a cost and a resource ---")
    print(f"{'edge':>8}  {'cost':>4}  {'resource':>8}")
    for vertex in sorted(graph):
        for other, (cost, resource) in sorted(graph[vertex].items()):
            if vertex < other:
                print(f"{str(vertex) + '-' + str(other):>8}  {cost:>4}  {resource:>8}")
    distance, parent = dijkstra(graph, 0)
    print(f"unconstrained shortest path 0 to 6: {rebuild(parent, 6)}, cost {distance[6]}")
    used = 0
    path = rebuild(parent, 6)
    for index in range(len(path) - 1):
        used += graph[path[index]][path[index + 1]][1]
    print(f"resource used by that path: {used}")
    print()


def budget_sweep() -> None:
    graph = sample_network()
    print("--- 8 tightening the resource budget changes the optimal path ---")
    print(f"{'budget':>6}  {'cost':>5}  {'resource':>8}  {'expanded':>8}  path")
    for budget in range(2, 13):
        cost, path, expanded = constrained_dijkstra(graph, 0, 6, budget)
        if path is None:
            print(f"{budget:>6}  {'none':>5}  {'-':>8}  {expanded:>8}  infeasible")
            continue
        resource = sum(graph[path[index]][path[index + 1]][1]
                       for index in range(len(path) - 1))
        shown = ' -> '.join(str(vertex) for vertex in path)
        print(f"{budget:>6}  {cost:>5}  {resource:>8}  {expanded:>8}  {shown}")
    print("the unconstrained optimum reappears once the budget is large enough")
    print()


def hop_constraint() -> None:
    graph = sample_network()
    print("--- 8 shortest path using at most k edges ---")
    layers = bounded_hops(graph, 0, 6)
    print(f"{'hops':>4}  " + '  '.join(f"{'d(' + str(vertex) + ')':>6}"
                                       for vertex in sorted(graph)))
    for hops, layer in enumerate(layers):
        cells = '  '.join(f"{('inf' if layer[vertex] == INFINITY else int(layer[vertex])):>6}"
                          for vertex in sorted(graph))
        print(f"{hops:>4}  {cells}")
    distance, _ = dijkstra(graph, 0)
    print(f"unrestricted distances: "
          f"{[int(distance[vertex]) for vertex in sorted(graph)]}")
    print("this is Bellman-Ford stopped early, each round allows one more edge")
    print()


def forbidden_example() -> None:
    graph = sample_network()
    print("--- 8 forbidding vertices ---")
    print(f"{'banned':>10}  {'cost':>5}  path")
    for banned in ([], [1], [2], [1, 2], [3], [4], [3, 4], [5]):
        cost, path = forbidden_vertices(graph, 0, 6, set(banned))
        shown = "no route" if path is None else ' -> '.join(str(vertex) for vertex in path)
        cost_text = "none" if cost == INFINITY else str(int(cost))
        print(f"{str(banned):>10}  {cost_text:>5}  {shown}")
    print()


def detour_network() -> WeightedGraph:
    return build_weighted(9, [
        (0, 1, 1, 1), (1, 2, 1, 1), (2, 8, 1, 1),
        (0, 3, 4, 1), (3, 4, 1, 1), (4, 8, 4, 1),
        (1, 5, 3, 1), (5, 6, 1, 1), (6, 2, 3, 1),
        (3, 7, 2, 1), (7, 4, 2, 1),
    ])


def must_visit_example() -> None:
    graph = detour_network()
    print("--- 8 requiring the route to pass through given vertices ---")
    print(f"{'required':>12}  {'cost':>5}  {'detour':>6}  route")
    base, _ = must_visit(graph, 0, 8, [])
    for required in ([], [5], [6], [5, 6], [3], [4], [3, 4], [7], [5, 7]):
        cost, path = must_visit(graph, 0, 8, required)
        shown = "no route" if path is None else ' -> '.join(str(vertex) for vertex in path)
        cost_text = "none" if cost == INFINITY else str(int(cost))
        detour = "-" if cost == INFINITY else f"+{int(cost - base)}"
        print(f"{str(required):>12}  {cost_text:>5}  {detour:>6}  {shown}")
    print("each forced stop adds a detour, the order of the stops is chosen by brute force")
    print()


def pareto_front() -> None:
    graph = sample_network()
    print("--- 8 the Pareto front of cost against resource ---")
    print(f"{'cost':>5}  {'resource':>8}  path")
    seen: Set[Tuple[int, int]] = set()
    front: List[Tuple[int, int, List[int]]] = []
    for budget in range(1, 20):
        cost, path, _ = constrained_dijkstra(graph, 0, 6, budget)
        if path is None:
            continue
        resource = sum(graph[path[index]][path[index + 1]][1]
                       for index in range(len(path) - 1))
        if (int(cost), resource) in seen:
            continue
        seen.add((int(cost), resource))
        front.append((int(cost), resource, path))
    for cost, resource, path in front:
        print(f"{cost:>5}  {resource:>8}  {' -> '.join(str(vertex) for vertex in path)}")
    print("no point on the front improves both objectives at once")
    print()


def cost_growth() -> None:
    print("--- 8 plain Dijkstra against the resource constrained version ---")
    print(f"{'n':>4}  {'m':>6}  {'budget':>6}  {'dijkstra (ms)':>13}"
          f"  {'constrained (ms)':>16}  {'states':>8}")
    random.seed(20260920)
    for order_value in (20, 40, 80, 160, 320):
        edges: List[Tuple[int, int, int, int]] = []
        for vertex in range(order_value - 1):
            edges.append((vertex, vertex + 1, random.randint(1, 9), random.randint(1, 4)))
        for _ in range(order_value):
            first = random.randrange(order_value)
            second = random.randrange(order_value)
            if first != second:
                edges.append((first, second, random.randint(1, 9), random.randint(1, 4)))
        graph = build_weighted(order_value, edges)
        start = time.perf_counter()
        dijkstra(graph, 0)
        plain_time = (time.perf_counter() - start) * 1000
        budget = order_value // 2
        start = time.perf_counter()
        _, _, expanded = constrained_dijkstra(graph, 0, order_value - 1, budget)
        constrained_time = (time.perf_counter() - start) * 1000
        print(f"{order_value:>4}  {len(edges):>6}  {budget:>6}  {plain_time:>13.3f}"
              f"  {constrained_time:>16.3f}  {expanded:>8}")
    print("the constrained search explores (vertex, resource) pairs, so cost grows with the budget")
    print()


def budget_cost_growth() -> None:
    print("--- 8 cost against the size of the budget, n fixed ---")
    order_value = 40
    edges: List[Tuple[int, int, int, int]] = []
    for vertex in range(order_value - 1):
        edges.append((vertex, vertex + 1, 9, 1))
    for vertex in range(0, order_value - 4, 4):
        edges.append((vertex, vertex + 4, 1, 12))
    graph = build_weighted(order_value, edges)
    print(f"{'budget':>6}  {'cost':>5}  {'shortcuts used':>14}  {'states':>8}  {'time (ms)':>9}")
    for budget in (5, 15, 30, 60, 120, 240):
        start = time.perf_counter()
        cost, path, expanded = constrained_dijkstra(graph, 0, order_value - 1, budget)
        elapsed = (time.perf_counter() - start) * 1000
        cost_text = "none" if cost == INFINITY else str(int(cost))
        shortcuts = 0
        if path is not None:
            shortcuts = sum(1 for index in range(len(path) - 1)
                            if abs(path[index + 1] - path[index]) == 4)
        print(f"{budget:>6}  {cost_text:>5}  {shortcuts:>14}  {expanded:>8}  {elapsed:>9.3f}")
    print("each shortcut is cheap but eats 12 units of resource, so the budget caps how many fit")
    print("the problem is NP-hard in general, the budget is the pseudo-polynomial factor")
    print()


worked_example()
budget_sweep()
hop_constraint()
forbidden_example()
must_visit_example()
pareto_front()
cost_growth()
budget_cost_growth()
