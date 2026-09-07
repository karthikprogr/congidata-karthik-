import requests, io
import pandas as pd, numpy as np

BASE = "http://localhost:8000/api"
r = requests.post(f"{BASE}/auth/login", json={"email":"rudraadmin@gmail.com","password":"adminrudra@1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

df = pd.DataFrame({
    "category": ["A","B","C","D","E"]*20,
    "region":   ["North","South","East","West","Central"]*20,
    "sales":    np.random.uniform(100,1000,100),
    "profit":   np.random.uniform(10,200,100),
    "quantity": np.random.randint(1,50,100).astype(float),
})
buf = io.BytesIO(); df.to_csv(buf, index=False); buf.seek(0)
requests.post(f"{BASE}/data/upload", files={"file": ("test.csv", buf, "text/csv")}, headers=headers)

tests = [
    # Data
    ("GET", "/data/info", None),
    ("GET", "/data/preview?n=10", None),
    ("GET", "/data/stats", None),
    ("GET", "/data/doctor", None),
    ("GET", "/data/datasets", None),
    # Analytics
    ("GET", "/analytics/stats", None),
    ("GET", "/analytics/anomaly", None),
    ("GET", "/analytics/timeseries?col=sales", None),
    # Viz
    ("GET", "/viz/overview", None),
    ("POST", "/viz/custom", {"chart_type":"bar","x_col":"category","y_col":"sales","title":"Test"}),
    # Reports
    ("GET", "/reports/profile", None),
    ("GET", "/reports/schedule", None),
    ("GET", "/reports/export/csv", None),
    # Workspaces
    ("GET", "/workspaces", None),
    ("POST", "/workspaces", {"name":"TestWS","description":"test"}),
    # Profile
    ("GET", "/profile/me", None),
    ("GET", "/profile/notifications", None),
    # Admin
    ("GET", "/admin/users", None),
    ("GET", "/admin/system", None),
    # Alerts
    ("GET", "/alerts/rules", None),
    ("GET", "/alerts/history", None),
    # ML
    ("GET", "/ml/explain", None),
    # Config/SMTP
    ("POST", "/config/smtp/test", None),
    # Ingest
    ("GET", "/ingest/keys", None),
    # Actions
    ("GET", "/actions/list", None),
    # Maps
    ("GET", "/maps/columns", None),
    # Catalog
    ("GET", "/catalog/tables", None),
    # Roadmap
    ("GET", "/roadmap/items", None),
]

passed, failed = [], []
for method, path, body in tests:
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=headers, timeout=10)
        else:
            r = requests.post(f"{BASE}{path}", json=body or {}, headers=headers, timeout=10)
        if r.status_code < 400:
            passed.append(f"{method} {path}")
        else:
            failed.append((f"{method} {path}", r.status_code))
    except Exception as e:
        failed.append((f"{method} {path}", str(e)[:40]))

print(f"PASSED: {len(passed)}/{len(tests)}")
if failed:
    print("FAILED:")
    for k,v in failed:
        print(f"  {k}: {v}")
