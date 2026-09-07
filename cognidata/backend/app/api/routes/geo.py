"""Geo Intelligence routes - live city data, history, pipeline."""
import sys, pathlib
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user

router = APIRouter(prefix="/geo", tags=["Geo Intelligence"])

def _boot():
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)

@router.get("/current")
def current(_: dict = Depends(get_current_user)):
    _boot()
    from agents.geo.geo_agent import get_current
    data = get_current()
    return {"cities": list(data.values())}

@router.get("/history/{city}")
def city_history(city: str, n: int = 60, _: dict = Depends(get_current_user)):
    _boot()
    from agents.geo.geo_agent import get_history
    return {"city": city, "history": get_history(city, n)}

@router.get("/history")
def all_history(n: int = 60, _: dict = Depends(get_current_user)):
    _boot()
    from agents.geo.geo_agent import get_all_history
    return get_all_history(n)


@router.post("/sync")
def sync_real_data(data: dict, _: dict = Depends(get_current_user)):
    """Accept manually entered city data and inject into geo simulation."""
    cities = data.get("cities", [])
    if not cities:
        return {"message": "No cities provided"}
    try:
        _boot()
        from agents.geo.geo_agent import _current, _lock
        with _lock:
            for c in cities:
                name = c.get("name", "")
                if name:
                    _current[name] = {
                        "name": name,
                        "lat": float(c.get("lat", 0)),
                        "lon": float(c.get("lon", 0)),
                        "sales": float(c.get("sales", 0)),
                        "satisfaction": float(c.get("satisfaction", 4.0)),
                        "orders": int(c.get("orders", 100)),
                        "region": c.get("region", "Custom"),
                        "anomaly": False,
                        "tier": "Mid",
                    }
        return {"message": f"Synced {len(cities)} cities", "count": len(cities)}
    except Exception as e:
        return {"message": f"Sync failed: {e}", "count": 0}
