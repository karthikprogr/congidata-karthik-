"""Advanced Analytics routes - 5 endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user
from app.services.data_store import get as get_df, save as save_df

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/stats")
def statistical_tests(user: dict = Depends(get_current_user)):
    from scipy import stats
    import numpy as np
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")
    nums = df.select_dtypes(include=np.number)
    result = []
    for col in nums.columns:
        data = nums[col].dropna().values
        if len(data) < 3: continue
        stat, p = stats.shapiro(data[:5000])  # cap for speed
        result.append({"column": col, "shapiro_stat": round(float(stat), 4),
                        "shapiro_p": round(float(p), 4), "normal": bool(p > 0.05),
                        "mean": round(float(data.mean()), 3), "std": round(float(data.std()), 3)})
    # Pearson correlations
    correlations = []
    cols = nums.columns.tolist()
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            a = nums[cols[i]].dropna(); b = nums[cols[j]].dropna()
            common = min(len(a), len(b))
            if common < 3: continue
            r, p = stats.pearsonr(a.values[:common], b.values[:common])
            correlations.append({"col_a": cols[i], "col_b": cols[j],
                                  "r": round(float(r), 4), "p": round(float(p), 4),
                                  "significant": bool(p < 0.05)})
    return {"normality_tests": result, "correlations": sorted(correlations, key=lambda x: abs(x["r"]), reverse=True)[:20]}


class ClusterRequest(BaseModel):
    k: int = 3
    algorithm: str = "K-Means"
    features: Optional[list] = None
    eps: float = 0.5
    min_samples: int = 5


@router.post("/cluster")
def cluster(req: ClusterRequest, user: dict = Depends(get_current_user)):
    import numpy as np
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    import json
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")

    # Select features
    if req.features:
        nums = df[req.features].select_dtypes(include=np.number).fillna(0)
    else:
        nums = df.select_dtypes(include=np.number).fillna(0)
    if len(nums.columns) < 2: raise HTTPException(422, "Need at least 2 numeric columns")

    scaler = StandardScaler()
    X = scaler.fit_transform(nums.values)

    # Choose algorithm
    algo = req.algorithm
    if algo == "DBSCAN":
        model = DBSCAN(eps=req.eps, min_samples=req.min_samples)
        labels = model.fit_predict(X)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    elif algo == "Agglomerative":
        k = max(2, min(req.k, 8))
        model = AgglomerativeClustering(n_clusters=k)
        labels = model.fit_predict(X)
        n_clusters = k
    elif algo == "Gaussian Mixture":
        k = max(2, min(req.k, 8))
        model = GaussianMixture(n_components=k, random_state=42)
        labels = model.fit_predict(X)
        n_clusters = k
    else:  # K-Means (default)
        k = max(2, min(req.k, 8))
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        n_clusters = k

    # PCA for 2D scatter
    pca2 = PCA(n_components=min(2, X.shape[1]))
    coords2 = pca2.fit_transform(X)

    # PCA for 3D scatter
    pca3 = PCA(n_components=min(3, X.shape[1]))
    coords3 = pca3.fit_transform(X)

    # Silhouette, Davies-Bouldin, Calinski-Harabasz scores
    silhouette = None
    davies_bouldin = None
    calinski_harabasz = None
    if n_clusters > 1 and len(set(labels)) > 1:
        try:
            from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
            silhouette = round(float(silhouette_score(X, labels)), 4)
            davies_bouldin = round(float(davies_bouldin_score(X, labels)), 4)
            calinski_harabasz = round(float(calinski_harabasz_score(X, labels)), 4)
        except Exception:
            pass

    # Correlation matrix
    corr = nums.corr()

    # Cluster summary
    df_labeled = nums.copy()
    df_labeled["_cluster"] = labels
    summary = []
    for c in sorted(set(labels)):
        if c == -1: continue
        grp = df_labeled[df_labeled["_cluster"] == c].drop(columns=["_cluster"])
        summary.append({"cluster": int(c), "size": int((labels == c).sum()), "centroid": str(grp.mean().round(2).to_dict())})

    return {
        "k": n_clusters,
        "n_clusters": n_clusters,
        "n_points": len(labels),
        "silhouette": silhouette,
        "davies_bouldin": davies_bouldin,
        "calinski_harabasz": calinski_harabasz,
        "scatter": {
            "x": coords2[:, 0].tolist(),
            "y": coords2[:, 1].tolist(),
            "labels": labels.tolist(),
        },
        "scatter3d": {
            "x": coords3[:, 0].tolist(),
            "y": coords3[:, 1].tolist(),
            "z": (coords3[:, 2].tolist() if coords3.shape[1] > 2 else coords3[:, 0].tolist()),
            "labels": labels.tolist(),
        },
        "cluster_sizes": {str(c): int((labels == c).sum()) for c in set(labels)},
        "correlation": {"values": corr.values.tolist(), "cols": corr.columns.tolist()},
        "summary": summary,
        "points": [{"x": float(coords2[i, 0]), "y": float(coords2[i, 1]), "cluster": int(labels[i])} for i in range(len(labels))],
        "variance_explained": [round(float(v), 3) for v in pca2.explained_variance_ratio_],
    }


@router.get("/anomaly")
def anomaly_detection(contamination: float = 0.1, features: str = "",
                      user: dict = Depends(get_current_user)):
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.decomposition import PCA
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")

    # Select features
    if features:
        feat_list = [f.strip() for f in features.split(",") if f.strip() in df.columns]
        nums = df[feat_list].select_dtypes(include=np.number).fillna(0) if feat_list else df.select_dtypes(include=np.number).fillna(0)
    else:
        nums = df.select_dtypes(include=np.number).fillna(0)

    if nums.empty: raise HTTPException(422, "No numeric columns")

    cont = max(0.01, min(0.5, contamination))
    model = IsolationForest(contamination=cont, random_state=42)
    scores_raw = model.fit_predict(nums.values)
    score_vals = model.score_samples(nums.values)

    is_anomaly = scores_raw == -1
    anomaly_count = int(is_anomaly.sum())
    normal_count = len(df) - anomaly_count

    # PCA for 2D scatter
    pca = PCA(n_components=min(2, nums.shape[1]))
    coords = pca.fit_transform(nums.values)

    df2 = df.copy()
    df2["anomaly_score"] = score_vals.round(4)
    df2["is_anomaly"] = is_anomaly
    anomalies = df2[df2["is_anomaly"]].head(50)

    return {
        "total": len(df),
        "anomalies": anomaly_count,
        "normal": normal_count,
        "anomaly_count": anomaly_count,
        "scores": score_vals.tolist(),
        "scatter": {
            "x": coords[:, 0].tolist(),
            "y": (coords[:, 1].tolist() if coords.shape[1] > 1 else coords[:, 0].tolist()),
            "is_anomaly": is_anomaly.tolist(),
        },
        "anomaly_rows": anomalies.replace({float("nan"): None}).to_dict("records"),
        "anomalous_records": anomalies.replace({float("nan"): None}).to_dict("records"),
    }


@router.get("/timeseries")
def timeseries(col: str, user: dict = Depends(get_current_user)):
    import numpy as np
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")
    if col not in df.columns: raise HTTPException(422, f"Column '{col}' not found")
    series = df[col].dropna().values.astype(float)
    if len(series) < 4: raise HTTPException(422, "Need at least 4 data points")
    # Simple trend decomposition without statsmodels
    n = len(series)
    x = np.arange(n)
    # Trend: linear regression
    coeffs = np.polyfit(x, series, 1)
    trend = np.polyval(coeffs, x)
    # Residual
    residual = series - trend
    return {
        "column": col,
        "values": series.tolist(),
        "trend": trend.tolist(),
        "residual": residual.tolist(),
        "slope": round(float(coeffs[0]), 4),
        "trend_direction": "up" if coeffs[0] > 0 else "down",
        "n": n,
    }


class EngineerRequest(BaseModel):
    expression: str
    new_col: str


@router.post("/engineer")
def feature_engineer(req: EngineerRequest, user: dict = Depends(get_current_user)):
    import re
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")
    # Safety check - reject dangerous expressions
    dangerous = ["import", "__", "exec", "eval", "open", "os.", "sys."]
    for d in dangerous:
        if d in req.expression:
            raise HTTPException(422, f"Expression contains forbidden term: {d}")
    try:
        df2 = df.copy()
        df2[req.new_col] = df2.eval(req.expression)
        save_df(user["sub"], df2)
        return {"message": f"Column '{req.new_col}' added", "rows": len(df2), "columns": len(df2.columns)}
    except Exception as e:
        raise HTTPException(422, f"Expression error: {e}")


# - 3D Embedding Space (UMAP / t-SNE) -

class EmbeddingRequest(BaseModel):
    method: str = "umap"          # umap | tsne | pca
    n_components: int = 3
    features: Optional[list] = None
    color_col: Optional[str] = None
    n_neighbors: int = 15         # UMAP
    perplexity: int = 30          # t-SNE


@router.post("/embedding")
def embedding_3d(req: EmbeddingRequest, user: dict = Depends(get_current_user)):
    """Reduce high-dimensional data to 3D for visualization."""
    import numpy as np
    import json
    import plotly.graph_objects as go
    df = get_df(user["sub"])
    if df is None: raise HTTPException(404, "No dataset found")

    # Select features
    if req.features:
        nums = df[req.features].select_dtypes(include=np.number).fillna(0)
    else:
        nums = df.select_dtypes(include=np.number).fillna(0)
    if len(nums.columns) < 2:
        raise HTTPException(422, "Need at least 2 numeric columns")

    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(nums.values)

    # Reduce dimensions
    try:
        if req.method == "umap":
            import umap
            reducer = umap.UMAP(n_components=min(3, req.n_components), n_neighbors=req.n_neighbors, random_state=42)
            coords = reducer.fit_transform(X)
        elif req.method == "tsne":
            from sklearn.manifold import TSNE
            coords = TSNE(n_components=min(3, req.n_components), perplexity=min(req.perplexity, len(X)-1), random_state=42).fit_transform(X)
        else:  # pca
            from sklearn.decomposition import PCA
            coords = PCA(n_components=min(3, req.n_components, X.shape[1])).fit_transform(X)
    except ImportError as e:
        # Fallback to PCA
        from sklearn.decomposition import PCA
        coords = PCA(n_components=min(3, req.n_components, X.shape[1])).fit_transform(X)

    # Color
    color_vals = None
    color_label = "Index"
    if req.color_col and req.color_col in df.columns:
        col_data = df[req.color_col]
        if col_data.dtype == object:
            from sklearn.preprocessing import LabelEncoder
            color_vals = LabelEncoder().fit_transform(col_data.astype(str)).tolist()
        else:
            color_vals = col_data.fillna(0).tolist()
        color_label = req.color_col
    else:
        color_vals = list(range(len(coords)))

    n_comp = coords.shape[1]
    if n_comp >= 3:
        fig = go.Figure(go.Scatter3d(
            x=coords[:, 0].tolist(), y=coords[:, 1].tolist(), z=coords[:, 2].tolist(),
            mode="markers",
            marker=dict(size=4, color=color_vals, colorscale="Viridis", opacity=0.7,
                        colorbar=dict(title=color_label, thickness=12)),
            text=[f"Row {i}" for i in range(len(coords))],
        ))
        fig.update_layout(
            title=f"3D Embedding ({req.method.upper()})",
            scene=dict(xaxis_title="Dim 1", yaxis_title="Dim 2", zaxis_title="Dim 3"),
            template="plotly_dark", height=550,
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig = go.Figure(go.Scatter(
            x=coords[:, 0].tolist(), y=coords[:, 1].tolist() if n_comp > 1 else [0]*len(coords),
            mode="markers",
            marker=dict(size=5, color=color_vals, colorscale="Viridis", opacity=0.7),
        ))
        fig.update_layout(title=f"2D Embedding ({req.method.upper()})", template="plotly_dark", height=450)

    return {
        "plotly_json": json.loads(fig.to_json()),
        "method": req.method,
        "n_points": len(coords),
        "n_features": len(nums.columns),
        "features_used": list(nums.columns),
    }
