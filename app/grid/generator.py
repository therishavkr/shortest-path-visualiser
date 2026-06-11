from __future__ import annotations

import numpy as np

from app.algorithms import bfs
from app.grid.types import Cell, Grid, GridSpec

MAX_GENERATION_ATTEMPTS = 10


def generate_grid(
    rows: int,
    cols: int,
    obstacle_density: float = 0.2,
    terrain_density: float = 0.15,
    allow_diagonal: bool = False,
    seed: int | None = None,
) -> GridSpec:
    """Generate a random grid with `start=(0, 0)` and `goal=(rows-1, cols-1)`.

    Walls are sampled at `obstacle_density`, then terrain at
    `terrain_density` among the remaining empty cells. Retries with a
    perturbed seed (up to `MAX_GENERATION_ATTEMPTS`) until the goal is
    reachable from the start; if every attempt fails, the last (possibly
    unsolvable) spec is returned and callers handle `found_path=False`.
    """
    start: Cell = (0, 0)
    goal: Cell = (rows - 1, cols - 1)

    spec: GridSpec | None = None
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        attempt_seed = None if seed is None else seed + attempt
        rng = np.random.default_rng(attempt_seed)

        wall_mask = rng.random((rows, cols)) < obstacle_density
        wall_mask[start] = False
        wall_mask[goal] = False

        terrain_mask = (rng.random((rows, cols)) < terrain_density) & ~wall_mask
        terrain_mask[start] = False
        terrain_mask[goal] = False

        walls = [(int(r), int(c)) for r, c in np.argwhere(wall_mask)]
        terrain = [(int(r), int(c)) for r, c in np.argwhere(terrain_mask)]

        spec = GridSpec(
            rows=rows,
            cols=cols,
            start=start,
            goal=goal,
            walls=walls,
            terrain=terrain,
            allow_diagonal=allow_diagonal,
        )

        if _is_solvable(spec):
            return spec

    return spec


def _is_solvable(spec: GridSpec) -> bool:
    grid = Grid.from_spec(spec)
    return bfs.search(grid).stats.found_path
