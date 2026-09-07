import pathlib
VIZ = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py")

BLOCK = r"""
        # Ultra-Rare / Expert-Level Chart Types
        elif ct in ("pdf plot", "probability density", "pdf"):
            import plotly.graph_objects as go, numpy as np
            try:
                from scipy.stats import gaussian_kde
                num_col = y if y and y in df.columns else x
                if num_col and num_col in df.columns:
                    vals = df[num_col].dropna().values
                    kde = gaussian_kde(vals)
                    xs = np.linspace(vals.min(), vals.max(), 300)
                    fig = go.Figure(go.Scatter(x=xs.tolist(), y=kde(xs).tolist(), mode="lines", fill="tozeroy", line=dict(color="#6366f1", width=2), fillcolor="rgba(99,102,241,0.15)", name="PDF"))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title=num_col, yaxis_title="Density")
                else:
                    fig = px.histogram(df, x=x, **kwargs)
            except ImportError:
                fig = px.histogram(df, x=x, **kwargs)

        elif ct in ("kaplan meier", "kaplan-meier", "survival curve", "survival"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                times = np.sort(df[num_col].dropna().values)
                n = len(times)
                survival = [1 - i/n for i in range(n)]
                fig = go.Figure(go.Scatter(x=times.tolist(), y=survival, mode="lines", line=dict(color="#6366f1", width=2, shape="hv"), name="S(t)"))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Time", yaxis_title="Survival Probability")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("periodogram", "power spectrum", "spectrum"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                vals = df[num_col].dropna().values
                freqs = np.fft.rfftfreq(len(vals))
                power = np.abs(np.fft.rfft(vals - vals.mean()))**2
                fig = go.Figure(go.Scatter(x=freqs[1:].tolist(), y=power[1:].tolist(), mode="lines", line=dict(color="#6366f1", width=1.5), fill="tozeroy", fillcolor="rgba(99,102,241,0.15)"))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Frequency", yaxis_title="Power")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("adjacency matrix", "adjacency"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                nodes = list(pd.unique(df[[src_col, tgt_col]].values.ravel()))[:30]
                n = len(nodes)
                idx = {nd: i for i, nd in enumerate(nodes)}
                mat = np.zeros((n, n))
                for _, row in df[[src_col, tgt_col]].dropna().head(500).iterrows():
                    if row[src_col] in idx and row[tgt_col] in idx:
                        mat[idx[row[src_col]]][idx[row[tgt_col]]] += 1
                fig = go.Figure(go.Heatmap(z=mat.tolist(), x=nodes, y=nodes, colorscale="Plasma", colorbar=dict(title="Connections")))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("pareto frontier", "pareto", "pareto chart"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            num_col = y if y and y in df.columns else (num_cols[0] if num_cols else None)
            if num_col:
                if cat_col:
                    counts = df[cat_col].value_counts().head(20)
                    labels, vals = counts.index.astype(str).tolist(), counts.values.tolist()
                else:
                    vals_raw = df[num_col].dropna().sort_values(ascending=False).head(20)
                    labels = [str(i) for i in vals_raw.index]
                    vals = vals_raw.tolist()
                total = sum(vals) or 1
                cumulative = [sum(vals[:i+1])/total*100 for i in range(len(vals))]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=labels, y=vals, name="Value", marker_color="#6366f1"))
                fig.add_trace(go.Scatter(x=labels, y=cumulative, mode="lines+markers", name="Cumulative %", yaxis="y2", line=dict(color="#f59e0b", width=2)))
                fig.update_layout(title=req.title, template="plotly_dark", yaxis2=dict(overlaying="y", side="right", range=[0,110], ticksuffix="%"))
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("manhattan plot", "manhattan"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            num_col = y if y and y in df.columns else (num_cols[0] if num_cols else None)
            if num_col:
                vals = df[num_col].dropna().values
                neg_log = -np.log10(np.clip(vals, 1e-300, 1))
                colors = ["#ef4444" if v > 7.3 else "#10b981" if v > 5 else "#52525b" for v in neg_log]
                fig = go.Figure(go.Scatter(x=list(range(len(neg_log))), y=neg_log.tolist(), mode="markers", marker=dict(color=colors, size=4, opacity=0.7)))
                fig.add_hline(y=7.3, line_dash="dash", line_color="#ef4444", annotation_text="p=5e-8")
                fig.add_hline(y=5, line_dash="dash", line_color="#f59e0b", annotation_text="p=1e-5")
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Position", yaxis_title="-log10(p)")
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("volcano plot", "volcano"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc:
                fc = df[xc].dropna().values
                pv = df[yc].dropna().values
                n = min(len(fc), len(pv))
                neg_log_p = -np.log10(np.clip(pv[:n], 1e-300, 1))
                colors = ["#ef4444" if (abs(f) > 1 and p > 1.3) else "#52525b" for f, p in zip(fc[:n], neg_log_p)]
                fig = go.Figure(go.Scatter(x=fc[:n].tolist(), y=neg_log_p.tolist(), mode="markers", marker=dict(color=colors, size=4, opacity=0.7)))
                fig.add_vline(x=1, line_dash="dash", line_color="rgba(255,255,255,0.2)")
                fig.add_vline(x=-1, line_dash="dash", line_color="rgba(255,255,255,0.2)")
                fig.add_hline(y=1.3, line_dash="dash", line_color="#f59e0b")
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Log2 Fold Change", yaxis_title="-log10(p-value)")
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("dual axis", "dual-axis", "multi axis", "twin axis"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            x_col = x if x and x in df.columns else df.columns[0]
            yc1 = y if y and y in df.columns else (num_cols[0] if num_cols else None)
            yc2 = num_cols[1] if len(num_cols) > 1 else yc1
            if yc1 and yc2:
                xs = df[x_col].astype(str).tolist()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=xs, y=df[yc1].fillna(0).tolist(), name=yc1, line=dict(color="#6366f1", width=2), yaxis="y1"))
                fig.add_trace(go.Bar(x=xs, y=df[yc2].fillna(0).tolist(), name=yc2, marker_color="rgba(16,185,129,0.4)", yaxis="y2"))
                fig.update_layout(title=req.title, template="plotly_dark", yaxis=dict(title=yc1, color="#6366f1"), yaxis2=dict(title=yc2, overlaying="y", side="right", color="#10b981"))
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("kpi traffic light", "traffic light", "rag chart"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:6]
            fig = go.Figure()
            for i, col in enumerate(num_cols):
                val = float(df[col].mean())
                mx = float(df[col].max()) or 1
                pct = val / mx
                color = "#22c55e" if pct >= 0.7 else "#f59e0b" if pct >= 0.4 else "#ef4444"
                fig.add_trace(go.Indicator(mode="number+delta", value=val, delta={"reference": mx * 0.6}, title={"text": col, "font": {"size": 12, "color": color}}, number={"font": {"color": color, "size": 24}}, domain={"row": 0, "column": i}))
            fig.update_layout(title=req.title, template="plotly_dark", grid={"rows": 1, "columns": max(1, len(num_cols)), "pattern": "independent"}, height=200)

        elif ct in ("log heatmap", "security heatmap", "event heatmap"):
            import plotly.graph_objects as go
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            num_col = y if y and y in df.columns else None
            if len(cat_cols) >= 2:
                rc, cc = cat_cols[0], cat_cols[1]
                if num_col and num_col in df.columns:
                    pivot = df.groupby([rc, cc])[num_col].sum().unstack(fill_value=0)
                else:
                    pivot = df.groupby([rc, cc]).size().unstack(fill_value=0)
                fig = go.Figure(go.Heatmap(z=pivot.values.tolist(), x=pivot.columns.astype(str).tolist(), y=pivot.index.astype(str).tolist(), colorscale="YlOrRd", colorbar=dict(title="Count")))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("delaunay", "delaunay triangulation"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc:
                try:
                    from scipy.spatial import Delaunay
                    pts = df[[xc, yc]].dropna().head(200).values
                    tri = Delaunay(pts)
                    fig = go.Figure()
                    for simplex in tri.simplices:
                        verts = pts[simplex]
                        fig.add_trace(go.Scatter(x=(verts[:, 0].tolist() + [verts[0, 0]]), y=(verts[:, 1].tolist() + [verts[0, 1]]), mode="lines", line=dict(color="rgba(99,102,241,0.4)", width=1), showlegend=False))
                    fig.add_trace(go.Scatter(x=pts[:, 0].tolist(), y=pts[:, 1].tolist(), mode="markers", marker=dict(color="#6366f1", size=5), name="Points"))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title=xc, yaxis_title=yc)
                except ImportError:
                    fig = px.scatter(df, x=xc, y=yc, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("convex hull", "hull plot"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc:
                try:
                    from scipy.spatial import ConvexHull
                    pts = df[[xc, yc]].dropna().head(300).values
                    hull = ConvexHull(pts)
                    hull_pts = np.append(hull.vertices, hull.vertices[0])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=pts[:, 0].tolist(), y=pts[:, 1].tolist(), mode="markers", marker=dict(color="#6366f1", size=4, opacity=0.5), name="Points"))
                    fig.add_trace(go.Scatter(x=pts[hull_pts, 0].tolist(), y=pts[hull_pts, 1].tolist(), mode="lines", line=dict(color="#f59e0b", width=2), fill="toself", fillcolor="rgba(245,158,11,0.1)", name="Hull"))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title=xc, yaxis_title=yc)
                except ImportError:
                    fig = px.scatter(df, x=xc, y=yc, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("cross correlation", "cross-correlation", "xcorr"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            if xc and yc and xc != yc:
                a = df[xc].dropna().values; b = df[yc].dropna().values
                n = min(len(a), len(b)); a, b = a[:n], b[:n]
                a = (a - a.mean()) / (a.std() or 1); b = (b - b.mean()) / (b.std() or 1)
                lags = min(40, n//2)
                xcorr = [float(np.correlate(a, np.roll(b, k))[0]) / n for k in range(-lags, lags+1)]
                lag_vals = list(range(-lags, lags+1))
                ci = 1.96 / np.sqrt(n)
                fig = go.Figure()
                for i, v in zip(lag_vals, xcorr):
                    fig.add_trace(go.Scatter(x=[i, i], y=[0, v], mode="lines", line=dict(color="#6366f1", width=1.5), showlegend=False))
                fig.add_hline(y=ci, line_dash="dash", line_color="#f59e0b")
                fig.add_hline(y=-ci, line_dash="dash", line_color="#f59e0b")
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Lag", yaxis_title="Cross-Correlation")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("variance analysis", "variance chart", "anova"):
            import plotly.graph_objects as go
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            num_col = y if y and y in df.columns else None
            if cat_col and num_col:
                colors = px.colors.qualitative.Plotly
                fig = go.Figure()
                for i, grp in enumerate(df[cat_col].dropna().unique()[:10]):
                    vals = df[df[cat_col] == grp][num_col].dropna().tolist()
                    if vals:
                        fig.add_trace(go.Box(y=vals, name=str(grp), marker_color=colors[i % len(colors)], boxmean="sd"))
                fig.update_layout(title=req.title, template="plotly_dark", yaxis_title=num_col, boxmode="group")
            else:
                fig = px.box(df, x=x, y=y, **kwargs)

        elif ct in ("composite", "composite chart", "multi-layer", "layered"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:4]
            x_col = x if x and x in df.columns else df.columns[0]
            colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"]
            fig = go.Figure()
            for i, col in enumerate(num_cols):
                xs = df[x_col].astype(str).tolist()
                ys = df[col].fillna(0).tolist()
                if i % 2 == 0:
                    fig.add_trace(go.Scatter(x=xs, y=ys, name=col, mode="lines", line=dict(color=colors[i], width=2)))
                else:
                    r, g, b = int(colors[i][1:3],16), int(colors[i][3:5],16), int(colors[i][5:7],16)
                    fig.add_trace(go.Bar(x=xs, y=ys, name=col, marker_color=f"rgba({r},{g},{b},0.5)"))
            fig.update_layout(title=req.title, template="plotly_dark", barmode="overlay", hovermode="x unified")

        elif ct in ("3d scatter volume", "3d volume", "volume scatter"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(num_cols) >= 3:
                xc, yc, zc = num_cols[0], num_cols[1], num_cols[2]
                cc = num_cols[3] if len(num_cols) > 3 else zc
                sample = df[[xc, yc, zc, cc]].dropna().head(500)
                fig = go.Figure(go.Scatter3d(x=sample[xc].tolist(), y=sample[yc].tolist(), z=sample[zc].tolist(), mode="markers", marker=dict(size=3, color=sample[cc].tolist(), colorscale="Plasma", opacity=0.6, colorbar=dict(title=cc))))
                fig.update_layout(title=req.title, template="plotly_dark", scene=dict(xaxis_title=xc, yaxis_title=yc, zaxis_title=zc))
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("pacf", "partial autocorrelation", "partial acf"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                try:
                    from statsmodels.tsa.stattools import pacf
                    vals = df[num_col].dropna().values
                    lags = min(40, len(vals)//2 - 1)
                    pacf_vals = pacf(vals, nlags=lags)
                    ci = 1.96 / np.sqrt(len(vals))
                    fig = go.Figure()
                    for i, v in enumerate(pacf_vals):
                        fig.add_trace(go.Scatter(x=[i, i], y=[0, v], mode="lines", line=dict(color="#8b5cf6", width=2), showlegend=False))
                    fig.add_hline(y=ci, line_dash="dash", line_color="#f59e0b")
                    fig.add_hline(y=-ci, line_dash="dash", line_color="#f59e0b")
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Lag", yaxis_title="PACF")
                except ImportError:
                    fig = px.line(df, x=x, y=y, **kwargs)
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("efficient frontier", "risk return", "risk-return"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(num_cols) >= 2:
                returns = df[num_cols].pct_change().dropna()
                results = []
                for _ in range(500):
                    w = np.random.dirichlet(np.ones(len(num_cols)))
                    ret = float(np.dot(w, returns.mean()) * 252)
                    risk = float(np.sqrt(np.dot(w.T, np.dot(returns.cov() * 252, w))))
                    results.append((risk, ret))
                risks, rets = zip(*results)
                fig = go.Figure(go.Scatter(x=list(risks), y=list(rets), mode="markers", marker=dict(color=list(rets), colorscale="Plasma", size=4, opacity=0.6, colorbar=dict(title="Return"))))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Risk (Std Dev)", yaxis_title="Expected Return")
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("gain chart", "lift chart", "cumulative gain"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:10]
            if features and target:
                try:
                    from sklearn.ensemble import RandomForestClassifier
                    X = df[features].fillna(0).head(500)
                    Y = (df[target].fillna(0).head(500) > df[target].median()).astype(int)
                    rf = RandomForestClassifier(n_estimators=20, random_state=42)
                    rf.fit(X, Y)
                    probs = rf.predict_proba(X)[:, 1]
                    sorted_idx = np.argsort(-probs)
                    n = len(Y); total_pos = Y.sum() or 1
                    gains = np.cumsum(Y.values[sorted_idx]) / total_pos
                    pcts = np.arange(1, n+1) / n * 100
                    fig = go.Figure([
                        go.Scatter(x=pcts.tolist(), y=(gains*100).tolist(), mode="lines", line=dict(color="#6366f1", width=2), name="Model"),
                        go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color="#52525b", dash="dash"), name="Baseline"),
                    ])
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="% Population", yaxis_title="% Positive Captured")
                except Exception:
                    fig = px.line(df, x=x, y=y, **kwargs)
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

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
print("Syntax OK - total lines:", len(open(VIZ, encoding="utf-8").readlines()))
