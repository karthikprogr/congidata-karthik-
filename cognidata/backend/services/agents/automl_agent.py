"""
AutoML Agent — trains multiple models, picks the best, explains with SHAP.
"""
import numpy as np
import pandas as pd
from typing import Optional
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    r2_score, accuracy_score, classification_report,
    mean_squared_error, mean_absolute_error, f1_score, roc_auc_score
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from xgboost import XGBRegressor, XGBClassifier
from lightgbm import LGBMRegressor, LGBMClassifier
from catboost import CatBoostRegressor, CatBoostClassifier
import optuna

# In-memory model store: {user_id: {model, feature_cols, target, task, score}}
_models: dict[str, dict] = {}

REGRESSION_MODELS = {
    "XGBoost":             XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
    "LightGBM":            LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
    "CatBoost":            CatBoostRegressor(iterations=100, random_state=42, verbose=0),
    "RandomForest":        RandomForestRegressor(n_estimators=100, random_state=42),
    "GradientBoosting":    GradientBoostingRegressor(n_estimators=100, random_state=42),
    "LinearRegression":    LinearRegression(),
    "Ridge":               Ridge(alpha=1.0),
    "DecisionTree":        DecisionTreeRegressor(max_depth=6, random_state=42),
}

CLASSIFICATION_MODELS = {
    "XGBoost":             XGBClassifier(n_estimators=100, random_state=42, verbosity=0),
    "LightGBM":            LGBMClassifier(n_estimators=100, random_state=42, verbose=-1),
    "CatBoost":            CatBoostClassifier(iterations=100, random_state=42, verbose=0),
    "RandomForest":        RandomForestClassifier(n_estimators=100, random_state=42),
    "GradientBoosting":    GradientBoostingClassifier(n_estimators=100, random_state=42),
    "LogisticRegression":  LogisticRegression(max_iter=500, random_state=42),
    "DecisionTree":        DecisionTreeClassifier(max_depth=6, random_state=42),
}


def _detect_task(y: pd.Series) -> str:
    """Detect regression vs classification."""
    if y.dtype == object or y.nunique() <= 10:
        return "classification"
    return "regression"


def _prepare(df: pd.DataFrame, target: str):
    """Encode categoricals, drop nulls, split features/target."""
    df = df.dropna(subset=[target]).copy()
    X = df.drop(columns=[target])
    y = df[target]

    # Encode categorical features
    for col in X.select_dtypes("object").columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))

    # Encode target if classification
    le_target = None
    if y.dtype == object:
        le_target = LabelEncoder()
        y = pd.Series(le_target.fit_transform(y.astype(str)), name=target)

    X = X.fillna(X.mean(numeric_only=True))
    return X, y, le_target


def optimize_hyperparameters(X: pd.DataFrame, y: pd.Series, model_name: str, task: str) -> dict:
    """Use Optuna to find optimal hyperparameters for XGBoost, LightGBM, CatBoost.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_name: Name of model to optimize ("XGBoost", "LightGBM", "CatBoost")
        task: Task type ("regression" or "classification")
    
    Returns:
        Dictionary of best hyperparameters
    """
    # Sample to 10,000 rows for optimization
    if len(X) > 10000:
        indices = np.random.RandomState(42).choice(len(X), 10000, replace=False)
        X_sample = X.iloc[indices]
        y_sample = y.iloc[indices]
    else:
        X_sample = X
        y_sample = y
    
    # Define objective function for Optuna
    def objective(trial):
        # Define search spaces based on model
        if model_name == "XGBoost":
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'random_state': 42,
                'verbosity': 0
            }
            if task == "regression":
                model = XGBRegressor(**params)
            else:
                model = XGBClassifier(**params)
        
        elif model_name == "LightGBM":
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'random_state': 42,
                'verbose': -1
            }
            if task == "regression":
                model = LGBMRegressor(**params)
            else:
                model = LGBMClassifier(**params)
        
        elif model_name == "CatBoost":
            params = {
                'iterations': trial.suggest_int('iterations', 50, 300),
                'depth': trial.suggest_int('depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'random_state': 42,
                'verbose': 0
            }
            if task == "regression":
                model = CatBoostRegressor(**params)
            else:
                model = CatBoostClassifier(**params)
        else:
            raise ValueError(f"Hyperparameter optimization not supported for {model_name}")
        
        # Use 3-fold cross-validation
        scoring = 'r2' if task == "regression" else 'accuracy'
        scores = cross_val_score(model, X_sample, y_sample, cv=3, scoring=scoring)
        return scores.mean()
    
    # Run Optuna optimization
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=20, show_progress_bar=False)
    
    return study.best_params


