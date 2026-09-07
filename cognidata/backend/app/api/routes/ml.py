"""
AutoML routes - train, predict, explain.
All JWT-protected.
"""
import sys, pathlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user
from app.services.data_store import get as get_df

router = APIRouter(prefix="/ml", tags=["AutoML"])

_p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
if _p not in sys.path:
    sys.path.insert(0, _p)

def _bootstrap():
    pass  # already done at import time


class TrainRequest(BaseModel):
    target: str


class PredictRequest(BaseModel):
    data: dict


@router.post("/train")
def train(req: TrainRequest, user: dict = Depends(get_current_user)):
    """Train AutoML on the user's uploaded dataset."""
    _bootstrap()
    from agents.automl_agent import run_automl
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found. Upload a file first.")
    result = run_automl(df, req.target, user_id=user["sub"])
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result


@router.post("/predict")
def predict(req: PredictRequest, user: dict = Depends(get_current_user)):
    """Run prediction using the trained model."""
    _bootstrap()
    from agents.automl_agent import predict as _predict
    result = _predict(user["sub"], req.data)
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result


@router.get("/explain")
def explain(user: dict = Depends(get_current_user)):
    """Generate SHAP feature importance for the trained model."""
    _bootstrap()
    from agents.automl_agent import explain_model
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found.")
    result = explain_model(user["sub"], df)
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result


# - AI Analyst specific endpoints -

class ClassifyRequest(BaseModel):
    target: str
    test_size: float = 0.2
    model: Optional[str] = None


class RegressRequest(BaseModel):
    target: str
    test_size: float = 0.2
    model: Optional[str] = None


class ExplainRequest(BaseModel):
    target: str
    model_type: str = "classification"


class CleanRequest(BaseModel):
    remove_duplicates: bool = True
    fill_missing: bool = True


def _pca3d(X, labels):
    """Return 3D PCA coordinates for visualization."""
    try:
        import numpy as np
        from sklearn.decomposition import PCA
        n_comp = min(3, X.shape[1])
        pca = PCA(n_components=n_comp)
        coords = pca.fit_transform(X)
        return {
            "x": coords[:, 0].tolist(),
            "y": coords[:, 1].tolist() if n_comp > 1 else coords[:, 0].tolist(),
            "z": coords[:, 2].tolist() if n_comp > 2 else coords[:, 0].tolist(),
            "labels": [float(l) for l in labels] if hasattr(labels, "__iter__") else [],
        }
    except Exception:
        return None


