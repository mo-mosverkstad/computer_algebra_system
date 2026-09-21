import graph_util
import random
import time

from typing import Dict, List, Optional, Tuple

Graph = Dict[int, set]


def greedy_colouring(graph: Graph, order: List[int]) -> Dict[int, int]:
    colouring: Dict[int, int] = {}
    for vertex in order:
        used = {colouring[other] for other in graph[vertex] if other in colouring}
        colour = 0
        while colour in used:
            colour += 1
        colouring[vertex] = colour
    return colouring


def welsh_powell(graph: Graph) -> Dict[int, int]:
    order = sorted(graph, key=lambda vertex: (-len(graph[vertex]), vertex))
    return greedy_colouring(graph, order)


def is_proper(graph: Graph, colouring: Dict[int, int]) -> bool:
    return all(colouring[vertex] != colouring[other]
               for vertex in graph for other in graph[vertex])


def colours_used(colouring: Dict[int, int]) -> int:
    return len(set(colouring.values()))


def colourable_with(graph: Graph, colours: int) -> Optional[Dict[int, int]]:
    vertices = sorted(graph, key=lambda vertex: (-len(graph[vertex]), vertex))
    colouring: Dict[int, int] = {}

    def extend(index: int, highest: int) -> bool:
        if index == len(vertices):
            return True
        vertex = vertices[index]
        forbidden = {colouring[other] for other in graph[vertex] if other in colouring}
        for colour in range(min(highest + 1, colours - 1) + 1):
            if colour in forbidden:
                continue
            colouring[vertex] = colour
            if extend(index + 1, max(highest, colour)):
                return True
            del colouring[vertex]
        return False

    return dict(colouring) if extend(0, -1) else None


def chromatic_number(graph: Graph) -> Tuple[int, Dict[int, int]]:
    upper = colours_used(welsh_powell(graph))
    best = welsh_powell(graph)
    for colours in range(1, upper):
        found = colourable_with(graph, colours)
        if found is not None:
            return colours, found
    return upper, best


def brooks_bounds(graph: Graph) -> Tuple[int, int, int]:
    clique = graph_util.greedy_clique_bound(graph)
    maximum_degree = max(len(graph[vertex]) for vertex in graph) if graph else 0
    return clique, maximum_degree + 1, colours_used(welsh_powell(graph))


def worked_example() -> None:
    graph = graph_util.build_graph(6, [(0, 1), (0, 2), (1, 2), (1, 3), (2, 4),
                                       (3, 4), (3, 5), (4, 5)])
    print("--- 1 worked example, 6 vertices ---")
    print(f"edges: {graph_util.render_edges(graph, 20)}")
    print(f"degrees: {graph_util.degrees(graph)}")

    naive = greedy_colouring(graph, sorted(graph))
    print(f"greedy in vertex order 0..5: {naive}, {colours_used(naive)} colours")
    smart = welsh_powell(graph)
    print(f"greedy in descending degree: {smart}, {colours_used(smart)} colours")

    for colours in (2, 3):
        found = colourable_with(graph, colours)
        print(f"{colours}-colourable?: {'yes ' + str(found) if found else 'no'}")

    number, colouring = chromatic_number(graph)
    print(f"chromatic number: {number}, proper?: {is_proper(graph, colouring)}")
    print("triangle 0-1-2 forces at least 3 colours")
    print()


def greedy_order_matters() -> None:
    graph = graph_util.complete_bipartite(3, 3)
    print("--- 1 greedy order matters, K(3,3) needs only 2 colours ---")
    bad_order = [0, 3, 1, 4, 2, 5]
    bad = greedy_colouring(graph, bad_order)
    good = welsh_powell(graph)
    print(f"order {bad_order}: {colours_used(bad)} colours {bad}")
    print(f"descending degree: {colours_used(good)} colours {good}")
    number, _ = chromatic_number(graph)
    print(f"true chromatic number: {number}")
    print()


