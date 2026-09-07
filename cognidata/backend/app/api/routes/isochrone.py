"""
Isochrone / Radius Map routes.

Backend:
  Option A - OSRM (self-hosted):  docker run -p 5000:5000 osrm/osrm-backend
  Option B - Valhalla (self-hosted): docker run -p 8002:8002 valhalla/valhalla
  Option C - Geometric fallback: haversine circles (no server needed)

The endpoint auto-detects which backend is available and falls back gracefully.
"""
import math
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/isochrone", tags=["Isochrone"])


class IsochroneRequest(BaseModel):
    lat: float
    lon: float
    minutes: list[int] = [5, 10, 20]   # travel-time rings
    mode: str = "driving"               # driving | walking | cycling
    osrm_url: str = "http://localhost:5000"
    valhalla_url: str = "http://localhost:8002"


class RadiusRequest(BaseModel):
    lat: float
    lon: float
    radii_km: list[float] = [1.0, 5.0, 10.0]
    label: str = "Center"


# - Geometric helpers -

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _circle_polygon(lat: float, lon: float, radius_km: float, n_pts: int = 64) -> list:
    """Generate a GeoJSON-style polygon ring for a circle."""
    R = 6371.0
    coords = []
    for i in range(n_pts + 1):
        angle = math.radians(i * 360 / n_pts)
        dlat = math.degrees(radius_km / R)
        dlon = math.degrees(radius_km / (R * math.cos(math.radians(lat))))
        coords.append([lon + dlon * math.sin(angle), lat + dlat * math.cos(angle)])
    return coords


def _speed_kmh(mode: str) -> float:
    return {"driving": 50.0, "walking": 5.0, "cycling": 15.0}.get(mode, 50.0)


def _time_to_radius(minutes: int, mode: str) -> float:
    """Approximate radius in km for a given travel time."""
    return _speed_kmh(mode) * minutes / 60.0


# - OSRM isochrone (table API) -

async def _osrm_isochrone(lat: float, lon: float, minutes: list[int],
                           mode: str, base_url: str) -> dict | None:
    """
    Use OSRM /table endpoint to compute reachable area.
    Generates a grid of candidate points, queries travel times, filters by threshold.
    """
    try:
        # Generate candidate grid (5km radius, 0.05- step)
        step = 0.05
        candidates = []
        for dlat in [i * step for i in range(-10, 11)]:
            for dlon in [i * step for i in range(-10, 11)]:
                candidates.append((lat + dlat, lon + dlon))

        # OSRM table: source=origin, destinations=candidates
        coords_str = f"{lon},{lat};" + ";".join(f"{c[1]},{c[0]}" for c in candidates)
        profile = {"driving": "car", "walking": "foot", "cycling": "bike"}.get(mode, "car")
        url = f"{base_url}/table/v1/{profile}/{coords_str}?sources=0&annotations=duration"

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()

        durations = data.get("durations", [[]])[0][1:]  # skip source itself
        if not durations:
            return None

        rings = {}
        for threshold in sorted(minutes, reverse=True):
            threshold_sec = threshold * 60
            reachable = [candidates[i] for i, d in enumerate(durations) if d is not None and d <= threshold_sec]
            if len(reachable) < 3:
                # Fallback to circle
                r_km = _time_to_radius(threshold, mode)
                rings[threshold] = _circle_polygon(lat, lon, r_km)
            else:
                # Convex hull of reachable points
                rings[threshold] = _convex_hull_polygon(reachable)

        return {"method": "osrm", "rings": rings}
    except Exception:
        return None


