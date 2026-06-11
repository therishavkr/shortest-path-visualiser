from __future__ import annotations

import time
from collections import deque

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
    """Breadth-first search. Ignores cell weights - finds the path with the
    fewest steps, not necessarily the lowest cost."""
    start_time = time.perf_counter()

    discovered: set[Cell] = {grid.start}
    came_from: dict[Cell, Cell] = {}
    queue: deque[Cell] = deque([grid.start])
    frames: list[FrameDelta] = []
    nodes_expanded = 0
    found = False

    while queue:
        current = queue.popleft()
        nodes_expanded += 1
        frame = FrameDelta(popped=current)

        if current == grid.goal:
            frames.append(frame)
            found = True
            break

        added: list[Cell] = []
        for neighbor, _cost in grid.neighbors(current):
            if neighbor not in discovered:
                discovered.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)
                added.append(neighbor)
        frame.frontier_added = added
        frames.append(frame)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(came_from, grid.start, grid.goal) if found else []

    return SearchResult(
        algorithm=AlgorithmName.BFS,
        heuristic=None,
        frames=frames,
        path=path,
        stats=SearchStats(
            nodes_expanded=nodes_expanded,
            nodes_visited=len(discovered),
            path_length=len(path),
            path_cost=path_cost(grid, path),
            execution_time_ms=elapsed_ms,
            found_path=found,
        ),
    )
