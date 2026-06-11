from __future__ import annotations

import math
from collections.abc import Callable
from enum import Enum

from app.grid.types import Cell

HeuristicFn = Callable[[Cell, Cell], float]


class HeuristicName(str, Enum):
    MANHATTAN = "manhattan"
    EUCLIDEAN = "euclidean"
    CHEBYSHEV = "chebyshev"


def manhattan(cell: Cell, goal: Cell) -> float:
    return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])


def euclidean(cell: Cell, goal: Cell) -> float:
    return math.hypot(cell[0] - goal[0], cell[1] - goal[1])


def chebyshev(cell: Cell, goal: Cell) -> float:
    """Octile distance: admissible lower bound when diagonal steps cost sqrt(2)
    and orthogonal steps cost 1 (the minimum, untextured terrain cost)."""
    dr = abs(cell[0] - goal[0])
    dc = abs(cell[1] - goal[1])
    return max(dr, dc) + (math.sqrt(2) - 1) * min(dr, dc)


HEURISTICS: dict[HeuristicName, HeuristicFn] = {
    HeuristicName.MANHATTAN: manhattan,
    HeuristicName.EUCLIDEAN: euclidean,
    HeuristicName.CHEBYSHEV: chebyshev,
}
