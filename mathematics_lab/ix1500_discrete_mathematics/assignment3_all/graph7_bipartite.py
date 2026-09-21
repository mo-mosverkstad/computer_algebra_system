import graph_util
import random
import time

from typing import Dict, List, Optional, Set, Tuple

Graph = Dict[int, set]


def two_colour(graph: Graph) -> Tuple[Optional[Dict[int, int]], Optional[List[int]]]:
    colour: Dict[int, int] = {}
    parent: Dict[int, Optional[int]] = {}
    for start in sorted(graph):
        if start in colour:
            continue
        colour[start] = 0
        parent[start] = None
        queue = [start]
        while queue:
            vertex = queue.pop(0)
            for other in sorted(graph[vertex]):
                if other not in colour:
                    colour[other] = 1 - colour[vertex]
                    parent[other] = vertex
                    queue.append(other)
                elif colour[other] == colour[vertex]:
                    return None, odd_cycle(parent, vertex, other)
    return colour, None


def odd_cycle(parent: Dict[int, Optional[int]], first: int, second: int) -> List[int]:
    first_chain = [first]
    while parent[first_chain[-1]] is not None:
        first_chain.append(parent[first_chain[-1]])
    second_chain = [second]
    while parent[second_chain[-1]] is not None:
        second_chain.append(parent[second_chain[-1]])
    shared = set(second_chain)
    meeting = next(vertex for vertex in first_chain if vertex in shared)
    upper = first_chain[:first_chain.index(meeting) + 1]
    lower = second_chain[:second_chain.index(meeting)]
    return upper + lower[::-1]


def parts(graph: Graph) -> Optional[Tuple[List[int], List[int]]]:
    colour, _ = two_colour(graph)
    if colour is None:
        return None
    left = sorted(vertex for vertex in colour if colour[vertex] == 0)
    right = sorted(vertex for vertex in colour if colour[vertex] == 1)
    return left, right


def hopcroft_karp(graph: Graph, left: List[int], right: List[int]) -> Dict[int, int]:
    match_left: Dict[int, Optional[int]] = {vertex: None for vertex in left}
    match_right: Dict[int, Optional[int]] = {vertex: None for vertex in right}

    def augment(vertex: int, visited: Set[int]) -> bool:
        for other in sorted(graph[vertex]):
            if other in visited:
                continue
            visited.add(other)
            if match_right[other] is None or augment(match_right[other], visited):
                match_left[vertex] = other
                match_right[other] = vertex
                return True
        return False

    for vertex in left:
        if match_left[vertex] is None:
            augment(vertex, set())
    return {vertex: other for vertex, other in match_left.items() if other is not None}


def minimum_vertex_cover(graph: Graph, left: List[int], right: List[int],
                         matching: Dict[int, int]) -> List[int]:
    matched_right = set(matching.values())
    unmatched_left = [vertex for vertex in left if vertex not in matching]
    reachable_left: Set[int] = set(unmatched_left)
    reachable_right: Set[int] = set()
    stack = list(unmatched_left)
    inverse = {other: vertex for vertex, other in matching.items()}
    while stack:
        vertex = stack.pop()
        for other in graph[vertex]:
            if other in reachable_right:
                continue
            if matching.get(vertex) == other:
                continue
            reachable_right.add(other)
            partner = inverse.get(other)
            if partner is not None and partner not in reachable_left:
                reachable_left.add(partner)
                stack.append(partner)
    cover = [vertex for vertex in left if vertex not in reachable_left]
    cover += [vertex for vertex in right if vertex in reachable_right]
    return sorted(cover)


def is_matching(graph: Graph, matching: Dict[int, int]) -> bool:
    if len(set(matching.values())) != len(matching):
        return False
    return all(other in graph[vertex] for vertex, other in matching.items())


def is_vertex_cover(graph: Graph, cover: List[int]) -> bool:
    chosen = set(cover)
    return all(first in chosen or second in chosen
               for first, second in graph_util.edge_list(graph))


