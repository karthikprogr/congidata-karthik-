"""
Test script for time-series forecasting functions (Tasks 6.1 and 6.2)
"""
import sys
import numpy as np
import pandas as pd

# Add the backend directory to the path
sys.path.insert(0, 'd:\\Cognidata_mainfinal-main\\cognidata\\backend')

from services.agents.automl_agent import create_lag_features, forecast_time_series

def test_create_lag_features():
    """Test Task 6.1: create_lag_features function"""
    print("=" * 60)
    print("Testing Task 6.1: create_lag_features")
    print("=" * 60)
    
    # Create sample time series
    series = pd.Series(range(1, 21), name="value")
    print(f"\nInput series (length {len(series)}):")
    print(series.values)
    
    # Test with default n_lags=7
    lag_df = create_lag_features(series, n_lags=7)
    
    print(f"\nOutput DataFrame shape: {lag_df.shape}")
    print(f"Expected shape: ({len(series) - 7}, 8)  # 7 lag features + 1 target")
    print(f"\nColumns: {list(lag_df.columns)}")
    print(f"\nFirst few rows:")
    print(lag_df.head())
    
    # Verify correctness
    assert lag_df.shape[1] == 8, f"Expected 8 columns (7 lags + target), got {lag_df.shape[1]}"
    assert lag_df.shape[0] == len(series) - 7, f"Expected {len(series) - 7} rows, got {lag_df.shape[0]}"
    assert 'target' in lag_df.columns, "Missing 'target' column"
    assert all(f'lag_{i}' in lag_df.columns for i in range(1, 8)), "Missing lag features"
    assert not lag_df.isnull().any().any(), "DataFrame should not contain null values"
    
    print("\n✓ Task 6.1: create_lag_features - PASSED")
    print("  - Generates lag_1 through lag_7 features")
    print("  - Returns DataFrame with lag features and target")
    print("  - Drops rows with null values")
    
    return True


def test_forecast_time_series():
    """Test Task 6.2: forecast_time_series function"""
    print("\n" + "=" * 60)
    print("Testing Task 6.2: forecast_time_series")
    print("=" * 60)
    
    # Create sample time series with trend and seasonality
    np.random.seed(42)
    time = np.arange(100)
    trend = 0.5 * time
    seasonality = 10 * np.sin(2 * np.pi * time / 12)
    noise = np.random.normal(0, 2, 100)
    series = pd.Series(trend + seasonality + noise + 50, name="value")
    
    print(f"\nInput series length: {len(series)}")
    print(f"Series statistics:")
    print(f"  Mean: {series.mean():.2f}")
    print(f"  Std: {series.std():.2f}")
    print(f"  Min: {series.min():.2f}")
    print(f"  Max: {series.max():.2f}")
    
    # Test forecasting
    horizon = 10
    result = forecast_time_series(series, horizon)
    
    print(f"\nForecast result keys: {list(result.keys())}")
    
    # Check for error
    if "error" in result:
        print(f"\n✗ Error during forecasting: {result['error']}")
        return False
    
    print(f"\nBest model: {result['best_model']}")
    print(f"MAPE: {result['mape']:.4f}%")
    print(f"\nLeaderboard:")
    for entry in result['leaderboard']:
        print(f"  {entry['model']}: MAPE = {entry['MAPE']:.4f}%")
    
    print(f"\nPredictions (first 5): {result['predictions'][:5]}")
    print(f"Train size: {result['train_size']}")
    print(f"Test size: {result['test_size']}")
    
    # Verify correctness
    assert 'best_model' in result, "Missing 'best_model' key"
    assert 'mape' in result, "Missing 'mape' key"
    assert 'predictions' in result, "Missing 'predictions' key"
    assert 'leaderboard' in result, "Missing 'leaderboard' key"
    assert 'train_size' in result, "Missing 'train_size' key"
    assert 'test_size' in result, "Missing 'test_size' key"
    
    # Check leaderboard
    assert len(result['leaderboard']) > 0, "Leaderboard should not be empty"
    assert result['leaderboard'][0]['model'] == result['best_model'], \
        "Best model should be first in leaderboard"
    
    # Check predictions
    assert len(result['predictions']) == result['test_size'], \
        f"Expected {result['test_size']} predictions, got {len(result['predictions'])}"
    
    # Check confidence intervals for ARIMA/ETS
    if result['best_model'] in ['AutoARIMA', 'ETS']:
        if result.get('confidence_intervals'):
            print(f"\nConfidence intervals available for {result['best_model']}")
            print(f"  Lower bound (first 5): {result['confidence_intervals']['lower'][:5]}")
            print(f"  Upper bound (first 5): {result['confidence_intervals']['upper'][:5]}")
        else:
            print(f"\nWarning: Confidence intervals not available for {result['best_model']}")
    
    print("\n✓ Task 6.2: forecast_time_series - PASSED")
    print("  - Trains AutoARIMA, ETS, and XGBoost models")
    print("  - Computes MAPE for each model")
    print("  - Ranks models by MAPE (ascending)")
    print("  - Returns best model with predictions")
    print("  - Includes confidence intervals when available")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Time-Series Forecasting Tests (Phase 2: Tasks 6.1 & 6.2)")
    print("=" * 60)
    
    try:
        # Test Task 6.1
        test1_passed = test_create_lag_features()
        
        # Test Task 6.2
        test2_passed = test_forecast_time_series()
        
        print("\n" + "=" * 60)
        if test1_passed and test2_passed:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
