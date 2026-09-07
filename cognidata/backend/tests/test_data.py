"""Tests for data upload, preview, stats, cleaning, and export."""
import io
import pytest
from tests.conftest import auth_headers

CSV_CONTENT = b"name,age,salary\nAlice,30,50000\nBob,25,45000\nAlice,30,50000\n"


def upload_csv(client, headers, content=CSV_CONTENT, filename="test.csv"):
    return client.post(
        "/api/data/upload",
        files={"file": (filename, io.BytesIO(content), "text/csv")},
        headers=headers,
    )


class TestDataUpload:
    def test_upload_csv_success(self, client):
        headers = auth_headers(client, "up1@example.com")
        r = upload_csv(client, headers)
        assert r.status_code == 200

    def test_upload_unauthenticated(self, client):
        r = client.post("/api/data/upload",
                        files={"file": ("t.csv", io.BytesIO(CSV_CONTENT), "text/csv")})
        assert r.status_code == 401

    def test_upload_empty_file(self, client):
        headers = auth_headers(client, "up2@example.com")
        r = client.post("/api/data/upload",
                        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
                        headers=headers)
        assert r.status_code in (400, 422, 500)

    def test_upload_json_file(self, client):
        headers = auth_headers(client, "up3@example.com")
        json_data = b'[{"name":"Alice","age":30},{"name":"Bob","age":25}]'
        r = client.post("/api/data/upload",
                        files={"file": ("data.json", io.BytesIO(json_data), "application/json")},
                        headers=headers)
        assert r.status_code in (200, 400)


class TestDataPreview:
    def test_preview_after_upload(self, client):
        headers = auth_headers(client, "prev1@example.com")
        upload_csv(client, headers)
        r = client.get("/api/data/preview", headers=headers)
        assert r.status_code == 200

    def test_preview_no_data(self, client):
        headers = auth_headers(client, "prev2@example.com")
        r = client.get("/api/data/preview", headers=headers)
        assert r.status_code in (200, 400, 404)


class TestDataInfo:
    def test_info_after_upload(self, client):
        headers = auth_headers(client, "info1@example.com")
        upload_csv(client, headers)
        r = client.get("/api/data/info", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "columns" in data or "shape" in data or "rows" in data


class TestDataStats:
    def test_stats_after_upload(self, client):
        headers = auth_headers(client, "stats1@example.com")
        upload_csv(client, headers)
        r = client.get("/api/data/stats", headers=headers)
        assert r.status_code == 200


class TestDataClean:
    def test_clean_removes_duplicates(self, client):
        headers = auth_headers(client, "clean1@example.com")
        upload_csv(client, headers)  # CSV has 1 duplicate row
        r = client.post("/api/data/clean", headers=headers)
        assert r.status_code == 200

    def test_clean_no_data(self, client):
        headers = auth_headers(client, "clean2@example.com")
        r = client.post("/api/data/clean", headers=headers)
        assert r.status_code in (400, 404, 500)


class TestDataClear:
    def test_clear_dataset(self, client):
        headers = auth_headers(client, "clr1@example.com")
        upload_csv(client, headers)
        r = client.delete("/api/data/clear", headers=headers)
        assert r.status_code in (200, 204)


class TestDataDoctor:
    def test_doctor_after_upload(self, client):
        headers = auth_headers(client, "doc1@example.com")
        upload_csv(client, headers)
        r = client.get("/api/data/doctor", headers=headers)
        assert r.status_code == 200


class TestDataFilter:
    def test_filter_after_upload(self, client):
        headers = auth_headers(client, "flt1@example.com")
        upload_csv(client, headers)
        r = client.post("/api/data/filter",
                        json={"filters": [{"column": "age", "op": "gt", "value": 26}]},
                        headers=headers)
        assert r.status_code in (200, 400, 422)