def _roc_curve(y_test, model, X_test):
    """Return ROC curve data for binary classification."""
    try:
        import numpy as np
        from sklearn.metrics import roc_curve, roc_auc_score
        if len(np.unique(y_test)) != 2:
            return None
        proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, proba)
        auc = float(roc_auc_score(y_test, proba))
        return {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": round(auc, 4)}
    except Exception:
        return None


def _clf_report(y_test, y_pred):
    """Return classification report as dict."""
    try:
        from sklearn.metrics import classification_report
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        return report
    except Exception:
        return None


@router.post("/classify")
def classify(req: ClassifyRequest, user: dict = Depends(get_current_user)):
    """LLM-guided classification."""
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    import plotly.graph_objects as go
    import json

    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    if req.target not in df.columns:
        raise HTTPException(422, f"Column '{req.target}' not found")

    # Prepare features
    X = df.drop(columns=[req.target]).select_dtypes(include=np.number).fillna(0)
    y = df[req.target]
    if y.dtype == object:
        le = LabelEncoder()
        y = le.fit_transform(y.astype(str))
    else:
        y = y.fillna(0).astype(int)

    if len(X.columns) == 0:
        raise HTTPException(422, "No numeric feature columns found")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=req.test_size, random_state=42)

    # Try models in order
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB

    models = [
        ("RandomForest", RandomForestClassifier(n_estimators=50, random_state=42)),
        ("GradientBoosting", GradientBoostingClassifier(n_estimators=50, random_state=42)),
        ("LogisticRegression", LogisticRegression(max_iter=500, random_state=42)),
        ("GaussianNB", GaussianNB()),
    ]

    best_model, best_name, best_acc = None, "", 0
    for name, m in models:
        try:
            m.fit(X_train, y_train)
            acc = accuracy_score(y_test, m.predict(X_test))
            if acc > best_acc:
                best_acc, best_model, best_name = acc, m, name
        except Exception:
            continue

    if best_model is None:
        raise HTTPException(422, "All models failed to train")

    y_pred = best_model.predict(X_test)
    f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    try:
        auc = float(roc_auc_score(y_test, best_model.predict_proba(X_test)[:, 1])) if len(np.unique(y)) == 2 else None
    except Exception:
        auc = None

    # Confusion matrix
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred)
    cm_fig = go.Figure(go.Heatmap(z=cm.tolist(), colorscale="Blues"))
    cm_fig.update_layout(title="Confusion Matrix", template="plotly_dark", height=300, margin=dict(l=20,r=20,t=40,b=20))

    # Feature importance
    fi_fig = None
    if hasattr(best_model, "feature_importances_"):
        fi = best_model.feature_importances_
        fi_fig = go.Figure(go.Bar(x=X.columns.tolist(), y=fi.tolist(), marker_color="#6366f1"))
        fi_fig.update_layout(title="Feature Importance", template="plotly_dark", height=280, margin=dict(l=20,r=20,t=40,b=20))

    return {
        "model": best_name,
        "accuracy": round(best_acc, 4),
        "f1": round(f1, 4),
        "auc": round(auc, 4) if auc else None,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "confusion_matrix": cm.tolist(),
        "feature_importance": {col: round(float(fi), 4) for col, fi in zip(X.columns, best_model.feature_importances_)} if hasattr(best_model, "feature_importances_") else None,
        "roc_curve": _roc_curve(y_test, best_model, X_test) if auc else None,
        "report": _clf_report(y_test, y_pred),
        "pca_3d": _pca3d(X_test.values, y_test),
    }


