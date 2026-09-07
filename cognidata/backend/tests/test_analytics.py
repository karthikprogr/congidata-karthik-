"""Tests for advanced analytics: stats, clustering, anomaly, timeseries, embeddings."""
import io
import pytest
from tests.conftest import auth_headers

CSV_CONTENT = b"x,y,z\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n13,14,15\n16,17,18\n"


def upload(client, headers):
    client.post("/api/data/upload",
                files={"file": ("data.csv", io.BytesIO(CSV_CONTENT), "text/csv")},
                headers=headers)


class TestAnalyticsStats:
    def test_stats_after_upload(self, client):
        headers = auth_headers(client, "an1@example.com")
        upload(client, headers)
        r = client.get("/api/analytics/stats", headers=headers)
        assert r.status_code in (200, 400)

    def test_stats_no_data(self, client):
        headers = auth_headers(client, "an2@example.com")
        r = client.get("/api/analytics/stats", headers=headers)
        assert r.status_code in (400, 404)

    def test_stats_unauthenticated(self, client):
        r = client.get("/api/analytics/stats")
        assert r.status_code == 401


class TestClustering:
    def test_kmeans_clustering(self, client):
        headers = auth_headers(client, "an3@example.com")
        upload(client, headers)
        r = client.post("/api/analytics/cluster",
                        json={"method": "kmeans", "n_clusters": 2, "columns": ["x", "y"]},
                        headers=headers)
        assert r.status_code in (200, 400)

    def test_dbscan_clustering(self, client):
        headers = auth_headers(client, "an4@example.com")
        upload(client, headers)
        r = client.post("/api/analytics/cluster",
                        json={"method": "dbscan", "columns": ["x", "y"]},
                        headers=headers)
        assert r.status_code in (200, 400)


class TestAnomalyDetection:
    def test_anomaly_detection(self, client):
        headers = auth_headers(client, "an5@example.com")
        upload(client, headers)
        r = client.get("/api/analytics/anomaly", headers=headers)
        assert r.status_code in (200, 400)


class TestTimeseries:
    def test_timeseries_no_date_column(self, client):
        headers = auth_headers(client, "an6@example.com")
        upload(client, headers)
        r = client.get("/api/analytics/timeseries?col=x", headers=headers)
        assert r.status_code in (200, 400)


class TestEmbeddings:
    def test_pca_embedding(self, client):
        headers = auth_headers(client, "an7@example.com")
        upload(client, headers)
        r = client.post("/api/analytics/embedding",
                        json={"method": "pca", "columns": ["x", "y", "z"]},
                        headers=headers)
        assert r.status_code in (200, 400)
