"""
AI Service — GPT-level intelligence with conversation memory.
"""
import hashlib, os, sys, pathlib
from typing import Any, Optional
import pandas as pd
from app.services.data_store import get as get_df, get_ai_cache
from app.services.chat_memory import add as mem_add, get_context, clear as mem_clear

def _add_services_path():
    p = str(pathlib.Path(__file__).resolve().parents[2] / "services")
    if p not in sys.path: sys.path.insert(0, p)

def _cache_key(user_id: str, question: str, df: Optional[pd.DataFrame]) -> str:
    h = ""
    if df is not None:
        try: h = hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()[:12]
        except: h = str(len(df))
    return hashlib.md5(f"{user_id}:{question.lower().strip()}:{h}".encode()).hexdigest()

def _serialise(obj: Any) -> Any:
    if isinstance(obj, pd.DataFrame):
        return obj.replace({float("nan"): None}).to_dict("records")
    if isinstance(obj, pd.Series):
        return obj.where(obj.notna(), None).to_dict()
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return obj

def run_query(question: str, api_key: str, user_id: str = "",
              data: Optional[list[dict]] = None) -> dict:
    os.environ["OPENAI_API_KEY"] = api_key
    _add_services_path()

    df = pd.DataFrame(data) if data else get_df(user_id)
    cache = get_ai_cache()
    key = _cache_key(user_id, question, df)

    if key in cache:
        return cache[key]

    from agents.controller import decide
    task = decide(question)
    history = get_context(user_id)
    
    # PRIORITY: Use RAG if indexed data exists (prevents "DATA AGENT NULL" errors)
    if task != "rag":
        try:
            from agents.rag.rag_agent import get_total_chunks
            if get_total_chunks(user_id) > 0:
                task = "rag"  # Force RAG when indexed data available
        except:
            pass

    # Store user message in memory
    mem_add(user_id, "user", question)

    try:
        result = _dispatch(task, question, df, api_key, history)
        resp = {"task_type": task, "status": "success", **result}
    except Exception as e:
        resp = {"task_type": task, "status": "error", "type": "error",
                "data": None, "code": None, "error": str(e)}

    # Store assistant response summary in memory
    mem_add(user_id, "assistant",
            f"[{task}] {str(resp.get('data', ''))[:200]}")

    cache[key] = resp
    return resp

