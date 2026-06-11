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
    """Greedy best-first search: always expands the cell that *looks*
    closest to the goal (by heuristic alone), ignoring the cost incurred so
    far. Fast, but can be led astray by terrain - may return a path that is
    more expensive than Dijkstra's/A*'s optimum."""
    if heuristic is None:
        raise ValueError("greedy requires a heuristic")

    start_time = time.perf_counter()

    counter = itertools.count()
    came_from: dict[Cell, Cell] = {}
    discovered: set[Cell] = {grid.start}
    expanded: set[Cell] = set()
    heap: list[tuple[float, int, Cell]] = [
        (heuristic(grid.start, grid.goal), next(counter), grid.start)
    ]
    frames: list[FrameDelta] = []
    found = False

    while heap:
        _h, _, current = heapq.heappop(heap)
        if current in expanded:
            continue
        expanded.add(current)
        frame = FrameDelta(popped=current)

        if current == grid.goal:
            frames.append(frame)
            found = True
            break

        added: list[Cell] = []
        for neighbor, _step_cost in grid.neighbors(current):
            if neighbor in discovered:
                continue
            discovered.add(neighbor)
            came_from[neighbor] = current
            heapq.heappush(heap, (heuristic(neighbor, grid.goal), next(counter), neighbor))
            added.append(neighbor)

        frame.frontier_added = added
        frames.append(frame)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(came_from, grid.start, grid.goal) if found else []

    return SearchResult(
        algorithm=AlgorithmName.GREEDY,
        heuristic=None,
        frames=frames,
        path=path,
        stats=SearchStats(
            nodes_expanded=len(expanded),
            nodes_visited=len(discovered),
            path_length=len(path),
            path_cost=path_cost(grid, path),
            execution_time_ms=elapsed_ms,
            found_path=found,
        ),
    )