def _convex_hull_polygon(points: list) -> list:
    """Simple gift-wrapping convex hull."""
    if len(points) < 3:
        return [[p[1], p[0]] for p in points]
    pts = sorted(set(points))
    def cross(O, A, B):
        return (A[0]-O[0])*(B[1]-O[1]) - (A[1]-O[1])*(B[0]-O[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return [[p[1], p[0]] for p in hull] + [[hull[0][1], hull[0][0]]]


# - Valhalla isochrone -

async def _valhalla_isochrone(lat: float, lon: float, minutes: list[int],
                               mode: str, base_url: str) -> dict | None:
    """Use Valhalla /isochrone endpoint directly."""
    try:
        costing = {"driving": "auto", "walking": "pedestrian", "cycling": "bicycle"}.get(mode, "auto")
        payload = {
            "locations": [{"lat": lat, "lon": lon}],
            "costing": costing,
            "contours": [{"time": m} for m in sorted(minutes)],
            "polygons": True,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{base_url}/isochrone", json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()

        rings = {}
        for i, feature in enumerate(data.get("features", [])):
            m = sorted(minutes)[i] if i < len(minutes) else minutes[-1]
            coords = feature.get("geometry", {}).get("coordinates", [[]])[0]
            rings[m] = coords

        return {"method": "valhalla", "rings": rings}
    except Exception:
        return None


# - Main endpoint -

@router.post("/compute")
async def compute_isochrone(req: IsochroneRequest, _: dict = Depends(get_current_user)):
    """
    Compute isochrone rings. Tries OSRM - Valhalla - geometric fallback.
    Returns GeoJSON-compatible polygon rings for each time threshold.
    """
    import json
    import plotly.graph_objects as go

    # Try OSRM
    result = await _osrm_isochrone(req.lat, req.lon, req.minutes, req.mode, req.osrm_url)

    # Try Valhalla
    if result is None:
        result = await _valhalla_isochrone(req.lat, req.lon, req.minutes, req.mode, req.valhalla_url)

    # Geometric fallback
    if result is None:
        rings = {}
        for m in sorted(req.minutes, reverse=True):
            r_km = _time_to_radius(m, req.mode)
            rings[m] = _circle_polygon(req.lat, req.lon, r_km)
        result = {"method": "geometric", "rings": rings}

    # Build Plotly figure
    colors = ["rgba(239,68,68,0.15)", "rgba(245,158,11,0.15)", "rgba(34,197,94,0.15)",
              "rgba(99,102,241,0.15)", "rgba(14,165,233,0.15)"]
    border_colors = ["#ef4444", "#f59e0b", "#22c55e", "#6366f1", "#0ea5e9"]

    traces = []
    for i, (minutes_val, ring) in enumerate(sorted(result["rings"].items(), reverse=True)):
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        color_idx = i % len(colors)
        traces.append(go.Scattermapbox(
            lat=lats, lon=lons,
            mode="lines",
            fill="toself",
            fillcolor=colors[color_idx],
            line=dict(color=border_colors[color_idx], width=2),
            name=f"{minutes_val} min ({req.mode})",
            hoverinfo="name",
        ))

    # Center point
    traces.append(go.Scattermapbox(
        lat=[req.lat], lon=[req.lon],
        mode="markers+text",
        marker=dict(size=12, color="#6366f1"),
        text=["- Origin"],
        textposition="top right",
        name="Origin",
    ))

    fig = go.Figure(traces)
    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", zoom=11,
                    center=dict(lat=req.lat, lon=req.lon)),
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(bgcolor="rgba(9,9,11,.8)", font=dict(color="#a1a1aa", size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Compute areas
    areas = {}
    for m, ring in result["rings"].items():
        r_km = _time_to_radius(int(m), req.mode)
        areas[m] = round(math.pi * r_km ** 2, 2)

    return {
        "plotly_json": json.loads(fig.to_json()),
        "method": result["method"],
        "rings": {str(k): v for k, v in result["rings"].items()},
        "areas_km2": {str(k): v for k, v in areas.items()},
        "center": {"lat": req.lat, "lon": req.lon},
        "mode": req.mode,
    }


@router.post("/radius")
async def radius_rings(req: RadiusRequest, _: dict = Depends(get_current_user)):
    """Simple radius rings (no routing - pure distance circles)."""
    import json
    import plotly.graph_objects as go

    colors = ["rgba(99,102,241,0.12)", "rgba(14,165,233,0.10)", "rgba(34,197,94,0.08)"]
    border_colors = ["#6366f1", "#0ea5e9", "#22c55e"]

    traces = []
    for i, r_km in enumerate(sorted(req.radii_km, reverse=True)):
        ring = _circle_polygon(req.lat, req.lon, r_km)
        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        c_idx = i % len(colors)
        traces.append(go.Scattermapbox(
            lat=lats, lon=lons,
            mode="lines",
            fill="toself",
            fillcolor=colors[c_idx],
            line=dict(color=border_colors[c_idx], width=2),
            name=f"{r_km} km radius",
        ))

    traces.append(go.Scattermapbox(
        lat=[req.lat], lon=[req.lon],
        mode="markers+text",
        marker=dict(size=12, color="#6366f1"),
        text=[f"- {req.label}"],
        textposition="top right",
        name=req.label,
    ))

    fig = go.Figure(traces)
    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", zoom=10,
                    center=dict(lat=req.lat, lon=req.lon)),
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(bgcolor="rgba(9,9,11,.8)", font=dict(color="#a1a1aa", size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return {
        "plotly_json": json.loads(fig.to_json()),
        "method": "geometric",
        "radii_km": req.radii_km,
        "areas_km2": {str(r): round(math.pi * r**2, 2) for r in req.radii_km},
    }
