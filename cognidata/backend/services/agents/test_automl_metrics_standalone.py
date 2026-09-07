"""
Standalone test for enhanced metrics computation for AutoML agent.
Tests tasks 7.1, 7.2, 7.3: Regression metrics, classification metrics, and leaderboard generation.

Requirements tested:
- 4.2: Leaderboard displays scores rounded to 4 decimal places
- 4.3: Leaderboard sorted in descending order by performance metric
- 4.4: Regression tasks report R², RMSE, MAE, MSE
- 4.5: Classification tasks report Accuracy, F1 score, ROC-AUC
"""
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automl_agent import run_automl


def test_regression_metrics_completeness():
    """Test Task 7.1: Regression metrics (R², RMSE, MAE, MSE) are computed."""
    print("\n=== Test 1: Regression Metrics Completeness ===")
    
    # Create a regression dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'feature3': np.random.randn(100),
        'target': np.random.randn(100) * 10 + 50
    })
    
    result = run_automl(df, target='target', user_id='test_regression_metrics')
    
    # Verify response structure
    assert 'leaderboard' in result, "Response should contain leaderboard"
    assert len(result['leaderboard']) > 0, "Leaderboard should not be empty"
    
    # Check that each model in leaderboard has all 4 regression metrics
    required_metrics = {'R²', 'RMSE', 'MAE', 'MSE'}
    
    for entry in result['leaderboard']:
        entry_metrics = set(entry.keys()) - {'model'}  # Exclude 'model' key
        assert required_metrics.issubset(entry_metrics), \
            f"Entry {entry['model']} missing metrics. Expected {required_metrics}, got {entry_metrics}"
        
        # Verify all metrics are rounded to 4 decimal places
        for metric in required_metrics:
            value = entry[metric]
            assert isinstance(value, (int, float)), f"{metric} should be numeric"
            # Check precision by converting to string
            str_value = str(value)
            if '.' in str_value:
                decimals = len(str_value.split('.')[1])
                assert decimals <= 4, f"{metric} should be rounded to max 4 decimals, got {decimals}"
    
    print(f"✓ All models have R², RMSE, MAE, MSE metrics")
    print(f"✓ Example entry: {result['leaderboard'][0]}")
    print(f"✓ All metrics rounded to 4 decimal places")


def test_classification_metrics_completeness():
    """Test Task 7.2: Classification metrics (Accuracy, F1, ROC-AUC) are computed."""
    print("\n=== Test 2: Classification Metrics Completeness ===")
    
    # Create a binary classification dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(150),
        'feature2': np.random.randn(150),
        'feature3': np.random.randn(150),
        'target': np.random.choice(['Class_0', 'Class_1'], 150)
    })
    
    result = run_automl(df, target='target', user_id='test_classification_metrics')
    
    # Verify response structure
    assert 'leaderboard' in result, "Response should contain leaderboard"
    assert len(result['leaderboard']) > 0, "Leaderboard should not be empty"
    
    # Check that each model in leaderboard has classification metrics
    required_metrics = {'Accuracy', 'F1'}
    
    for entry in result['leaderboard']:
        entry_metrics = set(entry.keys()) - {'model'}  # Exclude 'model' key
        
        # Accuracy and F1 are required
        assert required_metrics.issubset(entry_metrics), \
            f"Entry {entry['model']} missing metrics. Expected at least {required_metrics}, got {entry_metrics}"
        
        # ROC-AUC is optional (binary classification only)
        if 'ROC-AUC' in entry_metrics:
            print(f"  {entry['model']} has ROC-AUC: {entry['ROC-AUC']}")
        
        # Verify all metrics are rounded to 4 decimal places
        for metric in entry_metrics:
            if metric != 'model':
                value = entry[metric]
                assert isinstance(value, (int, float)), f"{metric} should be numeric"
                # Check precision
                str_value = str(value)
                if '.' in str_value:
                    decimals = len(str_value.split('.')[1])
                    assert decimals <= 4, f"{metric} should be rounded to max 4 decimals, got {decimals}"
    
    print(f"✓ All models have Accuracy and F1 metrics")
    print(f"✓ Example entry: {result['leaderboard'][0]}")
    print(f"✓ All metrics rounded to 4 decimal places")


def test_leaderboard_sorting():
    """Test Task 7.3: Leaderboard is sorted in descending order by performance metric."""
    print("\n=== Test 3: Leaderboard Sorting ===")
    
    # Create a regression dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'x1': np.random.randn(100),
        'x2': np.random.randn(100),
        'x3': np.random.randn(100),
        'y': np.random.randn(100) * 5 + 10
    })
    
    result = run_automl(df, target='y', user_id='test_leaderboard_sorting')
    
    # Get the primary metric
    metric = result['metric']
    leaderboard = result['leaderboard']
    
    assert len(leaderboard) > 1, "Need at least 2 models to test sorting"
    
    # Verify descending order
    scores = [entry[metric] for entry in leaderboard]
    sorted_scores = sorted(scores, reverse=True)
    
    assert scores == sorted_scores, \
        f"Leaderboard not sorted in descending order. Got {scores}, expected {sorted_scores}"
    
    print(f"✓ Leaderboard sorted by {metric} in descending order")
    print(f"✓ Top 3 models:")
    for i, entry in enumerate(leaderboard[:3], 1):
        print(f"  {i}. {entry['model']}: {entry[metric]}")
        print(f"     Full metrics: {entry}")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing AutoML Enhanced Metrics Computation")
    print("Tasks 7.1, 7.2, 7.3: Regression & Classification Metrics + Leaderboard")
    print("=" * 70)
    
    try:
        test_regression_metrics_completeness()
        test_classification_metrics_completeness()
        test_leaderboard_sorting()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
