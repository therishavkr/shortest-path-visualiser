import { useState } from "react";
import { searchGrid } from "./api/client";
import type { AlgorithmName, GridSpec, HeuristicName, SearchResult } from "./api/client";
import AlgorithmControls from "./components/AlgorithmControls";
import BenchmarkChart from "./components/BenchmarkChart";
import ComparisonView from "./components/ComparisonView";
import GridEditor from "./components/GridEditor";
import StatsPanel from "./components/StatsPanel";
import { computeFrameSets, usePlaybackClock } from "./hooks/useAnimationPlayback";
import { defaultGrid, requiresHeuristic } from "./types";
import "./App.css";

type Tab = "visualizer" | "comparison" | "benchmark";

const TABS: { id: Tab; label: string }[] = [
  { id: "visualizer", label: "Visualizer" },
  { id: "comparison", label: "Comparison" },
  { id: "benchmark", label: "Benchmark" },
];

const EMPTY_SET = new Set<string>();

function App() {
  const [grid, setGrid] = useState<GridSpec>(() => defaultGrid(20, 30));
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("astar");
  const [heuristic, setHeuristic] = useState<HeuristicName>("manhattan");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("visualizer");

  const playback = usePlaybackClock(result?.frames.length ?? 0);

  function handleGridChange(next: GridSpec) {
    setGrid(next);
    setResult(null);
  }

  async function runSearch() {
    setRunning(true);
    setError(null);
    try {
      const response = await searchGrid({
        grid,
        algorithm,
        heuristic: requiresHeuristic(algorithm) ? heuristic : undefined,
      });
      setResult(response);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setRunning(false);
    }
  }

  const { visited, frontier, updatedCells } = result
    ? computeFrameSets(result.frames, playback.frameIndex, grid.start)
    : { visited: EMPTY_SET, frontier: EMPTY_SET, updatedCells: EMPTY_SET };
  const path = result && playback.isComplete ? result.path : [];

  return (
    <div className="app">
      <header className="app-header">
        <h1>Shortest Path Benchmarker</h1>
        <p>BFS &middot; DFS &middot; Dijkstra &middot; Greedy Best-First &middot; A* &mdash; visualized step by step</p>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`tab${tab === t.id ? " active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === "visualizer" && (
          <>
            <GridEditor
              grid={grid}
              onChange={handleGridChange}
              disabled={running}
              visited={visited}
              frontier={frontier}
              updatedCells={updatedCells}
              path={path}
            />
            <AlgorithmControls
              algorithm={algorithm}
              heuristic={heuristic}
              onAlgorithmChange={setAlgorithm}
              onHeuristicChange={setHeuristic}
              onRun={runSearch}
              running={running}
              error={error}
              playback={playback}
              totalFrames={result?.frames.length ?? 0}
            />
            {result && <StatsPanel algorithm={result.algorithm} heuristic={result.heuristic} stats={result.stats} />}
          </>
        )}
        {tab === "comparison" && <ComparisonView grid={grid} />}
        {tab === "benchmark" && <BenchmarkChart />}
      </main>
    </div>
  );
}

export default App;
