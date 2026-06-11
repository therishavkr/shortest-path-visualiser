import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { runBenchmark } from "../api/client";
import type { AlgorithmConfig, AlgorithmName, BenchmarkPoint, BenchmarkResponse, HeuristicName } from "../api/client";
import {
  ALGORITHM_LABELS,
  ALL_ALGORITHMS,
  ALL_HEURISTICS,
  HEURISTIC_LABELS,
  defaultHeuristicFor,
  requiresHeuristic,
} from "../types";

const SIZE_OPTIONS = [10, 15, 20, 25, 30, 40, 50, 60];
const DEFAULT_SIZES = [10, 20, 30, 40];
const MAX_CONFIGS = 5;
const SERIES_COLORS = ["#5b9bd5", "#7cd992", "#f4b860", "#e57373", "#b388eb"];

const DEFAULT_CONFIGS: AlgorithmConfig[] = [
  { algorithm: "bfs" },
  { algorithm: "dijkstra" },
  { algorithm: "astar", heuristic: "manhattan" },
  { algorithm: "greedy", heuristic: "manhattan" },
];

function configLabel(algorithm: AlgorithmName, heuristic: HeuristicName | null): string {
  return heuristic ? `${ALGORITHM_LABELS[algorithm]} (${HEURISTIC_LABELS[heuristic]})` : ALGORITHM_LABELS[algorithm];
}

type SeriesRow = { size: number } & Record<string, number | null>;

function buildSeries(points: BenchmarkPoint[], metric: keyof BenchmarkPoint, labels: string[]): SeriesRow[] {
  const sizes = Array.from(new Set(points.map((p) => p.size))).sort((a, b) => a - b);
  return sizes.map((size) => {
    const row: SeriesRow = { size };
    for (const label of labels) {
      const point = points.find((p) => p.size === size && configLabel(p.algorithm, p.heuristic) === label);
      row[label] = point ? (point[metric] as number | null) : null;
    }
    return row;
  });
}

export default function BenchmarkChart() {
  const [selectedSizes, setSelectedSizes] = useState<number[]>(DEFAULT_SIZES);
  const [obstacleDensity, setObstacleDensity] = useState(0.2);
  const [terrainDensity, setTerrainDensity] = useState(0.15);
  const [allowDiagonal, setAllowDiagonal] = useState(false);
  const [trialsPerSize, setTrialsPerSize] = useState(3);
  const [seedText, setSeedText] = useState("1");
  const [configs, setConfigs] = useState<AlgorithmConfig[]>(DEFAULT_CONFIGS);
  const [response, setResponse] = useState<BenchmarkResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleSize(size: number) {
    setSelectedSizes((prev) =>
      prev.includes(size) ? prev.filter((s) => s !== size) : [...prev, size].sort((a, b) => a - b),
    );
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
    setConfigs((prev) => (prev.length >= MAX_CONFIGS ? prev : [...prev, { algorithm: "bfs" }]));
  }

  function removeConfig(index: number) {
    setConfigs((prev) => prev.filter((_, i) => i !== index));
  }

  async function run() {
    if (selectedSizes.length === 0 || configs.length === 0) return;
    setRunning(true);
    setError(null);
    try {
      const trimmed = seedText.trim();
      const seed = trimmed === "" ? null : Number(trimmed);
      const result = await runBenchmark({
        sizes: selectedSizes,
        obstacle_density: obstacleDensity,
        terrain_density: terrainDensity,
        allow_diagonal: allowDiagonal,
        configs,
        trials_per_size: trialsPerSize,
        seed,
      });
      setResponse(result);
    } catch (err) {
      setResponse(null);
      setError(err instanceof Error ? err.message : "Benchmark failed");
    } finally {
      setRunning(false);
    }
  }

  const labels = response ? Array.from(new Set(response.points.map((p) => configLabel(p.algorithm, p.heuristic)))) : [];
  const expandedSeries = response ? buildSeries(response.points, "nodes_expanded", labels) : [];
  const timeSeries = response ? buildSeries(response.points, "execution_time_ms", labels) : [];
  const costSeries = response ? buildSeries(response.points, "path_cost", labels) : [];

  return (
    <div className="benchmark">
      <p className="comparison-intro">
        Generate random grids of increasing size and measure how each algorithm scales: nodes expanded,
        wall-clock time, and path cost (averaged over {trialsPerSize} trial{trialsPerSize === 1 ? "" : "s"} per
        size).
      </p>

      <div className="benchmark-config">
        <div className="control-group">
          <span className="field-label">Grid sizes (N&times;N)</span>
          <div className="size-options">
            {SIZE_OPTIONS.map((size) => (
              <label key={size} className="checkbox">
                <input type="checkbox" checked={selectedSizes.includes(size)} onChange={() => toggleSize(size)} />
                {size}
              </label>
            ))}
          </div>
        </div>

        <div className="control-group">
          <label>
            Obstacle density ({Math.round(obstacleDensity * 100)}%)
            <input
              type="range"
              min={0}
              max={0.6}
              step={0.05}
              value={obstacleDensity}
              onChange={(e) => setObstacleDensity(Number(e.target.value))}
            />
          </label>
          <label>
            Terrain density ({Math.round(terrainDensity * 100)}%)
            <input
              type="range"
              min={0}
              max={0.6}
              step={0.05}
              value={terrainDensity}
              onChange={(e) => setTerrainDensity(Number(e.target.value))}
            />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={allowDiagonal} onChange={(e) => setAllowDiagonal(e.target.checked)} />
            Allow diagonal movement
          </label>
        </div>

        <div className="control-group">
          <label>
            Trials per size
            <input
              type="number"
              min={1}
              max={10}
              value={trialsPerSize}
              onChange={(e) => setTrialsPerSize(Number(e.target.value))}
            />
          </label>
          <label>
            Seed (optional)
            <input type="text" inputMode="numeric" placeholder="random" value={seedText} onChange={(e) => setSeedText(e.target.value)} />
          </label>
        </div>

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
          <button type="button" onClick={run} disabled={running}>
            {running ? "Running…" : "Run benchmark"}
          </button>
        </div>
      </div>

      {error && <span className="status error">{error}</span>}

      {response && (
        <>
          <div className="panel">
            <h3>Nodes expanded vs. grid size</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={expandedSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="size" stroke="var(--text)" label={{ value: "Grid size (N)", position: "insideBottom", offset: -2, fill: "var(--text)" }} />
                <YAxis stroke="var(--text)" />
                <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }} />
                <Legend />
                {labels.map((label, i) => (
                  <Line key={label} type="monotone" dataKey={label} stroke={SERIES_COLORS[i % SERIES_COLORS.length]} dot={{ r: 3 }} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <h3>Execution time (ms) vs. grid size</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={timeSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="size" stroke="var(--text)" label={{ value: "Grid size (N)", position: "insideBottom", offset: -2, fill: "var(--text)" }} />
                <YAxis stroke="var(--text)" />
                <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }} />
                <Legend />
                {labels.map((label, i) => (
                  <Line key={label} type="monotone" dataKey={label} stroke={SERIES_COLORS[i % SERIES_COLORS.length]} dot={{ r: 3 }} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <h3>Path cost vs. grid size</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={costSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="size" stroke="var(--text)" label={{ value: "Grid size (N)", position: "insideBottom", offset: -2, fill: "var(--text)" }} />
                <YAxis stroke="var(--text)" />
                <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }} />
                <Legend />
                {labels.map((label, i) => (
                  <Line key={label} type="monotone" dataKey={label} stroke={SERIES_COLORS[i % SERIES_COLORS.length]} dot={{ r: 3 }} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
