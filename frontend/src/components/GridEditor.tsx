import { useRef, useState } from "react";
import { getRandomGrid } from "../api/client";
import type { Cell, GridSpec } from "../api/client";
import { EDITOR_TOOLS, cellsEqual, computeCellSize, defaultGrid } from "../types";
import type { EditorTool } from "../types";
import GridCanvas from "./GridCanvas";

interface GridEditorProps {
  grid: GridSpec;
  onChange: (grid: GridSpec) => void;
  disabled?: boolean;
  visited?: Set<string>;
  frontier?: Set<string>;
  updatedCells?: Set<string>;
  path?: Cell[];
}

function clampDimension(value: number): number {
  return Math.max(2, Math.min(60, Math.round(value)));
}

export default function GridEditor({
  grid,
  onChange,
  disabled = false,
  visited,
  frontier,
  updatedCells,
  path,
}: GridEditorProps) {
  const [tool, setTool] = useState<EditorTool>("wall");
  const [rowsInput, setRowsInput] = useState(grid.rows);
  const [colsInput, setColsInput] = useState(grid.cols);
  const [obstacleDensity, setObstacleDensity] = useState(0.2);
  const [terrainDensity, setTerrainDensity] = useState(0.15);
  const [seedText, setSeedText] = useState("");
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [prevGridRows, setPrevGridRows] = useState(grid.rows);
  const [prevGridCols, setPrevGridCols] = useState(grid.cols);
  const paintModeRef = useRef<"add" | "remove">("add");

  if (prevGridRows !== grid.rows || prevGridCols !== grid.cols) {
    setPrevGridRows(grid.rows);
    setPrevGridCols(grid.cols);
    setRowsInput(grid.rows);
    setColsInput(grid.cols);
  }

  function paintCell(cell: Cell, isStart: boolean) {
    if (disabled) return;

    if (tool === "start" || tool === "goal") {
      if (!isStart) return;
      const other = tool === "start" ? grid.goal : grid.start;
      if (cellsEqual(cell, other)) return;
      const walls = grid.walls.filter((w) => !cellsEqual(w, cell));
      const terrain = grid.terrain.filter((t) => !cellsEqual(t, cell));
      onChange(tool === "start" ? { ...grid, walls, terrain, start: cell } : { ...grid, walls, terrain, goal: cell });
      return;
    }

    if (cellsEqual(cell, grid.start) || cellsEqual(cell, grid.goal)) return;

    if (tool === "erase") {
      const walls = grid.walls.filter((w) => !cellsEqual(w, cell));
      const terrain = grid.terrain.filter((t) => !cellsEqual(t, cell));
      if (walls.length !== grid.walls.length || terrain.length !== grid.terrain.length) {
        onChange({ ...grid, walls, terrain });
      }
      return;
    }

    if (tool === "wall") {
      const present = grid.walls.some((w) => cellsEqual(w, cell));
      if (isStart) paintModeRef.current = present ? "remove" : "add";
      if (paintModeRef.current === "remove") {
        if (!present) return;
        onChange({ ...grid, walls: grid.walls.filter((w) => !cellsEqual(w, cell)) });
      } else {
        if (present) return;
        onChange({
          ...grid,
          walls: [...grid.walls, cell],
          terrain: grid.terrain.filter((t) => !cellsEqual(t, cell)),
        });
      }
      return;
    }

    // tool === "terrain"
    const present = grid.terrain.some((t) => cellsEqual(t, cell));
    if (isStart) paintModeRef.current = present ? "remove" : "add";
    if (paintModeRef.current === "remove") {
      if (!present) return;
      onChange({ ...grid, terrain: grid.terrain.filter((t) => !cellsEqual(t, cell)) });
    } else {
      if (present) return;
      onChange({
        ...grid,
        terrain: [...grid.terrain, cell],
        walls: grid.walls.filter((w) => !cellsEqual(w, cell)),
      });
    }
  }

  function applyResize() {
    onChange(defaultGrid(clampDimension(rowsInput), clampDimension(colsInput)));
  }

  function clearObstacles() {
    onChange({ ...grid, walls: [], terrain: [] });
  }

  function toggleDiagonal() {
    onChange({ ...grid, allow_diagonal: !grid.allow_diagonal });
  }

  async function generateRandom() {
    setGenerating(true);
    setGenError(null);
    try {
      const trimmed = seedText.trim();
      const seed = trimmed === "" ? null : Number(trimmed);
      const spec = await getRandomGrid({
        rows: grid.rows,
        cols: grid.cols,
        obstacle_density: obstacleDensity,
        terrain_density: terrainDensity,
        allow_diagonal: grid.allow_diagonal,
        seed,
      });
      onChange(spec);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : "Failed to generate grid");
    } finally {
      setGenerating(false);
    }
  }

  const cellSize = computeCellSize(grid.rows, grid.cols);

  return (
    <div className="grid-editor">
      <div className="grid-editor-toolbar">
        <div className="tool-group">
          {EDITOR_TOOLS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`tool-btn${tool === t.id ? " active" : ""}`}
              onClick={() => setTool(t.id)}
              disabled={disabled}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button type="button" onClick={clearObstacles} disabled={disabled}>
          Clear obstacles
        </button>
        <label className="checkbox">
          <input type="checkbox" checked={grid.allow_diagonal} onChange={toggleDiagonal} disabled={disabled} />
          Allow diagonal movement
        </label>
      </div>

      <GridCanvas
        grid={grid}
        cellSize={cellSize}
        editable={!disabled}
        onPaintCell={paintCell}
        visited={visited}
        frontier={frontier}
        updatedCells={updatedCells}
        path={path}
      />

      <div className="legend">
        <span className="legend-item">
          <span className="swatch swatch-start" /> Start
        </span>
        <span className="legend-item">
          <span className="swatch swatch-goal" /> Goal
        </span>
        <span className="legend-item">
          <span className="swatch swatch-wall" /> Wall
        </span>
        <span className="legend-item">
          <span className="swatch swatch-terrain" /> Terrain (5&times; cost)
        </span>
      </div>

      <div className="grid-editor-controls">
        <div className="control-group">
          <label>
            Rows
            <input
              type="number"
              min={2}
              max={60}
              value={rowsInput}
              onChange={(e) => setRowsInput(Number(e.target.value))}
              disabled={disabled}
            />
          </label>
          <label>
            Cols
            <input
              type="number"
              min={2}
              max={60}
              value={colsInput}
              onChange={(e) => setColsInput(Number(e.target.value))}
              disabled={disabled}
            />
          </label>
          <button type="button" onClick={applyResize} disabled={disabled}>
            Resize
          </button>
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
              disabled={disabled}
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
              disabled={disabled}
            />
          </label>
          <label>
            Seed (optional)
            <input
              type="text"
              inputMode="numeric"
              placeholder="random"
              value={seedText}
              onChange={(e) => setSeedText(e.target.value)}
              disabled={disabled}
            />
          </label>
          <button type="button" onClick={generateRandom} disabled={disabled || generating}>
            {generating ? "Generating…" : "Generate random grid"}
          </button>
        </div>
        {genError && <span className="status error">{genError}</span>}
      </div>
    </div>
  );
}
