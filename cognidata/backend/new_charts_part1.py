        # ── Statistical & Distribution ────────────────────────────────────────
        elif ct in ("qq plot", "q-q plot", "quantile-quantile"):
            import plotly.graph_objects as go, numpy as np
            from scipy import stats
            num_col = y if y and y in df.columns else x
            if num_col and num_col in df.columns:
                vals = df[num_col].dropna().sort_values().values
                (osm, osr), (slope, intercept, r) = stats.probplot(vals, dist="norm")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(osm), y=list(osr), mode="markers",
                    marker=dict(color="#6366f1", size=4), name="Data"))
                fig.add_trace(go.Scatter(x=list(osm),
                    y=[slope*q+intercept for q in osm], mode="lines",
                    line=dict(color="#f59e0b", width=2), name="Normal Line"))
                fig.update_layout(title=req.title, template="plotly_dark",
                    xaxis_title="Theoretical Quantiles", yaxis_title="Sample Quantiles")
            else:
                fig = px.scatter(df, x=x, y=y, **kwargs)
