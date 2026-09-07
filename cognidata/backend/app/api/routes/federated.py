"""Federated Query routes - query Postgres/MySQL/BigQuery/SQLite without uploading data."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user

router = APIRouter(prefix="/federated", tags=["Federated"])

# In-memory connection store per user
_connections: dict[str, dict] = {}


class ConnectionConfig(BaseModel):
    name: str
    type: str          # postgres | mysql | sqlite | bigquery | snowflake
    host: str = ""
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    project_id: str = ""   # BigQuery
    dataset: str = ""      # BigQuery
    path: str = ""         # SQLite file path


class QueryRequest(BaseModel):
    connection_name: str
    query: str
    limit: int = 1000


class NLQueryRequest(BaseModel):
    connection_name: str
    question: str
    api_key: str = ""


def _build_url(cfg: dict) -> str:
    t = cfg["type"]
    if t == "postgres":
        return f"postgresql+psycopg2://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    elif t == "mysql":
        return f"mysql+pymysql://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    elif t == "sqlite":
        return f"sqlite:///{cfg['path']}"
    elif t == "snowflake":
        return f"snowflake://{cfg['username']}:{cfg['password']}@{cfg['host']}/{cfg['database']}"
    raise ValueError(f"Unsupported type: {t}")


@router.get("/connections")
def list_connections(user: dict = Depends(get_current_user)):
    uid = user["sub"]
    conns = _connections.get(uid, {})
    return [{"name": k, "type": v["type"], "database": v.get("database", ""), "host": v.get("host", "")}
            for k, v in conns.items()]


@router.post("/connections", status_code=201)
def add_connection(cfg: ConnectionConfig, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    if uid not in _connections:
        _connections[uid] = {}
    _connections[uid][cfg.name] = cfg.model_dump()
    return {"message": f"Connection '{cfg.name}' saved", "name": cfg.name}


@router.delete("/connections/{name}", status_code=204)
def delete_connection(name: str, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    _connections.get(uid, {}).pop(name, None)


@router.post("/connections/{name}/test")
def test_connection(name: str, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    cfg = _connections.get(uid, {}).get(name)
    if not cfg:
        raise HTTPException(404, f"Connection '{name}' not found")
    try:
        from sqlalchemy import create_engine, text
        url = _build_url(cfg)
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/connections/{name}/schema")
def get_schema(name: str, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    cfg = _connections.get(uid, {}).get(name)
    if not cfg:
        raise HTTPException(404, f"Connection '{name}' not found")
    try:
        from sqlalchemy import create_engine, inspect as sa_inspect
        url = _build_url(cfg)
        engine = create_engine(url)
        insp = sa_inspect(engine)
        tables = {}
        for table in insp.get_table_names()[:20]:
            cols = [{"name": c["name"], "type": str(c["type"])} for c in insp.get_columns(table)]
            tables[table] = cols
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(422, str(e))


@router.post("/query")
def run_query(req: QueryRequest, user: dict = Depends(get_current_user)):
    uid = user["sub"]
    cfg = _connections.get(uid, {}).get(req.connection_name)
    if not cfg:
        raise HTTPException(404, f"Connection '{req.connection_name}' not found")
    try:
        import pandas as pd
        from sqlalchemy import create_engine, text
        url = _build_url(cfg)
        engine = create_engine(url)
        # Safety: only SELECT
        q = req.query.strip()
        if not q.upper().startswith("SELECT"):
            raise HTTPException(422, "Only SELECT queries are allowed")
        with engine.connect() as conn:
            df = pd.read_sql(text(q), conn)
        df = df.head(req.limit)
        # Also save to user's data store for further analysis
        from app.services.data_store import save as save_df
        save_df(uid, df)
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "data": df.replace({float("nan"): None}).to_dict("records")[:100],
            "column_names": list(df.columns),
            "message": f"Query returned {len(df)} rows - loaded into dataset"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(422, str(e))


@router.post("/nl-query")
def nl_query(req: NLQueryRequest, user: dict = Depends(get_current_user)):
    """Natural language - SQL - execute on remote connection."""
    uid = user["sub"]
    cfg = _connections.get(uid, {}).get(req.connection_name)
    if not cfg:
        raise HTTPException(404, f"Connection '{req.connection_name}' not found")
    try:
        # Get schema for context
        from sqlalchemy import create_engine, inspect as sa_inspect
        url = _build_url(cfg)
        engine = create_engine(url)
        insp = sa_inspect(engine)
        schema_lines = []
        for table in insp.get_table_names()[:10]:
            cols = ", ".join(c["name"] for c in insp.get_columns(table))
            schema_lines.append(f"Table {table}: {cols}")
        schema_str = "\n".join(schema_lines)

        # LLM generates SQL
        import os, re
        from openai import OpenAI
        api_key = req.api_key or os.environ.get("OPENAI_API_KEY", "")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content":
                f"Database schema:\n{schema_str}\n\nGenerate a SELECT SQL query for: {req.question}\nReturn ONLY the SQL, no explanation."}],
            temperature=0.1, max_tokens=300,
        )
        sql = re.sub(r"```(?:sql)?|```", "", resp.choices[0].message.content.strip()).strip()

        # Execute
        import pandas as pd
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        df = df.head(500)
        from app.services.data_store import save as save_df
        save_df(uid, df)
        return {
            "sql": sql,
            "rows": len(df),
            "columns": len(df.columns),
            "data": df.replace({float("nan"): None}).to_dict("records")[:50],
        }
    except Exception as e:
        raise HTTPException(422, str(e))
