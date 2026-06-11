from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.algorithms.base import SearchResult
from app.algorithms.registry import run_search
from app.grid.generator import generate_grid
from app.grid.types import Grid, GridSpec
from app.schemas import CompareRequest, CompareResponse, RandomGridRequest, SearchRequest

router = APIRouter(prefix="/api", tags=["visualize"])


@router.post("/search", response_model=SearchResult)
def search(request: SearchRequest) -> SearchResult:
    grid = Grid.from_spec(request.grid)
    try:
        return run_search(grid, request.algorithm, request.heuristic)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    grid = Grid.from_spec(request.grid)
    results: list[SearchResult] = []
    for cfg in request.configs:
        try:
            results.append(run_search(grid, cfg.algorithm, cfg.heuristic))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CompareResponse(results=results)


@router.post("/grid/random", response_model=GridSpec)
def random_grid(request: RandomGridRequest) -> GridSpec:
    return generate_grid(**request.model_dump())
