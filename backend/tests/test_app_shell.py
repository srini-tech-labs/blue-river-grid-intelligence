from fastapi.testclient import TestClient

from backend import main


def test_health_is_static():
    client = TestClient(main.app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "app": "Blue River Grid Intelligence", "synthetic_environment": True}


def test_unknown_api_route_is_clean_json():
    r = TestClient(main.app).get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_spa_fallback_serves_index(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>app</html>")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    r = TestClient(main.app).get("/assets-360/TX-184")
    assert r.status_code == 200 and "app" in r.text


def test_spa_does_not_escape_static_dir(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>app</html>")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    r = TestClient(main.app).get("/../../etc/passwd")
    assert "root:" not in r.text
