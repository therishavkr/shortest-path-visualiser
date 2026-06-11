import math

import pytest

from app.algorithms import dijkstra
from app.algorithms.heuristics import HEURISTICS, HeuristicName, chebyshev, euclidean, manhattan
from app.grid.types import Grid, GridSpec


def test_manhattan_known_value():
    assert manhattan((0, 0), (3, 4)) == 7


def test_euclidean_known_value():
    assert euclidean((0, 0), (3, 4)) == 5.0


def test_chebyshev_known_value():
    expected = 4 + (math.sqrt(2) - 1) * 3
    assert math.isclose(chebyshev((0, 0), (3, 4)), expected)


def test_chebyshev_equals_euclidean_on_pure_diagonal():
    # When dr == dc, the octile distance collapses to straight-line distance.
    assert math.isclose(chebyshev((0, 0), (3, 3)), euclidean((0, 0), (3, 3)))


def test_heuristics_registry_matches_functions():
    assert HEURISTICS[HeuristicName.MANHATTAN] is manhattan
    assert HEURISTICS[HeuristicName.EUCLIDEAN] is euclidean
    assert HEURISTICS[HeuristicName.CHEBYSHEV] is chebyshev


# (heuristic, allow_diagonal) combinations that are mathematically
# admissible (never overestimate the true cost-to-goal):
#   - Manhattan assumes orthogonal-only movement, so it overestimates once
#     diagonal shortcuts (cost sqrt(2) < 2) are available - admissible only
#     when allow_diagonal=False.
#   - Euclidean (straight-line) and Chebyshev/octile (the exact no-obstacle
#     cost on an 8-connected grid) are lower bounds in both modes.
ADMISSIBLE_COMBOS = [
    (HeuristicName.MANHATTAN, False),
    (HeuristicName.EUCLIDEAN, False),
    (HeuristicName.EUCLIDEAN, True),
    (HeuristicName.CHEBYSHEV, False),
    (HeuristicName.CHEBYSHEV, True),
]


def _true_costs_to_goal(rows, cols, goal, walls, terrain, allow_diagonal):
    """Run Dijkstra from `goal` to get the optimal cost from every reachable
    cell to `goal` (edge weights are symmetric, so cost(cell->goal) ==
    cost(goal->cell))."""
    costs: dict[tuple[int, int], float] = {}
    for r in range(rows):
        for c in range(cols):
            cell = (r, c)
            if cell in walls or cell == goal:
                continue
            spec = GridSpec(
                rows=rows, cols=cols, start=goal, goal=cell,
                walls=list(walls), terrain=terrain, allow_diagonal=allow_diagonal,
            )
            grid = Grid.from_spec(spec)
            result = dijkstra.search(grid)
            if result.stats.found_path:
                costs[cell] = result.stats.path_cost
    return costs


GRID_ROWS, GRID_COLS = 6, 6
GRID_GOAL = (5, 5)
GRID_WALLS = {(2, 1), (2, 2), (2, 3)}
GRID_TERRAIN = [(3, 3), (3, 4), (4, 3)]


@pytest.mark.parametrize("heuristic_name,allow_diagonal", ADMISSIBLE_COMBOS)
def test_heuristics_are_admissible(heuristic_name, allow_diagonal):
    """Every (heuristic, movement-mode) combo above must never overestimate
    the true cost-to-goal, including when terrain makes the true cost higher
    than the untextured-grid lower bound."""
    heuristic = HEURISTICS[heuristic_name]
    true_costs = _true_costs_to_goal(
        GRID_ROWS, GRID_COLS, GRID_GOAL, GRID_WALLS, GRID_TERRAIN, allow_diagonal
    )

    for cell, true_cost in true_costs.items():
        assert heuristic(cell, GRID_GOAL) <= true_cost + 1e-9


def test_manhattan_overestimates_with_diagonal_movement():
    """Documents *why* Manhattan is excluded above for allow_diagonal=True:
    diagonal shortcuts (cost sqrt(2) < 2) mean the true cost can be lower
    than the orthogonal-only Manhattan distance, making it inadmissible. A*
    can therefore return a suboptimal path for this combination - a useful
    demonstration of why heuristic admissibility matters."""
    true_costs = _true_costs_to_goal(
        GRID_ROWS, GRID_COLS, GRID_GOAL, GRID_WALLS, GRID_TERRAIN, allow_diagonal=True
    )

    overestimates = [
        cell for cell, true_cost in true_costs.items()
        if manhattan(cell, GRID_GOAL) > true_cost + 1e-9
    ]
    assert overestimates, "expected at least one cell where Manhattan overestimates"