def run_automl(df: pd.DataFrame, target: str, user_id: str = "", hyperparameter_tuning: bool = False) -> dict:
    """Train multiple models, return best one with metrics."""
    if target not in df.columns:
        return {"error": f"Column '{target}' not found"}

    X, y, le_target = _prepare(df, target)
    task = _detect_task(y)
    models = CLASSIFICATION_MODELS if task == "classification" else REGRESSION_MODELS
    
    # Set metric based on task (needed for response even if all models fail)
    metric = "Accuracy" if task == "classification" else "R²"

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    results = []
    for name, model in models.items():
        try:
            # Apply hyperparameter optimization if enabled and model supports it
            if hyperparameter_tuning and name in ["XGBoost", "LightGBM", "CatBoost"]:
                # Optimize hyperparameters
                best_params = optimize_hyperparameters(X_train, y_train, name, task)
                
                # Create new model with optimized hyperparameters
                if name == "XGBoost":
                    if task == "regression":
                        model = XGBRegressor(**best_params, random_state=42, verbosity=0)
                    else:
                        model = XGBClassifier(**best_params, random_state=42, verbosity=0)
                elif name == "LightGBM":
                    if task == "regression":
                        model = LGBMRegressor(**best_params, random_state=42, verbose=-1)
                    else:
                        model = LGBMClassifier(**best_params, random_state=42, verbose=-1)
                elif name == "CatBoost":
                    if task == "regression":
                        model = CatBoostRegressor(**best_params, random_state=42, verbose=0)
                    else:
                        model = CatBoostClassifier(**best_params, random_state=42, verbose=0)
            
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            # Compute metrics based on task type
            if task == "regression":
                # Task 7.1: Compute R², RMSE, MAE, MSE for regression
                r2 = round(r2_score(y_test, preds), 4)
                mse = round(mean_squared_error(y_test, preds), 4)
                rmse = round(np.sqrt(mse), 4)
                mae = round(mean_absolute_error(y_test, preds), 4)
                
                results.append({
                    "name": name, 
                    "score": r2,  # Primary ranking metric
                    "model": model,
                    "metrics": {
                        "R²": r2,
                        "RMSE": rmse,
                        "MAE": mae,
                        "MSE": mse
                    }
                })
            else:
                # Task 7.2: Compute Accuracy, F1, ROC-AUC for classification
                accuracy = round(accuracy_score(y_test, preds), 4)
                f1 = round(f1_score(y_test, preds, average='weighted'), 4)
                
                # Compute ROC-AUC for binary classification only
                roc_auc = None
                if len(np.unique(y_test)) == 2:
                    try:
                        # Get probability predictions for ROC-AUC
                        if hasattr(model, 'predict_proba'):
                            proba = model.predict_proba(X_test)[:, 1]
                            roc_auc = round(roc_auc_score(y_test, proba), 4)
                    except Exception:
                        # If ROC-AUC computation fails, leave it as None
                        pass
                
                metrics_dict = {
                    "Accuracy": accuracy,
                    "F1": f1
                }
                if roc_auc is not None:
                    metrics_dict["ROC-AUC"] = roc_auc
                
                results.append({
                    "name": name,
                    "score": accuracy,  # Primary ranking metric
                    "model": model,
                    "metrics": metrics_dict
                })
        except Exception as e:
            # Resilient training: log error, assign -999, continue with remaining models
            print(f"Model {name} failed during training: {str(e)}")
            results.append({"name": name, "score": -999, "model": None, "error": str(e)})

    # Pick best (highest score, even if all models failed)
    best = max(results, key=lambda r: r["score"])

    # Store in memory (only if model training succeeded)
    if user_id and best["model"] is not None:
        _models[user_id] = {
            "model":        best["model"],
            "feature_cols": list(X.columns),
            "target":       target,
            "task":         task,
            "score":        best["score"],
            "metric":       metric,
        }

    # Task 7.3: Generate leaderboard sorted by performance metric, excluding failed models
    # Sort models by score in descending order, exclude models with score -999, format to 4 decimals
    leaderboard = []
    for r in sorted(results, key=lambda r: r["score"], reverse=True):
        if r["score"] != -999:
            # Include primary metric and all additional metrics
            entry = {"model": r["name"], metric: r["score"]}
            if "metrics" in r:
                # Add all metrics from the metrics dictionary
                for metric_name, metric_value in r["metrics"].items():
                    if metric_name != metric:  # Don't duplicate the primary metric
                        entry[metric_name] = metric_value
            leaderboard.append(entry)

    return {
        "best_model":  best["name"],
        "task":        task,
        "target":      target,
        "metric":      metric,
        "score":       best["score"],
        "leaderboard": leaderboard,
        "features":    list(X.columns),
        "train_rows":  len(X_train),
        "test_rows":   len(X_test),
    }


