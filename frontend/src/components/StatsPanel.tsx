import type { AlgorithmName, HeuristicName, SearchStats } from "../api/client";
import { ALGORITHM_LABELS, HEURISTIC_LABELS } from "../types";

interface StatsPanelProps {
  algorithm: AlgorithmName;
  heuristic: HeuristicName | null;
  stats: SearchStats;
}

export default function StatsPanel({ algorithm, heuristic, stats }: StatsPanelProps) {
  return (
    <div className="stats-panel">
      <div className="stats-title">
        {ALGORITHM_LABELS[algorithm]}
        {heuristic && <span className="badge">{HEURISTIC_LABELS[heuristic]}</span>}
        <span className={`badge ${stats.found_path ? "badge-analytical" : "badge-numeric"}`}>
          {stats.found_path ? "Path found" : "No path"}
        </span>
      </div>
      <div className="stats-grid">
        <div className="stat-cell">
          <span className="stat-label">Nodes expanded</span>
          <span className="stat-value">{stats.nodes_expanded}</span>
        </div>
        <div className="stat-cell">
          <span className="stat-label">Nodes visited</span>
          <span className="stat-value">{stats.nodes_visited}</span>
        </div>
        <div className="stat-cell">
          <span className="stat-label">Path length</span>
          <span className="stat-value">{stats.path_length || "—"}</span>
        </div>
        <div className="stat-cell">
          <span className="stat-label">Path cost</span>
          <span className="stat-value">{stats.path_cost !== null ? stats.path_cost.toFixed(3) : "—"}</span>
        </div>
        <div className="stat-cell">
          <span className="stat-label">Time</span>
          <span className="stat-value">{stats.execution_time_ms.toFixed(3)} ms</span>
        </div>
      </div>
    </div>
  );
}
