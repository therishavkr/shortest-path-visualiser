import pytest

from app.algorithms import bfs, dfs
from app.grid.types import Grid, GridSpec
from tests.helpers import (
    ALL_ALGORITHMS,
    corridor_grid,
    heuristic_for,
    run,
    terrain_grid,
)


def _replay(grid: Grid, result):
    """Replay frame deltas the same way the frontend would: maintain a
    `discovered` set (frontier-or-expanded) and an `expanded` set."""
    discovered = {grid.start}
    expanded: set = set()
    seen_pops: list = []

    for frame in result.frames:
        seen_pops.append(frame.popped)
        expanded.add(frame.popped)
        discovered.add(frame.popped)
        for cell in frame.frontier_added:
            discovered.add(cell)
        for cell in frame.updated:
            # `updated` cells must already be known (decrease-key on an
            # existing frontier entry), never a brand-new discovery.
            assert cell in discovered

    return discovered, expanded, seen_pops


GRIDS = {
    "corridor": corridor_grid(),
    "terrain": terrain_grid(),
    "terrain_diagonal": terrain_grid(allow_diagonal=True),
}


@pytest.mark.parametrize("grid_name", list(GRIDS))
@pytest.mark.parametrize("module", ALL_ALGORITHMS)
def test_frame_replay_matches_stats(module, grid_name):
    grid = GRIDS[grid_name]
    result = run(module, grid, heuristic_for(module))

    discovered, expanded, seen_pops = _replay(grid, result)

    assert len(expanded) == result.stats.nodes_expanded
    assert len(discovered) == result.stats.nodes_visited
    # Every popped cell is expanded exactly once - no duplicate frames.
    assert len(seen_pops) == len(set(seen_pops)) == len(result.frames)


@pytest.mark.parametrize("grid_name", list(GRIDS))
@pytest.mark.parametrize("module", ALL_ALGORITHMS)
def test_path_cells_were_all_discovered(module, grid_name):
    grid = GRIDS[grid_name]
    result = run(module, grid, heuristic_for(module))

    discovered, _expanded, _seen_pops = _replay(grid, result)

    for cell in result.path:
        assert cell in discovered


@pytest.mark.parametrize("module", [bfs, dfs])
def test_uninformed_algorithms_never_revisit_frontier(module):
    """BFS/DFS check `discovered` before enqueueing, so a cell should never
    appear in `frontier_added` more than once across the whole trace."""
    grid = corridor_grid()
    result = run(module, grid, None)

    seen: set = set()
    for frame in result.frames:
        for cell in frame.frontier_added:
            assert cell not in seen
            seen.add(cell)
        assert frame.updated == []


def test_no_path_replay_covers_entire_reachable_region():
    spec = GridSpec(rows=5, cols=5, start=(0, 0), goal=(4, 4), walls=[(3, 4), (4, 3)])
    grid = Grid.from_spec(spec)

    result = bfs.search(grid)
    discovered, expanded, _ = _replay(grid, result)

    assert result.stats.found_path is False
    assert grid.goal not in discovered
    assert len(expanded) == grid.rows * grid.cols - 2 - 1
