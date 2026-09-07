"""
Option D - Developer-First Platform
Admin-only: API docs, SDK examples, rate limiting info.
"""
from fastapi import APIRouter, Depends, Request
from app.core.deps import require_admin

router = APIRouter(prefix="/sdk", tags=["SDK"])


@router.get("/reference")
def api_reference(_: dict = Depends(require_admin)):
    """Full API reference with curl + Python SDK examples."""
    return {
        "version": "1.0",
        "base_url": "http://localhost:8000/api",
        "auth": {
            "type": "Bearer JWT",
            "header": "Authorization: Bearer <token>",
            "obtain": "POST /api/auth/login  -  {access_token}",
            "api_key_header": "X-API-Key: <your-api-key>  (alternative to JWT)",
        },
        "rate_limits": {
            "default": "100 req/min per user",
            "ai_endpoints": "20 req/min per user",
            "ingest": "1000 rows/min per stream",
        },
        "endpoints": _build_reference(),
        "python_sdk": _python_sdk_example(),
        "curl_examples": _curl_examples(),
        "javascript_sdk": _js_sdk_example(),
    }


@router.get("/quickstart")
def quickstart(_: dict = Depends(require_admin)):
    """Quickstart guide - admin only."""
    return {
        "steps": [
            {"step": 1, "title": "Register", "method": "POST", "path": "/api/auth/register",
             "body": {"email": "you@example.com", "password": "yourpassword"}},
            {"step": 2, "title": "Login", "method": "POST", "path": "/api/auth/login",
             "body": {"email": "you@example.com", "password": "yourpassword"},
             "returns": "access_token"},
            {"step": 3, "title": "Upload Data", "method": "POST", "path": "/api/data/upload",
             "note": "multipart/form-data, field name: file"},
            {"step": 4, "title": "Ask AI", "method": "POST", "path": "/api/ai/query",
             "body": {"question": "What are the top 5 products by revenue?"}},
            {"step": 5, "title": "Create Alert", "method": "POST", "path": "/api/alerts/rules",
             "body": {"metric": "revenue", "condition": "lt", "threshold": 1000, "message": "Revenue dropped"}},
            {"step": 6, "title": "Create Action (webhook)", "method": "POST", "path": "/api/actions",
             "body": {"name": "Notify Slack", "trigger": "alert", "type": "slack",
                      "url": "https://hooks.slack.com/services/..."}},
            {"step": 7, "title": "Stream Live Data", "method": "POST", "path": "/api/ingest/streams",
             "body": {"name": "my-stream"},
             "then": "POST /api/ingest/{stream_id} with X-Stream-Key header"},
        ]
    }


@router.get("/webhooks")
def webhook_guide(_: dict = Depends(require_admin)):
    """Guide for setting up webhook actions."""
    return {
        "overview": "COGNIDATA can POST to any URL when an alert fires.",
        "setup": [
            "1. Create an alert rule: POST /api/alerts/rules",
            "2. Create a webhook action: POST /api/actions  {type: 'webhook', url: '...', trigger: 'alert'}",
            "3. Optionally bind to a specific rule via rule_id",
            "4. When the alert fires, COGNIDATA POSTs the alert payload to your URL",
        ],
        "payload_example": {
            "source": "cognidata",
            "action": "My Webhook",
            "timestamp": "2026-04-02T10:00:00Z",
            "metric": "revenue",
            "value": 850,
            "threshold": 1000,
            "condition": "lt",
            "message": "Revenue dropped below threshold",
            "level": "critical",
        },
        "payload_template": "Use {metric}, {value}, {threshold}, {message} as placeholders in custom templates.",
        "slack_setup": "Create an Incoming Webhook at api.slack.com/apps, use the URL as action url with type='slack'",
    }


