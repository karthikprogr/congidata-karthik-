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
    "date":     pd.date_range("2023-01-01", periods=100, freq="D").astype(str).tolist(),
})
buf = io.BytesIO(); df.to_csv(buf, index=False); buf.seek(0)
requests.post(f"{BASE}/data/upload", files={"file": ("test.csv", buf, "text/csv")}, headers=headers)

ALL_CHARTS = [
    ("Bar","bar"),("Line","line"),("Scatter","scatter"),("Pie","pie"),
    ("Histogram","histogram"),("Box","box"),("Heatmap","heatmap"),("Area","area"),
    ("Treemap","treemap"),("Radar","radar"),("Waterfall","waterfall"),
    ("Stacked Bar","stacked_bar"),("Stacked Area","stacked_area"),
    ("Bubble","bubble"),("Violin","violin"),("Funnel","funnel"),("Sunburst","sunburst"),
    ("Marimekko","marimekko"),("Table with Charts","table_sparkline"),("3D Area","3d_area"),
    ("Sankey","sankey"),("Beeswarm","beeswarm"),("Bullet","bullet"),
    ("Small Multiples","small multiples"),("Rose","rose"),("Time Series","timeseries"),
    ("Infographic","infographic"),("Network Graph","network"),("Gantt","gantt"),
    ("Parallel Coordinates","parallel coordinates"),("Chord","chord"),("Hexbin","hexbin"),
    ("Ridgeline","ridgeline"),("Streamgraph","streamgraph"),("Dendrogram","dendrogram"),
    ("Voronoi","voronoi"),("Uncertainty","uncertainty"),("PCA","pca"),
    ("Choropleth","choropleth"),("Event Stream","event stream"),
    ("Q-Q Plot","qq plot"),("ECDF","ecdf"),("KDE","kde"),("Rug Plot","rug plot"),
    ("Dot Plot","dot plot"),("Lollipop","lollipop"),("Slope Chart","slope chart"),
    ("Dumbbell","dumbbell"),("Diverging Bar","diverging bar"),
    ("Candlestick","candlestick"),("Pair Plot","pair plot"),("Donut","donut"),
    ("Waffle","waffle"),("Pyramid","pyramid"),("100% Stacked","100% stacked"),
    ("ACF","acf"),("Contour","contour"),("Run Chart","run chart"),("Control Chart","control chart"),
    ("Polar Line","polar line"),("Radial Bar","radial bar"),("Circle Packing","circle packing"),
    ("Arc Diagram","arc diagram"),("Spiral","spiral"),("Funnel Area","funnel area"),
    ("Correlogram","correlogram"),("Cluster Heatmap","cluster heatmap"),
    ("Radial Heatmap","radial heatmap"),("Faceted Heatmap","faceted heatmap"),
    ("Icicle","icicle"),("Surface","surface"),
    ("Word Frequency","word frequency"),("Horizon","horizon"),("Animated Bubble","animated bubble"),
    ("PDF Plot","pdf plot"),("Kaplan-Meier","kaplan meier"),("Periodogram","periodogram"),
    ("Adjacency Matrix","adjacency matrix"),("Pareto","pareto frontier"),
    ("Manhattan","manhattan plot"),("Volcano","volcano plot"),
    ("Dual Axis","dual axis"),("KPI Traffic Light","kpi traffic light"),
    ("Efficient Frontier","efficient frontier"),("Gain Chart","gain chart"),
    ("Delaunay","delaunay"),("Convex Hull","convex hull"),
    ("Cross Correlation","cross correlation"),("PACF","pacf"),("Log Heatmap","log heatmap"),
    ("Variance Analysis","variance analysis"),("Composite","composite"),("3D Volume","3d scatter volume"),
    ("Nelson-Aalen","nelson aalen"),("Hazard Function","hazard function"),
    ("ACF Heatmap","autocorrelation heatmap"),("Scalogram","scalogram"),("Coherence","coherence"),
    ("Community Graph","community graph"),("Attack Graph","attack graph"),
    ("Animated Network","animated network"),("Linked Brushing","linked brushing"),
    ("Sensitivity Analysis","sensitivity analysis"),("Strategy Map","strategy map"),
    ("Balanced Scorecard","balanced scorecard"),
    ("Alpha Shape","alpha shape"),("Faceted Grid","faceted grid"),("User Journey","user journey"),
    ("Sankey Heatmap","sankey heatmap"),("Narrative","narrative"),("Storyboard","storyboard"),
    ("PDF Plot","pdf plot"),("Kaplan-Meier","kaplan meier"),("Periodogram","periodogram"),
    ("Dual Axis","dual axis"),("KPI Traffic Light","kpi traffic light"),
    ("Delaunay","delaunay"),("Convex Hull","convex hull"),
    ("Cross Correlation","cross correlation"),("PACF","pacf"),("Log Heatmap","log heatmap"),
    ("Variance Analysis","variance analysis"),("Composite","composite"),
    ("Nelson-Aalen","nelson aalen"),("Hazard Function","hazard function"),
    ("ACF Heatmap","autocorrelation heatmap"),("Scalogram","scalogram"),("Coherence","coherence"),
]

# Deduplicate
seen = set()
charts = [(n,c) for n,c in ALL_CHARTS if c not in seen and not seen.add(c)]

passed, failed = [], []
for name, ct in charts:
    try:
        r = requests.post(f"{BASE}/viz/custom",
            json={"chart_type":ct,"x_col":"category","y_col":"sales","title":name},
            headers=headers, timeout=20)
        if r.status_code == 200:
            passed.append(name)
        else:
            try: err = r.json().get("detail","?")[:80]
            except: err = r.text[:80]
            failed.append((name, ct, err))
    except Exception as e:
        failed.append((name, ct, str(e)[:60]))

print(f"PASSED: {len(passed)}/{len(charts)}")
print(f"FAILED: {len(failed)}/{len(charts)}")
if failed:
    print("\nFailed:")
    for n,c,e in failed:
        print(f"  {n} ({c}): {e}")
