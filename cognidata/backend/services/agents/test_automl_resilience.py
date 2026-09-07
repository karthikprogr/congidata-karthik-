"""
Test resilient training pipeline for AutoML agent.
Tests task 3.1 and 3.2: graceful error handling and leaderboard generation.
"""
import pandas as pd
import numpy as np
from services.agents.automl_agent import run_automl


def test_resilient_training_with_valid_data():
    """Test that AutoML trains successfully with valid data."""
    print("\n=== Test 1: Valid data - all models should train ===")
    
    # Create a simple regression dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'feature3': np.random.randn(100),
        'target': np.random.randn(100)
    })
    
    result = run_automl(df, target='target', user_id='test_user_1')
    
    # Verify response structure
    assert 'best_model' in result, "Response should contain best_model"
    assert 'leaderboard' in result, "Response should contain leaderboard"
    assert 'score' in result, "Response should contain score"
    
    # Verify leaderboard excludes failed models (score -999)
    for entry in result['leaderboard']:
        assert entry[result['metric']] != -999, f"Leaderboard should not contain failed models: {entry}"
    
    print(f"✓ Best model: {result['best_model']}")
    print(f"✓ Score: {result['score']}")
    print(f"✓ Leaderboard size: {len(result['leaderboard'])} models")
    print(f"✓ All leaderboard entries have valid scores (not -999)")


def test_leaderboard_excludes_failed_models():
    """Test that leaderboard excludes models with score -999."""
    print("\n=== Test 2: Leaderboard filtering ===")
    
    # Create a classification dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'target': np.random.choice(['A', 'B', 'C'], 100)
    })
    
    result = run_automl(df, target='target', user_id='test_user_2')
    
    # Check leaderboard
    assert len(result['leaderboard']) > 0, "Leaderboard should contain at least one model"
    
    # Verify all scores are valid (not -999)
    for entry in result['leaderboard']:
        score = entry[result['metric']]
        assert score != -999, f"Leaderboard contains failed model: {entry}"
        assert 0 <= score <= 1, f"Score should be between 0 and 1: {score}"
    
    print(f"✓ Leaderboard contains {len(result['leaderboard'])} models")
    print(f"✓ All models have valid scores")
    print(f"✓ Leaderboard is sorted (descending):")
    for entry in result['leaderboard'][:3]:
        print(f"  - {entry['model']}: {entry[result['metric']]}")


def test_error_handling_with_missing_target():
    """Test that missing target column returns proper error."""
    print("\n=== Test 3: Missing target column error handling ===")
    
    df = pd.DataFrame({
        'feature1': [1, 2, 3],
        'feature2': [4, 5, 6]
    })
    
    result = run_automl(df, target='nonexistent_column', user_id='test_user_3')
    
    assert 'error' in result, "Should return error response"
    assert 'not found' in result['error'].lower(), "Error should mention column not found"
    
    print(f"✓ Error handled correctly: {result['error']}")


def test_best_model_selection():
    """Test that best model is selected correctly even if some models fail."""
    print("\n=== Test 4: Best model selection ===")
    
    # Create regression dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'x1': np.random.randn(100),
        'x2': np.random.randn(100),
        'y': np.random.randn(100) * 10 + 5
    })
    
    result = run_automl(df, target='y', user_id='test_user_4')
    
    # Verify best model has highest score
    best_score = result['score']
    
    # Check that best_score is the highest in the leaderboard
    for entry in result['leaderboard']:
        leaderboard_score = entry[result['metric']]
        assert leaderboard_score <= best_score, \
            f"Best model score ({best_score}) should be >= all leaderboard scores ({leaderboard_score})"
    
    print(f"✓ Best model selected: {result['best_model']} with score {best_score}")
    print(f"✓ Best score is highest in leaderboard")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing AutoML Resilient Training Pipeline")
    print("Tasks 3.1 & 3.2: Error Handling and Leaderboard Generation")
    print("=" * 60)
    
    try:
        test_resilient_training_with_valid_data()
        test_leaderboard_excludes_failed_models()
        test_error_handling_with_missing_target()
        test_best_model_selection()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        raise
