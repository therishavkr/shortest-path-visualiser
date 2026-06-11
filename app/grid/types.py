from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, model_validator

Cell = tuple[int, int]

ORTHOGONAL_COST = 1.0
DIAGONAL_COST = math.sqrt(2)
TERRAIN_COST = 5.0

# Fixed exploration order, used by every algorithm for deterministic results.
_ORTHOGONAL_OFFSETS: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, 1), (0, -1))  # N, S, E, W
_DIAGONAL_OFFSETS: tuple[Cell, ...] = ((-1, 1), (1, 1), (1, -1), (-1, -1))  # NE, SE, SW, NW


class CellType(str, Enum):
    EMPTY = "empty"
    TERRAIN = "terrain"
    WALL = "wall"


class GridSpec(BaseModel):
    rows: int = Field(..., ge=2, le=60)
    cols: int = Field(..., ge=2, le=60)
    start: Cell
    goal: Cell
    walls: list[Cell] = Field(default_factory=list)
    terrain: list[Cell] = Field(default_factory=list)
    allow_diagonal: bool = False

    @model_validator(mode="after")
    def _validate(self) -> "GridSpec":
        def in_bounds(cell: Cell) -> bool:
            r, c = cell
            return 0 <= r < self.rows and 0 <= c < self.cols

        if not in_bounds(self.start):
            raise ValueError("start is out of bounds")
        if not in_bounds(self.goal):
            raise ValueError("goal is out of bounds")
        if self.start == self.goal:
            raise ValueError("start and goal must differ")

        wall_set = set(self.walls)
        terrain_set = set(self.terrain)

        for cell in wall_set | terrain_set:
            if not in_bounds(cell):
                raise ValueError(f"cell {cell} is out of bounds")

        if self.start in wall_set or self.goal in wall_set:
            raise ValueError("start/goal cannot be a wall")

        if wall_set & terrain_set:
            raise ValueError("a cell cannot be both wall and terrain")

        return self


@dataclass(frozen=True)
class Grid:
    """Runtime view of a GridSpec with O(1) lookups for search algorithms."""

    rows: int
    cols: int
    walls: frozenset[Cell]
    terrain: frozenset[Cell]
    start: Cell
    goal: Cell
    allow_diagonal: bool

    @classmethod
    def from_spec(cls, spec: GridSpec) -> "Grid":
        return cls(
            rows=spec.rows,
            cols=spec.cols,
            walls=frozenset(spec.walls),
            terrain=frozenset(spec.terrain),
            start=spec.start,
            goal=spec.goal,
            allow_diagonal=spec.allow_diagonal,
        )

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_walkable(self, cell: Cell) -> bool:
        return self.in_bounds(cell) and cell not in self.walls

    def cell_weight(self, cell: Cell) -> float:
        return TERRAIN_COST if cell in self.terrain else 1.0

    def neighbors(self, cell: Cell) -> Iterator[tuple[Cell, float]]:
        """Yield (neighbor, step_cost) in a fixed N,S,E,W[,NE,SE,SW,NW] order.

        step_cost is the orthogonal/diagonal base cost scaled by the
        destination cell's terrain weight. Diagonal moves are skipped if
        either adjacent orthogonal "corner" cell is not walkable, to avoid
        cutting through wall corners.
        """
        r, c = cell
        for dr, dc in _ORTHOGONAL_OFFSETS:
            nxt = (r + dr, c + dc)
            if self.is_walkable(nxt):
                yield nxt, ORTHOGONAL_COST * self.cell_weight(nxt)

        if self.allow_diagonal:
            for dr, dc in _DIAGONAL_OFFSETS:
                nxt = (r + dr, c + dc)
                if not self.is_walkable(nxt):
                    continue
                corner_a = (r + dr, c)
                corner_b = (r, c + dc)
                if not (self.is_walkable(corner_a) and self.is_walkable(corner_b)):
                    continue
                yield nxt, DIAGONAL_COST * self.cell_weight(nxt)
