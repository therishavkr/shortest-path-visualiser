export type Cell = [number, number];

export type AlgorithmName = "bfs" | "dfs" | "dijkstra" | "greedy" | "astar";
export type HeuristicName = "manhattan" | "euclidean" | "chebyshev";

export interface GridSpec {
  rows: number;
  cols: number;
  start: Cell;
  goal: Cell;
  walls: Cell[];
  terrain: Cell[];
  allow_diagonal: boolean;
}

export interface FrameDelta {
  popped: Cell;
  frontier_added: Cell[];
  updated: Cell[];
}

export interface SearchStats {
  nodes_expanded: number;
  nodes_visited: number;
  path_length: number;
  path_cost: number | null;
  execution_time_ms: number;
  found_path: boolean;
}

export interface SearchResult {
  algorithm: AlgorithmName;
  heuristic: HeuristicName | null;
  frames: FrameDelta[];
  path: Cell[];
  stats: SearchStats;
}

export interface AlgorithmConfig {
  algorithm: AlgorithmName;
  heuristic?: HeuristicName | null;
}

export interface SearchRequest {
  grid: GridSpec;
  algorithm: AlgorithmName;
  heuristic?: HeuristicName | null;
}

export interface CompareRequest {
  grid: GridSpec;
  configs: AlgorithmConfig[];
}

export interface CompareResponse {
  results: SearchResult[];
}

export interface RandomGridRequest {
  rows: number;
  cols: number;
  obstacle_density: number;
  terrain_density: number;
  allow_diagonal: boolean;
  seed?: number | null;
}

export interface BenchmarkRequest {
  sizes: number[];
  obstacle_density: number;
  terrain_density: number;
  allow_diagonal: boolean;
  configs: AlgorithmConfig[];
  trials_per_size: number;
  seed?: number | null;
}

export interface BenchmarkPoint {
  size: number;
  algorithm: AlgorithmName;
  heuristic: HeuristicName | null;
  nodes_expanded: number;
  path_cost: number | null;
  execution_time_ms: number;
  found_path_rate: number;
}

export interface BenchmarkResponse {
  points: BenchmarkPoint[];
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

class ApiError extends Error {}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? response.statusText;
    throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

function postJSON<TResponse>(path: string, body: unknown): Promise<TResponse> {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(handleResponse<TResponse>);
}

export function searchGrid(request: SearchRequest): Promise<SearchResult> {
  return postJSON("/search", request);
}

export function compareAlgorithms(request: CompareRequest): Promise<CompareResponse> {
  return postJSON("/compare", request);
}

export function getRandomGrid(request: RandomGridRequest): Promise<GridSpec> {
  return postJSON("/grid/random", request);
}

export function runBenchmark(request: BenchmarkRequest): Promise<BenchmarkResponse> {
  return postJSON("/benchmark", request);
}
