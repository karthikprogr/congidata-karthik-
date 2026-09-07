"""Maps routes - Choropleth, H3 hex binning, route/flow maps."""
import sys, pathlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user
from app.services.data_store import get as get_df

router = APIRouter(prefix="/maps", tags=["Maps"])

def _boot():
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)


class ChoroplethRequest(BaseModel):
    location_col: str
    value_col: str
    scope: str = "world"          # world | usa | europe | asia
    color_scale: str = "Viridis"
    title: str = "Choropleth Map"


class H3Request(BaseModel):
    lat_col: str
    lon_col: str
    value_col: Optional[str] = None
    resolution: int = 4           # H3 resolution 2-8
    color_scale: str = "Viridis"


class FlowRequest(BaseModel):
    origin_lat: str
    origin_lon: str
    dest_lat: str
    dest_lon: str
    value_col: Optional[str] = None


@router.post("/choropleth")
def choropleth(req: ChoroplethRequest, user: dict = Depends(get_current_user)):
    """Generate a choropleth map from a location column."""
    import json
    import plotly.express as px
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    if req.location_col not in df.columns:
        raise HTTPException(422, f"Column '{req.location_col}' not found")
    if req.value_col not in df.columns:
        raise HTTPException(422, f"Column '{req.value_col}' not found")

    try:
        fig = px.choropleth(
            df,
            locations=req.location_col,
            color=req.value_col,
            locationmode="country names",
            scope=req.scope if req.scope != "world" else None,
            color_continuous_scale=req.color_scale,
            title=req.title,
            template="plotly_dark",
        )
        fig.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False,
                     showcoastlines=True, coastlinecolor="#3f3f46",
                     showland=True, landcolor="#18181b",
                     showocean=True, oceancolor="#09090b"),
        )
        return {"plotly_json": json.loads(fig.to_json()), "rows": len(df)}
    except Exception as e:
        raise HTTPException(422, f"Choropleth error: {e}")


@router.post("/h3")
def h3_hex(req: H3Request, user: dict = Depends(get_current_user)):
    """Generate H3 hexagonal binning map."""
    import json
    import numpy as np
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    for col in [req.lat_col, req.lon_col]:
        if col not in df.columns:
            raise HTTPException(422, f"Column '{col}' not found")

    try:
        import h3
        lats = df[req.lat_col].dropna().astype(float)
        lons = df[req.lon_col].dropna().astype(float)
        vals = df[req.value_col].astype(float) if req.value_col and req.value_col in df.columns else None

        # Bin into H3 cells
        hex_counts: dict = {}
        hex_vals: dict = {}
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            h = h3.geo_to_h3(lat, lon, req.resolution)
            hex_counts[h] = hex_counts.get(h, 0) + 1
            if vals is not None:
                hex_vals[h] = hex_vals.get(h, 0) + float(vals.iloc[i])

        # Build scatter mapbox from hex centers
        hex_lats, hex_lons, hex_sizes, hex_colors, hex_texts = [], [], [], [], []
        for h, count in hex_counts.items():
            center = h3.h3_to_geo(h)
            hex_lats.append(center[0])
            hex_lons.append(center[1])
            hex_sizes.append(min(30, max(6, count * 2)))
            val = hex_vals.get(h, count)
            hex_colors.append(val)
            hex_texts.append(f"H3: {h[:8]}-<br>Count: {count}<br>Value: {val:.1f}")

        import plotly.graph_objects as go
        fig = go.Figure(go.Scattermapbox(
            lat=hex_lats, lon=hex_lons,
            mode="markers",
            marker=dict(size=hex_sizes, color=hex_colors,
                        colorscale=req.color_scale, opacity=0.75,
                        colorbar=dict(title="Value", thickness=12)),
            text=hex_texts, hoverinfo="text",
        ))
        fig.update_layout(
            mapbox=dict(style="carto-darkmatter", zoom=3,
                        center=dict(lat=float(np.mean(hex_lats)), lon=float(np.mean(hex_lons)))),
            height=500, margin=dict(l=0, r=0, t=0, b=0),
        )
        return {
            "plotly_json": json.loads(fig.to_json()),
            "hex_count": len(hex_counts),
            "resolution": req.resolution,
        }
    except ImportError:
        raise HTTPException(422, "h3 package not installed. Run: pip install h3")
    except Exception as e:
        raise HTTPException(422, f"H3 error: {e}")


@router.post("/flow")
def flow_map(req: FlowRequest, user: dict = Depends(get_current_user)):
    """Generate origin-destination flow/arc map."""
    import json
    import plotly.graph_objects as go
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    for col in [req.origin_lat, req.origin_lon, req.dest_lat, req.dest_lon]:
        if col not in df.columns:
            raise HTTPException(422, f"Column '{col}' not found")

    try:
        sample = df.head(200)
        traces = []
        for _, row in sample.iterrows():
            try:
                olat, olon = float(row[req.origin_lat]), float(row[req.origin_lon])
                dlat, dlon = float(row[req.dest_lat]), float(row[req.dest_lon])
                val = float(row[req.value_col]) if req.value_col and req.value_col in df.columns else 1
                traces.append(go.Scattermapbox(
                    lat=[olat, dlat], lon=[olon, dlon],
                    mode="lines+markers",
                    line=dict(width=max(1, min(4, val / 100)), color="#6366f1"),
                    marker=dict(size=[6, 10], color=["#10b981", "#ef4444"]),
                    showlegend=False, hoverinfo="skip",
                ))
            except (ValueError, TypeError):
                continue

        fig = go.Figure(traces)
        fig.update_layout(
            mapbox=dict(style="carto-darkmatter", zoom=2,
                        center=dict(lat=sample[req.origin_lat].mean(), lon=sample[req.origin_lon].mean())),
            height=500, margin=dict(l=0, r=0, t=0, b=0),
        )
        return {"plotly_json": json.loads(fig.to_json()), "flows": len(traces)}
    except Exception as e:
        raise HTTPException(422, f"Flow map error: {e}")


@router.get("/columns")
def get_geo_columns(user: dict = Depends(get_current_user)):
    """Detect likely geo columns in the dataset."""
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    import numpy as np
    cols = list(df.columns)
    lat_hints = [c for c in cols if any(k in c.lower() for k in ["lat", "latitude", "y_coord"])]
    lon_hints = [c for c in cols if any(k in c.lower() for k in ["lon", "lng", "longitude", "x_coord"])]
    loc_hints = [c for c in cols if any(k in c.lower() for k in ["country", "nation", "state", "city", "region", "location"])]
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    return {
        "all_cols": cols,
        "lat_hints": lat_hints,
        "lon_hints": lon_hints,
        "location_hints": loc_hints,
        "numeric_cols": num_cols,
    }
