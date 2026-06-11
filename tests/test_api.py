from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SMALL_GRID = {
    "rows": 5,
    "cols": 5,
    "start": [0, 0],
    "goal": [0, 4],
    "walls": [[0, 2], [1, 2], [2, 2], [3, 2]],
    "terrain": [],
    "allow_diagonal": False,
}


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_bfs():
    response = client.post("/api/search", json={"grid": SMALL_GRID, "algorithm": "bfs"})
    assert response.status_code == 200

    body = response.json()
    assert body["algorithm"] == "bfs"
    assert body["heuristic"] is None
    assert body["stats"]["found_path"] is True
    assert body["path"][0] == [0, 0]
    assert body["path"][-1] == [0, 4]


def test_search_astar_with_heuristic():
    response = client.post(
        "/api/search",
        json={"grid": SMALL_GRID, "algorithm": "astar", "heuristic": "manhattan"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["algorithm"] == "astar"
    assert body["heuristic"] == "manhattan"
    assert body["stats"]["found_path"] is True


def test_search_astar_without_heuristic_returns_400():
    response = client.post("/api/search", json={"grid": SMALL_GRID, "algorithm": "astar"})
    assert response.status_code == 400


def test_search_bfs_with_heuristic_returns_400():
    response = client.post(
        "/api/search",
        json={"grid": SMALL_GRID, "algorithm": "bfs", "heuristic": "manhattan"},
    )
    assert response.status_code == 400


def test_search_invalid_grid_returns_422():
    bad_grid = {**SMALL_GRID, "walls": [[0, 0]]}  # start sits inside a wall
    response = client.post("/api/search", json={"grid": bad_grid, "algorithm": "bfs"})
    assert response.status_code == 422


def test_compare_runs_each_config():
    response = client.post(
        "/api/compare",
        json={
            "grid": SMALL_GRID,
            "configs": [
                {"algorithm": "bfs"},
                {"algorithm": "astar", "heuristic": "manhattan"},
            ],
        },
    )
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["algorithm"] == "bfs"
    assert results[1]["algorithm"] == "astar"
    assert all(r["stats"]["found_path"] for r in results)


def test_random_grid_basic_shape():
    response = client.post(
        "/api/grid/random",
        json={"rows": 10, "cols": 10, "seed": 1},
    )
    assert response.status_code == 200

    spec = response.json()
    assert spec["rows"] == 10
    assert spec["cols"] == 10
    assert spec["start"] == [0, 0]
    assert spec["goal"] == [9, 9]


def test_random_grid_rejects_oversized_dimensions():
    response = client.post("/api/grid/random", json={"rows": 100, "cols": 10})
    assert response.status_code == 422


def test_benchmark_returns_one_point_per_size_and_config():
    response = client.post(
        "/api/benchmark",
        json={
            "sizes": [5, 6],
            "configs": [{"algorithm": "bfs"}],
            "trials_per_size": 1,
            "seed": 1,
        },
    )
    assert response.status_code == 200

    points = response.json()["points"]
    assert len(points) == 2
    sizes = {p["size"] for p in points}
    assert sizes == {5, 6}
    for point in points:
        assert point["algorithm"] == "bfs"
        assert 0.0 <= point["found_path_rate"] <= 1.0


def test_benchmark_rejects_size_below_minimum():
    response = client.post(
        "/api/benchmark",
        json={"sizes": [1], "configs": [{"algorithm": "bfs"}]},
    )
    assert response.status_code == 422


def test_benchmark_requires_heuristic_for_astar():
    response = client.post(
        "/api/benchmark",
        json={
            "sizes": [5],
            "configs": [{"algorithm": "astar"}],
            "trials_per_size": 1,
            "seed": 1,
        },
    )
    assert response.status_code == 400
