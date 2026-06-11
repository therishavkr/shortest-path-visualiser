import math

import pytest

from app.algorithms import astar, bfs, dfs, dijkstra, greedy, registry
from app.algorithms.base import AlgorithmName
from app.algorithms.heuristics import HeuristicName
from app.grid.types import Grid, GridSpec
from tests.helpers import (
    ALL_ALGORITHMS,
    assert_valid_path,
    corridor_grid,
    heuristic_for,
    run,
    terrain_grid,
    unreachable_goal_grid,
)


# ---------------------------------------------------------------------------
# BFS: shortest step-count path on an unweighted corridor grid
# ---------------------------------------------------------------------------

def test_bfs_finds_shortest_step_path_through_corridor_gap():
    grid = corridor_grid()
    result = bfs.search(grid)

    assert result.stats.found_path
    assert result.stats.path_length == 13  # 12 steps
    assert result.stats.path_cost == pytest.approx(12.0)
    assert_valid_path(grid, result.path)


# ---------------------------------------------------------------------------
# Weighted terrain: BFS/Greedy get fooled, Dijkstra/A* find the cheaper route
# ---------------------------------------------------------------------------

def test_bfs_takes_the_direct_but_expensive_route():
    grid = terrain_grid()
    result = bfs.search(grid)

    assert result.path == [(0, 0), (0, 1), (0, 2)]
    assert result.stats.path_cost == pytest.approx(6.0)  # 5 (terrain) + 1


def test_dijkstra_takes_the_cheaper_detour():
    grid = terrain_grid()
    result = dijkstra.search(grid)

    assert result.stats.found_path
    assert result.stats.path_cost == pytest.approx(4.0)
    assert_valid_path(grid, result.path)


@pytest.mark.parametrize("heuristic_name", list(HeuristicName))
def test_astar_matches_dijkstra_optimal_cost(heuristic_name):
    grid = terrain_grid()
    dijkstra_result = dijkstra.search(grid)
    astar_result = run(astar, grid, heuristic_name)

    assert astar_result.stats.found_path
    assert astar_result.stats.path_cost == pytest.approx(dijkstra_result.stats.path_cost)
    assert_valid_path(grid, astar_result.path)


def test_greedy_is_suboptimal_compared_to_dijkstra():
    grid = terrain_grid()
    dijkstra_result = dijkstra.search(grid)
    greedy_result = run(greedy, grid, HeuristicName.MANHATTAN)

    assert greedy_result.stats.found_path
    assert_valid_path(grid, greedy_result.path)
    assert greedy_result.stats.path_cost > dijkstra_result.stats.path_cost
    # Greedy is fooled into the same direct-but-expensive route as BFS.
    assert greedy_result.stats.path_cost == pytest.approx(6.0)


# ---------------------------------------------------------------------------
# DFS: finds *a* path, with the same reachability as the other algorithms
# ---------------------------------------------------------------------------

def test_dfs_finds_a_valid_path_on_corridor_grid():
    grid = corridor_grid()
    result = dfs.search(grid)

    assert result.stats.found_path
    assert_valid_path(grid, result.path)
    # DFS has no shortest-path guarantee, but it can't beat the true optimum.
    assert result.stats.path_cost >= 12.0


# ---------------------------------------------------------------------------
# Diagonal movement
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "allow_diagonal,expected_cost",
    [(False, 4.0), (True, 2 * math.sqrt(2))],
)
def test_diagonal_movement_changes_optimal_cost(allow_diagonal, expected_cost):
    spec = GridSpec(rows=3, cols=3, start=(0, 0), goal=(2, 2), allow_diagonal=allow_diagonal)
    grid = Grid.from_spec(spec)

    result = dijkstra.search(grid)

    assert result.stats.found_path
    assert result.stats.path_cost == pytest.approx(expected_cost)


# ---------------------------------------------------------------------------
# No-path case: goal is fully walled off
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module", ALL_ALGORITHMS)
def test_no_path_when_goal_is_walled_off(module):
    grid = unreachable_goal_grid()

    result = run(module, grid, heuristic_for(module))

    assert result.stats.found_path is False
    assert result.path == []
    assert result.stats.path_cost is None
    assert result.stats.path_length == 0
    # Every reachable cell (all but the 2 walls and the isolated goal) gets expanded.
    assert result.stats.nodes_expanded == grid.rows * grid.cols - 2 - 1


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module", ALL_ALGORITHMS)
def test_search_is_deterministic(module):
    grid = corridor_grid()

    first = run(module, grid, heuristic_for(module))
    second = run(module, grid, heuristic_for(module))

    # execution_time_ms naturally varies between runs; everything else
    # (frames, path, and the rest of the stats) must be identical.
    first_dump = first.model_dump(exclude={"stats": {"execution_time_ms"}})
    second_dump = second.model_dump(exclude={"stats": {"execution_time_ms"}})
    assert first_dump == second_dump


# ---------------------------------------------------------------------------
# Registry dispatch + heuristic validation
# ---------------------------------------------------------------------------

def test_registry_runs_each_algorithm():
    grid = corridor_grid()

    for algo in AlgorithmName:
        heuristic = HeuristicName.MANHATTAN if algo in registry.HEURISTIC_REQUIRED else None
        result = registry.run_search(grid, algo, heuristic)
        assert result.algorithm == algo
        assert result.heuristic == heuristic
        assert result.stats.found_path


def test_registry_rejects_heuristic_for_uninformed_algorithms():
    grid = corridor_grid()
    with pytest.raises(ValueError):
        registry.run_search(grid, AlgorithmName.BFS, HeuristicName.MANHATTAN)


def test_registry_requires_heuristic_for_informed_algorithms():
    grid = corridor_grid()
    with pytest.raises(ValueError):
        registry.run_search(grid, AlgorithmName.ASTAR, None)
    with pytest.raises(ValueError):
        registry.run_search(grid, AlgorithmName.GREEDY, None)
