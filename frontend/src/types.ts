import type { AlgorithmName, Cell, GridSpec, HeuristicName } from "./api/client";

export type EditorTool = "wall" | "terrain" | "erase" | "start" | "goal";

export const EDITOR_TOOLS: { id: EditorTool; label: string }[] = [
  { id: "wall", label: "Wall" },
  { id: "terrain", label: "Terrain" },
  { id: "erase", label: "Erase" },
  { id: "start", label: "Start" },
  { id: "goal", label: "Goal" },
];

export const ALGORITHM_LABELS: Record<AlgorithmName, string> = {
  bfs: "Breadth-First Search",
  dfs: "Depth-First Search",
  dijkstra: "Dijkstra",
  greedy: "Greedy Best-First",
  astar: "A*",
};

export const HEURISTIC_LABELS: Record<HeuristicName, string> = {
  manhattan: "Manhattan",
  euclidean: "Euclidean",
  chebyshev: "Chebyshev (Octile)",
};

export const ALL_ALGORITHMS: AlgorithmName[] = ["bfs", "dfs", "dijkstra", "greedy", "astar"];
export const ALL_HEURISTICS: HeuristicName[] = ["manhattan", "euclidean", "chebyshev"];

export function requiresHeuristic(algorithm: AlgorithmName): boolean {
  return algorithm === "greedy" || algorithm === "astar";
}

export function defaultHeuristicFor(algorithm: AlgorithmName): HeuristicName | null {
  return requiresHeuristic(algorithm) ? "manhattan" : null;
}

export function cellKey(cell: Cell): string {
  return `${cell[0]},${cell[1]}`;
}

export function cellsEqual(a: Cell, b: Cell): boolean {
  return a[0] === b[0] && a[1] === b[1];
}

export function computeCellSize(
  rows: number,
  cols: number,
  maxDimensionPx = 640,
  minCellPx = 8,
  maxCellPx = 28,
): number {
  const size = Math.floor(maxDimensionPx / Math.max(rows, cols));
  return Math.max(minCellPx, Math.min(maxCellPx, size));
}

export function defaultGrid(rows: number, cols: number): GridSpec {
  return {
    rows,
    cols,
    start: [0, 0],
    goal: [rows - 1, cols - 1],
    walls: [],
    terrain: [],
    allow_diagonal: false,
  };
}
