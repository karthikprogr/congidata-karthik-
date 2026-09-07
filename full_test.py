import requests, io, json
import pandas as pd, numpy as np

BASE = "http://localhost:8000/api"

def login():
    r = requests.post(f"{BASE}/auth/login", json={"email":"rudraadmin@gmail.com","password":"adminrudra@1234"})
    return r.json()["access_token"]

def h(token):
    return {"Authorization": f"Bearer {token}"}

token = login()
headers = h(token)
print("=== LOGIN OK ===")

# Upload dataset
df = pd.DataFrame({
    "category": ["A","B","C","D","E"]*20,
    "region":   ["North","South","East","West","Central"]*20,
    "sales":    np.random.uniform(100,1000,100),
    "profit":   np.random.uniform(10,200,100),
    "quantity": np.random.randint(1,50,100).astype(float),
})
buf = io.BytesIO(); df.to_csv(buf, index=False); buf.seek(0)
r = requests.post(f"{BASE}/data/upload", files={"file": ("test.csv", buf, "text/csv")}, headers=headers)
print(f"Upload: {r.status_code}")

results = {}

# 1. DATA endpoints
for ep in ["/data/info", "/data/preview?n=10", "/data/stats", "/data/doctor"]:
    r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
    results[ep] = r.status_code

# 2. ANALYTICS
for ep in ["/analytics/summary", "/analytics/correlations", "/analytics/outliers"]:
    r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
    results[ep] = r.status_code

# 3. VIZ overview
r = requests.get(f"{BASE}/viz/overview", headers=headers, timeout=15)
results["/viz/overview"] = r.status_code

# 4. REPORTS
for ep in ["/reports/profile", "/reports/schedule", "/reports/export/csv", "/reports/export/json"]:
    r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
    results[ep] = r.status_code

# 5. WORKSPACE
r = requests.post(f"{BASE}/workspaces", json={"name":"Test WS","description":"test"}, headers=headers, timeout=10)
ws_id = r.json().get("id") if r.status_code == 200 else None
results["/workspaces POST"] = r.status_code
r = requests.get(f"{BASE}/workspaces", headers=headers, timeout=10)
results["/workspaces GET"] = r.status_code
if ws_id:
    r = requests.get(f"{BASE}/workspaces/{ws_id}", headers=headers, timeout=10)
    results[f"/workspaces/{ws_id}"] = r.status_code
    r = requests.get(f"{BASE}/workspaces/{ws_id}/members", headers=headers, timeout=10)
    results[f"/workspaces/{ws_id}/members"] = r.status_code

# 6. PROFILE
for ep in ["/profile/me", "/profile/notifications", "/profile/activity"]:
    r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
    results[ep] = r.status_code

# 7. ADMIN
for ep in ["/admin/users", "/admin/stats", "/admin/logs"]:
    r = requests.get(f"{BASE}{ep}", headers=headers, timeout=10)
    results[ep] = r.status_code

# 8. ALERTS
r = requests.get(f"{BASE}/alerts", headers=headers, timeout=10)
results["/alerts GET"] = r.status_code

# 9. MAPS
r = requests.get(f"{BASE}/maps/columns", headers=headers, timeout=10)
results["/maps/columns"] = r.status_code

# 10. ML
r = requests.get(f"{BASE}/ml/status", headers=headers, timeout=10)
results["/ml/status"] = r.status_code

# 11. SMTP test
r = requests.post(f"{BASE}/config/test-email", headers=headers, timeout=15)
results["/config/test-email"] = r.status_code

# 12. DATASETS
r = requests.get(f"{BASE}/data/datasets", headers=headers, timeout=10)
results["/data/datasets"] = r.status_code

# 13. INGEST
r = requests.get(f"{BASE}/ingest/status", headers=headers, timeout=10)
results["/ingest/status"] = r.status_code

# 14. ACTIONS
r = requests.get(f"{BASE}/actions", headers=headers, timeout=10)
results["/actions GET"] = r.status_code

# 15. ANALYST
r = requests.post(f"{BASE}/analyst/insights", json={"question":"What are the top categories?"}, headers=headers, timeout=20)
results["/analyst/insights"] = r.status_code

print("\n=== FEATURE TEST RESULTS ===")
passed = sum(1 for v in results.values() if v < 400)
failed = [(k,v) for k,v in results.items() if v >= 400]
print(f"PASSED: {passed}/{len(results)}")
if failed:
    print("FAILED:")
    for k,v in failed:
        print(f"  {k}: HTTP {v}")
