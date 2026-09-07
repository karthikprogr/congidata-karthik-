import sys, pathlib
import pandas as pd
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.services.data_store import get as get_df
from fastapi import HTTPException

router = APIRouter(prefix="/viz", tags=["Visualization"])

# Bootstrap once at module load time - not on every request
_services_path = str(pathlib.Path(__file__).resolve().parents[3] / "services")
if _services_path not in sys.path:
    sys.path.insert(0, _services_path)

def _bootstrap():
    pass  # already done at import time

@router.get("/overview")
def overview(max_charts: int = 6, palette: str = "Indigo",
             user: dict = Depends(get_current_user)):
    _bootstrap()
    from agents.viz_agent import auto_overview
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found. Upload a file first.")
    charts = auto_overview(df, palette=palette, max_charts=min(max_charts, 12))
    return {"charts": charts, "total": len(charts)}

@router.get("/kpis")
def kpis(palette: str = "Indigo", user: dict = Depends(get_current_user)):
    _bootstrap()
    from agents.viz_agent import kpi_charts
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found. Upload a file first.")
    return kpi_charts(df, palette=palette)

@router.get("/health")
def health(): return {"status": "ok"}


class CustomChartRequest:
    pass

from pydantic import BaseModel
from typing import Optional

class ChartRequest(BaseModel):
    chart_type: str = "Bar"
    x: str = ""
    x_col: str = ""   # alias sent by frontend
    y: str = ""
    y_col: str = ""   # alias sent by frontend
    color: Optional[str] = None
    size: Optional[str] = None
    title: str = "Chart"

