"""
Hybrid data agent — rule-based first, LLM fallback for complex queries.
"""
import re
from typing import Optional
import numpy as np
import pandas as pd

PATTERNS = [
    (r"\btop\s*(\d+)\b",              "_top_n"),
    (r"\bbottom\s*(\d+)\b",           "_bottom_n"),
    (r"\bsum\b",                       "_sum"),
    (r"\b(average|mean)\b",           "_mean"),
    (r"\bcount\b",                     "_count"),
    (r"\bmax(imum)?\b",               "_max"),
    (r"\bmin(imum)?\b",               "_min"),
    (r"\bcorrelation|corr\b",         "_correlation"),
    (r"\bmissing|null|nan\b",         "_missing"),
    (r"\bduplicate\b",                 "_duplicates"),
    (r"\bdescribe|statistics\b",      "_describe"),
    (r"\bshape|size|rows|columns\b",  "_shape"),
    (r"\bunique\b",                    "_unique"),
    (r"\bgroup.*by\b",                 "_groupby"),
    (r"\bvalue.count\b",              "_value_counts"),
    (r"\bsort.*(desc|highest|largest)\b", "_sort_desc"),
    (r"\bsort.*(asc|lowest|smallest)\b",  "_sort_asc"),
]

class DataAgent:
    def run(self, question: str, df: Optional[pd.DataFrame]):
        if df is None: return None, "", "No dataset loaded"
        q = question.lower().strip()
        for pattern, handler in PATTERNS:
            m = re.search(pattern, q)
            if m:
                try:
                    result, code = getattr(self, handler)(q, df, m)
                    if result is not None: return result, code, "success"
                except Exception: pass
        return self._llm(question, df)

    def _top_n(self, q, df, m):
        n = int(m.group(1)); col = self._num(q, df)
        return (df.nlargest(n, col) if col else df.head(n)), f"df.nlargest({n}, '{col}')"

    def _bottom_n(self, q, df, m):
        n = int(m.group(1)); col = self._num(q, df)
        return (df.nsmallest(n, col) if col else df.tail(n)), f"df.nsmallest({n}, '{col}')"

    def _sum(self, q, df, m):
        col = self._num(q, df)
        if col: return pd.Series({col: df[col].sum()}), f"df['{col}'].sum()"
        return df.select_dtypes("number").sum(), "df.sum(numeric_only=True)"

    def _mean(self, q, df, m):
        col = self._num(q, df)
        if col: return pd.Series({col: round(float(df[col].mean()), 4)}), f"df['{col}'].mean()"
        return df.select_dtypes("number").mean().round(4), "df.mean(numeric_only=True)"

    def _count(self, q, df, m):
        return pd.Series({"rows": len(df), "columns": len(df.columns)}), "df.shape"

    def _max(self, q, df, m):
        col = self._num(q, df)
        return (pd.Series({col: df[col].max()}) if col else df.select_dtypes("number").max()), ""

    def _min(self, q, df, m):
        col = self._num(q, df)
        return (pd.Series({col: df[col].min()}) if col else df.select_dtypes("number").min()), ""

    def _correlation(self, q, df, m):
        nums = df.select_dtypes("number")
        if len(nums.columns) < 2: return None, ""
        return nums.corr().round(3), "df.corr(numeric_only=True)"

    def _missing(self, q, df, m):
        miss = df.isnull().sum(); miss = miss[miss > 0].sort_values(ascending=False)
        pct = (miss / len(df) * 100).round(1)
        return pd.DataFrame({"missing_count": miss, "missing_pct": pct}), "df.isnull().sum()"

    def _duplicates(self, q, df, m):
        return pd.Series({"duplicate_rows": int(df.duplicated().sum())}), "df.duplicated().sum()"

    def _describe(self, q, df, m):
        return df.describe().round(3), "df.describe()"

    def _shape(self, q, df, m):
        return pd.Series({"rows": len(df), "columns": len(df.columns)}), "df.shape"

    def _unique(self, q, df, m):
        col = self._any_col(q, df)
        if col: return pd.Series({col: str(df[col].unique().tolist()[:50])}), f"df['{col}'].unique()"
        return pd.Series({c: df[c].nunique() for c in df.columns}), "df.nunique()"

    def _groupby(self, q, df, m):
        cats = df.select_dtypes("object").columns.tolist()
        nums = df.select_dtypes("number").columns.tolist()
        if cats and nums:
            r = df.groupby(cats[0])[nums[0]].sum().reset_index().sort_values(nums[0], ascending=False).head(20)
            return r, f"df.groupby('{cats[0]}')['{nums[0]}'].sum()"
        return None, ""

    def _value_counts(self, q, df, m):
        col = self._any_col(q, df) or (df.select_dtypes("object").columns.tolist() or [None])[0]
        if col:
            r = df[col].value_counts().head(20).reset_index(); r.columns = [col, "count"]
            return r, f"df['{col}'].value_counts()"
        return None, ""

    def _sort_desc(self, q, df, m):
        col = self._num(q, df)
        return (df.sort_values(col, ascending=False).head(20), f"df.sort_values('{col}', ascending=False)") if col else (None, "")

    def _sort_asc(self, q, df, m):
        col = self._num(q, df)
        return (df.sort_values(col).head(20), f"df.sort_values('{col}')") if col else (None, "")

    def _llm(self, question, df):
        try:
            from agents.llm_agent import run_llm_query
            return run_llm_query(question, df)
        except Exception as e:
            return None, "", str(e)

    def _num(self, q, df):
        for col in df.select_dtypes("number").columns:
            if col.lower() in q: return col
        nums = df.select_dtypes("number").columns.tolist()
        return nums[0] if nums else None

    def _any_col(self, q, df):
        for col in df.columns:
            if col.lower() in q: return col
        return None

data_agent = DataAgent()
