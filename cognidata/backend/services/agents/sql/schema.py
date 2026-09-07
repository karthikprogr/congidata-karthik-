"""
Schema loader — introspects SQLite tables for SQL agent context.
"""
import sqlite3
from typing import Optional


def get_schema(db_path: str) -> str:
    """Return schema description for all tables."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        lines = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
            lines.append(f"Table {table} ({count} rows): {col_desc}")
            # Sample row
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            row = cursor.fetchone()
            if row:
                lines.append(f"  Sample: {dict(zip([c[1] for c in cols], row))}")
        conn.close()
        return "\n".join(lines)
    except Exception as e:
        return f"Schema error: {e}"


def dataframe_schema(df) -> str:
    """Return schema description for a pandas DataFrame."""
    import pandas as pd
    lines = [f"DataFrame: {df.shape[0]} rows × {df.shape[1]} columns"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isnull().sum())
        if df[col].dtype == object:
            top = df[col].value_counts().head(3).to_dict()
            lines.append(f"  {col} ({dtype}, {nulls} nulls): top={top}")
        else:
            lines.append(f"  {col} ({dtype}, {nulls} nulls): min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}")
    return "\n".join(lines)
