import { useState } from "react";
import { compareAlgorithms } from "../api/client";
import type { AlgorithmConfig, AlgorithmName, GridSpec, HeuristicName, SearchResult } from "../api/client";
import { computeFrameSets, usePlaybackClock } from "../hooks/useAnimationPlayback";
import {
  ALGORITHM_LABELS,
  ALL_ALGORITHMS,
  ALL_HEURISTICS,
  HEURISTIC_LABELS,
  computeCellSize,
  defaultHeuristicFor,
  requiresHeuristic,
} from "../types";
import GridCanvas from "./GridCanvas";
import PlaybackBar from "./PlaybackBar";
import StatsPanel from "./StatsPanel";

const MAX_CONFIGS = 4;

const DEFAULT_CONFIGS: AlgorithmConfig[] = [
  { algorithm: "bfs" },
  { algorithm: "dijkstra" },
  { algorithm: "astar", heuristic: "manhattan" },
];

interface ComparisonViewProps {
  grid: GridSpec;
}

export default function ComparisonView({ grid }: ComparisonViewProps) {
  const [configs, setConfigs] = useState<AlgorithmConfig[]>(DEFAULT_CONFIGS);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maxFrames = results.reduce((max, r) => Math.max(max, r.frames.length), 0);
  const playback = usePlaybackClock(maxFrames);

  async function runComparison() {
    setRunning(true);
    setError(null);
    try {
      const response = await compareAlgorithms({ grid, configs });
      setResults(response.results);
    } catch (err) {
      setResults([]);
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setRunning(false);
    }
  }

  function updateAlgorithm(index: number, algorithm: AlgorithmName) {
    setConfigs((prev) =>
      prev.map((c, i) => (i === index ? { algorithm, heuristic: defaultHeuristicFor(algorithm) ?? undefined } : c)),
    );
  }

  function updateHeuristic(index: number, heuristic: HeuristicName) {
    setConfigs((prev) => prev.map((c, i) => (i === index ? { ...c, heuristic } : c)));
  }

  function addConfig() {
    setConfigs((prev) => (prev.length >= MAX_CONFIGS ? prev : [...prev, { algorithm: "greedy", heuristic: "manhattan" }]));
  }

  function removeConfig(index: number) {
    setConfigs((prev) => prev.filter((_, i) => i !== index));
  }

  const cellSize = computeCellSize(grid.rows, grid.cols, 360);

  return (
    <div className="comparison">
      <p className="comparison-intro">
        Run multiple algorithms on the same grid and watch them expand side by side on a single shared
        timeline.
      </p>

      <div className="comparison-config">
        {configs.map((config, i) => (
          <div className="comparison-config-row" key={i}>
            <select value={config.algorithm} onChange={(e) => updateAlgorithm(i, e.target.value as AlgorithmName)}>
              {ALL_ALGORITHMS.map((algo) => (
                <option key={algo} value={algo}>
                  {ALGORITHM_LABELS[algo]}
                </option>
              ))}
            </select>
            {requiresHeuristic(config.algorithm) && (
              <select
                value={config.heuristic ?? "manhattan"}
                onChange={(e) => updateHeuristic(i, e.target.value as HeuristicName)}
              >
                {ALL_HEURISTICS.map((h) => (
                  <option key={h} value={h}>
                    {HEURISTIC_LABELS[h]}
                  </option>
                ))}
              </select>
            )}
            {configs.length > 1 && (
              <button type="button" onClick={() => removeConfig(i)}>
                Remove
              </button>
            )}
          </div>
        ))}
        <div className="comparison-config-row">
          {configs.length < MAX_CONFIGS && (
            <button type="button" onClick={addConfig}>
              Add algorithm
            </button>
          )}
          <button type="button" onClick={runComparison} disabled={running}>
            {running ? "Running…" : "Compare"}
          </button>
        </div>
      </div>

      {error && <span className="status error">{error}</span>}

      {results.length > 0 && (
        <>
          <PlaybackBar playback={playback} totalFrames={maxFrames} />

          <div className="comparison-grid">
            {results.map((result, i) => {
              const { visited, frontier, updatedCells } = computeFrameSets(result.frames, playback.frameIndex, grid.start);
              const path = playback.isComplete ? result.path : [];
              return (
                <div className="comparison-cell" key={i}>
                  <GridCanvas
                    grid={grid}
                    cellSize={cellSize}
                    visited={visited}
                    frontier={frontier}
                    updatedCells={updatedCells}
                    path={path}
                  />
                  <StatsPanel algorithm={result.algorithm} heuristic={result.heuristic} stats={result.stats} />
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
