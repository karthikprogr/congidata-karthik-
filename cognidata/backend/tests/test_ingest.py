"""Tests for Live Data Ingest — streams, webhook ingestion."""
from tests.conftest import auth_headers


class TestStreamCRUD:
    def test_list_streams_empty(self, client):
        headers = auth_headers(client, "ing1@example.com")
        r = client.get("/api/ingest/streams", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_stream(self, client):
        headers = auth_headers(client, "ing2@example.com")
        r = client.post("/api/ingest/streams", json={"name": "sales-stream", "max_rows": 5000}, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert "stream_id" in data
        assert "api_key" in data
        assert "endpoint" in data

    def test_get_stream(self, client):
        headers = auth_headers(client, "ing3@example.com")
        created = client.post("/api/ingest/streams", json={"name": "test"}, headers=headers).json()
        r = client.get(f"/api/ingest/streams/{created['stream_id']}", headers=headers)
        assert r.status_code == 200
        assert r.json()["name"] == "test"

    def test_delete_stream(self, client):
        headers = auth_headers(client, "ing4@example.com")
        created = client.post("/api/ingest/streams", json={"name": "del-me"}, headers=headers).json()
        r = client.delete(f"/api/ingest/streams/{created['stream_id']}", headers=headers)
        assert r.status_code == 204

    def test_clear_stream_rows(self, client):
        headers = auth_headers(client, "ing5@example.com")
        created = client.post("/api/ingest/streams", json={"name": "clr"}, headers=headers).json()
        r = client.delete(f"/api/ingest/streams/{created['stream_id']}/rows", headers=headers)
        assert r.status_code == 204

    def test_streams_unauthenticated(self, client):
        r = client.get("/api/ingest/streams")
        assert r.status_code == 401


class TestStreamIngestion:
    def test_ingest_single_row(self, client):
        headers = auth_headers(client, "ing6@example.com")
        created = client.post("/api/ingest/streams", json={"name": "live"}, headers=headers).json()
        stream_id = created["stream_id"]
        api_key = created["api_key"]
        r = client.post(f"/api/ingest/{stream_id}",
                        json={"revenue": 1200, "region": "APAC"},
                        headers={"X-Stream-Key": api_key})
        assert r.status_code == 200
        assert r.json()["appended"] == 1
        assert r.json()["total"] == 1

    def test_ingest_batch_rows(self, client):
        headers = auth_headers(client, "ing7@example.com")
        created = client.post("/api/ingest/streams", json={"name": "batch"}, headers=headers).json()
        stream_id = created["stream_id"]
        api_key = created["api_key"]
        r = client.post(f"/api/ingest/{stream_id}",
                        json=[{"v": 1}, {"v": 2}, {"v": 3}],
                        headers={"X-Stream-Key": api_key})
        assert r.status_code == 200
        assert r.json()["appended"] == 3

    def test_ingest_wrong_key(self, client):
        headers = auth_headers(client, "ing8@example.com")
        created = client.post("/api/ingest/streams", json={"name": "secure"}, headers=headers).json()
        r = client.post(f"/api/ingest/{created['stream_id']}",
                        json={"v": 1},
                        headers={"X-Stream-Key": "wrong-key"})
        assert r.status_code == 401

    def test_ingest_nonexistent_stream(self, client):
        r = client.post("/api/ingest/nonexistent-stream-id",
                        json={"v": 1},
                        headers={"X-Stream-Key": "any"})
        assert r.status_code == 404

    def test_load_stream_as_dataset(self, client):
        headers = auth_headers(client, "ing9@example.com")
        created = client.post("/api/ingest/streams", json={"name": "loadme"}, headers=headers).json()
        stream_id = created["stream_id"]
        api_key = created["api_key"]
        # Add rows
        client.post(f"/api/ingest/{stream_id}",
                    json=[{"x": i, "y": i * 2} for i in range(10)],
                    headers={"X-Stream-Key": api_key})
        # Load as dataset
        r = client.post(f"/api/ingest/streams/{stream_id}/load", headers=headers)
        assert r.status_code == 200
        assert r.json()["rows"] == 10

    def test_load_empty_stream_fails(self, client):
        headers = auth_headers(client, "ing10@example.com")
        created = client.post("/api/ingest/streams", json={"name": "empty"}, headers=headers).json()
        r = client.post(f"/api/ingest/streams/{created['stream_id']}/load", headers=headers)
        assert r.status_code == 400
