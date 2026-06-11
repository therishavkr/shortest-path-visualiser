# Shortest Path Benchmarker

A full-stack pathfinding visualizer and benchmarker: a Python search engine
implementing five classic graph-search algorithms (BFS, DFS, Dijkstra, Greedy
Best-First, A*) over a weighted grid, exposed via FastAPI and visualized with
a React + TypeScript dashboard. Every search returns a complete step-by-step
trace, so the frontend can animate the *exact* exploration order — not a
re-simulation — with play/pause/step/speed controls.

## Why this project exists

It's a classic CS-fundamentals showcase done properly: correct, tested
implementations of five algorithms sharing one interface, a documented
discussion of heuristic admissibility (including a deliberately-included case
where A* returns a *suboptimal* path), a side-by-side algorithm comparison
view, and a benchmarking tool that measures how each algorithm scales with
grid size. See [Interview talking points](#interview-talking-points).

## Architecture

```
shortest-path-benchmarker/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # pydantic-settings (CORS origins)
│   ├── schemas.py                # Pydantic request/response models
│   │
│   ├── algorithms/
│   │   ├── base.py               # AlgorithmName, FrameDelta, SearchResult/Stats,
│   │   │                          # reconstruct_path, path_cost
│   │   ├── heuristics.py          # manhattan / euclidean / chebyshev (octile)
│   │   ├── bfs.py, dfs.py, dijkstra.py, greedy.py, astar.py
│   │   └── registry.py            # run_search(grid, algorithm, heuristic) dispatcher
│   │
│   ├── grid/
│   │   ├── types.py               # GridSpec (Pydantic), Grid (runtime), cost model
│   │   └── generator.py           # generate_grid(...) - solvable random grids
│   │
│   └── routers/
│       ├── visualize.py           # POST /api/search, /api/compare, /api/grid/random
│       └── benchmark.py           # POST /api/benchmark
│
├── tests/                          # pytest suite (101 tests)
└── frontend/                        # Vite + React + TypeScript dashboard
    └── src/
        ├── api/client.ts            # typed fetch wrappers
        ├── hooks/useAnimationPlayback.ts  # playback clock + frame replay
        └── components/
            ├── GridEditor.tsx / GridCanvas.tsx
            ├── AlgorithmControls.tsx / PlaybackBar.tsx / StatsPanel.tsx
            ├── ComparisonView.tsx
            └── BenchmarkChart.tsx
```

### Trace-based architecture

Each search runs to completion **once**, server-side, and returns its full
step-by-step trace as `frames: FrameDelta[]`:

```python
class FrameDelta(BaseModel):
    popped: Cell                  # the cell expanded this step
    frontier_added: list[Cell]    # newly discovered cells
    updated: list[Cell]           # frontier cells whose tentative cost improved
```

The frontend never re-runs the algorithm. `computeFrameSets(frames, frameIndex,
start)` replays frames `0..frameIndex` into `visited` / `frontier` /
`updatedCells` sets, and `usePlaybackClock` drives `frameIndex` forward on a
timer (or via step/scrub). This keeps the algorithm implementations free of
any UI concerns and makes the animation perfectly reproducible — scrubbing
backwards is just replaying a shorter prefix of the same array.

### Cost model

| Move | Cost |
| --- | --- |
| Orthogonal step | `1.0` |
| Diagonal step (if `allow_diagonal`) | `√2` |
| Entering a terrain cell | step cost × `5.0` |

Diagonal moves are blocked if either adjacent orthogonal "corner" cell is a
wall (no cutting through corners).

## Algorithms & theory

| Algorithm | Strategy | Optimality |
| --- | --- | --- |
| **BFS** | FIFO queue, expands in discovery order | Fewest *steps* — ignores terrain weights |
| **DFS** | LIFO stack | Finds *a* path, not the shortest or cheapest |
| **Dijkstra** | Uniform-cost search (min-heap on `g(n)`) | Lowest-cost path, terrain-aware |
| **Greedy Best-First** | Min-heap on `h(n)` only | Fast, but can be misled by terrain into a costlier path |
| **A\*** | Min-heap on `f(n) = g(n) + h(n)` | Lowest-cost path **iff** `h` is admissible |

All five share `reconstruct_path` and `path_cost` from `app/algorithms/base.py`
and are dispatched through a single registry (`run_search`), so adding a
sixth algorithm means adding one module and one registry entry.

### Heuristics & admissibility

Three heuristics are available for Greedy Best-First and A*:

- **Manhattan** — `|dr| + |dc|`. Exact cost-to-goal on an orthogonal-only grid.
- **Euclidean** — straight-line distance. Always a lower bound.
- **Chebyshev / octile** — `max(dr,dc) + (√2-1)·min(dr,dc)`. The exact
  no-obstacle cost on an 8-connected grid; always a lower bound.

A heuristic is **admissible** if it never overestimates the true
remaining cost — this is the precondition for A*'s optimality guarantee.
`tests/test_heuristics.py` checks this directly against ground-truth costs
(computed via Dijkstra from every cell to the goal):

| Heuristic | `allow_diagonal=False` | `allow_diagonal=True` |
| --- | --- | --- |
| Manhattan | admissible | **inadmissible** |
| Euclidean | admissible | admissible |
| Chebyshev/octile | admissible | admissible |

**Why Manhattan breaks with diagonal movement**: Manhattan distance assumes
only orthogonal steps (cost `1` each). Once diagonal shortcuts (cost `√2 <
2`) are available, the true cost to a diagonally-offset goal can be *lower*
than the Manhattan estimate — so the heuristic overestimates, violating
admissibility. The API does **not** restrict this combination: running A*
with Manhattan + `allow_diagonal=true` is allowed and can return a
**suboptimal** path, which `test_manhattan_overestimates_with_diagonal_movement`
documents as a deliberate, demonstrable example of why admissibility matters
— pick it in the Visualizer next to Dijkstra to see the gap.

### Random grid generation

`generate_grid(rows, cols, obstacle_density, terrain_density, allow_diagonal,
seed)` places walls and terrain via independent `numpy` random masks, pins
`start=(0,0)` and `goal=(rows-1,cols-1)` as non-wall, and retries (re-seeded)
up to 10 times until a BFS confirms the grid is solvable — falling back to
the last attempt if every retry produces a disconnected grid.

## API

All endpoints are under `/api`. Interactive docs at `/docs` once the server
is running.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/search` | Run one `(algorithm, heuristic?)` over a `grid`. Returns `frames`, `path`, `stats`. `400` if the heuristic requirement isn't satisfied (A*/Greedy require one; others reject one) |
| `POST` | `/api/compare` | Run up to 5 `(algorithm, heuristic?)` configs over the same grid in one request |
| `POST` | `/api/grid/random` | Generate a random solvable `GridSpec` |
| `POST` | `/api/benchmark` | Run each config across multiple grid sizes × trials, returning per-size averages (`nodes_expanded`, `execution_time_ms`, `path_cost`, `found_path_rate`) |

## Frontend

A three-tab dashboard (Vite + React 19 + TypeScript + Recharts):

- **Visualizer** — paint walls/terrain/start/goal directly on the grid (or
  generate a random solvable grid), pick an algorithm + heuristic, run it,
  and scrub through the animated trace with play/pause/step/speed controls.
  The same canvas serves as both the paint editor and the search animation.
- **Comparison** — run up to 4 algorithm configs side by side on the same
  grid with a single shared playback clock, so you can directly compare e.g.
  BFS vs. Dijkstra vs. A* (Manhattan) exploration patterns and final paths.
- **Benchmark** — generate random grids at several sizes (10×10 → 60×60),
  run each configured algorithm for multiple trials per size, and plot nodes
  expanded / execution time / path cost vs. grid size with Recharts.

## Running locally

### Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

`/api/health` should return `{"status": "ok"}`. Copy `.env.example` to `.env`
to override CORS origins.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5174`. The Vite dev server proxies `/api/*` to
`http://127.0.0.1:8002`.

### Docker Compose

```bash
docker compose up --build
```

This builds and runs the API (`http://localhost:8002`) and a static,
nginx-served production build of the frontend (`http://localhost:5174`),
which proxies `/api/*` to the `api` container.

## Testing

```bash
pytest        # full suite (101 tests)
```

Coverage includes:
- Each algorithm's correctness (path validity, optimality where applicable,
  determinism)
