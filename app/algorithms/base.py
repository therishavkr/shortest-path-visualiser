from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.algorithms.heuristics import HeuristicName
from app.grid.types import Cell, DIAGONAL_COST, Grid, ORTHOGONAL_COST


class AlgorithmName(str, Enum):
    BFS = "bfs"
    DFS = "dfs"
    DIJKSTRA = "dijkstra"
    GREEDY = "greedy"
    ASTAR = "astar"


class FrameDelta(BaseModel):
    """One step of a search trace.

    `popped` is the cell expanded this step (frontend: move it from the
    frontier set into the visited set). `frontier_added` are newly
    discovered cells to add to the frontier. `updated` are cells already in
    the frontier whose tentative cost improved (Dijkstra/A* decrease-key) -
    purely a visual cue, frontier set membership doesn't change for these.
    """

    popped: Cell
    frontier_added: list[Cell] = []
    updated: list[Cell] = []


class SearchStats(BaseModel):
    nodes_expanded: int
    nodes_visited: int
    path_length: int
    path_cost: float | None
    execution_time_ms: float
    found_path: bool


class SearchResult(BaseModel):
    algorithm: AlgorithmName
    heuristic: HeuristicName | None
    frames: list[FrameDelta]
    path: list[Cell]
    stats: SearchStats


def reconstruct_path(came_from: dict[Cell, Cell], start: Cell, goal: Cell) -> list[Cell]:
    if goal != start and goal not in came_from:
        return []
    path = [goal]
    current = goal
    while current != start:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def path_cost(grid: Grid, path: list[Cell]) -> float | None:
    if not path:
        return None
    cost = 0.0
    for a, b in zip(path, path[1:]):
        is_diagonal = a[0] != b[0] and a[1] != b[1]
        step_base = DIAGONAL_COST if is_diagonal else ORTHOGONAL_COST
        cost += step_base * grid.cell_weight(b)
    return cost
