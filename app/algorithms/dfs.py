from __future__ import annotations

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
    """Depth-first search (explicit stack). Finds *a* path, not necessarily
    the shortest or cheapest one - useful as a contrast to the informed
    searches."""
    start_time = time.perf_counter()

    discovered: set[Cell] = {grid.start}
    came_from: dict[Cell, Cell] = {}
    stack: list[Cell] = [grid.start]
    frames: list[FrameDelta] = []
    nodes_expanded = 0
    found = False

    while stack:
        current = stack.pop()
        nodes_expanded += 1
        frame = FrameDelta(popped=current)

        if current == grid.goal:
            frames.append(frame)
            found = True
            break

        added: list[Cell] = []
        # Push in reverse so the first-listed neighbor (N) ends up on top
        # of the stack and is explored first, matching the fixed N,S,E,W
        # priority order used by the other algorithms.
        for neighbor, _cost in reversed(list(grid.neighbors(current))):
            if neighbor not in discovered:
                discovered.add(neighbor)
                came_from[neighbor] = current
                stack.append(neighbor)
                added.append(neighbor)
        frame.frontier_added = added
        frames.append(frame)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(came_from, grid.start, grid.goal) if found else []

    return SearchResult(
        algorithm=AlgorithmName.DFS,
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