def _dispatch(task: str, question: str, df, api_key: str, history: list) -> dict:
    _add_services_path()
    from agents.data_agent import data_agent
    from agents.llm_agent import run_llm_query, run_insight, select_chart_type
    from agents.viz_agent import auto_overview

    if task == "report":
        # Generate PDF report
        try:
            insights = run_insight(df, api_key, history=history) if df is not None else ""
            from agents.reports.pdf_generator import generate_pdf
            pdf_bytes = generate_pdf(df, title="COGNIDATA Report", insights=insights) if df is not None else b""
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode() if pdf_bytes else ""
            return {"type": "report", "data": {"pdf_b64": pdf_b64, "size_kb": round(len(pdf_bytes)/1024, 1)}, "code": None}
        except Exception as e:
            return {"type": "text", "data": f"Report generation failed: {e}", "code": None}

    elif task == "geo":
        # Geo agent — return current city data
        try:
            from agents.geo.geo_agent import get_current
            cities = list(get_current().values())
            import json, plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scattermapbox(
                lat=[c["lat"] for c in cities],
                lon=[c["lon"] for c in cities],
                text=[f"{c['name']}: {c.get('sales',0):.0f}" for c in cities],
                mode="markers",
                marker=dict(size=[max(8, c.get("sales",100)/500) for c in cities],
                            color=[c.get("sales",0) for c in cities],
                            colorscale="RdYlGn", opacity=0.8),
            ))
            fig.update_layout(mapbox=dict(style="carto-darkmatter", zoom=1, center=dict(lat=20, lon=0)),
                              height=400, margin=dict(l=0,r=0,t=0,b=0))
            return {"type": "chart", "data": json.loads(fig.to_json()), "code": None,
                    "extra": {"cities": len(cities), "anomalies": sum(1 for c in cities if c.get("anomaly"))}}
        except Exception as e:
            return {"type": "text", "data": f"Geo data: {e}", "code": None}

    elif task == "sql":
        # SQL agent — NL to pandas
        try:
            from agents.sql.sql_agent import run_sql_agent
            result = run_sql_agent(question, df, api_key, history=history)
            import pandas as pd
            r = result.get("result")
            if isinstance(r, pd.DataFrame):
                data = r.replace({float("nan"): None}).to_dict("records")
                return {"type": "table", "data": data[:20], "code": result.get("code")}
            elif isinstance(r, pd.Series):
                return {"type": "json", "data": r.where(r.notna(), None).to_dict(), "code": result.get("code")}
            else:
                return {"type": "text", "data": str(r) if r is not None else "No result", "code": result.get("code")}
        except Exception as e:
            return {"type": "text", "data": f"SQL error: {e}", "code": None}

    elif task == "rag":
        # RAG agent — document context + LLM answer
        try:
            from agents.rag.rag_agent import query as rag_query
            answer = rag_query(user_id, question, api_key)
            return {"type": "text", "data": answer, "code": None}
        except Exception as e:
            # Fallback to insight
            text = run_insight(df, api_key, history=history, question=question)
            return {"type": "text", "data": text, "code": None}

    elif task == "data":
        # Try rule-based first, fall back to LLM with memory
        result, code, status = data_agent.run(question, df)
        if result is None:
            result, code, status = run_llm_query(question, df, user_id="", history=history)

        r = _serialise(result)

        # Smart chart type selection for tabular results
        if isinstance(r, list) and r and isinstance(r[0], dict) and len(r) > 1:
            try:
                result_df = pd.DataFrame(r)
                chart_type = select_chart_type(result_df, question)
                if chart_type != "table":
                    from agents.viz_agent import _fig
                    import plotly.express as px
                    nums = result_df.select_dtypes("number").columns.tolist()
                    cats = result_df.select_dtypes("object").columns.tolist()
                    if nums and cats and chart_type == "bar":
                        fig = px.bar(result_df, x=cats[0], y=nums[0],
                                     template="plotly_dark", title=question[:60])
                        return {"type": "chart", "data": _fig(fig), "code": code}
            except Exception:
                pass
            return {"type": "table", "data": r[:20], "code": code}

        t = "text" if isinstance(r, str) else "json"
        return {"type": t, "data": r, "code": code}

    elif task == "insight":
        # Pass the question for context-aware responses
        text = run_insight(df, api_key, history=history, question=question)
        return {"type": "text", "data": text, "code": None}

    elif task == "anomaly":
        from sklearn.ensemble import IsolationForest
        if df is None: return {"type": "text", "data": "No data", "code": None}
        nums = df.select_dtypes(include="number")
        if nums.empty: return {"type": "text", "data": "No numeric columns for anomaly detection", "code": None}
        model = IsolationForest(contamination=0.1, random_state=42)
        df2 = df.copy()
        df2["anomaly_score"] = model.fit_predict(nums)
        df2["is_anomaly"] = df2["anomaly_score"] == -1
        anomalies = df2[df2["is_anomaly"]].head(20)
        return {"type": "table", "data": _serialise(anomalies), "code": "IsolationForest(contamination=0.1)"}

    elif task == "ml":
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import r2_score
        import numpy as np
        if df is None: return {"type": "text", "data": "No data", "code": None}
        nums = df.select_dtypes(include=np.number).columns.tolist()
        if len(nums) < 2: return {"type": "text", "data": "Need at least 2 numeric columns", "code": None}
        target = nums[-1]; features = nums[:-1]
        X = df[features].fillna(0); y = df[target].fillna(0)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        score = round(r2_score(y_test, model.predict(X_test)), 4)
        importances = dict(zip(features, model.feature_importances_.round(4).tolist()))
        return {
            "type": "text",
            "data": f"RandomForest trained on '{target}'\nR² score: {score}\nFeature importance: {importances}",
            "code": f"RandomForestRegressor(n_estimators=100) → target: {target}, R²: {score}"
        }

    elif task == "visualization":
        if df is None: return {"type": "text", "data": "No data", "code": None}
        charts = auto_overview(df, max_charts=1)
        return {"type": "chart", "data": charts[0]["plotly_json"] if charts else None, "code": None}

    else:
        result, code, _ = run_llm_query(question, df, history=history)
        r = _serialise(result)
        return {"type": "table" if isinstance(r, list) else "text", "data": r, "code": code}


def clear_memory(user_id: str) -> None:
    mem_clear(user_id)
    cache = get_ai_cache()
    keys = [k for k in list(cache.keys()) if k.startswith(user_id)]
    for k in keys:
        try: del cache[k]
        except: pass
