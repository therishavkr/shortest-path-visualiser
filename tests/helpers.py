"""Shared grid fixtures and helpers for algorithm tests (not collected by pytest)."""

from app.algorithms import astar, bfs, dfs, dijkstra, greedy
from app.algorithms.heuristics import HEURISTICS, HeuristicName
from app.grid.types import Grid, GridSpec

ALL_ALGORITHMS = [bfs, dfs, dijkstra, greedy, astar]


def assert_valid_path(grid: Grid, path: list[tuple[int, int]]) -> None:
    assert path[0] == grid.start
    assert path[-1] == grid.goal
    assert len(set(path)) == len(path)  # no repeated cells / cycles
    for a, b in zip(path, path[1:]):
        neighbor_cells = {c for c, _ in grid.neighbors(a)}
        assert b in neighbor_cells, f"{b} is not a valid neighbor of {a}"


def run(module, grid: Grid, heuristic_name: HeuristicName | None = None):
    heuristic = HEURISTICS[heuristic_name] if heuristic_name else None
    return module.search(grid, heuristic)


def heuristic_for(module) -> HeuristicName | None:
    return HeuristicName.MANHATTAN if module in (astar, greedy) else None


def corridor_grid() -> Grid:
    # 5x5 grid; a wall spans column 2 for rows 0-3, leaving a single gap at
    # (4, 2). The only way across is via that gap.
    spec = GridSpec(
        rows=5, cols=5, start=(0, 0), goal=(0, 4),
        walls=[(0, 2), (1, 2), (2, 2), (3, 2)],
    )
    return Grid.from_spec(spec)


def terrain_grid(allow_diagonal: bool = False) -> Grid:
    # 3x3 grid; the direct route from (0,0) to (0,2) crosses an expensive
    # terrain cell at (0,1), while a detour through row 1 stays cheap.
    spec = GridSpec(
        rows=3, cols=3, start=(0, 0), goal=(0, 2),
        terrain=[(0, 1)], allow_diagonal=allow_diagonal,
    )
    return Grid.from_spec(spec)


def unreachable_goal_grid() -> Grid:
    # 5x5 grid; (4,4) is a corner whose only two neighbors are walls.
    spec = GridSpec(rows=5, cols=5, start=(0, 0), goal=(4, 4), walls=[(3, 4), (4, 3)])
    return Grid.from_spec(spec)
