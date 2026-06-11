from __future__ import annotations

import heapq
import itertools
import time

from app.algorithms.base import (
    AlgorithmName,
    FrameDelta,
    SearchResult,
    SearchStats,
    path_cost,
    reconstruct_path,
)
from app.algorithms.heuristics import HeuristicFn
from app.grid.types import Cell, Grid


def search(grid: Grid, heuristic: HeuristicFn | None = None) -> SearchResult:
    """A* search: f(n) = g(n) + h(n). With an admissible heuristic this finds
    the same optimal cost as Dijkstra while expanding fewer nodes."""
    if heuristic is None:
        raise ValueError("astar requires a heuristic")

    start_time = time.perf_counter()

    counter = itertools.count()
    g_score: dict[Cell, float] = {grid.start: 0.0}
    came_from: dict[Cell, Cell] = {}
    expanded: set[Cell] = set()
    h_start = heuristic(grid.start, grid.goal)
    heap: list[tuple[float, int, Cell]] = [(h_start, next(counter), grid.start)]
    frames: list[FrameDelta] = []
    found = False

    while heap:
        _f, _, current = heapq.heappop(heap)
        if current in expanded:
            continue  # stale entry from a decrease-key
        expanded.add(current)
        frame = FrameDelta(popped=current)

        if current == grid.goal:
            frames.append(frame)
            found = True
            break

        added: list[Cell] = []
        updated: list[Cell] = []
        for neighbor, step_cost in grid.neighbors(current):
            if neighbor in expanded:
                continue
            tentative_g = g_score[current] + step_cost
            if tentative_g < g_score.get(neighbor, float("inf")):
                first_time = neighbor not in g_score
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + heuristic(neighbor, grid.goal)
                heapq.heappush(heap, (f_score, next(counter), neighbor))
                (added if first_time else updated).append(neighbor)

        frame.frontier_added = added
        frame.updated = updated
        frames.append(frame)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(came_from, grid.start, grid.goal) if found else []

    return SearchResult(
        algorithm=AlgorithmName.ASTAR,
        heuristic=None,
        frames=frames,
        path=path,
        stats=SearchStats(
            nodes_expanded=len(expanded),
            nodes_visited=len(g_score),
            path_length=len(path),
            path_cost=path_cost(grid, path),
            execution_time_ms=elapsed_ms,
            found_path=found,
        ),
    )
