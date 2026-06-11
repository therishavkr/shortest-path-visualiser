import type { PlaybackClock } from "../hooks/useAnimationPlayback";

interface PlaybackBarProps {
  playback: PlaybackClock;
  totalFrames: number;
}

export default function PlaybackBar({ playback, totalFrames }: PlaybackBarProps) {
  const hasFrames = totalFrames > 0;

  return (
    <div className="playback-controls">
      <button type="button" onClick={playback.reset} disabled={!hasFrames || playback.frameIndex < 0}>
        ⏮ Reset
      </button>
      <button type="button" onClick={playback.stepBackward} disabled={!hasFrames || playback.frameIndex < 0}>
        ◀ Step
      </button>
      {playback.isPlaying ? (
        <button type="button" onClick={playback.pause}>
          ⏸ Pause
        </button>
      ) : (
        <button type="button" onClick={playback.play} disabled={!hasFrames || playback.isComplete}>
          ▶ Play
        </button>
      )}
      <button type="button" onClick={playback.stepForward} disabled={!hasFrames || playback.isComplete}>
        Step ▶
      </button>
      <label className="speed-control">
        Speed
        <input
          type="range"
          min={1}
          max={60}
          value={playback.speed}
          onChange={(e) => playback.setSpeed(Number(e.target.value))}
        />
        <span>{playback.speed} fps</span>
      </label>
      {hasFrames && (
        <input
          type="range"
          className="frame-scrubber"
          min={-1}
          max={totalFrames - 1}
          value={playback.frameIndex}
          onChange={(e) => playback.seek(Number(e.target.value))}
        />
      )}
      {hasFrames && (
        <span className="frame-counter">
          {playback.frameIndex + 1} / {totalFrames}
        </span>
      )}
    </div>
  );
}
