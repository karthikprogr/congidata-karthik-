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

# Test only the charts most likely to fail (complex ones)
charts = [
    ("SHAP","shap"),("ROC Curve","roc curve"),("Precision Recall","precision recall"),
    ("Confusion Matrix","confusion matrix"),("Learning Curve","learning curve"),
    ("Monte Carlo","monte carlo"),("Drawdown","drawdown"),
    ("Efficient Frontier","efficient frontier"),("Gain Chart","gain chart"),
    ("Faceted Heatmap","faceted heatmap"),("Animated Bubble","animated bubble"),
    ("Sankey Heatmap","sankey heatmap"),("Narrative","narrative"),("Storyboard","storyboard"),
    ("Balanced Scorecard","balanced scorecard"),("Strategy Map","strategy map"),
    ("Sensitivity Analysis","sensitivity analysis"),("Linked Brushing","linked brushing"),
    ("Animated Network","animated network"),("Community Graph","community graph"),
    ("Scalogram","scalogram"),("Coherence","coherence"),("ACF Heatmap","autocorrelation heatmap"),
    ("Faceted Grid","faceted grid"),("User Journey","user journey"),
    ("Waffle","waffle"),("Icicle","icicle"),("Surface","surface"),
    ("Cluster Heatmap","cluster heatmap"),("Dendrogram","dendrogram"),
]

failed = []
for name, ct in charts:
    try:
        r = requests.post(f"{BASE}/viz/custom",
            json={"chart_type":ct,"x_col":"category","y_col":"sales","title":name},
            headers=headers, timeout=15)
        if r.status_code != 200:
            try: err = r.json().get("detail","?")[:100]
            except: err = r.text[:100]
            failed.append((name, err))
        else:
            print(f"OK  {name}")
    except Exception as e:
        failed.append((name, str(e)[:60]))

print(f"\nFailed ({len(failed)}):")
for n,e in failed:
    print(f"  FAIL {n}: {e}")
