import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

PALETTES = {
    "Indigo":  ["#6366f1","#8b5cf6","#a855f7","#c084fc"],
    "Emerald": ["#10b981","#059669","#34d399","#6ee7b7"],
    "Sunset":  ["#f59e0b","#ef4444","#f97316","#ec4899"],
    "Ocean":   ["#0ea5e9","#06b6d4","#3b82f6","#6366f1"],
}

def _fig(fig) -> dict:
    return json.loads(fig.to_json())

def auto_overview(df: pd.DataFrame, palette: str = "Indigo", max_charts: int = 6) -> list[dict]:
    colors = PALETTES.get(palette, PALETTES["Indigo"])
    nums = df.select_dtypes(include=np.number).columns.tolist()
    cats = df.select_dtypes(include="object").columns.tolist()
    charts = []

    if nums:
        fig = px.histogram(df, x=nums[0], title=f"Distribution: {nums[0]}",
                           color_discrete_sequence=colors, template="plotly_dark")
        charts.append({"title": f"Distribution: {nums[0]}", "plotly_json": _fig(fig)})

    if len(nums) >= 2:
        fig = px.scatter(df, x=nums[0], y=nums[1], title=f"{nums[0]} vs {nums[1]}",
                         color_discrete_sequence=colors, template="plotly_dark", opacity=0.7)
        charts.append({"title": f"{nums[0]} vs {nums[1]}", "plotly_json": _fig(fig)})

    if cats and nums:
        agg = df.groupby(cats[0])[nums[0]].mean().reset_index()
        fig = px.bar(agg, x=cats[0], y=nums[0], title=f"Avg {nums[0]} by {cats[0]}",
                     color_discrete_sequence=colors, template="plotly_dark")
        charts.append({"title": f"Avg {nums[0]} by {cats[0]}", "plotly_json": _fig(fig)})

    if len(nums) >= 2:
        corr = df[nums[:8]].corr()
        fig = px.imshow(corr, title="Correlation Matrix", template="plotly_dark",
                        color_continuous_scale="RdBu_r", text_auto=".2f")
        charts.append({"title": "Correlation Matrix", "plotly_json": _fig(fig)})

    if cats:
        vc = df[cats[0]].value_counts().reset_index()
        vc.columns = [cats[0], "count"]
        fig = px.pie(vc, names=cats[0], values="count", title=f"{cats[0]} Breakdown",
                     color_discrete_sequence=colors, template="plotly_dark", hole=0.4)
        charts.append({"title": f"{cats[0]} Breakdown", "plotly_json": _fig(fig)})

    if nums:
        fig = px.area(df.reset_index(), x="index", y=nums[0], title=f"Trend: {nums[0]}",
                      color_discrete_sequence=colors, template="plotly_dark")
        charts.append({"title": f"Trend: {nums[0]}", "plotly_json": _fig(fig)})

    return charts[:max_charts]

def kpi_charts(df: pd.DataFrame, palette: str = "Indigo") -> list[dict]:
    colors = PALETTES.get(palette, PALETTES["Indigo"])
    nums = df.select_dtypes(include=np.number).columns.tolist()
    result = []
    for col in nums[:6]:
        val = float(df[col].mean())
        fig = go.Figure(go.Indicator(
            mode="number", value=val,
            number={"font": {"size": 40, "color": colors[0]}},
            title={"text": f"Avg {col}", "font": {"size": 13, "color": "#94a3b8"}},
        ))
        fig.update_layout(height=130, margin=dict(l=10,r=10,t=30,b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        result.append({"column": col, "value": round(val, 3), "plotly_json": _fig(fig)})
    return result
