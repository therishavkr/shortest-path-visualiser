import { useEffect, useState } from "react";
import type { Cell, FrameDelta } from "../api/client";
import { cellKey } from "../types";

export interface PlaybackClock {
  frameIndex: number;
  isPlaying: boolean;
  speed: number;
  isComplete: boolean;
  play: () => void;
  pause: () => void;
  stepForward: () => void;
  stepBackward: () => void;
  reset: () => void;
  seek: (index: number) => void;
  setSpeed: (speed: number) => void;
}

/** Drives a frame index from -1 (nothing shown yet) to totalFrames - 1. */
export function usePlaybackClock(totalFrames: number): PlaybackClock {
  const [frameIndex, setFrameIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(15);
  const [prevTotalFrames, setPrevTotalFrames] = useState(totalFrames);

  if (prevTotalFrames !== totalFrames) {
    setPrevTotalFrames(totalFrames);
    setFrameIndex(-1);
    setIsPlaying(false);
  }

  const isComplete = frameIndex >= totalFrames - 1;

  if (isPlaying && isComplete) {
    setIsPlaying(false);
  }

  useEffect(() => {
    if (!isPlaying || isComplete) return;
    const id = setTimeout(() => setFrameIndex((i) => Math.min(i + 1, totalFrames - 1)), 1000 / speed);
    return () => clearTimeout(id);
  }, [isPlaying, isComplete, frameIndex, speed, totalFrames]);

  return {
    frameIndex,
    isPlaying,
    speed,
    isComplete,
    play: () => {
      if (totalFrames > 0) setIsPlaying(true);
    },
    pause: () => setIsPlaying(false),
    stepForward: () => setFrameIndex((i) => Math.min(i + 1, totalFrames - 1)),
    stepBackward: () => setFrameIndex((i) => Math.max(i - 1, -1)),
    reset: () => {
      setFrameIndex(-1);
      setIsPlaying(false);
    },
    seek: (index: number) => setFrameIndex(Math.max(-1, Math.min(index, totalFrames - 1))),
    setSpeed,
  };
}

export interface FrameSets {
  visited: Set<string>;
  frontier: Set<string>;
  updatedCells: Set<string>;
}

/** Replays `frames[0..frameIndex]` into the discovered/expanded sets a frontend would track. */
export function computeFrameSets(frames: FrameDelta[], frameIndex: number, start: Cell): FrameSets {
  const visited = new Set<string>();
  const frontier = new Set<string>([cellKey(start)]);
  let updatedCells = new Set<string>();

  const limit = Math.min(frameIndex, frames.length - 1);
  for (let i = 0; i <= limit; i++) {
    const frame = frames[i];
    const poppedKey = cellKey(frame.popped);
    visited.add(poppedKey);
    frontier.delete(poppedKey);
    for (const cell of frame.frontier_added) frontier.add(cellKey(cell));
    updatedCells = i === limit ? new Set(frame.updated.map(cellKey)) : new Set();
  }

  return { visited, frontier, updatedCells };
}
