"""Tests for Deep Analyst endpoints (Option A features)."""
import io
from tests.conftest import auth_headers

CSV = b"product,revenue,units,region\nWidget,5000,100,APAC\nGadget,8000,200,EU\nTool,3000,50,US\n"


def upload(client, headers):
    client.post("/api/data/upload",
                files={"file": ("data.csv", io.BytesIO(CSV), "text/csv")},
                headers=headers)


class TestDeepReason:
    def test_reason_no_dataset(self, client):
        headers = auth_headers(client, "an1@example.com")
        r = client.post("/api/analyst/reason",
                        json={"question": "What is the top product?"},
                        headers=headers)
        assert r.status_code == 400

    def test_reason_requires_auth(self, client):
        r = client.post("/api/analyst/reason", json={"question": "test"})
        assert r.status_code == 401


class TestAutoInsights:
    def test_auto_insights_no_dataset(self, client):
        headers = auth_headers(client, "an2@example.com")
        r = client.post("/api/analyst/auto-insights",
                        json={"focus": "general", "max_insights": 3},
                        headers=headers)
        assert r.status_code == 400

    def test_auto_insights_requires_auth(self, client):
        r = client.post("/api/analyst/auto-insights", json={"focus": "general"})
        assert r.status_code == 401

    def test_auto_insights_valid_focus_options(self, client):
        headers = auth_headers(client, "an3@example.com")
        upload(client, headers)
        for focus in ["general", "anomaly", "trend", "comparison", "decision"]:
            r = client.post("/api/analyst/auto-insights",
                            json={"focus": focus, "max_insights": 2},
                            headers=headers)
            # Will fail with 500 if no API key, but should not be 401/422
            assert r.status_code in (200, 500)


class TestDecisionEngine:
    def test_decide_no_dataset(self, client):
        headers = auth_headers(client, "an4@example.com")
        r = client.post("/api/analyst/decide",
                        json={"goal": "increase revenue", "constraints": ""},
                        headers=headers)
        assert r.status_code == 400

    def test_decide_requires_auth(self, client):
        r = client.post("/api/analyst/decide", json={"goal": "test"})
        assert r.status_code == 401


class TestNarrate:
    def test_narrate_no_dataset(self, client):
        headers = auth_headers(client, "an5@example.com")
        r = client.post("/api/analyst/narrate", headers=headers)
        assert r.status_code == 400

    def test_narrate_requires_auth(self, client):
        r = client.post("/api/analyst/narrate")
        assert r.status_code == 401
