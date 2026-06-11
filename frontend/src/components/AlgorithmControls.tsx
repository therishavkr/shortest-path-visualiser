import type { AlgorithmName, HeuristicName } from "../api/client";
import type { PlaybackClock } from "../hooks/useAnimationPlayback";
import { ALGORITHM_LABELS, ALL_ALGORITHMS, ALL_HEURISTICS, HEURISTIC_LABELS, requiresHeuristic } from "../types";
import PlaybackBar from "./PlaybackBar";

interface AlgorithmControlsProps {
  algorithm: AlgorithmName;
  heuristic: HeuristicName | null;
  onAlgorithmChange: (algorithm: AlgorithmName) => void;
  onHeuristicChange: (heuristic: HeuristicName) => void;
  onRun: () => void;
  running: boolean;
  error: string | null;
  playback: PlaybackClock;
  totalFrames: number;
}

export default function AlgorithmControls({
  algorithm,
  heuristic,
  onAlgorithmChange,
  onHeuristicChange,
  onRun,
  running,
  error,
  playback,
  totalFrames,
}: AlgorithmControlsProps) {
  const showHeuristic = requiresHeuristic(algorithm);

  return (
    <div className="algorithm-controls">
      <div className="control-group">
        <label>
          Algorithm
          <select value={algorithm} onChange={(e) => onAlgorithmChange(e.target.value as AlgorithmName)}>
            {ALL_ALGORITHMS.map((algo) => (
              <option key={algo} value={algo}>
                {ALGORITHM_LABELS[algo]}
              </option>
            ))}
          </select>
        </label>
        {showHeuristic && (
          <label>
            Heuristic
            <select value={heuristic ?? "manhattan"} onChange={(e) => onHeuristicChange(e.target.value as HeuristicName)}>
              {ALL_HEURISTICS.map((h) => (
                <option key={h} value={h}>
                  {HEURISTIC_LABELS[h]}
                </option>
              ))}
            </select>
          </label>
        )}
        <button type="button" onClick={onRun} disabled={running}>
          {running ? "Running…" : "Run"}
        </button>
      </div>

      {error && <span className="status error">{error}</span>}

      <PlaybackBar playback={playback} totalFrames={totalFrames} />
    </div>
  );
}