@router.post("/custom")
def custom_chart(req: ChartRequest, user: dict = Depends(get_current_user)):
    """Build a custom chart from column selections."""
    import plotly.express as px
    import json, hashlib
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(404, "No dataset found")

    # Support both x/y and x_col/y_col field names
    x = req.x or req.x_col
    y = req.y or req.y_col

    # - Result cache: same user + same params + same dataset shape - return cached -
    cache_key = hashlib.md5(
        f"{user['email']}:{req.chart_type}:{x}:{y}:{req.color}:{req.size}:{len(df)}:{list(df.columns)}".encode()
    ).hexdigest()
    from app.services.data_store import get_ai_cache
    _cache = get_ai_cache()
    cached = _cache.get(f"chart:{cache_key}")
    if cached:
        return cached

    # - Sample large datasets for faster rendering -
    MAX_ROWS = 5000
    if len(df) > MAX_ROWS:
        df = df.sample(n=MAX_ROWS, random_state=42).reset_index(drop=True)

    try:
        ct = req.chart_type.lower()
        kwargs = dict(title=req.title, template="plotly_dark")
        if req.color and req.color in df.columns:
            kwargs["color"] = req.color

        if ct == "bar":
            fig = px.bar(df, x=x, y=y, **kwargs)
        elif ct == "line":
            fig = px.line(df, x=x, y=y, **kwargs)
        elif ct == "scatter":
            fig = px.scatter(df, x=x, y=y, **kwargs)
        elif ct == "pie":
            # If values column is non-numeric or missing, use value_counts instead
            import numpy as np
            if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]):
                fig = px.pie(df, names=x, values=y, **kwargs)
            else:
                # Count occurrences of each category
                counts = df[x].value_counts().reset_index()
                counts.columns = [x, "count"]
                fig = px.pie(counts, names=x, values="count", **kwargs)
        elif ct == "histogram":
            fig = px.histogram(df, x=x, **kwargs)
        elif ct == "box":
            fig = px.box(df, x=x, y=y, **kwargs)
        elif ct == "area":
            fig = px.area(df, x=x, y=y, **kwargs)
        elif ct == "heatmap":
            import numpy as np
            nums = df.select_dtypes(include=np.number)
            corr = nums.corr()
            import plotly.graph_objects as go
            fig = go.Figure(go.Heatmap(z=corr.values.tolist(), x=corr.columns.tolist(), y=corr.columns.tolist(), colorscale="RdBu"))
            fig.update_layout(title=req.title, template="plotly_dark")
        elif ct == "treemap":
            fig = px.treemap(df, path=[x], values=y, **kwargs)
        elif ct in ("radar", "spider", "circular"):
            # Radar/Spider chart
            import plotly.graph_objects as go
            import numpy as np
            nums = df.select_dtypes(include=np.number).columns.tolist()[:8]
            means = df[nums].mean().tolist()
            fig = go.Figure(go.Scatterpolar(r=means, theta=nums, fill="toself", name="Mean Values"))
            fig.update_layout(title=req.title, template="plotly_dark", polar=dict(radialaxis=dict(visible=True)))
        elif ct == "waterfall":
            import plotly.graph_objects as go
            vals = df[y].dropna().head(20).tolist() if y and y in df.columns else []
            labels = df[x].head(20).astype(str).tolist() if x and x in df.columns else [str(i) for i in range(len(vals))]
            fig = go.Figure(go.Waterfall(x=labels, y=vals, name="Waterfall",
                connector={"line": {"color": "rgb(63,63,63)"}},
                increasing={"marker": {"color": "#22c55e"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#6366f1"}}))
            fig.update_layout(title=req.title, template="plotly_dark")
        elif ct in ("stacked_bar", "stacked bar"):
            fig = px.bar(df, x=x, y=y, color=req.color or y, barmode="stack", **{k:v for k,v in kwargs.items() if k!="color"})
        elif ct in ("stacked_area", "stacked area"):
            fig = px.area(df, x=x, y=y, color=req.color or y, **{k:v for k,v in kwargs.items() if k!="color"})
        elif ct == "bubble":
            import numpy as np
            size_col = req.size or y
            if size_col and size_col in df.columns and pd.api.types.is_numeric_dtype(df[size_col]):
                # Plotly requires size >= 0 - shift negative values up
                size_vals = df[size_col].fillna(0)
                mn = size_vals.min()
                if mn < 0:
                    size_vals = size_vals - mn  # shift so min = 0
                size_vals = size_vals + 1  # ensure all > 0
                df = df.copy()
                df["__bubble_size__"] = size_vals
                fig = px.scatter(df, x=x, y=y, size="__bubble_size__", color=req.color, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, color=req.color, **kwargs)
        elif ct in ("violin",):
            fig = px.violin(df, x=x, y=y, box=True, **kwargs)
        elif ct in ("funnel",):
            fig = px.funnel(df, x=y, y=x, **kwargs)
        elif ct in ("sunburst",):
            fig = px.sunburst(df, path=[x], values=y, **kwargs)
        elif ct in ("marimekko", "variable width", "mekko"):
            # Marimekko / Variable Width Column Chart
            import plotly.graph_objects as go
            import numpy as np
            if x and y and x in df.columns and y in df.columns:
                grp = df.groupby(x)[y].sum().reset_index()
                total = grp[y].sum()
                widths = (grp[y] / total * 100).tolist()
                labels = grp[x].astype(str).tolist()
                values = grp[y].tolist()
                # Build bars with variable widths using x offsets
                offsets = [0] + list(np.cumsum(widths[:-1]))
                colors = px.colors.qualitative.Plotly
                traces = []
                for i, (lbl, w, v, off) in enumerate(zip(labels, widths, values, offsets)):
                    traces.append(go.Bar(
                        x=[off + w/2], y=[v], width=[w],
                        name=lbl, marker_color=colors[i % len(colors)],
                        text=f"{lbl}<br>{v:.0f}", textposition="inside",
                    ))
                fig = go.Figure(traces)
                fig.update_layout(
                    title=req.title, template="plotly_dark", barmode="overlay",
                    xaxis=dict(title="Share (%)", tickvals=[o+w/2 for o,w in zip(offsets,widths)], ticktext=labels),
                    yaxis_title=y, showlegend=False,
                )
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)
        elif ct in ("table_sparkline", "table with charts", "embedded table"):
            # Table with embedded sparklines
            import plotly.graph_objects as go
            import numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:5]
            cat_cols = df.select_dtypes(include="object").columns.tolist()[:2]
            display_cols = (cat_cols + num_cols)[:6]
            sample = df[display_cols].head(20)
            # Build sparkline as unicode bar chars per numeric column
            def sparkline(series):
                mn, mx = series.min(), series.max()
                rng = mx - mn or 1
                bars = "-"
                return "".join(bars[int((v - mn) / rng * 7)] for v in series.dropna().head(10))
            header_vals = list(display_cols)
            cell_vals = []
            for col in display_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    cell_vals.append([f"{v:.2f}" if pd.notna(v) else "-" for v in sample[col]])
                else:
                    cell_vals.append([str(v)[:20] for v in sample[col]])
            # Add sparkline row for numeric cols
            spark_row = []
            for col in display_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    spark_row.append(sparkline(df[col]))
                else:
                    spark_row.append("")
            fig = go.Figure(go.Table(
                header=dict(values=header_vals, fill_color="#18181b", font=dict(color="#a1a1aa", size=12), align="left"),
                cells=dict(values=cell_vals, fill_color="#09090b", font=dict(color="#e4e4e7", size=11), align="left"),
            ))
            fig.update_layout(title=req.title, template="plotly_dark")
        elif ct in ("3d area", "3d_area", "surface"):
            # 3D Area / Surface Chart
            import plotly.graph_objects as go
            import numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(num_cols) >= 2:
                xc, yc = num_cols[0], num_cols[1]
                zc = num_cols[2] if len(num_cols) > 2 else num_cols[0]
                sample = df[[xc, yc, zc]].dropna().head(500)
                fig = go.Figure(go.Scatter3d(
                    x=sample[xc], y=sample[yc], z=sample[zc],
                    mode="lines+markers",
                    marker=dict(size=3, color=sample[zc], colorscale="Viridis", opacity=0.8),
                    line=dict(color="#6366f1", width=2),
                ))
                fig.update_layout(
                    title=req.title, template="plotly_dark",
                    scene=dict(xaxis_title=xc, yaxis_title=yc, zaxis_title=zc),
                )
            else:
                fig = px.area(df, x=x, y=y, **kwargs)

        # - 2026 Trending Chart Types -
        elif ct in ("sankey", "alluvial", "flow"):
            # Alluvial / Sankey Flow Diagram
            import plotly.graph_objects as go
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns else None
                grp = df.groupby([src_col, tgt_col])
                if val_col and pd.api.types.is_numeric_dtype(df[val_col]):
                    flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index()
                    flow_vals = flows[val_col].tolist()
                else:
                    flows = df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                    flow_vals = flows["count"].tolist()
                all_nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(all_nodes)}
                fig = go.Figure(go.Sankey(
                    node=dict(label=all_nodes, pad=15, thickness=20,
                              color=["#6366f1"] * len(all_nodes)),
                    link=dict(
                        source=[node_idx[s] for s in flows[src_col]],
                        target=[node_idx[t] for t in flows[tgt_col]],
                        value=flow_vals,
                        color="rgba(99,102,241,0.3)",
                    )
                ))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("beeswarm", "bee swarm", "strip"):
            # Beeswarm / Strip Plot - individual data points without overlap
            import plotly.graph_objects as go
            import numpy as np
            num_col = y if y and y in df.columns else x
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            if cat_col:
                fig = px.strip(df, x=cat_col, y=num_col, color=cat_col,
                               stripmode="overlay", **{k:v for k,v in kwargs.items() if k!="color"})
            else:
                vals = df[num_col].dropna().head(500).tolist()
                jitter = np.random.uniform(-0.3, 0.3, len(vals))
                fig = go.Figure(go.Scatter(
                    x=jitter, y=vals, mode="markers",
                    marker=dict(color="#6366f1", size=5, opacity=0.7),
                    name=num_col,
                ))
                fig.update_layout(title=req.title, template="plotly_dark",
                                  xaxis=dict(showticklabels=False, title=""),
                                  yaxis_title=num_col)

        elif ct in ("bullet", "bullet chart", "kpi bullet"):
            # Bullet Chart - actual vs target vs performance range
            import plotly.graph_objects as go
            import numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:6]
            if not num_cols:
                fig = px.bar(df, x=x, y=y, **kwargs)
            else:
                means = df[num_cols].mean()
                maxes = df[num_cols].max()
                targets = means * 1.1  # target = 10% above mean
                fig = go.Figure()
                for i, col in enumerate(num_cols):
                    fig.add_trace(go.Indicator(
                        mode="number+gauge+delta",
                        value=float(means[col]),
                        delta={"reference": float(targets[col])},
                        title={"text": col, "font": {"size": 11}},
                        gauge={
                            "axis": {"range": [0, float(maxes[col])]},
                            "bar": {"color": "#6366f1"},
                            "steps": [
                                {"range": [0, float(means[col]) * 0.5], "color": "rgba(239,68,68,.2)"},
                                {"range": [float(means[col]) * 0.5, float(means[col]) * 0.9], "color": "rgba(251,191,36,.2)"},
                                {"range": [float(means[col]) * 0.9, float(maxes[col])], "color": "rgba(34,197,94,.2)"},
                            ],
                            "threshold": {"line": {"color": "#f59e0b", "width": 3}, "value": float(targets[col])},
                        },
                        domain={"row": i, "column": 0},
                    ))
                fig.update_layout(
                    title=req.title, template="plotly_dark",
                    grid={"rows": len(num_cols), "columns": 1, "pattern": "independent"},
                    height=max(300, len(num_cols) * 120),
                )

        elif ct in ("small multiples", "grid charts", "facet"):
            # Small Multiples / Facet Grid
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            num_col = y if y and y in df.columns else (x if x and x in df.columns else None)
            if cat_col and num_col:
                fig = px.histogram(df, x=num_col, facet_col=cat_col,
                                   facet_col_wrap=3, **kwargs)
                fig.update_layout(height=500)
            elif num_col:
                num_cols = df.select_dtypes(include="number").columns.tolist()[:6]
                fig = px.histogram(df, x=num_cols[0], facet_col_wrap=3, **kwargs)
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("rose", "polar area", "nightingale", "coxcomb"):
            # Rose / Polar Area Chart (Nightingale)
            import plotly.graph_objects as go
            import numpy as np
            if x and x in df.columns:
                counts = df[x].value_counts().head(12)
                labels = counts.index.astype(str).tolist()
                values = counts.values.tolist()
            else:
                num_cols = df.select_dtypes(include=np.number).columns.tolist()[:12]
                labels = num_cols
                values = df[num_cols].mean().tolist()
            fig = go.Figure(go.Barpolar(
                r=values, theta=labels,
                marker=dict(
                    color=values, colorscale="Plasma",
                    line=dict(color="rgba(255,255,255,.1)", width=1),
                ),
                opacity=0.85,
            ))
            fig.update_layout(
                title=req.title, template="plotly_dark",
                polar=dict(radialaxis=dict(visible=True, showticklabels=False)),
            )

        elif ct in ("timeseries", "time series", "multi timeseries", "time-series"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:5]
            x_col = x if x and x in df.columns else df.columns[0]
            colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
            fig = go.Figure()
            for i, col in enumerate(num_cols):
                vals = df[col].dropna()
                xs = df[x_col].head(len(vals)).astype(str).tolist()
                fig.add_trace(go.Scatter(
                    x=xs, y=vals.tolist(), mode="lines",
                    name=col, line=dict(color=colors[i % len(colors)], width=2),
                    fill="tozeroy" if i == 0 else "tonexty",
                ))
            fig.update_layout(
                title=req.title, template="plotly_dark",
                hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True)),
            )

        elif ct in ("infographic", "story", "summary"):
            # Infographic-style Summary Chart
            import plotly.graph_objects as go
            import numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:4]
            fig = go.Figure()
            colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"]
            for i, col in enumerate(num_cols):
                mean_val = float(df[col].mean())
                max_val = float(df[col].max())
                fig.add_trace(go.Indicator(
                    mode="number+delta",
                    value=mean_val,
                    delta={"reference": max_val * 0.8, "relative": True},
                    title={"text": f"<b>{col}</b><br><span style='font-size:0.8em'>avg</span>",
                           "font": {"size": 13, "color": colors[i % len(colors)]}},
                    number={"font": {"color": colors[i % len(colors)], "size": 28}},
                    domain={"row": 0, "column": i},
                ))
            fig.update_layout(
                title=req.title, template="plotly_dark",
                grid={"rows": 1, "columns": len(num_cols), "pattern": "independent"},
                height=220,
            )

        elif ct in ("network", "network graph", "graph", "force graph"):
            # Network Graph - relationship visualization using scatter + lines
            import plotly.graph_objects as go
            import numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                pairs = df[[src_col, tgt_col]].dropna().head(80)
                nodes = list(pd.unique(pairs[[src_col, tgt_col]].values.ravel()))
                n = len(nodes)
                # Circular layout
                angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
                pos = {node: (np.cos(a), np.sin(a)) for node, a in zip(nodes, angles)}
                # Edge traces
                edge_x, edge_y = [], []
                for _, row in pairs.iterrows():
                    x0, y0 = pos[row[src_col]]
                    x1, y1 = pos[row[tgt_col]]
                    edge_x += [x0, x1, None]
                    edge_y += [y0, y1, None]
                edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                    line=dict(width=1, color="rgba(99,102,241,0.4)"), hoverinfo="none")
                # Node traces
                node_x = [pos[n][0] for n in nodes]
                node_y = [pos[n][1] for n in nodes]
                # Count connections per node
                deg = pairs[src_col].value_counts().to_dict()
                deg.update({k: deg.get(k, 0) + v for k, v in pairs[tgt_col].value_counts().items()})
                node_sizes = [max(8, min(30, deg.get(nd, 1) * 3)) for nd in nodes]
                node_trace = go.Scatter(
                    x=node_x, y=node_y, mode="markers+text",
                    text=[str(nd)[:15] for nd in nodes],
                    textposition="top center",
                    textfont=dict(size=9, color="#a1a1aa"),
                    marker=dict(size=node_sizes, color=node_sizes,
                                colorscale="Plasma", showscale=True,
                                colorbar=dict(title="Connections", thickness=12)),
                    hovertext=[f"{nd} ({deg.get(nd,0)} connections)" for nd in nodes],
                    hoverinfo="text",
                )
                fig = go.Figure([edge_trace, node_trace])
                fig.update_layout(
                    title=req.title, template="plotly_dark",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                )
            else:
                # Fallback: correlation network from numeric cols
                import numpy as np
                num_cols = df.select_dtypes(include=np.number).columns.tolist()[:10]
                corr = df[num_cols].corr().abs()
                n = len(num_cols)
                angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
                pos = {col: (np.cos(a), np.sin(a)) for col, a in zip(num_cols, angles)}
                edge_x, edge_y = [], []
                for i, c1 in enumerate(num_cols):
                    for j, c2 in enumerate(num_cols):
                        if i < j and corr.loc[c1, c2] > 0.5:
                            x0, y0 = pos[c1]; x1, y1 = pos[c2]
                            edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
                node_trace = go.Scatter(
                    x=[pos[c][0] for c in num_cols], y=[pos[c][1] for c in num_cols],
                    mode="markers+text", text=num_cols, textposition="top center",
                    textfont=dict(size=9, color="#a1a1aa"),
                    marker=dict(size=14, color="#6366f1"),
                )
                edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                    line=dict(width=1, color="rgba(99,102,241,0.4)"), hoverinfo="none")
                fig = go.Figure([edge_trace, node_trace])
                fig.update_layout(title=f"{req.title} (Correlation Network)", template="plotly_dark",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

        elif ct in ("gantt", "gantt chart", "timeline", "project timeline"):
            # Gantt Chart - project/task timeline
            import plotly.graph_objects as go
            import numpy as np
            # Try to find task, start, end columns by name heuristics
            cols_lower = {c.lower(): c for c in df.columns}
            task_col = next((cols_lower[k] for k in cols_lower if any(w in k for w in ["task","name","item","activity","label"])), None)
            start_col = next((cols_lower[k] for k in cols_lower if any(w in k for w in ["start","begin","from"])), None)
            end_col = next((cols_lower[k] for k in cols_lower if any(w in k for w in ["end","finish","to","due"])), None)
            # Fallback: use x as task, y as duration, build synthetic start/end
            if not task_col:
                task_col = x if x and x in df.columns else df.columns[0]
            if start_col and end_col:
                sample = df[[task_col, start_col, end_col]].dropna().head(20)
                fig = px.timeline(sample, x_start=start_col, x_end=end_col, y=task_col,
                                  color=task_col, **{k:v for k,v in kwargs.items() if k!="color"})
                fig.update_yaxes(autorange="reversed")
            else:
                # Synthetic Gantt from numeric column as duration
                num_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                if not num_col:
                    num_cols = df.select_dtypes(include=np.number).columns.tolist()
                    num_col = num_cols[0] if num_cols else None
                sample = df[[task_col] + ([num_col] if num_col else [])].dropna().head(15)
                tasks = sample[task_col].astype(str).tolist()
                durations = sample[num_col].tolist() if num_col else [1] * len(tasks)
                # Build cumulative start times
                starts = [0] + list(np.cumsum(durations[:-1]))
                colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#0ea5e9"]
                fig = go.Figure()
                for i, (task, start, dur) in enumerate(zip(tasks, starts, durations)):
                    fig.add_trace(go.Bar(
                        x=[dur], y=[task], orientation="h",
                        base=start, name=task,
                        marker_color=colors[i % len(colors)],
                        text=f"{dur:.1f}", textposition="inside",
                    ))
                fig.update_layout(
                    title=req.title, template="plotly_dark",
                    barmode="overlay", showlegend=False,
                    xaxis_title="Duration / Units",
                    yaxis=dict(autorange="reversed"),
                )

        # - Ultra-Advanced / AI-Era Chart Types -
        elif ct in ("parallel coordinates", "parallel coords", "parallel"):
            # Parallel Coordinates - high-dimensional data, each line = one record
            import numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:12]
            if not num_cols:
                fig = px.bar(df, x=x, y=y, **kwargs)
            else:
                import plotly.graph_objects as go
                color_col = num_cols[0]
                dims = [dict(range=[df[c].min(), df[c].max()],
                             label=c, values=df[c].dropna().tolist()) for c in num_cols]
                fig = go.Figure(go.Parcoords(
                    line=dict(color=df[color_col], colorscale="Plasma",
                              showscale=True, colorbar=dict(title=color_col, thickness=12)),
                    dimensions=dims,
                ))
                fig.update_layout(title=req.title, template="plotly_dark")

        elif ct in ("chord", "chord diagram"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                if val_col:
                    flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index()
                    flow_vals = flows[val_col].tolist()
                else:
                    flows = df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                    flow_vals = flows["count"].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
                fig = go.Figure(go.Sankey(
                    node=dict(label=nodes, pad=20, thickness=15,
                              color=px.colors.qualitative.Plotly[:len(nodes)]),
                    link=dict(
                        source=[node_idx[s] for s in flows[src_col]],
                        target=[node_idx[t] for t in flows[tgt_col]],
                        value=flow_vals,
                    )
                ))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        # - Advanced / AI-Era Chart Types -
        elif ct in ("parallel coordinates", "parallel coords", "parallel"):
            import numpy as np, plotly.graph_objects as go
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:12]
            if not num_cols:
                fig = px.bar(df, x=x, y=y, **kwargs)
            else:
                color_col = num_cols[0]
                dims = [dict(range=[float(df[c].min()), float(df[c].max())],
                             label=c, values=df[c].fillna(0).tolist()) for c in num_cols]
                fig = go.Figure(go.Parcoords(
                    line=dict(color=df[color_col].fillna(0), colorscale="Plasma",
                              showscale=True, colorbar=dict(title=color_col, thickness=12)),
                    dimensions=dims,
                ))
                fig.update_layout(title=req.title, template="plotly_dark")

        elif ct in ("chord", "chord diagram"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                if val_col:
                    flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index()
                    flow_vals = flows[val_col].tolist()
                else:
                    flows = df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                    flow_vals = flows["count"].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
        elif ct in ("chord", "chord diagram"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index() if val_col else df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                flow_vals = flows[val_col if val_col else "count"].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
                fig = go.Figure(go.Sankey(
                    arrangement="circular",
                    node=dict(label=nodes, pad=20, thickness=15,
                              color=px.colors.qualitative.Plotly[:len(nodes)]),
                    link=dict(
                        source=[node_idx[s] for s in flows[src_col]],
                        target=[node_idx[t] for t in flows[tgt_col]],
                        value=flow_vals,
                        color=[f"rgba(99,102,241,{min(0.8, v/mx):.2f})" for v in flow_vals],
                    )
                ))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

            import numpy as np, plotly.graph_objects as go
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:12]
            if not num_cols:
                fig = px.bar(df, x=x, y=y, **kwargs)
            else:
                color_col = num_cols[0]
                dims = [dict(range=[float(df[c].min()), float(df[c].max())],
                             label=c, values=df[c].fillna(0).tolist()) for c in num_cols]
                fig = go.Figure(go.Parcoords(
                    line=dict(color=df[color_col].fillna(0), colorscale="Plasma",
                              showscale=True, colorbar=dict(title=color_col, thickness=12)),
                    dimensions=dims,
                ))
                fig.update_layout(title=req.title, template="plotly_dark")

        elif ct in ("chord", "chord diagram"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index() if val_col else df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                flow_vals = flows[val_col if val_col else "count"].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
                fig = go.Figure(go.Sankey(
                    arrangement="circular",
                    node=dict(label=nodes, pad=20, thickness=15,
                              color=px.colors.qualitative.Plotly[:len(nodes)]),
                    link=dict(
                        source=[node_idx[s] for s in flows[src_col]],
                        target=[node_idx[t] for t in flows[tgt_col]],
                        value=flow_vals,
                        color=[f"rgba(99,102,241,{min(0.8, v/mx):.2f})" for v in flow_vals],
                    )
                ))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("hexbin", "hex", "hexagonal"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc:
                fig = go.Figure(go.Histogram2d(
                    x=df[xc].dropna(), y=df[yc].dropna(),
                    colorscale="Plasma", nbinsx=30, nbinsy=30,
                    colorbar=dict(title="Count"),
                ))
                fig.update_layout(title=req.title, template="plotly_dark",
                                  xaxis_title=xc, yaxis_title=yc)
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("ridgeline", "ridge", "joy plot", "joyplot"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            colors = px.colors.qualitative.Plotly
            fig = go.Figure()
            if cat_col and num_col:
                for i, grp in enumerate(df[cat_col].dropna().unique()[:10]):
                    vals = df[df[cat_col] == grp][num_col].dropna().tolist()
                    if vals:
                        fig.add_trace(go.Violin(x=vals, name=str(grp), side="positive",
                            orientation="h", line_color=colors[i % len(colors)],
                            meanline_visible=True))
            else:
                for i, col in enumerate(df.select_dtypes(include=np.number).columns.tolist()[:6]):
                    vals = df[col].dropna().tolist()
                    fig.add_trace(go.Violin(x=vals, name=col, side="positive",
                        orientation="h", line_color=colors[i % len(colors)],
                        meanline_visible=True))
            fig.update_layout(title=req.title, template="plotly_dark",
                              violingap=0, violinmode="overlay")

        elif ct in ("streamgraph", "stream", "stream graph"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:6]
            x_col = x if x and x in df.columns else df.columns[0]
            colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9"]
            fig = go.Figure()
            for i, col in enumerate(num_cols):
                fig.add_trace(go.Scatter(
                    x=df[x_col].astype(str).tolist(), y=df[col].fillna(0).tolist(),
                    name=col, mode="lines", stackgroup="one", groupnorm="percent",
                    line=dict(width=0.5, color=colors[i % len(colors)]),
                ))
            fig.update_layout(title=req.title, template="plotly_dark",
                              hovermode="x unified", yaxis_title="% Share")

        elif ct in ("dendrogram", "hierarchical clustering", "cluster tree"):
            import plotly.figure_factory as ff, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:20]
            if len(num_cols) >= 2:
                sample = df[num_cols].dropna().head(50)
                fig = ff.create_dendrogram(sample.values,
                    labels=[str(i) for i in sample.index],
                    colorscale=px.colors.sequential.Plasma)
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("voronoi", "voronoi diagram", "spatial partition"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            # Always use numeric columns for voronoi, ignore x/y if they're categorical
            xc = num_cols[0] if num_cols else None
            yc = num_cols[1] if len(num_cols) > 1 else xc
            if xc and yc:
                try:
                    from scipy.spatial import Voronoi
                    pts = df[[xc, yc]].dropna().head(200).values
                    vor = Voronoi(pts)
                    fig = go.Figure()
                    for simplex in vor.ridge_vertices:
                        if -1 not in simplex:
                            p1, p2 = vor.vertices[simplex[0]], vor.vertices[simplex[1]]
                            fig.add_trace(go.Scatter(x=[p1[0], p2[0]], y=[p1[1], p2[1]],
                                mode="lines", line=dict(color="rgba(99,102,241,0.5)", width=1),
                                showlegend=False, hoverinfo="none"))
                    fig.add_trace(go.Scatter(x=pts[:, 0], y=pts[:, 1], mode="markers",
                        marker=dict(color="#6366f1", size=5), name="Points"))
                    fig.update_layout(title=req.title, template="plotly_dark",
                                      xaxis_title=xc, yaxis_title=yc)
                except ImportError:
                    fig = px.scatter(df, x=xc, y=yc, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("uncertainty", "confidence bands", "forecast bands", "probabilistic"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            x_col = x if x and x in df.columns else df.columns[0]
            if num_col and num_col in df.columns:
                vals = df[num_col].fillna(0)
                xs = df[x_col].astype(str).tolist()
                window = max(3, len(vals) // 20)
                mean = vals.rolling(window, min_periods=1).mean()
                std = vals.rolling(window, min_periods=1).std().fillna(0)
                fig = go.Figure([
                    go.Scatter(x=xs, y=(mean + 2*std).tolist(), mode="lines",
                               line=dict(width=0), showlegend=False),
                    go.Scatter(x=xs, y=(mean - 2*std).tolist(), mode="lines",
                               fill="tonexty", fillcolor="rgba(99,102,241,0.15)",
                               line=dict(width=0), name="95% CI"),
                    go.Scatter(x=xs, y=mean.tolist(), mode="lines",
                               line=dict(color="#6366f1", width=2), name="Mean"),
                    go.Scatter(x=xs, y=vals.tolist(), mode="markers",
                               marker=dict(color="#f59e0b", size=3, opacity=0.5), name="Actual"),
                ])
                fig.update_layout(title=req.title, template="plotly_dark", hovermode="x unified")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("tsne", "t-sne", "umap", "embedding", "pca", "dimensionality reduction"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(num_cols) >= 2:
                from sklearn.preprocessing import StandardScaler
                from sklearn.decomposition import PCA as _PCA
                sample = df[num_cols].dropna().head(500)
                scaled = StandardScaler().fit_transform(sample)
                n_comp = min(2, scaled.shape[1])
                coords = _PCA(n_components=n_comp).fit_transform(scaled)
                cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
                hover = df[cat_col].iloc[sample.index].astype(str).tolist() if cat_col else [str(i) for i in sample.index]
                fig = go.Figure(go.Scatter(
                    x=coords[:, 0], y=coords[:, 1] if n_comp > 1 else [0]*len(coords),
                    mode="markers",
                    marker=dict(size=5, opacity=0.7, color=list(range(len(coords))), colorscale="Plasma"),
                    text=hover, hoverinfo="text",
                ))
                fig.update_layout(title=f"{req.title} (PCA 2D)", template="plotly_dark",
                                  xaxis_title="PC1", yaxis_title="PC2")
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("shap", "feature importance", "shap plot"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:15]
            if features and target:
                from sklearn.ensemble import RandomForestRegressor
                rf = RandomForestRegressor(n_estimators=30, max_depth=4, random_state=42)
                rf.fit(df[features].fillna(0).head(500), df[target].fillna(0).head(500))
                imp = rf.feature_importances_
                idx = np.argsort(imp)
                fig = go.Figure(go.Bar(
                    x=imp[idx], y=[features[i] for i in idx], orientation="h",
                    marker=dict(color=imp[idx], colorscale="Plasma"),
                ))
                fig.update_layout(title=f"{req.title} - Feature Importance",
                                  template="plotly_dark",
                                  xaxis_title="Importance", yaxis_title="Feature")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("choropleth", "geo heatmap", "geospatial", "map heatmap"):
            import plotly.graph_objects as go
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            num_cols = df.select_dtypes(include="number").columns.tolist()
            loc_col = x if x and x in df.columns else (cat_cols[0] if cat_cols else None)
            val_col = y if y and y in df.columns else (num_cols[0] if num_cols else None)
            if loc_col and val_col:
                agg = df.groupby(loc_col)[val_col].mean().reset_index()
                fig = go.Figure(go.Choropleth(
                    locations=agg[loc_col].astype(str), z=agg[val_col],
                    locationmode="country names", colorscale="Plasma",
                    colorbar_title=val_col,
                ))
                fig.update_layout(title=req.title, template="plotly_dark",
                                  geo=dict(showframe=False, showcoastlines=True,
                                           bgcolor="rgba(0,0,0,0)"))
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("event stream", "event timeline", "temporal events"):
            import plotly.graph_objects as go
            cat_col = x if x and x in df.columns else df.columns[0]
            events = df[[cat_col]].dropna().head(100)[cat_col].astype(str).tolist()
            times = list(range(len(events)))
            unique_events = list(dict.fromkeys(events))
            colors = px.colors.qualitative.Plotly
            color_map = {e: colors[i % len(colors)] for i, e in enumerate(unique_events)}
            fig = go.Figure()
            for evt in unique_events:
                idxs = [i for i, e in enumerate(events) if e == evt]
                fig.add_trace(go.Scatter(
                    x=[times[i] for i in idxs], y=[evt]*len(idxs), mode="markers",
                    marker=dict(symbol="line-ns", size=16,
                                line=dict(width=2, color=color_map[evt])),
                    name=evt,
                ))
            fig.update_layout(title=req.title, template="plotly_dark",
                              xaxis_title="Event Index", yaxis_title="Event Type",
                              hovermode="closest")

        else:
            fig = px.bar(df, x=x, y=y, **kwargs)

        fig.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
        result = {"plotly_json": json.loads(fig.to_json()), "title": req.title}
        try:
            _cache[f"chart:{cache_key}"] = result
        except Exception:
            pass
        return result
    except Exception as e:
        raise HTTPException(422, f"Chart error: {e}")
