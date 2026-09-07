import requests
BASE = "http://localhost:8000/api"
r = requests.post(f"{BASE}/auth/login", json={"email":"rudraadmin@gmail.com","password":"adminrudra@1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

tests = [
    ("GET", "/ingest/streams"),
    ("GET", "/actions"),
    ("GET", "/catalog/columns"),
    ("GET", "/roadmap/features"),
    ("GET", "/alerts/rules"),
    ("GET", "/alerts/history"),
    ("POST", "/config/smtp/test"),
]

for method, path in tests:
    if method == "GET":
        r = requests.get(f"{BASE}{path}", headers=headers, timeout=10)
    else:
        r = requests.post(f"{BASE}{path}", json={}, headers=headers, timeout=10)
    status = "OK" if r.status_code < 400 else "FAIL"
    print(f"{status} {method} {path}: {r.status_code}")