- Heuristic admissibility (and the documented Manhattan + diagonal
  exception)
- Frame-trace replay invariants (visited/frontier bookkeeping matches the
  algorithm's own state)
- Random grid generation (determinism with a seed, solvability retries,
  start/goal/wall/terrain invariants)
- FastAPI endpoint contracts (validation errors, heuristic requirements,
  compare/benchmark aggregation)

## Interview talking points

- **One interface, five algorithms**: BFS/DFS/Dijkstra/Greedy/A* all return
  the same `SearchResult` shape and share `reconstruct_path`/`path_cost` —
  the registry pattern (`run_search`) means the API and frontend never branch
  on algorithm-specific logic.
- **Trace-based animation, not re-simulation**: the backend computes the full
  search trace once; the frontend replays `FrameDelta[]` through a pure
  `computeFrameSets` function driven by a playback clock — scrubbing,
  stepping, and speed changes are all "free" (no recomputation, no
  re-running the algorithm).
- **Heuristic admissibility, demonstrated not just asserted**: the README and
  test suite don't just claim Manhattan is "usually fine" — they prove it's
  inadmissible under diagonal movement with a ground-truth comparison, and
  the API deliberately allows that combination so the suboptimal result is
  visible in the UI.
- **Weighted-graph search with real terrain costs**: Dijkstra and A* are
  cost-aware (5× terrain penalty), while BFS/Greedy ignoring cost is itself
  the point of comparison — the Comparison tab makes the cost/speed tradeoff
  visible.
- **Solvability-aware procedural generation**: random grids are validated
  with a BFS reachability check and regenerated (seeded) until solvable,
  rather than hoping a random density doesn't disconnect the grid.
- **Empirical complexity analysis**: the Benchmark tab runs real trials across
  grid sizes and plots nodes-expanded/time/cost vs. N — turning Big-O theory
  into measured data.
- **Full-stack delivery**: typed API contracts (Pydantic ↔ hand-written
  TypeScript client), a canvas-based renderer reused for both editing and
  animation, and a Dockerized deployment.
