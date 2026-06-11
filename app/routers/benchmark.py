from __future__ import annotations

from statistics import mean

from fastapi import APIRouter, HTTPException

from app.algorithms.registry import run_search
from app.grid.generator import generate_grid
from app.grid.types import Grid
from app.schemas import BenchmarkPoint, BenchmarkRequest, BenchmarkResponse

router = APIRouter(prefix="/api", tags=["benchmark"])


@router.post("/benchmark", response_model=BenchmarkResponse)
def benchmark(request: BenchmarkRequest) -> BenchmarkResponse:
    points: list[BenchmarkPoint] = []

    for size in request.sizes:
        for cfg in request.configs:
            expanded: list[int] = []
            costs: list[float] = []
            times: list[float] = []
            solved = 0

            for trial in range(request.trials_per_size):
                trial_seed = None if request.seed is None else request.seed + trial
                spec = generate_grid(
                    rows=size,
                    cols=size,
                    obstacle_density=request.obstacle_density,
                    terrain_density=request.terrain_density,
                    allow_diagonal=request.allow_diagonal,
                    seed=trial_seed,
                )
                grid = Grid.from_spec(spec)
                try:
                    result = run_search(grid, cfg.algorithm, cfg.heuristic)
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc

                expanded.append(result.stats.nodes_expanded)
                times.append(result.stats.execution_time_ms)
                if result.stats.found_path:
                    solved += 1
                    costs.append(result.stats.path_cost)

            points.append(
                BenchmarkPoint(
                    size=size,
                    algorithm=cfg.algorithm,
                    heuristic=cfg.heuristic,
                    nodes_expanded=mean(expanded),
                    path_cost=mean(costs) if costs else None,
                    execution_time_ms=mean(times),
                    found_path_rate=solved / request.trials_per_size,
                )
            )

    return BenchmarkResponse(points=points)