def known_families() -> None:
    print("--- 1 chromatic numbers of known families ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'clique':>6}  {'chi':>4}  {'greedy':>6}"
          f"  {'max degree + 1':>14}")
    families: List[Tuple[str, Graph, str]] = [
        ("K5", graph_util.complete_graph(5), "5"),
        ("C5 odd cycle", graph_util.cycle_graph(5), "3"),
        ("C6 even cycle", graph_util.cycle_graph(6), "2"),
        ("path P6", graph_util.path_graph(6), "2"),
        ("K(3,3) bipartite", graph_util.complete_bipartite(3, 3), "2"),
        ("Petersen", graph_util.petersen_graph(), "3"),
        ("wheel W5 odd rim", graph_util.wheel_graph(5), "4"),
        ("wheel W6 even rim", graph_util.wheel_graph(6), "3"),
        ("grid 3x4", graph_util.grid_graph(3, 4), "2"),
        ("cube Q3", graph_util.hypercube_graph(3), "2"),
    ]
    for name, graph, expected in families:
        clique, degree_bound, greedy = brooks_bounds(graph)
        number, colouring = chromatic_number(graph)
        flag = "" if str(number) == expected else f"  <- expected {expected}"
        print(f"{name:>18}  {graph_util.order(graph):>3}  {graph_util.size(graph):>4}"
              f"  {clique:>6}  {number:>4}  {greedy:>6}  {degree_bound:>14}{flag}")
    print()


def bounds_table() -> None:
    print("--- 1 clique number <= chi <= max degree + 1, with Brooks' exceptions ---")
    print(f"{'graph':>18}  {'clique':>6}  {'chi':>4}  {'max degree + 1':>14}  {'tight':>12}")
    families: List[Tuple[str, Graph]] = [
        ("K4", graph_util.complete_graph(4)),
        ("C5", graph_util.cycle_graph(5)),
        ("C7", graph_util.cycle_graph(7)),
        ("Petersen", graph_util.petersen_graph()),
        ("K(2,3)", graph_util.complete_bipartite(2, 3)),
    ]
    for name, graph in families:
        clique, degree_bound, _ = brooks_bounds(graph)
        number, _ = chromatic_number(graph)
        if number == degree_bound:
            tight = "upper tight"
        elif number == clique:
            tight = "lower tight"
        else:
            tight = "strictly between"
        print(f"{name:>18}  {clique:>6}  {number:>4}  {degree_bound:>14}  {tight:>12}")
    print("Brooks: chi = max degree + 1 only for complete graphs and odd cycles")
    print()


def map_colouring() -> None:
    names = ["Skane", "Blekinge", "Smaland", "Halland", "Vastergotland", "Ostergotland"]
    adjacency = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (2, 4), (2, 5), (3, 4), (4, 5)]
    graph = graph_util.build_graph(len(names), adjacency)
    number, colouring = chromatic_number(graph)
    print("--- 1 the original application: colouring a map ---")
    print(f"regions: {len(names)}, shared borders: {graph_util.size(graph)}")
    for vertex in sorted(graph):
        print(f"  {names[vertex]:>14}  colour {colouring[vertex]}")
    print(f"colours needed: {number}, four colour theorem guarantees at most 4")
    print()


def cost_growth() -> None:
    print("--- 1 exact colouring is exponential, greedy is linear ---")
    print(f"{'graph':>18}  {'n':>3}  {'m':>4}  {'chi':>4}  {'exact (ms)':>10}  {'greedy (ms)':>11}")
    random.seed(20260920)
    for order_value in (8, 12, 16, 20, 24, 28, 32, 36, 40, 44):
        edges = [(first, second)
                 for first in range(order_value)
                 for second in range(first + 1, order_value)
                 if random.random() < 0.5]
        graph = graph_util.build_graph(order_value, edges)
        start = time.perf_counter()
        number, _ = chromatic_number(graph)
        exact_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        welsh_powell(graph)
        greedy_time = (time.perf_counter() - start) * 1000
        print(f"{'random p=0.5':>18}  {order_value:>3}  {graph_util.size(graph):>4}"
              f"  {number:>4}  {exact_time:>10.3f}  {greedy_time:>11.3f}")
    for order_value in (5, 6, 7, 8, 9, 10):
        graph = graph_util.complete_graph(order_value)
        start = time.perf_counter()
        number, _ = chromatic_number(graph)
        exact_time = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        welsh_powell(graph)
        greedy_time = (time.perf_counter() - start) * 1000
        print(f"{'complete K' + str(order_value):>18}  {order_value:>3}"
              f"  {graph_util.size(graph):>4}  {number:>4}  {exact_time:>10.3f}"
              f"  {greedy_time:>11.3f}")
    print()


worked_example()
greedy_order_matters()
known_families()
bounds_table()
map_colouring()
cost_growth()
