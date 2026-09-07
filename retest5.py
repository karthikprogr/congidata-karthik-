import requests
BASE = "http://localhost:8000/api"
r = requests.post(f"{BASE}/auth/login", json={"email":"rudraadmin@gmail.com","password":"adminrudra@1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

charts = [("Time Series","timeseries"),("Chord","chord"),("Ridgeline","ridgeline"),
          ("Streamgraph","streamgraph"),("Voronoi","voronoi")]

for name, ct in charts:
    r2 = requests.post(f"{BASE}/viz/custom", json={"chart_type":ct,"x_col":"category","y_col":"sales","title":name}, headers=headers, timeout=10)
    if r2.status_code == 200:
        print(f"  PASS {name}")
    else:
        try: err = r2.json().get("detail","?")[:80]
        except: err = r2.text[:80]
        print(f"  FAIL {name}: {err}")