def predict(user_id: str, input_data: dict) -> dict:
    """Run prediction using the stored model for this user."""
    if user_id not in _models:
        return {"error": "No trained model found. Run AutoML first."}

    stored = _models[user_id]
    model = stored["model"]
    feature_cols = stored["feature_cols"]

    try:
        row = pd.DataFrame([input_data])
        # Align columns
        for col in feature_cols:
            if col not in row.columns:
                row[col] = 0
        row = row[feature_cols].fillna(0)

        pred = model.predict(row)
        return {
            "prediction": float(pred[0]) if stored["task"] == "regression" else int(pred[0]),
            "target": stored["target"],
            "task": stored["task"],
        }
    except Exception as e:
        return {"error": str(e)}


def explain_model(user_id: str, df: pd.DataFrame) -> dict:
    """Generate SHAP feature importance for the stored model."""
    if user_id not in _models:
        return {"error": "No trained model found. Run AutoML first."}

    stored = _models[user_id]
    model = stored["model"]
    feature_cols = stored["feature_cols"]

    try:
        import shap, json

        X, _, _ = _prepare(df, stored["target"])
        X = X[feature_cols].head(100)  # cap for speed

        # Use TreeExplainer for tree models, LinearExplainer for linear
        model_name = type(model).__name__
        if "Forest" in model_name or "Boosting" in model_name or "Tree" in model_name:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
        else:
            explainer = shap.LinearExplainer(model, X)
            shap_values = explainer.shap_values(X)

        # Mean absolute SHAP per feature
        mean_shap = np.abs(shap_values).mean(axis=0)
        importance = dict(zip(feature_cols, mean_shap.round(4).tolist()))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        # Build Plotly bar chart
        import plotly.express as px
        imp_df = pd.DataFrame(list(importance.items()), columns=["feature", "importance"])
        fig = px.bar(imp_df, x="importance", y="feature", orientation="h",
                     title="SHAP Feature Importance",
                     template="plotly_dark",
                     color="importance",
                     color_continuous_scale="Viridis")
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(300, len(feature_cols) * 30))

        return {
            "importance": importance,
            "plotly_json": json.loads(fig.to_json()),
            "model": model_name,
            "target": stored["target"],
        }
    except Exception as e:
        # Fallback: use built-in feature_importances_ if available
        try:
            if hasattr(model, "feature_importances_"):
                imp = dict(zip(feature_cols, model.feature_importances_.round(4).tolist()))
                imp = dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
                import plotly.express as px, json
                imp_df = pd.DataFrame(list(imp.items()), columns=["feature", "importance"])
                fig = px.bar(imp_df, x="importance", y="feature", orientation="h",
                             title="Feature Importance (built-in)",
                             template="plotly_dark")
                return {"importance": imp, "plotly_json": json.loads(fig.to_json()),
                        "model": type(model).__name__, "target": stored["target"]}
        except Exception:
            pass
        return {"error": str(e)}


def create_lag_features(series: pd.Series, n_lags: int = 7) -> pd.DataFrame:
    """Create lag features for time-series forecasting.
    
    Args:
        series: Time-series data as pandas Series
        n_lags: Number of lag features to generate (default: 7)
    
    Returns:
        DataFrame with lag features (lag_1 through lag_n_lags) and target column
        Rows with null values (first n_lags rows) are dropped
    """
    df = pd.DataFrame()
    
    # Generate lag features lag_1 through lag_n_lags
    for i in range(1, n_lags + 1):
        df[f'lag_{i}'] = series.shift(i)
    
    # Add target column
    df['target'] = series.values
    
    # Drop rows with null values (first n_lags rows)
    df = df.dropna()
    
    return df