def worked_example() -> None:
    graph = graph_util.build_graph(7, [(0, 4), (0, 5), (1, 4), (1, 6), (2, 5),
                                       (2, 6), (3, 6)])
    print("--- 7 worked example, bipartite by breadth first two colouring ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    colour, cycle = two_colour(graph)
    print(f"colouring: {colour}")
    left, right = parts(graph)
    print(f"left part {left}, right part {right}")
    print(f"every edge crosses?: "
          f"{all(colour[first] != colour[second] for first, second in graph_util.edge_list(graph))}")
    matching = hopcroft_karp(graph, left, right)
    print(f"maximum matching: {matching}, size {len(matching)}")
    cover = minimum_vertex_cover(graph, left, right, matching)
    print(f"minimum vertex cover: {cover}, size {len(cover)}")
    print(f"Konig: matching size {len(matching)} = cover size {len(cover)}")
    print()


def odd_cycle_example() -> None:
    graph = graph_util.cycle_graph(5)
    print("--- 7 an odd cycle is the obstruction ---")
    print(f"C5 edges: {graph_util.render_edges(graph, 20)}")
    colour, cycle = two_colour(graph)
    print(f"two colouring: {colour}, conflict cycle {cycle}")
    print(f"cycle length {len(cycle)}, odd so no two colouring exists")
    print()

    graph = graph_util.cycle_graph(6)
    colour, cycle = two_colour(graph)
    print(f"C6 two colouring: {colour}, conflict {cycle}")
    print("even cycles alternate cleanly")
    print()


def families_table() -> None:
    print("--- 7 bipartite tests and the two theorems ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'bipartite':>9}  {'parts':>9}"
          f"  {'matching':>8}  {'cover':>5}  {'Konig':>5}")
    families: List[Tuple[str, Graph]] = [
        ("path P6", graph_util.path_graph(6)),
        ("C6 cycle", graph_util.cycle_graph(6)),
        ("C7 cycle", graph_util.cycle_graph(7)),
        ("K(3,3)", graph_util.complete_bipartite(3, 3)),
        ("K(2,4)", graph_util.complete_bipartite(2, 4)),
        ("K4", graph_util.complete_graph(4)),
        ("grid 3x4", graph_util.grid_graph(3, 4)),
        ("cube Q3", graph_util.hypercube_graph(3)),
        ("cube Q4", graph_util.hypercube_graph(4)),
        ("Petersen", graph_util.petersen_graph()),
        ("tree wheel-free", graph_util.path_graph(9)),
    ]
    for name, graph in families:
        found = parts(graph)
        if found is None:
            print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
                  f"  {'False':>9}  {'-':>9}  {'-':>8}  {'-':>5}  {'-':>5}")
            continue
        left, right = found
        matching = hopcroft_karp(graph, left, right)
        cover = minimum_vertex_cover(graph, left, right, matching)
        print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
              f"  {'True':>9}  {str(len(left)) + '+' + str(len(right)):>9}"
              f"  {len(matching):>8}  {len(cover):>5}"
              f"  {str(len(matching) == len(cover)):>5}")
    print("Konig's theorem: in a bipartite graph the maximum matching equals the minimum cover")
    print()


def halls_condition() -> None:
    print("--- 7 Hall's condition, a perfect matching on the left needs |N(S)| >= |S| ---")
    cases: List[Tuple[str, Graph, List[int], List[int]]] = []

    graph = graph_util.build_graph(6, [(0, 3), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4)])
    cases.append(("three left, two right neighbours", graph, [0, 1, 2], [3, 4, 5]))

    graph = graph_util.build_graph(6, [(0, 3), (1, 3), (1, 4), (2, 4), (2, 5)])
    cases.append(("chain, condition holds", graph, [0, 1, 2], [3, 4, 5]))

    graph = graph_util.complete_bipartite(3, 3)
    cases.append(("K(3,3)", graph, [0, 1, 2], [3, 4, 5]))

    print(f"{'case':>34}  {'|left|':>6}  {'matching':>8}  {'saturated':>9}"
          f"  {'Hall holds':>10}")
    for name, graph, left, right in cases:
        matching = hopcroft_karp(graph, left, right)
        saturated = len(matching) == len(left)
        holds = hall_condition_holds(graph, left)
        print(f"{name:>34}  {len(left):>6}  {len(matching):>8}  {str(saturated):>9}"
              f"  {str(holds):>10}")
    print()


