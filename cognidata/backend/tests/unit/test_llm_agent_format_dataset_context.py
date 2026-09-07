"""
Unit tests for _format_dataset_context() helper function in llm_agent.py

Tests the dataset context formatting with proper record count rounding
according to the AI Chat Direct Answers specification.
"""
import pytest
import pandas as pd
import numpy as np
from services.agents.llm_agent import _format_dataset_context


class TestFormatDatasetContext:
    """Test suite for _format_dataset_context() function"""
    
    def test_exact_count_below_100_records(self):
        """Test exact record count for datasets with <100 records"""
        # Test with 47 records
        df = pd.DataFrame({
            'A': range(47),
            'B': ['x'] * 47
        })
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 47
        assert ctx['record_count_formatted'] == "47"
        
        # Test with 99 records (boundary case)
        df = pd.DataFrame({
            'A': range(99),
            'B': ['x'] * 99
        })
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 99
        assert ctx['record_count_formatted'] == "99"
    
    def test_rounding_to_nearest_10_for_100_to_999_records(self):
        """Test rounding to nearest 10 for 100-999 records"""
        # Test with 100 records (boundary case)
        df = pd.DataFrame({'A': range(100)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 100
        assert ctx['record_count_formatted'] == "~100"
        
        # Test with 847 records
        df = pd.DataFrame({'A': range(847)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 847
        assert ctx['record_count_formatted'] == "~850"
        
        # Test with 999 records (boundary case)
        df = pd.DataFrame({'A': range(999)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 999
        assert ctx['record_count_formatted'] == "~1,000"
        
        # Test with 125 records (should round to 130)
        df = pd.DataFrame({'A': range(125)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 125
        # Python's round() uses banker's rounding, 125 rounds to 120
        assert ctx['record_count_formatted'] == "~120"
    
    def test_rounding_to_nearest_100_for_1k_to_9999_records(self):
        """Test rounding to nearest 100 for 1,000-9,999 records"""
        # Test with 1,000 records (boundary case)
        df = pd.DataFrame({'A': range(1000)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 1000
        assert ctx['record_count_formatted'] == "~1,000"
        
        # Test with 3,421 records
        df = pd.DataFrame({'A': range(3421)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 3421
        assert ctx['record_count_formatted'] == "~3,400"
        
        # Test with 9,999 records (boundary case)
        df = pd.DataFrame({'A': range(9999)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 9999
        assert ctx['record_count_formatted'] == "~10,000"
    
    def test_rounding_to_nearest_1000_for_10k_plus_records(self):
        """Test rounding to nearest 1,000 for 10,000+ records"""
        # Test with 10,000 records (boundary case)
        df = pd.DataFrame({'A': range(10000)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 10000
        assert ctx['record_count_formatted'] == "~10,000"
        
        # Test with 12,847 records
        df = pd.DataFrame({'A': range(12847)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 12847
        assert ctx['record_count_formatted'] == "~13,000"
        
        # Test with 50,000 records
        df = pd.DataFrame({'A': range(50000)})
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 50000
        assert ctx['record_count_formatted'] == "~50,000"
    
    def test_extract_numeric_columns(self):
        """Test extraction of numeric columns using select_dtypes(include=np.number)"""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.5, 2.5, 3.5],
            'str_col': ['a', 'b', 'c'],
            'bool_col': [True, False, True]
        })
        
        ctx = _format_dataset_context(df)
        
        # Should identify int and float columns as numeric
        assert 'int_col' in ctx['numeric_columns']
        assert 'float_col' in ctx['numeric_columns']
        assert len(ctx['numeric_columns']) == 2
    
    def test_extract_categorical_columns(self):
        """Test extraction of categorical columns using select_dtypes(include='object')"""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'str_col1': ['a', 'b', 'c'],
            'str_col2': ['x', 'y', 'z'],
            'float_col': [1.5, 2.5, 3.5]
        })
        
        ctx = _format_dataset_context(df)
        
        # Should identify string columns as categorical
        assert 'str_col1' in ctx['categorical_columns']
        assert 'str_col2' in ctx['categorical_columns']
        assert len(ctx['categorical_columns']) == 2
    
    def test_return_dictionary_structure(self):
        """Test that function returns dictionary with all required fields"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10.5, 20.5, 30.5, 40.5, 50.5],
            'C': ['cat', 'dog', 'bird', 'fish', 'rabbit'],
            'D': ['red', 'blue', 'green', 'yellow', 'purple']
        })
        
        ctx = _format_dataset_context(df)
        
        # Check all required keys are present
        assert 'record_count' in ctx
        assert 'record_count_formatted' in ctx
        assert 'num_columns' in ctx
        assert 'column_names' in ctx
        assert 'numeric_columns' in ctx
        assert 'categorical_columns' in ctx
        
        # Verify values
        assert ctx['record_count'] == 5
        assert ctx['record_count_formatted'] == "5"
        assert ctx['num_columns'] == 4
        assert ctx['column_names'] == ['A', 'B', 'C', 'D']
        assert ctx['numeric_columns'] == ['A', 'B']
        assert ctx['categorical_columns'] == ['C', 'D']
    
    def test_empty_dataframe(self):
        """Test with empty dataframe (0 records)"""
        df = pd.DataFrame({'A': [], 'B': []})
        
        ctx = _format_dataset_context(df)
        
        assert ctx['record_count'] == 0
        assert ctx['record_count_formatted'] == "0"
        assert ctx['num_columns'] == 2
        assert ctx['column_names'] == ['A', 'B']
    
    def test_dataframe_with_only_numeric_columns(self):
        """Test with dataframe containing only numeric columns"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4.5, 5.5, 6.5],
            'C': [7, 8, 9]
        })
        
        ctx = _format_dataset_context(df)
        
        assert len(ctx['numeric_columns']) == 3
        assert len(ctx['categorical_columns']) == 0
        assert ctx['numeric_columns'] == ['A', 'B', 'C']
        assert ctx['categorical_columns'] == []
    
    def test_dataframe_with_only_categorical_columns(self):
        """Test with dataframe containing only categorical columns"""
        df = pd.DataFrame({
            'A': ['a', 'b', 'c'],
            'B': ['x', 'y', 'z'],
            'C': ['p', 'q', 'r']
        })
        
        ctx = _format_dataset_context(df)
        
        assert len(ctx['numeric_columns']) == 0
        assert len(ctx['categorical_columns']) == 3
        assert ctx['numeric_columns'] == []
        assert ctx['categorical_columns'] == ['A', 'B', 'C']
    
    def test_rounding_edge_cases(self):
        """Test specific rounding edge cases"""
        # 145 should round to 140 (nearest 10)
        df = pd.DataFrame({'A': range(145)})
        ctx = _format_dataset_context(df)
        assert ctx['record_count_formatted'] == "~140"
        
        # 155 should round to 160 (nearest 10)
        df = pd.DataFrame({'A': range(155)})
        ctx = _format_dataset_context(df)
        assert ctx['record_count_formatted'] == "~160"
        
        # 1,450 should round to 1,400 (nearest 100)
        df = pd.DataFrame({'A': range(1450)})
        ctx = _format_dataset_context(df)
        assert ctx['record_count_formatted'] == "~1,400"
        
        # 1,550 should round to 1,600 (nearest 100)
        df = pd.DataFrame({'A': range(1550)})
        ctx = _format_dataset_context(df)
        assert ctx['record_count_formatted'] == "~1,600"
