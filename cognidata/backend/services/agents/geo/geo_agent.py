"""
Geo Intelligence Agent — 15 cities, 5-phase ML pipeline, real-time simulation.
"""
import random
import time
import threading
import numpy as np
from collections import deque
from datetime import datetime

CITIES = [
    # India
    {"name": "Mumbai",    "lat": 19.076, "lon": 72.877, "region": "West India"},
    {"name": "Delhi",     "lat": 28.704, "lon": 77.102, "region": "North India"},
    {"name": "Bangalore", "lat": 12.972, "lon": 77.594, "region": "South India"},
    {"name": "Chennai",   "lat": 13.083, "lon": 80.270, "region": "South India"},
    {"name": "Hyderabad", "lat": 17.385, "lon": 78.487, "region": "South India"},
    {"name": "Kolkata",   "lat": 22.573, "lon": 88.364, "region": "East India"},
    {"name": "Pune",      "lat": 18.520, "lon": 73.856, "region": "West India"},
    {"name": "Ahmedabad", "lat": 23.023, "lon": 72.572, "region": "West India"},
    {"name": "Jaipur",    "lat": 26.912, "lon": 75.787, "region": "North India"},
    {"name": "Surat",     "lat": 21.170, "lon": 72.831, "region": "West India"},
    # Global
    {"name": "New York",  "lat": 40.713, "lon": -74.006, "region": "Americas"},
    {"name": "London",    "lat": 51.508, "lon": -0.128,  "region": "Europe"},
    {"name": "Tokyo",     "lat": 35.689, "lon": 139.692, "region": "Asia Pacific"},
    {"name": "Sydney",    "lat": -33.869, "lon": 151.209, "region": "Asia Pacific"},
    {"name": "Dubai",     "lat": 25.205, "lon": 55.271,  "region": "Middle East"},
]

HISTORY_SIZE = 300
_history: dict[str, deque] = {c["name"]: deque(maxlen=HISTORY_SIZE) for c in CITIES}
_current: dict[str, dict] = {}
_lock = threading.Lock()
_running = False
_thread = None


def _generate_tick() -> dict[str, dict]:
    """Generate one tick of simulated city data."""
    tick = {}
    for city in CITIES:
        name = city["name"]
        prev = _current.get(name, {})
        base_sales = prev.get("sales", random.uniform(8000, 15000))
        sales = max(1000, base_sales + random.gauss(0, 500))
        tick[name] = {
            **city,
            "sales":       round(sales, 2),
            "satisfaction": round(random.uniform(3.0, 5.0), 2),
            "orders":      random.randint(50, 500),
            "timestamp":   datetime.utcnow().isoformat(),
        }
    return tick


def _run_pipeline(data: dict) -> dict:
    """5-phase ML pipeline on current city data."""
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    from sklearn.linear_model import LinearRegression
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    df = pd.DataFrame(list(data.values()))
    result = data.copy()

    # Phase 1: Anomaly detection
    try:
        sales = df[["sales"]].values
        iso = IsolationForest(contamination=0.15, random_state=42)
        labels = iso.fit_predict(sales)
        for i, city in enumerate(df["name"]):
            result[city]["anomaly"] = bool(labels[i] == -1)
    except Exception:
        pass

    # Phase 2: Forecasting (linear trend from history)
    try:
        for city_name in df["name"]:
            hist = list(_history[city_name])
            if len(hist) >= 5:
                X = np.arange(len(hist)).reshape(-1, 1)
                y = np.array([h["sales"] for h in hist])
                model = LinearRegression().fit(X, y)
                next_pred = model.predict([[len(hist)]])[0]
                result[city_name]["forecast"] = round(float(next_pred), 2)
            else:
                result[city_name]["forecast"] = result[city_name]["sales"]
    except Exception:
        pass

    # Phase 3: Segmentation
    try:
        if len(df) >= 3:
            scaler = StandardScaler()
            features = scaler.fit_transform(df[["sales", "satisfaction", "orders"]])
            km = KMeans(n_clusters=3, random_state=42, n_init=10)
            clusters = km.fit_predict(features)
            # Map clusters to tiers by mean sales
            cluster_means = {c: df.iloc[clusters == c]["sales"].mean() for c in range(3)}
            sorted_clusters = sorted(cluster_means, key=cluster_means.get, reverse=True)
            tier_map = {sorted_clusters[0]: "High", sorted_clusters[1]: "Mid", sorted_clusters[2]: "Low"}
            for i, city_name in enumerate(df["name"]):
                result[city_name]["tier"] = tier_map[clusters[i]]
    except Exception:
        pass

    return result


def start_simulation():
    """Start background simulation thread."""
    global _running, _thread
    if _running:
        return
    _running = True

    def _loop():
        while _running:
            tick = _generate_tick()
            processed = _run_pipeline(tick)
            with _lock:
                for name, data in processed.items():
                    _current[name] = data
                    _history[name].append(data)
            time.sleep(5)  # was 2s — reduced CPU load

    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()


def stop_simulation():
    global _running
    _running = False


def get_current() -> dict:
    with _lock:
        return dict(_current)


def get_history(city: str, n: int = 60) -> list:
    with _lock:
        return list(_history.get(city, []))[-n:]


def get_all_history(n: int = 60) -> dict:
    with _lock:
        return {city: list(hist)[-n:] for city, hist in _history.items()}


# Auto-start is handled by background_services.py — do NOT auto-start on import
# to avoid "No module named agents" errors before sys.path is configured.
# Call start_simulation() explicitly after setting up the path.
