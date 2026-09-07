"""
Real-time data streaming via Server-Sent Events (SSE).
Pushes live ingest stream rows to the frontend as they arrive.
"""
import asyncio
import json
import time
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/stream", tags=["Stream"])


def _auth_from_query(token: str) -> dict | None:
    """Validate JWT token passed as query param (EventSource can't set headers)."""
    try:
        from app.core.security import decode_token
        return decode_token(token)
    except Exception:
        return None


@router.get("/live/{stream_id}")
async def stream_live(stream_id: str, request: Request,
                      token: str = Query(...)):
    """
    SSE endpoint - pushes new rows from an ingest stream as they arrive.
    Auth via ?token= query param (EventSource limitation).
    """
    user = _auth_from_query(token)
    if not user:
        async def _unauth():
            yield f"data: {json.dumps({'error': 'Unauthorized'})}\n\n"
        return StreamingResponse(_unauth(), media_type="text/event-stream")

    from app.api.routes.ingest import _streams

    async def event_generator():
        s = _streams.get(stream_id)
        if not s or s.get("owner") != user["email"]:
            yield f"data: {json.dumps({'error': 'Stream not found'})}\n\n"
            return

        last_count = len(s.get("rows", []))
        yield f"data: {json.dumps({'type': 'connected', 'stream': s['name'], 'rows': last_count})}\n\n"

        while True:
            if await request.is_disconnected():
                break

            s = _streams.get(stream_id)
            if not s:
                break

            rows = s.get("rows", [])
            current_count = len(rows)

            if current_count > last_count:
                new_rows = rows[last_count:current_count]
                for row in new_rows:
                    payload = {
                        "type": "row",
                        "data": row,
                        "total": current_count,
                        "ts": row.get("_ts", ""),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                last_count = current_count

            # Heartbeat every 1s to keep connection alive
            yield f"data: {json.dumps({'type': 'heartbeat', 'total': current_count, 'ts': time.time()})}\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/live/{stream_id}/snapshot")
async def stream_snapshot(stream_id: str, n: int = 100,
                           token: str = Query(...)):
    """Return the last N rows of a stream as JSON for initial chart render."""
    from fastapi import HTTPException
    user = _auth_from_query(token)
    if not user:
        raise HTTPException(401, "Unauthorized")

    from app.api.routes.ingest import _streams
    s = _streams.get(stream_id)
    if not s or s.get("owner") != user["email"]:
        raise HTTPException(404, "Stream not found")

    rows = s.get("rows", [])[-n:]
    schema = s.get("schema", {})
    numeric_cols = [k for k, v in schema.items() if v in ("int", "float") and k != "_ts"]
    return {
        "rows": rows,
        "total": len(s["rows"]),
        "schema": schema,
        "numeric_cols": numeric_cols,
        "name": s["name"],
    }