def _build_reference():
    return {
        "auth": [
            {"method": "POST", "path": "/auth/register", "body": {"email": "str", "password": "str"}},
            {"method": "POST", "path": "/auth/login", "body": {"email": "str", "password": "str"}, "returns": "access_token"},
            {"method": "POST", "path": "/auth/logout"},
            {"method": "POST", "path": "/auth/2fa/setup"},
            {"method": "POST", "path": "/auth/change-password", "body": {"old_password": "str", "new_password": "str"}},
        ],
        "data": [
            {"method": "POST", "path": "/data/upload", "note": "multipart/form-data file field"},
            {"method": "GET",  "path": "/data/preview"},
            {"method": "GET",  "path": "/data/stats"},
            {"method": "POST", "path": "/data/clean"},
            {"method": "GET",  "path": "/data/doctor"},
        ],
        "ai": [
            {"method": "POST", "path": "/ai/query", "body": {"question": "str"}},
            {"method": "POST", "path": "/ai/chat", "body": {"query": "str"}},
            {"method": "POST", "path": "/ai/vision", "note": "multipart with image file + question"},
        ],
        "alerts": [
            {"method": "GET",  "path": "/alerts/rules"},
            {"method": "POST", "path": "/alerts/rules", "body": {"metric": "str", "condition": "gt|lt|eq|gte|lte", "threshold": "float"}},
            {"method": "POST", "path": "/alerts/check", "body": {"metric_name": "value"}},
            {"method": "GET",  "path": "/alerts/history"},
        ],
        "actions": [
            {"method": "GET",  "path": "/actions"},
            {"method": "POST", "path": "/actions", "body": {"name": "str", "type": "webhook|slack|email", "url": "str", "trigger": "alert|manual"}},
            {"method": "POST", "path": "/actions/{id}/run"},
            {"method": "GET",  "path": "/actions/logs"},
        ],
        "ingest": [
            {"method": "POST", "path": "/ingest/streams", "body": {"name": "str"}},
            {"method": "GET",  "path": "/ingest/streams"},
            {"method": "POST", "path": "/ingest/{stream_id}", "auth": "X-Stream-Key header", "body": {"field": "value"}},
            {"method": "POST", "path": "/ingest/streams/{id}/load", "note": "Load stream into active dataset"},
        ],
        "analytics": [
            {"method": "GET",  "path": "/analytics/stats"},
            {"method": "POST", "path": "/analytics/cluster", "body": {"algorithm": "K-Means|DBSCAN|Agglomerative|Gaussian Mixture", "k": 3}},
            {"method": "GET",  "path": "/analytics/anomaly"},
            {"method": "GET",  "path": "/analytics/timeseries", "params": "col=column_name"},
            {"method": "POST", "path": "/analytics/embedding", "body": {"method": "umap|tsne|pca"}},
        ],
        "ml": [
            {"method": "POST", "path": "/ml/train", "body": {"target": "str", "task": "classification|regression"}},
            {"method": "POST", "path": "/ml/predict"},
            {"method": "GET",  "path": "/ml/explain"},
        ],
        "workspaces": [
            {"method": "GET",  "path": "/workspaces"},
            {"method": "POST", "path": "/workspaces", "body": {"name": "str", "description": "str"}},
            {"method": "POST", "path": "/workspaces/{id}/invite", "body": {"email": "str", "role": "viewer|editor"}},
            {"method": "POST", "path": "/workspaces/join", "body": {"token": "str"}},
        ],
    }


def _python_sdk_example():
    return '''
import requests

BASE = "http://localhost:8000/api"

# 1. Login
token = requests.post(f"{BASE}/auth/login",
    json={"email": "you@example.com", "password": "pass"}).json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. Upload CSV
with open("data.csv", "rb") as f:
    requests.post(f"{BASE}/data/upload", files={"file": f}, headers=headers)

# 3. Ask AI
answer = requests.post(f"{BASE}/ai/query",
    json={"question": "What is the average revenue by region?"},
    headers=headers).json()["answer"]

# 4. Create alert
requests.post(f"{BASE}/alerts/rules",
    json={"metric": "revenue", "condition": "lt", "threshold": 1000},
    headers=headers)

# 5. Create webhook action
requests.post(f"{BASE}/actions",
    json={"name": "Slack Alert", "type": "slack",
          "url": "https://hooks.slack.com/...", "trigger": "alert"},
    headers=headers)

# 6. Stream live data
stream = requests.post(f"{BASE}/ingest/streams",
    json={"name": "live-sales"}, headers=headers).json()

requests.post(f"{BASE}/ingest/{stream['stream_id']}",
    json={"revenue": 850, "region": "APAC"},
    headers={"X-Stream-Key": stream["api_key"]})
'''


def _curl_examples():
    return {
        "login": 'curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d \'{"email":"you@example.com","password":"pass"}\'',
        "upload": 'curl -X POST http://localhost:8000/api/data/upload -H "Authorization: Bearer TOKEN" -F "file=@data.csv"',
        "query":  'curl -X POST http://localhost:8000/api/ai/query -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d \'{"question":"top 5 products"}\'',
        "ingest": 'curl -X POST http://localhost:8000/api/ingest/STREAM_ID -H "X-Stream-Key: YOUR_KEY" -H "Content-Type: application/json" -d \'{"revenue":1200,"region":"EU"}\'',
    }


def _js_sdk_example():
    return '''
const BASE = "http://localhost:8000/api";

// Login
const { access_token } = await fetch(`${BASE}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "you@example.com", password: "pass" })
}).then(r => r.json());

const headers = { Authorization: `Bearer ${access_token}`, "Content-Type": "application/json" };

// Ask AI
const { answer } = await fetch(`${BASE}/ai/query`, {
  method: "POST", headers,
  body: JSON.stringify({ question: "What is the trend in sales?" })
}).then(r => r.json());

// Stream live data
const stream = await fetch(`${BASE}/ingest/streams`, {
  method: "POST", headers,
  body: JSON.stringify({ name: "live-feed" })
}).then(r => r.json());

await fetch(`${BASE}/ingest/${stream.stream_id}`, {
  method: "POST",
  headers: { "X-Stream-Key": stream.api_key, "Content-Type": "application/json" },
  body: JSON.stringify({ revenue: 1500, region: "US" })
});
'''
