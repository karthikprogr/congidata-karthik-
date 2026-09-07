"""XAI (Explainable AI) agent — SHAP + feature importance explanations."""
from typing import Optional


def explain(model, X, feature_names: list, max_features: int = 15) -> dict:
    """Generate SHAP or fallback feature importance explanation."""
    import numpy as np

    result = {"method": None, "feature_importance": {}, "shap_values": None}

    # Try SHAP first
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X[:100])
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        mean_shap = np.abs(shap_vals).mean(axis=0)
        fi = dict(zip(feature_names, mean_shap.round(4).tolist()))
        fi_sorted = dict(sorted(fi.items(), key=lambda x: abs(x[1]), reverse=True)[:max_features])
        result["method"] = "SHAP TreeExplainer"
        result["feature_importance"] = fi_sorted
        result["shap_values"] = mean_shap.tolist()
        return result
    except Exception:
        pass

    # Fallback: model feature_importances_
    if hasattr(model, "feature_importances_"):
        fi = dict(zip(feature_names, model.feature_importances_.round(4).tolist()))
        fi_sorted = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)[:max_features])
        result["method"] = "feature_importances_"
        result["feature_importance"] = fi_sorted
        return result

    # Fallback: linear model coefficients
    if hasattr(model, "coef_"):
        coefs = model.coef_.flatten() if model.coef_.ndim > 1 else model.coef_
        fi = dict(zip(feature_names, np.abs(coefs).round(4).tolist()))
        fi_sorted = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)[:max_features])
        result["method"] = "coef_ (linear)"
        result["feature_importance"] = fi_sorted
        return result

    result["method"] = "none"
    return result


def explain_prediction(model, X_sample, feature_names: list) -> dict:
    """Explain a single prediction using SHAP waterfall or fallback."""
    import numpy as np
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        vals = shap_vals[0] if shap_vals.ndim > 1 else shap_vals
        contributions = dict(zip(feature_names, vals.round(4).tolist()))
        return {"method": "SHAP", "contributions": contributions,
                "base_value": float(explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[0])}
    except Exception:
        pass
    return {"method": "none", "contributions": {}}
