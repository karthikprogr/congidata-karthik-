"""
WebSocket endpoint - streams all query types as tokens.
- Rule-based (data/anomaly/ml/visualization): streams result as JSON chunks
- LLM insight/sql/rag: streams tokens as they arrive from OpenAI
"""
import os, sys, pathlib, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from app.core.security import decode_token

router = APIRouter()

# Bootstrap once at module load
_p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
if _p not in sys.path:
    sys.path.insert(0, _p)

def _bootstrap():
    pass  # already done at import time


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    _bootstrap()

    try:
        # First message must be auth token
        auth_msg = await websocket.receive_text()
        try:
            payload = json.loads(auth_msg)
            token = payload.get("token", "")
            user = decode_token(token)
        except (JWTError, Exception):
            await websocket.send_text(json.dumps({"type": "error", "data": "Unauthorized"}))
            await websocket.close()
            return

        user_id = user.get("sub", "")
        api_key = os.environ.get("OPENAI_API_KEY", "")

        await websocket.send_text(json.dumps({"type": "connected", "data": "Ready"}))

        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            question = data.get("query", "")
            client_key = data.get("api_key", "")
            if client_key:
                api_key = client_key

            if not question:
                continue

            await _handle_query(websocket, question, api_key, user_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
        except Exception:
            pass


async def _handle_query(websocket: WebSocket, question: str, api_key: str, user_id: str):
    """Route query to the right handler and stream the response."""
    from agents.controller import decide
    from app.services.data_store import get as get_df

    task = decide(question)
    df = get_df(user_id)

    await websocket.send_text(json.dumps({"type": "start", "task_type": task}))

    try:
        if task in ("data", "anomaly", "ml", "visualization"):
            await _stream_structured(websocket, question, api_key, user_id, task, df)
        elif task == "sql":
            await _stream_sql(websocket, question, api_key, user_id, df)
        elif task == "rag":
            await _stream_rag(websocket, question, api_key, user_id, df)
        elif task == "geo":
            await _stream_geo(websocket, user_id)
        else:
            # insight / general - stream LLM tokens
            await _stream_llm(websocket, question, df, api_key, user_id, task)
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))


async def _stream_structured(websocket: WebSocket, question: str, api_key: str,
                              user_id: str, task: str, df):
    """Run rule-based query and stream result as a single result frame."""
    import asyncio
    from app.services.ai_service import run_query

    # Run in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_query, question, api_key, user_id)

    await websocket.send_text(json.dumps({"type": "result", **result}))
    await websocket.send_text(json.dumps({"type": "done", "task_type": task}))


async def _stream_llm(websocket: WebSocket, question: str, df, api_key: str,
                      user_id: str, task: str):
    """Stream LLM tokens for insight/general queries."""
    if df is None:
        await websocket.send_text(json.dumps({"type": "token", "data": "No dataset loaded. Please upload a file first."}))
        await websocket.send_text(json.dumps({"type": "done", "task_type": task}))
        return

    try:
        import numpy as np
        from openai import AsyncOpenAI
        from app.services.chat_memory import get_context, add as mem_add

        # Use OpenAI API
        client = AsyncOpenAI(api_key=api_key)
        history = get_context(user_id)

        nums = df.select_dtypes(include=np.number)
        summary = f"Shape: {df.shape}\nColumns: {list(df.columns)}\n"
        if not nums.empty:
            desc = nums.describe().loc[["mean", "std", "min", "max"]].round(2)
            summary += f"Stats:\n{desc.to_string()}"

        messages = [{"role": "system", "content": "You are a senior data analyst. Be concise and actionable."}]
        # Inject memory context
        for h in history[-4:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": f"Dataset:\n{summary}\n\nQuestion: {question}"})

        mem_add(user_id, "user", question)

        full_response = []
        stream = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.1,
            max_tokens=600,
            stream=True,
        )

        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                full_response.append(token)
                await websocket.send_text(json.dumps({"type": "token", "data": token}))

        mem_add(user_id, "assistant", "".join(full_response)[:300])
        await websocket.send_text(json.dumps({"type": "done", "task_type": task}))

    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))