def hall_condition_holds(graph: Graph, left: List[int]) -> bool:
    for mask in range(1, 1 << len(left)):
        subset = [left[index] for index in range(len(left)) if mask >> index & 1]
        if len(graph_util.neighbours_of_set(graph, subset)) < len(subset):
            return False
    return True


def hall_violation() -> None:
    graph = graph_util.build_graph(6, [(0, 3), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4)])
    left = [0, 1, 2]
    print("--- 7 locating the set that violates Hall's condition ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    for mask in range(1, 1 << len(left)):
        subset = [left[index] for index in range(len(left)) if mask >> index & 1]
        neighbours = graph_util.neighbours_of_set(graph, subset)
        marker = "  <- violates Hall" if len(neighbours) < len(subset) else ""
        print(f"  S = {subset}, N(S) = {sorted(neighbours)}, "
              f"|S| = {len(subset)}, |N(S)| = {len(neighbours)}{marker}")
    print()


def two_colouring_is_the_chromatic_number() -> None:
    print("--- 7 bipartite is exactly the same as 2-colourable ---")
    print(f"{'graph':>18}  {'bipartite':>9}  {'odd cycle':>22}  {'chi':>3}")
    for name, graph in (("C6", graph_util.cycle_graph(6)),
                        ("C7", graph_util.cycle_graph(7)),
                        ("K(2,3)", graph_util.complete_bipartite(2, 3)),
                        ("K3", graph_util.complete_graph(3)),
                        ("Petersen", graph_util.petersen_graph()),
                        ("grid 4x4", graph_util.grid_graph(4, 4))):
        colour, cycle = two_colour(graph)
        bipartite = colour is not None
        cycle_text = "none" if cycle is None else str(cycle)
        print(f"{name:>18}  {str(bipartite):>9}  {cycle_text:>22}  {2 if bipartite else 3:>3}")
    print()


def cost_growth() -> None:
    print("--- 7 both the test and the matching are polynomial ---")
    print(f"{'n':>5}  {'m':>7}  {'bipartite (ms)':>14}  {'matching (ms)':>13}  {'matching':>8}")
    random.seed(20260920)
    for side in (10, 20, 40, 80, 160, 320):
        edges = [(first, side + second)
                 for first in range(side)
                 for second in range(side)
                 if random.random() < 4.0 / side]
        graph = graph_util.build_graph(2 * side, edges)
        start = time.perf_counter()
        found = parts(graph)
        bipartite_time = (time.perf_counter() - start) * 1000
        left = list(range(side))
        right = list(range(side, 2 * side))
        start = time.perf_counter()
        matching = hopcroft_karp(graph, left, right)
        matching_time = (time.perf_counter() - start) * 1000
        print(f"{2 * side:>5}  {len(edges):>7}  {bipartite_time:>14.3f}"
              f"  {matching_time:>13.3f}  {len(matching):>8}")
    print("contrast this with the chromatic number and Hamiltonian cycle problems")
    print()


def applications() -> None:
    students = ["Anna", "Bo", "Cecilia", "David"]
    projects = ["RSA", "sieve", "graphs", "coding"]
    preferences = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 2), (3, 2), (3, 3)]
    edges = [(student, len(students) + project) for student, project in preferences]
    graph = graph_util.build_graph(len(students) + len(projects), edges)
    left = list(range(len(students)))
    right = list(range(len(students), len(students) + len(projects)))
    matching = hopcroft_karp(graph, left, right)
    print("--- 7 application: assigning students to projects ---")
    for student in left:
        if student in matching:
            project = matching[student] - len(students)
            print(f"  {students[student]:>8} -> {projects[project]}")
        else:
            print(f"  {students[student]:>8} -> unassigned")
    print(f"assigned {len(matching)} of {len(students)}, "
          f"valid matching?: {is_matching(graph, matching)}")
    print(f"Hall's condition holds?: {hall_condition_holds(graph, left)}")
    print()


worked_example()
odd_cycle_example()
families_table()
two_colouring_is_the_chromatic_number()
halls_condition()
hall_violation()
applications()
cost_growth()
