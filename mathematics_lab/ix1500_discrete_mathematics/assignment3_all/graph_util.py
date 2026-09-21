from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

Edge = Tuple[int, int]
Graph = Dict[int, Set[int]]


def build_graph(order: int, edges: Iterable[Edge]) -> Graph:
    graph: Graph = {vertex: set() for vertex in range(order)}
    for first, second in edges:
        if first == second:
            continue
        graph[first].add(second)
        graph[second].add(first)
    return graph


def edge_list(graph: Graph) -> List[Edge]:
    edges: List[Edge] = []
    for vertex in sorted(graph):
        for other in sorted(graph[vertex]):
            if vertex < other:
                edges.append((vertex, other))
    return edges


def order(graph: Graph) -> int:
    return len(graph)


def size(graph: Graph) -> int:
    return sum(len(neighbours) for neighbours in graph.values()) // 2


def degrees(graph: Graph) -> Dict[int, int]:
    return {vertex: len(neighbours) for vertex, neighbours in graph.items()}


def degree_sequence(graph: Graph) -> List[int]:
    return sorted(degrees(graph).values(), reverse=True)


def complete_graph(order_value: int) -> Graph:
    return build_graph(order_value, [(first, second)
                                     for first in range(order_value)
                                     for second in range(first + 1, order_value)])


def cycle_graph(order_value: int) -> Graph:
    return build_graph(order_value, [(vertex, (vertex + 1) % order_value)
                                     for vertex in range(order_value)])


def path_graph(order_value: int) -> Graph:
    return build_graph(order_value, [(vertex, vertex + 1)
                                     for vertex in range(order_value - 1)])


def complete_bipartite(left: int, right: int) -> Graph:
    return build_graph(left + right, [(first, left + second)
                                      for first in range(left)
                                      for second in range(right)])


def petersen_graph() -> Graph:
    edges: List[Edge] = []
    for vertex in range(5):
        edges.append((vertex, (vertex + 1) % 5))
        edges.append((vertex, vertex + 5))
        edges.append((vertex + 5, (vertex + 2) % 5 + 5))
    return build_graph(10, edges)


def wheel_graph(rim: int) -> Graph:
    edges: List[Edge] = [(vertex, (vertex + 1) % rim) for vertex in range(rim)]
    edges += [(rim, vertex) for vertex in range(rim)]
    return build_graph(rim + 1, edges)


def grid_graph(rows: int, columns: int) -> Graph:
    edges: List[Edge] = []
    for row in range(rows):
        for column in range(columns):
            vertex = row * columns + column
            if column + 1 < columns:
                edges.append((vertex, vertex + 1))
            if row + 1 < rows:
                edges.append((vertex, vertex + columns))
    return build_graph(rows * columns, edges)


def hypercube_graph(dimension: int) -> Graph:
    order_value = 1 << dimension
    edges: List[Edge] = []
    for vertex in range(order_value):
        for bit in range(dimension):
            other = vertex ^ (1 << bit)
            if vertex < other:
                edges.append((vertex, other))
    return build_graph(order_value, edges)


def connected_components(graph: Graph) -> List[List[int]]:
    seen: Set[int] = set()
    components: List[List[int]] = []
    for start in sorted(graph):
        if start in seen:
            continue
        stack = [start]
        component: List[int] = []
        seen.add(start)
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for other in sorted(graph[vertex]):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        components.append(sorted(component))
    return components


def is_connected(graph: Graph) -> bool:
    active = [vertex for vertex in graph if graph[vertex]]
    if not active:
        return len(graph) <= 1
    components = [component for component in connected_components(graph)
                  if any(graph[vertex] for vertex in component)]
    return len(components) == 1


def neighbours_of_set(graph: Graph, vertices: Iterable[int]) -> Set[int]:
    result: Set[int] = set()
    for vertex in vertices:
        result |= graph[vertex]
    return result - set(vertices)


def is_clique(graph: Graph, vertices: List[int]) -> bool:
    for index, first in enumerate(vertices):
        for second in vertices[index + 1:]:
            if second not in graph[first]:
                return False
    return True


def greedy_clique_bound(graph: Graph) -> int:
    best = 0
    for start in sorted(graph, key=lambda vertex: -len(graph[vertex])):
        clique = [start]
        for candidate in sorted(graph[start], key=lambda vertex: -len(graph[vertex])):
            if all(candidate in graph[member] for member in clique):
                clique.append(candidate)
        best = max(best, len(clique))
    return best


def describe(name: str, graph: Graph) -> str:
    return (f"{name}: {order(graph)} vertices, {size(graph)} edges, "
            f"degrees {degree_sequence(graph)}")


def render_edges(graph: Graph, limit: int = 12) -> str:
    edges = edge_list(graph)
    shown = ' '.join(f"{first}-{second}" for first, second in edges[:limit])
    return shown + (" .." if len(edges) > limit else "")
