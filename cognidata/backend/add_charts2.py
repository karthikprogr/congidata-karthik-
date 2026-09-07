import pathlib

VIZ = pathlib.Path(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py")

BLOCK = """
        # ML & AI Specific
        elif ct in ("roc curve", "roc", "auc"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:10]
            if features and target:
                try:
                    from sklearn.ensemble import RandomForestClassifier
                    from sklearn.metrics import roc_curve, auc
                    from sklearn.preprocessing import label_binarize
                    X = df[features].fillna(0).head(500)
                    Y = (df[target].fillna(0).head(500) > df[target].median()).astype(int)
                    rf = RandomForestClassifier(n_estimators=20, random_state=42)
                    rf.fit(X, Y)
                    probs = rf.predict_proba(X)[:, 1]
                    fpr, tpr, _ = roc_curve(Y, probs)
                    roc_auc = auc(fpr, tpr)
                    fig = go.Figure([
                        go.Scatter(x=fpr.tolist(), y=tpr.tolist(), mode="lines", line=dict(color="#6366f1", width=2), name=f"ROC (AUC={roc_auc:.3f})"),
                        go.Scatter(x=[0,1], y=[0,1], mode="lines", line=dict(color="#52525b", dash="dash"), name="Random"),
                    ])
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="FPR", yaxis_title="TPR")
                except Exception as e:
                    fig = px.scatter(df, x=x, y=y, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("precision recall", "pr curve", "precision-recall"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:10]
            if features and target:
                try:
                    from sklearn.ensemble import RandomForestClassifier
                    from sklearn.metrics import precision_recall_curve, average_precision_score
                    X = df[features].fillna(0).head(500)
                    Y = (df[target].fillna(0).head(500) > df[target].median()).astype(int)
                    rf = RandomForestClassifier(n_estimators=20, random_state=42)
                    rf.fit(X, Y)
                    probs = rf.predict_proba(X)[:, 1]
                    prec, rec, _ = precision_recall_curve(Y, probs)
                    ap = average_precision_score(Y, probs)
                    fig = go.Figure(go.Scatter(x=rec.tolist(), y=prec.tolist(), mode="lines", line=dict(color="#10b981", width=2), name=f"AP={ap:.3f}"))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Recall", yaxis_title="Precision")
                except Exception:
                    fig = px.scatter(df, x=x, y=y, **kwargs)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("confusion matrix", "confusion"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:10]
            if features and target:
                try:
                    from sklearn.ensemble import RandomForestClassifier
                    from sklearn.metrics import confusion_matrix
                    X = df[features].fillna(0).head(500)
                    Y = (df[target].fillna(0).head(500) > df[target].median()).astype(int)
                    rf = RandomForestClassifier(n_estimators=20, random_state=42)
                    rf.fit(X, Y)
                    cm = confusion_matrix(Y, rf.predict(X))
                    labels = ["Negative", "Positive"]
                    fig = go.Figure(go.Heatmap(z=cm.tolist(), x=labels, y=labels, colorscale="Blues", text=cm.tolist(), texttemplate="%{text}", showscale=True))
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Predicted", yaxis_title="Actual")
                except Exception:
                    fig = px.bar(df, x=x, y=y, **kwargs)
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("learning curve", "learning curves"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            target = y if y and y in df.columns else (num_cols[-1] if num_cols else None)
            features = [c for c in num_cols if c != target][:10]
            if features and target:
                try:
                    from sklearn.ensemble import RandomForestRegressor
                    from sklearn.model_selection import learning_curve
                    X = df[features].fillna(0).head(500)
                    Y = df[target].fillna(0).head(500)
                    sizes, train_s, val_s = learning_curve(RandomForestRegressor(n_estimators=10, random_state=42), X, Y, cv=3, n_jobs=1, train_sizes=np.linspace(0.1,1.0,8))
                    fig = go.Figure([
                        go.Scatter(x=sizes.tolist(), y=train_s.mean(axis=1).tolist(), mode="lines+markers", name="Train Score", line=dict(color="#6366f1")),
                        go.Scatter(x=sizes.tolist(), y=val_s.mean(axis=1).tolist(), mode="lines+markers", name="Val Score", line=dict(color="#10b981")),
                    ])
                    fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Training Size", yaxis_title="Score")
                except Exception:
                    fig = px.line(df, x=x, y=y, **kwargs)
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("monte carlo", "monte carlo simulation", "simulation"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                vals = df[num_col].dropna().values
                mu, sigma = float(np.mean(vals)), float(np.std(vals))
                n_sims, n_steps = 100, min(len(vals), 100)
                fig = go.Figure()
                for i in range(n_sims):
                    sim = np.cumsum(np.random.normal(mu/n_steps, sigma/np.sqrt(n_steps), n_steps))
                    fig.add_trace(go.Scatter(x=list(range(n_steps)), y=sim.tolist(), mode="lines", line=dict(width=0.5, color=f"rgba(99,102,241,0.15)"), showlegend=False))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Steps", yaxis_title="Value")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("drawdown", "drawdown chart", "underwater"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                vals = df[num_col].dropna().values
                cummax = np.maximum.accumulate(vals)
                drawdown = (vals - cummax) / (cummax + 1e-10) * 100
                xs = list(range(len(drawdown)))
                fig = go.Figure([
                    go.Scatter(x=xs, y=drawdown.tolist(), mode="lines", fill="tozeroy", line=dict(color="#ef4444", width=1.5), fillcolor="rgba(239,68,68,0.2)", name="Drawdown %"),
                ])
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Period", yaxis_title="Drawdown %")
            else:
                fig = px.line(df, x=x, y=y, **kwargs)

        elif ct in ("correlogram", "correlation matrix", "covariance matrix"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:15]
            if len(num_cols) >= 2:
                corr = df[num_cols].corr()
                fig = go.Figure(go.Heatmap(z=corr.values.tolist(), x=corr.columns.tolist(), y=corr.columns.tolist(), colorscale="RdBu", zmid=0, text=[[f"{v:.2f}" for v in row] for row in corr.values], texttemplate="%{text}", colorbar=dict(title="r")))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("cluster heatmap", "clustered heatmap"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:20]
            if len(num_cols) >= 2:
                try:
                    from scipy.cluster.hierarchy import linkage, dendrogram
                    from scipy.spatial.distance import pdist
                    sample = df[num_cols].dropna().head(50)
                    row_link = linkage(pdist(sample.values), method="ward")
                    row_order = dendrogram(row_link, no_plot=True)["leaves"]
                    col_link = linkage(pdist(sample.values.T), method="ward")
                    col_order = dendrogram(col_link, no_plot=True)["leaves"]
                    reordered = sample.iloc[row_order, col_order]
                    fig = go.Figure(go.Heatmap(z=reordered.values.tolist(), x=[num_cols[i] for i in col_order], y=[str(reordered.index[i]) for i in range(len(row_order))], colorscale="Plasma"))
                    fig.update_layout(title=req.title, template="plotly_dark")
                except ImportError:
                    corr = df[num_cols].corr()
                    fig = go.Figure(go.Heatmap(z=corr.values.tolist(), x=corr.columns.tolist(), y=corr.columns.tolist(), colorscale="Plasma"))
                    fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("icicle", "icicle chart", "partition"):
            cat_cols = df.select_dtypes(include="object").columns.tolist()[:3]
            num_col = y if y and y in df.columns else None
            if len(cat_cols) >= 1:
                path = cat_cols[:min(3, len(cat_cols))]
                if num_col and num_col in df.columns:
                    fig = px.icicle(df, path=path, values=num_col, **kwargs)
                else:
                    fig = px.icicle(df, path=path, **kwargs)
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("surface", "surface plot", "3d surface"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(num_cols) >= 2:
                xc, yc = num_cols[0], num_cols[1]
                zc = num_cols[2] if len(num_cols) > 2 else num_cols[0]
                sample = df[[xc, yc, zc]].dropna().head(400)
                try:
                    from scipy.interpolate import griddata
                    xi = np.linspace(sample[xc].min(), sample[xc].max(), 30)
                    yi = np.linspace(sample[yc].min(), sample[yc].max(), 30)
                    XI, YI = np.meshgrid(xi, yi)
                    ZI = griddata((sample[xc], sample[yc]), sample[zc], (XI, YI), method="linear")
                    fig = go.Figure(go.Surface(x=xi.tolist(), y=yi.tolist(), z=ZI.tolist(), colorscale="Plasma"))
                except Exception:
                    fig = go.Figure(go.Scatter3d(x=sample[xc], y=sample[yc], z=sample[zc], mode="markers", marker=dict(size=3, color=sample[zc], colorscale="Plasma")))
                fig.update_layout(title=req.title, template="plotly_dark", scene=dict(xaxis_title=xc, yaxis_title=yc, zaxis_title=zc))
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("radial heatmap", "circular heatmap"):
            import plotly.graph_objects as go, numpy as np
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:12]
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            if num_cols:
                if cat_col:
                    groups = df[cat_col].dropna().unique()[:12]
                    r_vals = [float(df[df[cat_col]==g][num_cols[0]].mean()) for g in groups]
                    theta = [str(g) for g in groups]
                else:
                    r_vals = df[num_cols].mean().tolist()
                    theta = num_cols
                fig = go.Figure(go.Barpolar(r=r_vals, theta=theta, marker=dict(color=r_vals, colorscale="Plasma", line=dict(color="rgba(255,255,255,0.1)", width=1)), opacity=0.85))
                fig.update_layout(title=req.title, template="plotly_dark", polar=dict(radialaxis=dict(visible=True, showticklabels=False)))
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("word frequency", "word chart", "word bar"):
            import plotly.graph_objects as go
            cat_col = x if x and x in df.columns else df.columns[0]
            text_data = " ".join(df[cat_col].dropna().astype(str).tolist())
            words = [w.lower().strip(".,!?;:") for w in text_data.split() if len(w) > 3]
            from collections import Counter
            counts = Counter(words).most_common(20)
            if counts:
                words_list, freqs = zip(*counts)
                fig = go.Figure(go.Bar(x=list(freqs), y=list(words_list), orientation="h", marker=dict(color=list(freqs), colorscale="Plasma")))
                fig.update_layout(title=req.title, template="plotly_dark", xaxis_title="Frequency", yaxis=dict(autorange="reversed"))
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

        elif ct in ("horizon", "horizon chart", "horizon area"):
            import plotly.graph_objects as go, numpy as np
            num_col = y if y and y in df.columns else x
            x_col = x if x and x in df.columns else df.columns[0]
            if num_col and num_col in df.columns:
                vals = df[num_col].fillna(0).values
                xs = df[x_col].astype(str).tolist()
                bands = 3
                mx = float(np.max(np.abs(vals))) or 1
                colors_pos = ["rgba(99,102,241,0.3)", "rgba(99,102,241,0.6)", "rgba(99,102,241,0.9)"]
                colors_neg = ["rgba(239,68,68,0.3)", "rgba(239,68,68,0.6)", "rgba(239,68,68,0.9)"]
                fig = go.Figure()
                for b in range(bands):
                    lo, hi = b*mx/bands, (b+1)*mx/bands
                    pos_y = [v if lo <= v <= hi else (hi if v > hi else 0) for v in vals]
                    neg_y = [-v if lo <= -v <= hi else (hi if -v > hi else 0) for v in vals]
                    fig.add_trace(go.Scatter(x=xs, y=pos_y, fill="tozeroy", mode="none", fillcolor=colors_pos[b], name=f"+Band{b+1}", showlegend=b==0))
                    fig.add_trace(go.Scatter(x=xs, y=[-v for v in neg_y], fill="tozeroy", mode="none", fillcolor=colors_neg[b], name=f"-Band{b+1}", showlegend=b==0))
                fig.update_layout(title=req.title, template="plotly_dark", hovermode="x unified")
            else:
                fig = px.area(df, x=x, y=y, **kwargs)

        elif ct in ("animated bubble", "bubble animation", "animated scatter"):
            import plotly.express as px_
            num_cols = df.select_dtypes(include="number").columns.tolist()
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            xc = x if x and x in df.columns else (num_cols[0] if num_cols else None)
            yc = y if y and y in df.columns else (num_cols[1] if len(num_cols) > 1 else xc)
            size_c = num_cols[2] if len(num_cols) > 2 else yc
            color_c = cat_cols[0] if cat_cols else None
            anim_c = cat_cols[1] if len(cat_cols) > 1 else (num_cols[3] if len(num_cols) > 3 else None)
            if xc and yc:
                kw = dict(title=req.title, template="plotly_dark")
                if color_c: kw["color"] = color_c
                if anim_c: kw["animation_frame"] = anim_c
                fig = px_.scatter(df.head(500), x=xc, y=yc, size=size_c if size_c and size_c in df.columns else None, **kw)
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)

        elif ct in ("faceted heatmap", "facet heatmap", "grid heatmap"):
            import plotly.graph_objects as go, numpy as np
            from plotly.subplots import make_subplots
            num_cols = df.select_dtypes(include=np.number).columns.tolist()[:4]
            cat_col = x if x and x in df.columns and not pd.api.types.is_numeric_dtype(df[x]) else None
            if cat_col and len(num_cols) >= 2:
                groups = df[cat_col].dropna().unique()[:4]
                n = len(groups)
                cols_n = min(2, n)
                rows_n = (n + cols_n - 1) // cols_n
                fig = make_subplots(rows=rows_n, cols=cols_n, subplot_titles=[str(g) for g in groups])
                for i, grp in enumerate(groups):
                    sub = df[df[cat_col] == grp][num_cols].dropna()
                    corr = sub.corr()
                    r, c = divmod(i, cols_n)
                    fig.add_trace(go.Heatmap(z=corr.values.tolist(), x=num_cols, y=num_cols, colorscale="Plasma", showscale=(i==0)), row=r+1, col=c+1)
                fig.update_layout(title=req.title, template="plotly_dark", height=500)
            else:
                num_cols2 = df.select_dtypes(include=np.number).columns.tolist()[:8]
                if len(num_cols2) >= 2:
                    corr = df[num_cols2].corr()
                    fig = go.Figure(go.Heatmap(z=corr.values.tolist(), x=corr.columns.tolist(), y=corr.columns.tolist(), colorscale="Plasma"))
                    fig.update_layout(title=req.title, template="plotly_dark")
                else:
                    fig = px.bar(df, x=x, y=y, **kwargs)

"""

with open(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py", "a", encoding="utf-8") as f:
    f.write(BLOCK)

# Now append the final else + return
TAIL = """
        else:
            fig = px.bar(df, x=x, y=y, **kwargs)

        fig.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
        return {"plotly_json": json.loads(fig.to_json()), "title": req.title}
    except Exception as e:
        raise HTTPException(422, f"Chart error: {e}")
"""
with open(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py", "a", encoding="utf-8") as f:
    f.write(TAIL)

import ast
ast.parse(open(r"D:\cogni-2-main\cognidata\backend\app\api\routes\viz.py").read())
print("Syntax OK")

