from fastapi import APIRouter
from app.api.routes import (
    health, auth, data, ai, viz, admin, ws, ml,
    sql, reports, geo, rag, roadmap, profile, config,
    workspaces, debug, analytics, maps, alerts,
    federated, semantic, pipeline, catalog, isochrone,
    actions, ingest, sdk, analyst, stream
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(data.router)
api_router.include_router(ai.router)
api_router.include_router(viz.router)
api_router.include_router(admin.router)
api_router.include_router(ws.router)
api_router.include_router(ml.router)
api_router.include_router(sql.router)
api_router.include_router(reports.router)
api_router.include_router(geo.router)
api_router.include_router(rag.router)
api_router.include_router(roadmap.router)
api_router.include_router(profile.router)
api_router.include_router(config.router)
api_router.include_router(workspaces.router)
api_router.include_router(debug.router)
api_router.include_router(analytics.router)
api_router.include_router(maps.router)
api_router.include_router(alerts.router)
api_router.include_router(federated.router)
api_router.include_router(semantic.router)
api_router.include_router(pipeline.router)
api_router.include_router(catalog.router)
api_router.include_router(isochrone.router)
api_router.include_router(actions.router)
api_router.include_router(ingest.router)
api_router.include_router(sdk.router)
api_router.include_router(analyst.router)
api_router.include_router(stream.router)
