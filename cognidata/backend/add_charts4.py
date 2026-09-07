import pathlib
VIZ = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py")
BLOCK = """
        # Expert-Level Chart Types Batch 4
        elif ct in ("nelson aalen", "nelson-aalen", "cumulative hazard"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                times = np.sort(df[num_col].dropna().values)
                n = len(times)
                cumhaz = np.array([sum(1/(n-j) for j in range(i+1)) for i in range(n)])
                fig = go.Figure(go.Scatter(x=times.tolist(), y=cumhaz.tolist(), mode="lines", line=dict(color="#8b5cf6", width=2, shape="hv"), name="H(t)"))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Time", yaxis_title="Cumulative Hazard")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("hazard function", "hazard plot", "hazard rate"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                times = np.sort(df[num_col].dropna().values)
                n = len(times)
                hazard = np.array([1/(n-i) if n-i > 0 else 0 for i in range(n)])
                fig = go.Figure(go.Scatter(x=times.tolist(), y=hazard.tolist(), mode="lines", fill="tozeroy", line=dict(color="#ef4444", width=2), fillcolor="rgba(239,68,68,0.15)", name="h(t)"))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Time", yaxis_title="Hazard Rate")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("autocorrelation heatmap", "acf heatmap", "auto-correlation heatmap"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:8]
            if len(num_cols) >= 2:
                lags = min(20, len(df)//4)
                acf_matrix = []
                for col in num_cols:
                    vals = df[col].dropna().values
                    row = [np.corrcoef(vals[:-k], vals[k:])[0,1] if k > 0 else 1.0 for k in range(lags+1)]
                    acf_matrix.append(row)
                fig = go.Figure(go.Heatmap(z=acf_matrix, x=list(range(lags+1)), y=num_cols, colorscale="RdBu", zmid=0, colorbar=dict(title="ACF")))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Lag", yaxis_title="Variable")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("scalogram", "wavelet", "wavelet plot"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                vals = df[num_col].dropna().values[:256]
                n = len(vals)
                scales = np.arange(1, min(64, n//4)+1)
                cwt = np.zeros((len(scales), n))
                for i, s in enumerate(scales):
                    kernel_size = min(int(s*4), n)
                    kernel = np.exp(-0.5*(np.linspace(-2,2,kernel_size))**2) * np.cos(2*np.pi*np.linspace(-2,2,kernel_size))
                    if len(kernel) <= n:
                        conv = np.convolve(vals, kernel[::-1], mode="same")
                        cwt[i] = np.abs(conv)
                fig = go.Figure(go.Heatmap(z=cwt.tolist(), x=list(range(n)), y=scales.tolist(), colorscale="Plasma", colorbar=dict(title="Magnitude")))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Time", yaxis_title="Scale")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("coherence", "coherence plot", "spectral coherence"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc and xc != yc:
                a = df[xc].dropna().values; b = df[yc].dropna().values
                n = min(len(a), len(b)); a, b = a[:n], b[:n]
                fa = np.fft.rfft(a - a.mean()); fb = np.fft.rfft(b - b.mean())
                freqs = np.fft.rfftfreq(n)
                coherence = np.abs(fa * np.conj(fb))**2 / (np.abs(fa)**2 * np.abs(fb)**2 + 1e-10)
                fig = go.Figure(go.Scatter(x=freqs[1:].tolist(), y=coherence[1:].tolist(), mode="lines", line=dict(color="#6366f1", width=2), fill="tozeroy", fillcolor="rgba(99,102,241,0.15)"))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Frequency", yaxis_title="Coherence", yaxis=dict(range=[0,1]))
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("community graph", "community detection", "cluster network"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:10]
            if len(num_cols) >= 3:
                corr = df[num_cols].corr().abs()
                n = len(num_cols)
                angles = np.linspace(0, 2*np.pi, n, endpoint=False)
                pos = {col: (np.cos(a), np.sin(a)) for col, a in zip(num_cols, angles)}
                threshold = 0.5
                communities = {}
                for i, c1 in enumerate(num_cols):
                    for j, c2 in enumerate(num_cols):
                        if i < j and corr.loc[c1, c2] > threshold:
                            grp = min(i, j) % 4
                            communities[c1] = grp; communities[c2] = grp
                colors_c = ["#6366f1","#10b981","#f59e0b","#ef4444"]
                edge_x, edge_y = [], []
                for i, c1 in enumerate(num_cols):
                    for j, c2 in enumerate(num_cols):
                        if i < j and corr.loc[c1, c2] > threshold:
                            x0,y0 = pos[c1]; x1,y1 = pos[c2]
                            edge_x += [x0,x1,None]; edge_y += [y0,y1,None]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="rgba(99,102,241,0.3)", width=1), showlegend=False))
                fig.add_trace(go.Scatter(x=[pos[c][0] for c in num_cols], y=[pos[c][1] for c in num_cols], mode="markers+text", text=num_cols, textposition="top center", textfont=dict(size=9), marker=dict(size=14, color=[colors_c[communities.get(c,0)] for c in num_cols])))
                fig.update_layout(title=req.title, template="plotly_dark", showlegend=False, xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False))
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("sensitivity analysis", "sensitivity plot", "tornado sensitivity"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:12]
            if features and target:
                base = float(df[target].mean())
                sensitivities = []
                for feat in features:
                    low = df[df[feat] < df[feat].quantile(0.25)][target].mean()
                    high = df[df[feat] > df[feat].quantile(0.75)][target].mean()
                    sensitivities.append((feat, float(low - base), float(high - base)))
                sensitivities.sort(key=lambda x: abs(x[2]-x[1]), reverse=True)
                feats, lows, highs = zip(*sensitivities)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=list(feats), x=list(lows), orientation="h", name="Low (-25%)", marker_color="#ef4444"))
                fig.add_trace(go.Bar(y=list(feats), x=list(highs), orientation="h", name="High (+75%)", marker_color="#10b981"))
                fig.update_layout(title=req.title, template="plotly_dark", barmode="overlay", xaxis_title="Impact on Target")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("strategy map", "balanced scorecard", "scorecard"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:8]
            perspectives = ["Financial", "Customer", "Internal Process", "Learning & Growth"]
            fig = go.Figure()
            colors_s = ["#6366f1","#10b981","#f59e0b","#ef4444"]
            for i, (persp, color) in enumerate(zip(perspectives, colors_s)):
                cols_in_persp = num_cols[i*2:(i+1)*2] if len(num_cols) > i*2 else []
                for j, col in enumerate(cols_in_persp):
                    val = float(df[col].mean()) if col in df.columns else 0
                    mx = float(df[col].max()) if col in df.columns else 1
                    pct = val/mx*100 if mx else 0
                    fig.add_trace(go.Indicator(mode="gauge+number", value=pct, title={"text": f"{persp}<br>{col}", "font": {"size": 10, "color": color}}, gauge={"axis": {"range": [0,100]}, "bar": {"color": color}, "bgcolor": "rgba(0,0,0,0)"}, domain={"row": i, "column": j}))
            fig.update_layout(title=req.title, template="plotly_dark", grid={"rows": 4, "columns": 2, "pattern": "independent"}, height=600)

        elif ct in ("attack graph", "threat map", "security graph"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                pairs = df[[src_col, tgt_col]].dropna().head(60)
                nodes = list(pd.unique(pairs[[src_col, tgt_col]].values.ravel()))
                n = len(nodes)
                angles = np.linspace(0, 2*np.pi, n, endpoint=False)
                pos = {nd: (np.cos(a)*2, np.sin(a)*2) for nd, a in zip(nodes, angles)}
                deg = pairs[src_col].value_counts().to_dict()
                edge_x, edge_y = [], []
                for _, row in pairs.iterrows():
                    x0,y0 = pos[row[src_col]]; x1,y1 = pos[row[tgt_col]]
                    edge_x += [x0,x1,None]; edge_y += [y0,y1,None]
                node_sizes = [max(10, min(40, deg.get(nd,1)*5)) for nd in nodes]
                node_colors = ["#ef4444" if deg.get(nd,0) > 3 else "#f59e0b" if deg.get(nd,0) > 1 else "#22c55e" for nd in nodes]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="rgba(239,68,68,0.3)", width=1), showlegend=False))
                fig.add_trace(go.Scatter(x=[pos[nd][0] for nd in nodes], y=[pos[nd][1] for nd in nodes], mode="markers+text", text=[str(nd)[:12] for nd in nodes], textposition="top center", textfont=dict(size=8), marker=dict(size=node_sizes, color=node_colors), name="Nodes"))
                fig.update_layout(title=req.title, template="plotly_dark", showlegend=False, xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False))
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("user journey", "journey map", "clickstream", "scroll map"):
            import plotly.graph_objects as go
            cat_col = x if x and x in df.columns else df.columns[0]
            num_col = y if y and y in df.columns else None
            sample = df[[cat_col] + ([num_col] if num_col else [])].dropna().head(20)
            steps = sample[cat_col].astype(str).tolist()
            values = sample[num_col].tolist() if num_col else [1]*len(steps)
            colors_j = ["#6366f1","#8b5cf6","#a78bfa","#c4b5fd","#ddd6fe","#10b981","#34d399","#6ee7b7","#f59e0b","#fbbf24"]
            fig = go.Figure()
            for i, (step, val) in enumerate(zip(steps, values)):
                fig.add_trace(go.Scatter(x=[i], y=[val], mode="markers+text", text=[step[:15]], textposition="top center", marker=dict(size=20, color=colors_j[i % len(colors_j)]), showlegend=False))
                if i > 0:
                    fig.add_trace(go.Scatter(x=[i-1, i], y=[values[i-1], val], mode="lines", line=dict(color="rgba(99,102,241,0.4)", width=2), showlegend=False))
            fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Step", yaxis_title=num_col or "Value")

        elif ct in ("alpha shape", "alpha hull", "concave hull"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc:
                try:
                    from scipy.spatial import Delaunay
                    pts = df[[xc, yc]].dropna().head(200).values
                    tri = Delaunay(pts)
                    alpha = 0.3
                    edges = set()
                    for simplex in tri.simplices:
                        for i in range(3):
                            edge = tuple(sorted([simplex[i], simplex[(i+1)%3]]))
                            p1, p2 = pts[edge[0]], pts[edge[1]]
                            length = np.linalg.norm(p2-p1)
                            if length < alpha * np.sqrt(len(pts)):
                                edges.add(edge)
                    fig = go.Figure()
                    for e in edges:
                        p1, p2 = pts[e[0]], pts[e[1]]
                        fig.add_trace(go.Scatter(x=[p1[0],p2[0]], y=[p1[1],p2[1]], mode="lines", line=dict(color="rgba(99,102,241,0.5)", width=1), showlegend=False))
                    fig.add_trace(go.Scatter(x=pts[:,0].tolist(), y=pts[:,1].tolist(), mode="markers", marker=dict(color="#6366f1", size=4), name="Points"))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title=xc, yaxis_title=yc)
                except ImportError:
                    fig = px.scatter(df, x=xc, y=yc, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("faceted grid", "facet grid", "multi facet"):
            import plotly.graph_objects as go, numpy as np
            from plotly.subplots import make_subplots
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:6]
            if len(num_cols) >= 2:
                n = len(num_cols)
                cols_n = min(3, n); rows_n = (n + cols_n - 1) // cols_n
                fig = make_subplots(rows=rows_n, cols=cols_n, subplot_titles=num_cols)
                colors_f = ["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#0ea5e9"]
                for i, col in enumerate(num_cols):
                    r, c = divmod(i, cols_n)
                    vals = df[col].dropna().values
                    fig.add_trace(go.Histogram(x=vals.tolist(), marker_color=colors_f[i % len(colors_f)], showlegend=False), row=r+1, col=c+1)
                fig.update_layout(title=req.title, template="plotly_dark", height=500)
            else:
                fig = px.histogram(df, x=x, **kwargs)

        elif ct in ("animated network", "network animation", "dynamic network"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                pairs = df[[src_col, tgt_col]].dropna().head(40)
                nodes = list(pd.unique(pairs[[src_col, tgt_col]].values.ravel()))
                n = len(nodes)
                angles = np.linspace(0, 2*np.pi, n, endpoint=False)
                pos = {nd: (np.cos(a), np.sin(a)) for nd, a in zip(nodes, angles)}
                frames = []
                for k in range(1, min(len(pairs)+1, 10)):
                    sub = pairs.head(k)
                    ex, ey = [], []
                    for _, row in sub.iterrows():
                        x0,y0 = pos[row[src_col]]; x1,y1 = pos[row[tgt_col]]
                        ex += [x0,x1,None]; ey += [y0,y1,None]
                    frames.append(go.Frame(data=[
                        go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(99,102,241,0.4)", width=1)),
                        go.Scatter(x=[pos[nd][0] for nd in nodes], y=[pos[nd][1] for nd in nodes], mode="markers+text", text=[str(nd)[:10] for nd in nodes], marker=dict(color="#6366f1", size=10)),
                    ]))
                fig = go.Figure(data=[go.Scatter(x=[], y=[], mode="lines"), go.Scatter(x=[pos[nd][0] for nd in nodes], y=[pos[nd][1] for nd in nodes], mode="markers+text", text=[str(nd)[:10] for nd in nodes], marker=dict(color="#6366f1", size=10))], frames=frames)
                fig.update_layout(title=req.title, template="plotly_dark", showlegend=False, xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False), updatemenus=[dict(type="buttons", buttons=[dict(label="Play", method="animate", args=[None])])])
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("linked brushing", "brushing", "drill-down", "interactive drilldown"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:4]
            if len(num_cols) >= 2:
                from plotly.subplots import make_subplots
                fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{num_cols[0]} vs {num_cols[1]}", f"Distribution of {num_cols[0]}"])
                sample = df[num_cols].dropna().head(500)
                fig.add_trace(go.Scatter(x=sample[num_cols[0]].tolist(), y=sample[num_cols[1]].tolist(), mode="markers", marker=dict(color="#6366f1", size=4, opacity=0.6), name="Scatter"), row=1, col=1)
                fig.add_trace(go.Histogram(x=sample[num_cols[0]].tolist(), marker_color="#10b981", name="Histogram"), row=1, col=2)
                fig.update_layout(title=req.title, template="plotly_dark", height=400)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("narrative", "storyboard", "data story"):
            import plotly.graph_objects as go, numpy as np
            from plotly.subplots import make_subplots
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:3]
            cat_cols = df.select_dtypes(include="object").columns.tolist()[:1]
            if num_cols:
                fig = make_subplots(rows=2, cols=2, subplot_titles=["Trend", "Distribution", "Composition", "Summary"], specs=[[{},{}],[{},{"type":"indicator"}]])
                x_col = df.columns[0]
                xs = df[x_col].astype(str).tolist()
                fig.add_trace(go.Scatter(x=xs, y=df[num_cols[0]].fillna(0).tolist(), mode="lines", line=dict(color="#6366f1", width=2), name=num_cols[0]), row=1, col=1)
                fig.add_trace(go.Histogram(x=df[num_cols[0]].dropna().tolist(), marker_color="#10b981", showlegend=False), row=1, col=2)
                if cat_cols:
                    counts = df[cat_cols[0]].value_counts().head(5)
                    fig.add_trace(go.Bar(x=counts.index.astype(str).tolist(), y=counts.values.tolist(), marker_color="#f59e0b", showlegend=False), row=2, col=1)
                else:
                    fig.add_trace(go.Bar(x=xs[:20], y=df[num_cols[0]].fillna(0).tolist()[:20], marker_color="#f59e0b", showlegend=False), row=2, col=1)
                fig.add_trace(go.Indicator(mode="number+delta", value=float(df[num_cols[0]].mean()), delta={"reference": float(df[num_cols[0]].median())}, title={"text": f"Avg {num_cols[0]}"}, number={"font": {"color": "#6366f1"}}), row=2, col=2)
                fig.update_layout(title=req.title, template="plotly_dark", height=500)
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("sankey heatmap", "sankey+heatmap", "flow heatmap"):
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            num_cols = df.select_dtypes(include="number").columns.tolist()
            if len(cat_cols) >= 2 and num_cols:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = num_cols[0]
                flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index()
                flow_vals = flows[val_col].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
                fig = make_subplots(rows=1, cols=2, subplot_titles=["Flow (Sankey)", "Pivot Heatmap"], specs=[[{"type":"sankey"},{"type":"heatmap"}]])
                fig.add_trace(go.Sankey(node=dict(label=nodes, pad=10, thickness=15, color=["#6366f1"]*len(nodes)), link=dict(source=[node_idx[s] for s in flows[src_col]], target=[node_idx[t] for t in flows[tgt_col]], value=flow_vals, color=[f"rgba(99,102,241,{min(0.8,v/mx):.2f})" for v in flow_vals])), row=1, col=1)
                pivot = df.groupby([src_col, tgt_col])[val_col].sum().unstack(fill_value=0)
                fig.add_trace(go.Heatmap(z=pivot.values.tolist(), x=pivot.columns.astype(str).tolist(), y=pivot.index.astype(str).tolist(), colorscale="Plasma"), row=1, col=2)
                fig.update_layout(title=req.title, template="plotly_dark", height=450)
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

"""
TAIL = """
        else:
            fig = px.bar(df, x=x, y=y, **kwargs)

        fig.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
        return {"plotly_json": json.loads(fig.to_json()), "title": req.title}
    except Exception as e:
        raise HTTPException(422, f"Chart error: {e}")
"""
with open(VIZ, "a", encoding="utf-8") as f:
    f.write(BLOCK)
    f.write(TAIL)
import ast
ast.parse(open(VIZ, encoding="utf-8").read())
print("Syntax OK - lines:", len(open(VIZ, encoding="utf-8").readlines()))

