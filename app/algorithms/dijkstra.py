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
    """Dijkstra's algorithm. Cost-aware uniform-cost search - always finds
    the lowest-cost path, accounting for weighted terrain."""
    start_time = time.perf_counter()

    counter = itertools.count()
    dist: dict[Cell, float] = {grid.start: 0.0}
    came_from: dict[Cell, Cell] = {}
    expanded: set[Cell] = set()
    heap: list[tuple[float, int, Cell]] = [(0.0, next(counter), grid.start)]
    frames: list[FrameDelta] = []
    found = False

    while heap:
        cost, _, current = heapq.heappop(heap)
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
            new_dist = cost + step_cost
            if new_dist < dist.get(neighbor, float("inf")):
                first_time = neighbor not in dist
                dist[neighbor] = new_dist
                came_from[neighbor] = current
                heapq.heappush(heap, (new_dist, next(counter), neighbor))
                (added if first_time else updated).append(neighbor)

        frame.frontier_added = added
        frame.updated = updated
        frames.append(frame)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(came_from, grid.start, grid.goal) if found else []

    return SearchResult(
        algorithm=AlgorithmName.DIJKSTRA,
        heuristic=None,
        frames=frames,
        path=path,
        stats=SearchStats(
            nodes_expanded=len(expanded),
            nodes_visited=len(dist),
            path_length=len(path),
            path_cost=path_cost(grid, path),
            execution_time_ms=elapsed_ms,
            found_path=found,
        ),
    )