def forecast_time_series(series: pd.Series, horizon: int) -> dict:
    """Forecast time-series using AutoARIMA, ETS, and XGBoost models.
    
    Trains three forecasting models, ranks them by MAPE, and returns the best performer.
    
    Args:
        series: Time-series data as pandas Series
        horizon: Number of periods to forecast
    
    Returns:
        Dictionary containing:
            - best_model: Name of best-performing model
            - predictions: Forecasted values
            - confidence_intervals: Lower and upper bounds (if available)
            - mape: Mean Absolute Percentage Error on test set
            - leaderboard: All models ranked by MAPE
    """
    # Split into train/test (80-20)
    split_idx = int(len(series) * 0.8)
    train = series.iloc[:split_idx]
    test = series.iloc[split_idx:]
    
    results = []
    
    # 1. Train AutoARIMA model
    try:
        from pmdarima import auto_arima
        
        arima_model = auto_arima(
            train,
            seasonal=True,
            m=12,
            stepwise=True,
            suppress_warnings=True,
            error_action='ignore'
        )
        
        # Forecast on test set
        arima_preds, arima_conf_int = arima_model.predict(
            n_periods=len(test),
            return_conf_int=True
        )
        
        # Compute MAPE
        arima_mape = np.mean(np.abs((test.values - arima_preds) / test.values)) * 100
        
        results.append({
            "name": "AutoARIMA",
            "mape": round(arima_mape, 4),
            "model": arima_model,
            "predictions": arima_preds,
            "confidence_intervals": {
                "lower": arima_conf_int[:, 0].tolist(),
                "upper": arima_conf_int[:, 1].tolist()
            }
        })
    except Exception as e:
        print(f"AutoARIMA failed: {str(e)}")
        results.append({"name": "AutoARIMA", "mape": 999999, "error": str(e)})
    
    # 2. Train ETS model
    try:
        from statsforecast import StatsForecast
        from statsforecast.models import AutoETS
        
        # Prepare data for statsforecast
        train_df = pd.DataFrame({
            'unique_id': ['series'] * len(train),
            'ds': range(len(train)),
            'y': train.values
        })
        
        sf = StatsForecast(
            models=[AutoETS(season_length=12)],
            freq=1
        )
        sf.fit(train_df)
        
        # Forecast on test set with prediction intervals
        ets_forecast = sf.predict(h=len(test), level=[95])
        ets_preds = ets_forecast['AutoETS'].values
        
        # Compute MAPE
        ets_mape = np.mean(np.abs((test.values - ets_preds) / test.values)) * 100
        
        # ETS provides prediction intervals
        ets_conf_int = None
        if 'AutoETS-lo-95' in ets_forecast.columns and 'AutoETS-hi-95' in ets_forecast.columns:
            ets_conf_int = {
                "lower": ets_forecast['AutoETS-lo-95'].values.tolist(),
                "upper": ets_forecast['AutoETS-hi-95'].values.tolist()
            }
        
        results.append({
            "name": "ETS",
            "mape": round(ets_mape, 4),
            "model": sf,
            "predictions": ets_preds,
            "confidence_intervals": ets_conf_int
        })
    except Exception as e:
        print(f"ETS failed: {str(e)}")
        results.append({"name": "ETS", "mape": 999999, "error": str(e)})
    
    # 3. Train XGBoost time-series model
    try:
        # Create lag features
        lag_df = create_lag_features(train, n_lags=7)
        X_train = lag_df.drop('target', axis=1)
        y_train = lag_df['target']
        
        # Train XGBoost model
        xgb_model = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
        xgb_model.fit(X_train, y_train)
        
        # Generate recursive predictions on test set
        xgb_preds = []
        history = list(train.values[-7:])  # Last 7 values from train
        
        for _ in range(len(test)):
            # Create feature vector from last 7 values
            features = np.array(history[-7:]).reshape(1, -1)[:, ::-1]  # Reverse to match lag order
            pred = xgb_model.predict(features)[0]
            xgb_preds.append(pred)
            history.append(pred)
        
        xgb_preds = np.array(xgb_preds)
        
        # Compute MAPE
        xgb_mape = np.mean(np.abs((test.values - xgb_preds) / test.values)) * 100
        
        results.append({
            "name": "XGBoost",
            "mape": round(xgb_mape, 4),
            "model": xgb_model,
            "predictions": xgb_preds,
            "confidence_intervals": None  # XGBoost doesn't provide confidence intervals
        })
    except Exception as e:
        print(f"XGBoost time-series failed: {str(e)}")
        results.append({"name": "XGBoost", "mape": 999999, "error": str(e)})
    
    # Rank models by MAPE (ascending - lower is better)
    results = sorted(results, key=lambda r: r.get("mape", 999999))
    
    # Select best model
    best = results[0]
    
    # Generate leaderboard (exclude failed models)
    leaderboard = [
        {"model": r["name"], "MAPE": r["mape"]}
        for r in results
        if r["mape"] < 999999
    ]
    
    # If best model failed, return error
    if best["mape"] >= 999999:
        return {"error": "All forecasting models failed to train"}
    
    # Return best model with predictions
    return {
        "best_model": best["name"],
        "mape": best["mape"],
        "predictions": best["predictions"].tolist() if hasattr(best["predictions"], 'tolist') else list(best["predictions"]),
        "confidence_intervals": best.get("confidence_intervals"),
        "leaderboard": leaderboard,
        "train_size": len(train),
        "test_size": len(test)
    }
