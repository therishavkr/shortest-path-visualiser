from __future__ import annotations

from collections.abc import Callable

from app.algorithms import astar, bfs, dfs, dijkstra, greedy
from app.algorithms.base import AlgorithmName, SearchResult
from app.algorithms.heuristics import HEURISTICS, HeuristicFn, HeuristicName
from app.grid.types import Grid

ALGORITHMS: dict[AlgorithmName, Callable[[Grid, HeuristicFn | None], SearchResult]] = {
    AlgorithmName.BFS: bfs.search,
    AlgorithmName.DFS: dfs.search,
    AlgorithmName.DIJKSTRA: dijkstra.search,
    AlgorithmName.GREEDY: greedy.search,
    AlgorithmName.ASTAR: astar.search,
}

HEURISTIC_REQUIRED = {AlgorithmName.GREEDY, AlgorithmName.ASTAR}


def run_search(
    grid: Grid,
    algorithm: AlgorithmName,
    heuristic: HeuristicName | None = None,
) -> SearchResult:
    """Validate the (algorithm, heuristic) combination and dispatch to the
    matching search implementation. Raises ValueError on an invalid
    combination - routers translate this into a 400 response."""
    requires_heuristic = algorithm in HEURISTIC_REQUIRED
    if requires_heuristic and heuristic is None:
        raise ValueError(f"{algorithm.value} requires a heuristic")
    if not requires_heuristic and heuristic is not None:
        raise ValueError(f"{algorithm.value} does not accept a heuristic")

    heuristic_fn = HEURISTICS[heuristic] if heuristic is not None else None
    result = ALGORITHMS[algorithm](grid, heuristic_fn)
    return result.model_copy(update={"heuristic": heuristic})
