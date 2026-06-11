import math

import pytest
from pydantic import ValidationError

from app.grid.types import DIAGONAL_COST, Grid, GridSpec, TERRAIN_COST


def make_spec(**overrides):
    base = dict(rows=5, cols=5, start=(0, 0), goal=(4, 4), walls=[], terrain=[], allow_diagonal=False)
    base.update(overrides)
    return GridSpec(**base)


def test_valid_spec():
    spec = make_spec()
    grid = Grid.from_spec(spec)
    assert grid.rows == 5
    assert grid.cols == 5
    assert grid.start == (0, 0)
    assert grid.goal == (4, 4)


@pytest.mark.parametrize(
    "overrides",
    [
        {"start": (5, 0)},  # out of bounds
        {"goal": (0, 5)},  # out of bounds
        {"start": (4, 4), "goal": (4, 4)},  # start == goal
        {"walls": [(0, 0)]},  # start in wall
        {"walls": [(4, 4)]},  # goal in wall
        {"walls": [(1, 1)], "terrain": [(1, 1)]},  # wall and terrain overlap
        {"walls": [(10, 10)]},  # wall out of bounds
    ],
)
def test_invalid_spec_raises(overrides):
    with pytest.raises(ValidationError):
        make_spec(**overrides)


def test_in_bounds_and_is_walkable():
    spec = make_spec(walls=[(2, 2)])
    grid = Grid.from_spec(spec)

    assert grid.in_bounds((0, 0))
    assert grid.in_bounds((4, 4))
    assert not grid.in_bounds((-1, 0))
    assert not grid.in_bounds((5, 0))
    assert not grid.in_bounds((0, 5))

    assert grid.is_walkable((0, 0))
    assert not grid.is_walkable((2, 2))  # wall
    assert not grid.is_walkable((5, 5))  # out of bounds


def test_cell_weight():
    spec = make_spec(terrain=[(1, 1)])
    grid = Grid.from_spec(spec)

    assert grid.cell_weight((0, 0)) == 1.0
    assert grid.cell_weight((1, 1)) == TERRAIN_COST


def test_neighbors_orthogonal_order_interior_cell():
    spec = make_spec()
    grid = Grid.from_spec(spec)

    neighbors = list(grid.neighbors((2, 2)))
    cells = [c for c, _ in neighbors]

    # Fixed N, S, E, W order
    assert cells == [(1, 2), (3, 2), (2, 3), (2, 1)]
    assert all(cost == 1.0 for _, cost in neighbors)


def test_neighbors_corner_cell_no_diagonal():
    spec = make_spec()
    grid = Grid.from_spec(spec)

    neighbors = list(grid.neighbors((0, 0)))
    cells = [c for c, _ in neighbors]

    # Only S and E are in bounds for the top-left corner
    assert cells == [(1, 0), (0, 1)]


def test_neighbors_terrain_weight_applied_to_destination():
    spec = make_spec(terrain=[(1, 2)])
    grid = Grid.from_spec(spec)

    neighbors = dict(grid.neighbors((2, 2)))
    assert neighbors[(1, 2)] == TERRAIN_COST  # moving onto terrain costs more
    assert neighbors[(3, 2)] == 1.0


def test_neighbors_diagonal_enabled():
    spec = make_spec(allow_diagonal=True)
    grid = Grid.from_spec(spec)

    neighbors = list(grid.neighbors((2, 2)))
    cells = [c for c, _ in neighbors]

    # N, S, E, W, then NE, SE, SW, NW
    assert cells == [
        (1, 2), (3, 2), (2, 3), (2, 1),
        (1, 3), (3, 3), (3, 1), (1, 1),
    ]
    diagonal_costs = [cost for cell, cost in neighbors if cell in {(1, 3), (3, 3), (3, 1), (1, 1)}]
    assert all(math.isclose(cost, DIAGONAL_COST) for cost in diagonal_costs)


def test_neighbors_diagonal_corner_cutting_blocked():
    # Wall directly above (2,2) blocks the NE/NW diagonal "corners".
    spec = make_spec(walls=[(1, 2)], allow_diagonal=True)
    grid = Grid.from_spec(spec)

    cells = {c for c, _ in grid.neighbors((2, 2))}

    assert (1, 3) not in cells  # NE corner-cut through (1,2)
    assert (1, 1) not in cells  # NW corner-cut through (1,2)
    assert (3, 3) in cells  # SE unaffected
    assert (3, 1) in cells  # SW unaffected