async def _stream_sql(websocket: WebSocket, question: str, api_key: str, user_id: str, df):
    """Run SQL agent and stream result."""
    import asyncio
    if df is None:
        await websocket.send_text(json.dumps({"type": "token", "data": "No dataset loaded."}))
        await websocket.send_text(json.dumps({"type": "done", "task_type": "sql"}))
        return

    try:
        from agents.sql.sql_agent import run_sql_agent
        from app.services.chat_memory import get_context
        import pandas as pd

        loop = asyncio.get_event_loop()
        history = get_context(user_id)
        result = await loop.run_in_executor(None, run_sql_agent, question, df, api_key, history)

        r = result.get("result")
        if isinstance(r, pd.DataFrame):
            data = r.replace({float("nan"): None}).to_dict("records")
            payload = {"type": "result", "task_type": "sql", "status": "success",
                       "type_": "table", "data": data[:20], "code": result.get("code")}
        else:
            payload = {"type": "result", "task_type": "sql", "status": "success",
                       "type_": "text", "data": str(r), "code": result.get("code")}

        await websocket.send_text(json.dumps(payload))
        await websocket.send_text(json.dumps({"type": "done", "task_type": "sql"}))
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))


async def _stream_rag(websocket: WebSocket, question: str, api_key: str, user_id: str, df):
    """Stream RAG answer token by token using OpenAI streaming."""
    try:
        import numpy as np
        from openai import AsyncOpenAI
        from agents.rag.rag_agent import query as rag_query

        # Get RAG answer with streaming via OpenAI
        import asyncio
        loop = asyncio.get_event_loop()

        # Retrieve context chunks from vector store if available
        context = ""
        try:
            from agents.rag.rag_agent import _stores, _get_embedder
            store = _stores.get(user_id)
            if store and len(store) > 0:
                embedder = _get_embedder()
                if embedder:
                    q_emb = embedder.encode([question])[0]
                else:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    vec = TfidfVectorizer(max_features=256)
                    q_emb = vec.fit_transform([question]).toarray()[0]
                chunks = store.search(q_emb, top_k=5)
                context = "\n".join(chunks)
        except Exception:
            pass

        if not context and df is not None:
            # Fallback: use dataset summary as context
            nums = df.select_dtypes(include=np.number)
            context = f"Dataset shape: {df.shape}\nColumns: {list(df.columns)}"
            if not nums.empty:
                context += f"\nStats:\n{nums.describe().loc[['mean','std']].round(2).to_string()}"

        messages = [
            {"role": "system", "content": "Answer based on the provided data context. Be precise."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        # Initialize OpenAI client for RAG
        client = AsyncOpenAI(api_key=api_key)
        
        stream = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.1,
            max_tokens=500,
            stream=True,
        )

        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                await websocket.send_text(json.dumps({"type": "token", "data": token}))

        await websocket.send_text(json.dumps({"type": "done", "task_type": "rag"}))
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))


async def _stream_geo(websocket: WebSocket, user_id: str):
    """Stream geo data as a result frame."""
    try:
        from agents.geo.geo_agent import get_current
        import json as _json
        import plotly.graph_objects as go

        cities = list(get_current().values())
        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(
            lat=[c["lat"] for c in cities],
            lon=[c["lon"] for c in cities],
            text=[f"{c['name']}: {c.get('sales', 0):.0f}" for c in cities],
            mode="markers",
            marker=dict(
                size=[max(8, c.get("sales", 100) / 500) for c in cities],
                color=[c.get("sales", 0) for c in cities],
                colorscale="RdYlGn", opacity=0.8,
            ),
        ))
        fig.update_layout(
            mapbox=dict(style="carto-darkmatter", zoom=1, center=dict(lat=20, lon=0)),
            height=400, margin=dict(l=0, r=0, t=0, b=0),
        )
        payload = {
            "type": "result", "task_type": "geo", "status": "success",
            "type_": "chart", "data": _json.loads(fig.to_json()),
            "extra": {"cities": len(cities), "anomalies": sum(1 for c in cities if c.get("anomaly"))},
        }
        await websocket.send_text(json.dumps(payload))
        await websocket.send_text(json.dumps({"type": "done", "task_type": "geo"}))
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
