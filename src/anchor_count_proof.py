"""Exact PAM-3 count by cube cycles, checked against all 9P8 injections.

This module imports neither census implementation. The count concerns exactly
the displayed words and pairwise noncontraction, not an unpublished program.
"""
from __future__ import annotations

from itertools import permutations
from math import factorial

WORDS = (0, 1, 3, 4, 5, 7, 12, 13, 15)
CYCLE = (0, 1, 3, 7, 15, 13, 12, 4)
FIRST_EDGE_CYCLES = (
    (0, 1, 3, 2, 6, 7, 5, 4),
    (0, 1, 3, 7, 5, 4, 6, 2),
    (0, 1, 5, 4, 6, 7, 3, 2),
    (0, 1, 5, 7, 3, 2, 6, 4),
)

def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def distance(a: int, b: int) -> int:
    return sum(x != y for x, y in zip(f"{a:04b}", f"{b:04b}"))

def is_cube_cycle(order: tuple[int, ...]) -> bool:
    return len(order) == len(set(order)) == 8 and all(
        distance(order[i], order[(i + 1) % 8]) == 1 for i in range(8)
    )

def verify_count(spec: dict, delivered: set[tuple[int, ...]]) -> dict:
    need(spec["message_bits"] == 3 and spec["channel_bits"] == 4, "different dimensions")
    need(spec["messages"] == [f"{x:03b}" for x in range(8)], "different message order")
    need(tuple(int(x, 2) for x in spec["allowed_codewords"]) == WORDS, "different displayed words")
    need(spec["source_text_reported_pairwise_count"] == 72, "source quotation changed")

    # Any codeword-distance-one edge must become a cube edge under f^{-1}.
    # A retained center has degree four if a corner is omitted. Omitting an
    # edge midpoint instead leaves a connected graph with bipartition 5:3.
    # Neither graph embeds bijectively into the degree-three, balanced cube.
    cases = []
    for omitted in WORDS:
        vertices = set(WORDS) - {omitted}
        graph = {x: {y for y in vertices if distance(x, y) == 1} for x in vertices}
        reached = {min(vertices)}
        todo = list(reached)
        while todo:
            for y in graph[todo.pop()]:
                if y not in reached:
                    reached.add(y)
                    todo.append(y)
        sizes = sorted(sum(x.bit_count() % 2 == parity for x in vertices) for parity in (0, 1))
        max_degree = max(map(len, graph.values()))
        if omitted == 5:
            need(all(len(neighbors) == 2 for neighbors in graph.values()), "center omission is not C8")
            reason = "C8"
        elif max_degree == 4:
            reason = "retained center degree four exceeds cube degree three"
        else:
            need(len(reached) == 8 and sizes == [3, 5], "midpoint obstruction changed")
            reason = "connected 5:3 bipartition cannot biject to cube 4:4"
        cases.append({"omitted": f"{omitted:04b}", "max_degree": max_degree, "bipartition_sizes": sizes, "reason": reason})

    first_edge = {tuple((0, 1, *tail)) for tail in permutations(range(2, 8))
                  if is_cube_cycle(tuple((0, 1, *tail)))}
    need(first_edge == set(FIRST_EDGE_CYCLES), "four first-edge completions differ")
    walks = {tuple((start, *tail)) for start in range(8)
             for tail in permutations(x for x in range(8) if x != start)
             if is_cube_cycle(tuple((start, *tail)))}
    need(len(walks) == 8 * 3 * len(first_edge) == 96, "cube-cycle count differs")
    by_cycles = set()
    for walk in walks:
        mapping = [0] * 8
        for code, message in zip(CYCLE, walk):
            mapping[message] = code
        by_cycles.add(tuple(mapping))

    # Direct unpruned census of every injection. Unlike the producers this
    # loop visits all 362,880 candidates and never prunes a partial mapping.
    pairs = [(i, j, distance(i, j)) for i in range(8) for j in range(i)]
    brute = set()
    candidates = 0
    for mapping in permutations(WORDS, 8):
        candidates += 1
        if all(distance(mapping[i], mapping[j]) >= target for i, j, target in pairs):
            brute.add(mapping)
    need(candidates == factorial(9), "unpruned candidate coverage differs")
    need(brute == by_cycles == delivered and len(brute) == 96, "three mapping sets differ")

    # The 48 message-cube isometries act freely on injective encoders. Thus
    # any complete set satisfying these same constraints has size 0 mod 48.
    def transform(x: int, permutation: tuple[int, ...], shift: int) -> int:
        return sum(((x >> old) & 1) << new for new, old in enumerate(permutation)) ^ shift
    orbits = []
    remaining = set(brute)
    while remaining:
        representative = min(remaining)
        orbit = {tuple(representative[transform(x, perm, shift)] for x in range(8))
                 for perm in permutations(range(3)) for shift in range(8)}
        need(len(orbit) == 48 and orbit <= remaining, "cube isometry orbit differs")
        orbits.append(len(orbit))
        remaining -= orbit
    need(orbits == [48, 48] and 72 % 48 != 0, "orbit accounting changed")
    return {
        "accepted": True,
        "exact_count": 96,
        "source_reported_count": 72,
        "difference": 24,
        "resolution": "reported count is inconsistent with the displayed words and pairwise inequality",
        "omission_cases": cases,
        "codeword_cycle": [f"{x:04b}" for x in CYCLE],
        "cube_cycle_first_edge_completions": [[f"{x:03b}" for x in walk] for walk in FIRST_EDGE_CYCLES],
        "cube_cycle_count_factors": [8, 3, 4],
        "unpruned_injections_checked": candidates,
        "input_isometry_orbit_sizes": orbits,
        "all_mapping_sets_equal": True,
        "scope": "Exact mathematical count for the printed conditions; no assertion about the unavailable source implementation or author intent.",
    }