@router.post("/regress")
def regress(req: RegressRequest, user: dict = Depends(get_current_user)):
    """LLM-guided regression."""
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    import plotly.graph_objects as go
    import json

    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found")
    if req.target not in df.columns:
        raise HTTPException(422, f"Column '{req.target}' not found")

    X = df.drop(columns=[req.target]).select_dtypes(include=np.number).fillna(0)
    y = df[req.target].fillna(0).astype(float)

    if len(X.columns) == 0:
        raise HTTPException(422, "No numeric feature columns found")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=req.test_size, random_state=42)

    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge

    models = [
        ("RandomForest", RandomForestRegressor(n_estimators=50, random_state=42)),
        ("GradientBoosting", GradientBoostingRegressor(n_estimators=50, random_state=42)),
        ("Ridge", Ridge()),
    ]

    best_model, best_name, best_r2 = None, "", -999
    for name, m in models:
        try:
            m.fit(X_train, y_train)
            r2 = r2_score(y_test, m.predict(X_test))
            if r2 > best_r2:
                best_r2, best_model, best_name = r2, m, name
        except Exception:
            continue

    if best_model is None:
        raise HTTPException(422, "All models failed")

    y_pred = best_model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae  = float(mean_absolute_error(y_test, y_pred))

    # Predicted vs Actual
    pva = go.Figure()
    pva.add_trace(go.Scatter(x=y_test.tolist(), y=y_pred.tolist(), mode="markers", marker=dict(color="#6366f1", opacity=0.6), name="Predictions"))
    mn, mx = float(min(y_test.min(), y_pred.min())), float(max(y_test.max(), y_pred.max()))
    pva.add_trace(go.Scatter(x=[mn,mx], y=[mn,mx], mode="lines", line=dict(color="#ef4444", dash="dash"), name="Perfect Fit"))
    pva.update_layout(title="Predicted vs Actual", template="plotly_dark", height=300, margin=dict(l=20,r=20,t=40,b=20))

    # Feature importance
    fi_fig = None
    if hasattr(best_model, "feature_importances_"):
        fi = best_model.feature_importances_
        fi_fig = go.Figure(go.Bar(x=X.columns.tolist(), y=fi.tolist(), marker_color="#10b981"))
        fi_fig.update_layout(title="Feature Importance", template="plotly_dark", height=280, margin=dict(l=20,r=20,t=40,b=20))

    import json as _json
    residuals = (y_test.values - y_pred).tolist()
    return {
        "model": best_name,
        "r2": round(float(best_r2), 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mse": round(float(mean_squared_error(y_test, y_pred)), 4),
        "predictions": {"actual": y_test.tolist(), "predicted": y_pred.tolist()},
        "residuals": residuals,
        "pred_vs_actual": None,  # frontend builds from predictions
        "residual_plot": None,   # frontend builds from residuals
        "feature_importance": {col: round(float(fi), 4) for col, fi in zip(X.columns, best_model.feature_importances_)} if hasattr(best_model, "feature_importances_") else None,
        "pca_3d": _pca3d(X_test.values, y_pred),
    }


@router.post("/explain")
def explain_shap(req: ExplainRequest, user: dict = Depends(get_current_user)):
    """SHAP explanation for classification or regression."""
    import numpy as np
    import plotly.graph_objects as go
    import json

    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found")

    X = df.drop(columns=[req.target], errors="ignore").select_dtypes(include=np.number).fillna(0)
    y = df[req.target].fillna(0)

    try:
        import shap
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        if req.model_type == "classification":
            m = RandomForestClassifier(n_estimators=30, random_state=42)
            m.fit(X, y.astype(str))
        else:
            m = RandomForestRegressor(n_estimators=30, random_state=42)
            m.fit(X, y.astype(float))

        explainer = shap.TreeExplainer(m)
        shap_vals = explainer.shap_values(X.head(100))
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        mean_shap = np.abs(shap_vals).mean(axis=0)
        fig = go.Figure(go.Bar(x=X.columns.tolist(), y=mean_shap.tolist(), marker_color="#8b5cf6"))
        fig.update_layout(title="SHAP Feature Importance (mean |SHAP|)", template="plotly_dark", height=300, margin=dict(l=20,r=20,t=40,b=20))
        return {"chart": json.loads(fig.to_json()), "explainer": "TreeExplainer"}
    except ImportError:
        # Fallback without SHAP
        fi = getattr(m, "feature_importances_", None)
        if fi is not None:
            fig = go.Figure(go.Bar(x=X.columns.tolist(), y=fi.tolist(), marker_color="#8b5cf6"))
            fig.update_layout(title="Feature Importance (no SHAP)", template="plotly_dark", height=300, margin=dict(l=20,r=20,t=40,b=20))
            return {"chart": json.loads(fig.to_json()), "explainer": "feature_importances_"}
        raise HTTPException(422, "SHAP not installed. Run: pip install shap")


@router.post("/clean")
def clean_dataset(user: dict = Depends(get_current_user)):
    """LLM-guided data cleaning."""
    from app.services.data_store import save as save_df
    df = get_df(user["sub"])
    if df is None:
        raise HTTPException(404, "No dataset found")

    orig_rows = len(df)
    orig_cols = len(df.columns)

    # Remove duplicates
    df = df.drop_duplicates()
    rows_removed = orig_rows - len(df)

    # Fill missing values
    nulls_filled = 0
    for col in df.columns:
        n = df[col].isnull().sum()
        if n > 0:
            if df[col].dtype == object:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "unknown")
            else:
                df[col] = df[col].fillna(df[col].median())
            nulls_filled += n

    save_df(user["sub"], df)
    return {
        "rows_removed": int(rows_removed),
        "nulls_filled": int(nulls_filled),
        "cols_dropped": 0,
        "encodings": 0,
        "rows": len(df),
        "columns": len(df.columns),
    }
