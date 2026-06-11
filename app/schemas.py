from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.algorithms.base import AlgorithmName, FrameDelta, SearchResult, SearchStats
from app.algorithms.heuristics import HeuristicName
from app.grid.types import Cell, GridSpec

__all__ = [
    "AlgorithmName",
    "HeuristicName",
    "Cell",
    "GridSpec",
    "FrameDelta",
    "SearchStats",
    "SearchResult",
    "AlgorithmConfig",
    "SearchRequest",
    "CompareRequest",
    "CompareResponse",
    "RandomGridRequest",
    "BenchmarkRequest",
    "BenchmarkPoint",
    "BenchmarkResponse",
]


class AlgorithmConfig(BaseModel):
    algorithm: AlgorithmName
    heuristic: HeuristicName | None = None


class SearchRequest(BaseModel):
    grid: GridSpec
    algorithm: AlgorithmName
    heuristic: HeuristicName | None = None


class CompareRequest(BaseModel):
    grid: GridSpec
    configs: list[AlgorithmConfig] = Field(..., min_length=1, max_length=5)


class CompareResponse(BaseModel):
    results: list[SearchResult]


class RandomGridRequest(BaseModel):
    rows: int = Field(25, ge=2, le=60)
    cols: int = Field(30, ge=2, le=60)
    obstacle_density: float = Field(0.2, ge=0.0, le=0.6)
    terrain_density: float = Field(0.15, ge=0.0, le=0.6)
    allow_diagonal: bool = False
    seed: int | None = None


class BenchmarkRequest(BaseModel):
    sizes: list[int] = Field(default=[10, 20, 30, 40, 50], min_length=1, max_length=8)
    obstacle_density: float = Field(0.2, ge=0.0, le=0.6)
    terrain_density: float = Field(0.15, ge=0.0, le=0.6)
    allow_diagonal: bool = False
    configs: list[AlgorithmConfig] = Field(..., min_length=1, max_length=5)
    trials_per_size: int = Field(3, ge=1, le=10)
    seed: int | None = None

    @field_validator("sizes")
    @classmethod
    def _validate_sizes(cls, sizes: list[int]) -> list[int]:
        for size in sizes:
            if not (2 <= size <= 60):
                raise ValueError(f"size {size} must be between 2 and 60")
        return sizes


class BenchmarkPoint(BaseModel):
    size: int
    algorithm: AlgorithmName
    heuristic: HeuristicName | None
    nodes_expanded: float
    path_cost: float | None
    execution_time_ms: float
    found_path_rate: float


class BenchmarkResponse(BaseModel):
    points: list[BenchmarkPoint]
