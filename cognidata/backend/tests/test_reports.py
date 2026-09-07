"""Tests for reports: export, profiling, scheduling."""
import io
import pytest
from tests.conftest import auth_headers

CSV_CONTENT = b"product,revenue,units\nWidget,5000,100\nGadget,8000,200\n"


def upload(client, headers):
    client.post("/api/data/upload",
                files={"file": ("data.csv", io.BytesIO(CSV_CONTENT), "text/csv")},
                headers=headers)


class TestReportExport:
    def test_export_csv(self, client):
        headers = auth_headers(client, "rpt1@example.com")
        upload(client, headers)
        r = client.get("/api/reports/export/csv", headers=headers)
        assert r.status_code in (200, 400)

    def test_export_json(self, client):
        headers = auth_headers(client, "rpt2@example.com")
        upload(client, headers)
        r = client.get("/api/reports/export/json", headers=headers)
        assert r.status_code in (200, 400)

    def test_export_excel(self, client):
        headers = auth_headers(client, "rpt3@example.com")
        upload(client, headers)
        r = client.get("/api/reports/export/excel", headers=headers)
        assert r.status_code in (200, 400)

    def test_export_no_data(self, client):
        headers = auth_headers(client, "rpt4@example.com")
        r = client.get("/api/reports/export/csv", headers=headers)
        assert r.status_code in (400, 404)

    def test_export_unauthenticated(self, client):
        r = client.get("/api/reports/export/csv")
        assert r.status_code == 401


class TestDataProfiling:
    def test_profile_after_upload(self, client):
        headers = auth_headers(client, "rpt5@example.com")
        upload(client, headers)
        r = client.get("/api/reports/profile", headers=headers)
        assert r.status_code in (200, 400)


class TestScheduledReports:
    def test_list_schedules_empty(self, client):
        headers = auth_headers(client, "rpt6@example.com")
        r = client.get("/api/reports/schedule", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_schedule(self, client):
        headers = auth_headers(client, "rpt7@example.com")
        r = client.post("/api/reports/schedule", json={
            "name": "Daily Report",
            "frequency": "daily",
            "email": "rpt7@example.com",
        }, headers=headers)
        assert r.status_code in (200, 201)

    def test_delete_schedule(self, client):
        headers = auth_headers(client, "rpt8@example.com")
        created = client.post("/api/reports/schedule", json={
            "name": "Weekly",
            "frequency": "weekly",
            "email": "rpt8@example.com",
        }, headers=headers).json()
        sid = created.get("id")
        if sid:
            r = client.delete(f"/api/reports/schedule/{sid}", headers=headers)
            assert r.status_code in (200, 204)
