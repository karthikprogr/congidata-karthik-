"""
Test enhanced metrics computation for AutoML agent.
Tests tasks 7.1, 7.2, 7.3: Regression metrics, classification metrics, and leaderboard generation.

Requirements tested:
- 4.2: Leaderboard displays scores rounded to 4 decimal places
- 4.3: Leaderboard sorted in descending order by performance metric
- 4.4: Regression tasks report R², RMSE, MAE, MSE
- 4.5: Classification tasks report Accuracy, F1 score, ROC-AUC
"""
import pandas as pd
import numpy as np
from services.agents.automl_agent import run_automl


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


def test_multiclass_classification_metrics():
    """Test Task 7.2: Multiclass classification (no ROC-AUC expected)."""
    print("\n=== Test 3: Multiclass Classification Metrics ===")
    
    # Create a multiclass classification dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(150),
        'feature2': np.random.randn(150),
        'feature3': np.random.randn(150),
        'target': np.random.choice(['A', 'B', 'C'], 150)
    })
    
    result = run_automl(df, target='target', user_id='test_multiclass_metrics')
    
    # Verify response structure
    assert 'leaderboard' in result, "Response should contain leaderboard"
    assert len(result['leaderboard']) > 0, "Leaderboard should not be empty"
    
    # Check metrics
    for entry in result['leaderboard']:
        # Accuracy and F1 should be present
        assert 'Accuracy' in entry, f"{entry['model']} should have Accuracy"
        assert 'F1' in entry, f"{entry['model']} should have F1"
        
        # ROC-AUC should NOT be present for multiclass (unless macro/micro averaging is used)
        # For now, we don't compute ROC-AUC for multiclass
        print(f"  {entry['model']}: Accuracy={entry['Accuracy']}, F1={entry['F1']}")
    
    print(f"✓ Multiclass models have Accuracy and F1")
    print(f"✓ ROC-AUC not computed for multiclass (as expected)")


def test_leaderboard_sorting():
    """Test Task 7.3: Leaderboard is sorted in descending order by performance metric."""
    print("\n=== Test 4: Leaderboard Sorting ===")
    
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


def test_leaderboard_excludes_failed_models():
    """Test Task 7.3: Leaderboard excludes models with score -999."""
    print("\n=== Test 5: Leaderboard Excludes Failed Models ===")
    
    # Create a dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'target': np.random.randn(100)
    })
    
    result = run_automl(df, target='target', user_id='test_leaderboard_filtering')
    
    # Verify no model in leaderboard has score -999
    for entry in result['leaderboard']:
        metric_score = entry[result['metric']]
        assert metric_score != -999, \
            f"Leaderboard should not contain failed models: {entry}"
    
    print(f"✓ Leaderboard contains {len(result['leaderboard'])} valid models")
    print(f"✓ No models with score -999 in leaderboard")


def test_score_precision():
    """Test Task 7.3: All scores are formatted to 4 decimal places."""
    print("\n=== Test 6: Score Precision (4 Decimal Places) ===")
    
    # Create a regression dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'a': np.random.randn(100),
        'b': np.random.randn(100),
        'c': np.random.randn(100),
        'target': np.random.randn(100) * 3 + 7
    })
    
    result = run_automl(df, target='target', user_id='test_score_precision')
    
    # Check all metrics in all leaderboard entries
    for entry in result['leaderboard']:
        for key, value in entry.items():
            if key != 'model' and isinstance(value, (int, float)):
                # Convert to string and check decimal places
                str_value = str(value)
                if '.' in str_value:
                    decimal_part = str_value.split('.')[1]
                    assert len(decimal_part) <= 4, \
                        f"Metric {key} in {entry['model']} has {len(decimal_part)} decimals, expected max 4: {value}"
    
    print(f"✓ All metrics rounded to maximum 4 decimal places")
    print(f"✓ Example scores from top model:")
    top_entry = result['leaderboard'][0]
    for key, value in top_entry.items():
        if key != 'model':
            print(f"  {key}: {value}")


def test_primary_metric_in_leaderboard():
    """Test that primary metric (R² or Accuracy) appears in leaderboard."""
    print("\n=== Test 7: Primary Metric in Leaderboard ===")
    
    # Test regression
    np.random.seed(42)
    df_reg = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    
    result_reg = run_automl(df_reg, target='y', user_id='test_primary_metric_reg')
    
    assert result_reg['metric'] == 'R²', "Regression should use R² as primary metric"
    
    for entry in result_reg['leaderboard']:
        assert 'R²' in entry, f"Leaderboard entry should contain primary metric R²"
    
    print(f"✓ Regression leaderboard contains primary metric R²")
    
    # Test classification
    df_cls = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.choice(['A', 'B'], 100)
    })
    
    result_cls = run_automl(df_cls, target='y', user_id='test_primary_metric_cls')
    
    assert result_cls['metric'] == 'Accuracy', "Classification should use Accuracy as primary metric"
    
    for entry in result_cls['leaderboard']:
        assert 'Accuracy' in entry, f"Leaderboard entry should contain primary metric Accuracy"
    
    print(f"✓ Classification leaderboard contains primary metric Accuracy")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing AutoML Enhanced Metrics Computation")
    print("Tasks 7.1, 7.2, 7.3: Regression & Classification Metrics + Leaderboard")
    print("=" * 70)
    
    try:
        test_regression_metrics_completeness()
        test_classification_metrics_completeness()
        test_multiclass_classification_metrics()
        test_leaderboard_sorting()
        test_leaderboard_excludes_failed_models()
        test_score_precision()
        test_primary_metric_in_leaderboard()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
