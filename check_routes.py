import requests
BASE = "http://localhost:8000/api"
r = requests.post(f"{BASE}/auth/login", json={"email":"rudraadmin@gmail.com","password":"adminrudra@1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check correct paths
tests = [
    ("GET", "/analytics/describe"),
    ("GET", "/analytics/correlation"),
    ("GET", "/analytics/outlier"),
    ("GET", "/admin/users"),
    ("GET", "/admin/system"),
    ("GET", "/alerts/list"),
    ("GET", "/alerts/"),
    ("GET", "/ml/models"),
    ("POST", "/config/smtp/test"),
    ("GET", "/config/smtp"),
    ("GET", "/ingest/keys"),
    ("POST", "/analyst/query"),
    ("GET", "/analyst/"),
]

for method, path in tests:
    if method == "GET":
        r = requests.get(f"{BASE}{path}", headers=headers, timeout=5)
    else:
        r = requests.post(f"{BASE}{path}", json={}, headers=headers, timeout=5)
    print(f"{method} {path}: {r.status_code}")
