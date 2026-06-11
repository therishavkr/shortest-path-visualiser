from app.grid.generator import generate_grid
from app.grid.types import Grid


def test_generate_grid_is_solvable_by_default():
    spec = generate_grid(rows=10, cols=10, seed=42)
    grid = Grid.from_spec(spec)

    assert spec.start == (0, 0)
    assert spec.goal == (9, 9)
    from app.algorithms import bfs

    assert bfs.search(grid).stats.found_path


def test_generate_grid_is_deterministic_with_seed():
    first = generate_grid(rows=12, cols=15, seed=7)
    second = generate_grid(rows=12, cols=15, seed=7)

    assert first.model_dump() == second.model_dump()


def test_generate_grid_different_seeds_differ():
    first = generate_grid(rows=12, cols=15, seed=1)
    second = generate_grid(rows=12, cols=15, seed=2)

    assert first.model_dump() != second.model_dump()


def test_zero_density_yields_empty_grid():
    spec = generate_grid(rows=8, cols=8, obstacle_density=0.0, terrain_density=0.0, seed=3)

    assert spec.walls == []
    assert spec.terrain == []


def test_walls_and_terrain_never_overlap_and_spare_start_goal():
    spec = generate_grid(rows=15, cols=15, obstacle_density=0.3, terrain_density=0.3, seed=99)

    walls = set(spec.walls)
    terrain = set(spec.terrain)

    assert walls.isdisjoint(terrain)
    assert spec.start not in walls
    assert spec.start not in terrain
    assert spec.goal not in walls
    assert spec.goal not in terrain


def test_unsolvable_grid_returned_after_exhausting_attempts():
    # obstacle_density=1.0 walls every cell except start/goal, isolating
    # both - every retry produces the same fully-walled grid.
    spec = generate_grid(rows=5, cols=5, obstacle_density=1.0, terrain_density=0.0, seed=1)
    grid = Grid.from_spec(spec)

    from app.algorithms import bfs

    assert bfs.search(grid).stats.found_path is False


def test_allow_diagonal_is_passed_through():
    spec = generate_grid(rows=6, cols=6, allow_diagonal=True, seed=5)
    assert spec.allow_diagonal is True
