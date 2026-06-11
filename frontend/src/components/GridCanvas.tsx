import { useEffect, useRef } from "react";
import type { Cell, GridSpec } from "../api/client";
import { cellKey } from "../types";

interface GridCanvasProps {
  grid: GridSpec;
  cellSize?: number;
  visited?: Set<string>;
  frontier?: Set<string>;
  updatedCells?: Set<string>;
  path?: Cell[];
  editable?: boolean;
  onPaintCell?: (cell: Cell, isStart: boolean) => void;
}

const COLORS = {
  empty: "#161a23",
  wall: "#3a3f4d",
  terrain: "#7a5230",
  start: "#7cd992",
  goal: "#e57373",
  visited: "rgba(91, 155, 213, 0.45)",
  frontier: "rgba(91, 155, 213, 0.18)",
  updated: "rgba(244, 184, 96, 0.6)",
  path: "#f4b860",
  grid: "#262b38",
};

export default function GridCanvas({
  grid,
  cellSize = 20,
  visited,
  frontier,
  updatedCells,
  path,
  editable = false,
  onPaintCell,
}: GridCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isPaintingRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const width = grid.cols * cellSize;
    const height = grid.rows * cellSize;
    canvas.width = width;
    canvas.height = height;

    const wallSet = new Set(grid.walls.map(cellKey));
    const terrainSet = new Set(grid.terrain.map(cellKey));
    const pathSet = new Set((path ?? []).map(cellKey));

    for (let r = 0; r < grid.rows; r++) {
      for (let c = 0; c < grid.cols; c++) {
        const key = `${r},${c}`;
        const x = c * cellSize;
        const y = r * cellSize;

        let base = COLORS.empty;
        if (wallSet.has(key)) base = COLORS.wall;
        else if (terrainSet.has(key)) base = COLORS.terrain;
        ctx.fillStyle = base;
        ctx.fillRect(x, y, cellSize, cellSize);

        if (visited?.has(key)) {
          ctx.fillStyle = COLORS.visited;
          ctx.fillRect(x, y, cellSize, cellSize);
        } else if (frontier?.has(key)) {
          ctx.fillStyle = COLORS.frontier;
          ctx.fillRect(x, y, cellSize, cellSize);
        }

        if (updatedCells?.has(key)) {
          ctx.fillStyle = COLORS.updated;
          ctx.fillRect(x, y, cellSize, cellSize);
        }

        if (pathSet.has(key)) {
          const pad = cellSize * 0.25;
          ctx.fillStyle = COLORS.path;
          ctx.fillRect(x + pad, y + pad, cellSize - pad * 2, cellSize - pad * 2);
        }
      }
    }

    // Start/goal markers drawn last so they always stay visible.
    const [sr, sc] = grid.start;
    const [gr, gc] = grid.goal;
    ctx.fillStyle = COLORS.start;
    ctx.fillRect(sc * cellSize, sr * cellSize, cellSize, cellSize);
    ctx.fillStyle = COLORS.goal;
    ctx.fillRect(gc * cellSize, gr * cellSize, cellSize, cellSize);

    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let r = 0; r <= grid.rows; r++) {
      ctx.moveTo(0, r * cellSize + 0.5);
      ctx.lineTo(width, r * cellSize + 0.5);
    }
    for (let c = 0; c <= grid.cols; c++) {
      ctx.moveTo(c * cellSize + 0.5, 0);
      ctx.lineTo(c * cellSize + 0.5, height);
    }
    ctx.stroke();
  }, [grid, cellSize, visited, frontier, updatedCells, path]);

  function cellFromEvent(e: React.MouseEvent<HTMLCanvasElement>): Cell | null {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const col = Math.floor(((e.clientX - rect.left) / rect.width) * grid.cols);
    const row = Math.floor(((e.clientY - rect.top) / rect.height) * grid.rows);
    if (row < 0 || row >= grid.rows || col < 0 || col >= grid.cols) return null;
    return [row, col];
  }

  function handleMouseDown(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!editable || !onPaintCell) return;
    isPaintingRef.current = true;
    const cell = cellFromEvent(e);
    if (cell) onPaintCell(cell, true);
  }

  function handleMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!editable || !onPaintCell || !isPaintingRef.current) return;
    const cell = cellFromEvent(e);
    if (cell) onPaintCell(cell, false);
  }

  function handleMouseUp() {
    isPaintingRef.current = false;
  }

  return (
    <canvas
      ref={canvasRef}
      className={`grid-canvas${editable ? " editable" : ""}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    />
  );
}
