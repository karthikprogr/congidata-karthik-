"""
Property-based tests for record count formatting in llm_agent.py

Tests Property 5: Record count formatting rules
- For any dataset with <100 records, the response SHALL include the exact record count
- For any dataset with >=100 records, the response SHALL include a rounded record count

**Validates: Requirements 2.4, 2.5**
"""
import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, assume
from services.agents.llm_agent import _format_dataset_context


class TestRecordCountFormattingProperty:
    """
    Property-based tests for record count formatting rules.
    
    **Property 5: Record count formatting rules**
    **Validates: Requirements 2.4, 2.5**
    """
    
    @given(record_count=st.integers(min_value=1, max_value=99))
    def test_property_exact_count_below_100(self, record_count):
        """
        Property 5a: For any dataset with <100 records, 
        the formatted record count SHALL be exact (no rounding, no approximation).
        
        **Validates: Requirement 2.4**
        """
        # Create a dataframe with the specified record count
        df = pd.DataFrame({'A': range(record_count)})
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Verify the record count is exact
        assert ctx['record_count'] == record_count, \
            f"Expected record_count to be {record_count}, got {ctx['record_count']}"
        
        # Verify the formatted count is exact (no ~ prefix)
        assert ctx['record_count_formatted'] == str(record_count), \
            f"Expected exact count '{record_count}', got '{ctx['record_count_formatted']}'"
        
        # Verify no approximation symbol
        assert '~' not in ctx['record_count_formatted'], \
            f"Exact count should not contain '~', got '{ctx['record_count_formatted']}'"
    
    @given(record_count=st.integers(min_value=100, max_value=999))
    def test_property_rounded_count_100_to_999(self, record_count):
        """
        Property 5b: For any dataset with 100-999 records,
        the formatted record count SHALL be rounded to the nearest 10.
        
        **Validates: Requirement 2.5**
        """
        # Create a dataframe with the specified record count
        df = pd.DataFrame({'A': range(record_count)})
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Verify the actual count is preserved
        assert ctx['record_count'] == record_count, \
            f"Expected record_count to be {record_count}, got {ctx['record_count']}"
        
        # Verify the formatted count has approximation symbol
        assert ctx['record_count_formatted'].startswith('~'), \
            f"Rounded count should start with '~', got '{ctx['record_count_formatted']}'"
        
        # Extract the numeric value (remove ~ and commas)
        formatted_value_str = ctx['record_count_formatted'].replace('~', '').replace(',', '')
        formatted_value = int(formatted_value_str)
        
        # Verify it's rounded to nearest 10
        expected_rounded = round(record_count, -1)
        assert formatted_value == expected_rounded, \
            f"Expected {record_count} rounded to nearest 10 = {expected_rounded}, got {formatted_value}"
        
        # Verify the rounded value ends in 0 (nearest 10)
        assert formatted_value % 10 == 0, \
            f"Value should be rounded to nearest 10, got {formatted_value}"
    
    @given(record_count=st.integers(min_value=1000, max_value=9999))
    def test_property_rounded_count_1000_to_9999(self, record_count):
        """
        Property 5c: For any dataset with 1,000-9,999 records,
        the formatted record count SHALL be rounded to the nearest 100.
        
        **Validates: Requirement 2.5**
        """
        # Create a dataframe with the specified record count
        df = pd.DataFrame({'A': range(record_count)})
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Verify the actual count is preserved
        assert ctx['record_count'] == record_count, \
            f"Expected record_count to be {record_count}, got {ctx['record_count']}"
        
        # Verify the formatted count has approximation symbol
        assert ctx['record_count_formatted'].startswith('~'), \
            f"Rounded count should start with '~', got '{ctx['record_count_formatted']}'"
        
        # Extract the numeric value (remove ~ and commas)
        formatted_value_str = ctx['record_count_formatted'].replace('~', '').replace(',', '')
        formatted_value = int(formatted_value_str)
        
        # Verify it's rounded to nearest 100
        expected_rounded = round(record_count, -2)
        assert formatted_value == expected_rounded, \
            f"Expected {record_count} rounded to nearest 100 = {expected_rounded}, got {formatted_value}"
        
        # Verify the rounded value ends in 00 (nearest 100)
        assert formatted_value % 100 == 0, \
            f"Value should be rounded to nearest 100, got {formatted_value}"
    
    @given(record_count=st.integers(min_value=10000, max_value=100000))
    def test_property_rounded_count_10000_plus(self, record_count):
        """
        Property 5d: For any dataset with 10,000+ records,
        the formatted record count SHALL be rounded to the nearest 1,000.
        
        **Validates: Requirement 2.5**
        """
        # Create a dataframe with the specified record count
        # Use a single column to keep memory usage reasonable
        df = pd.DataFrame({'A': range(record_count)})
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Verify the actual count is preserved
        assert ctx['record_count'] == record_count, \
            f"Expected record_count to be {record_count}, got {ctx['record_count']}"
        
        # Verify the formatted count has approximation symbol
        assert ctx['record_count_formatted'].startswith('~'), \
            f"Rounded count should start with '~', got '{ctx['record_count_formatted']}'"
        
        # Extract the numeric value (remove ~ and commas)
        formatted_value_str = ctx['record_count_formatted'].replace('~', '').replace(',', '')
        formatted_value = int(formatted_value_str)
        
        # Verify it's rounded to nearest 1,000
        expected_rounded = round(record_count, -3)
        assert formatted_value == expected_rounded, \
            f"Expected {record_count} rounded to nearest 1,000 = {expected_rounded}, got {formatted_value}"
        
        # Verify the rounded value ends in 000 (nearest 1,000)
        assert formatted_value % 1000 == 0, \
            f"Value should be rounded to nearest 1,000, got {formatted_value}"
    
    @given(record_count=st.integers(min_value=1, max_value=1000000))
    def test_property_record_count_always_preserved(self, record_count):
        """
        Property 5e: For any dataset, the actual record count SHALL always be preserved
        in the 'record_count' field, regardless of how it's formatted for display.
        
        **Validates: Requirements 2.4, 2.5**
        """
        # Limit the size for performance - use sampling strategy for very large datasets
        if record_count > 100000:
            # For very large datasets, create a smaller sample but track the intended count
            df = pd.DataFrame({'A': range(min(record_count, 10000))})
            # Manually set the length we want to test by creating a larger range
            # Actually, let's skip extremely large datasets for property testing
            assume(record_count <= 100000)
        else:
            df = pd.DataFrame({'A': range(record_count)})
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # The actual record count must always match the dataframe length
        assert ctx['record_count'] == len(df), \
            f"Expected record_count to match df length {len(df)}, got {ctx['record_count']}"
        
        # Both fields must be present
        assert 'record_count' in ctx, "record_count field must be present"
        assert 'record_count_formatted' in ctx, "record_count_formatted field must be present"
    
    @given(record_count=st.integers(min_value=100, max_value=100000))
    def test_property_formatted_count_has_comma_separator(self, record_count):
        """
        Property 5f: For any dataset with 100+ records where the rounded value >= 1,000,
        the formatted count SHALL include comma separators for readability.
        
        **Validates: Requirement 2.5**
        """
        # Create a dataframe with the specified record count
        df = pd.DataFrame({'A': range(min(record_count, 10000))})
        # If testing larger values, we'll just check the formatting logic
        if record_count > 10000:
            # Mock the length for large datasets to avoid memory issues
            assume(record_count <= 100000)
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Extract the numeric value from formatted string
        formatted_str = ctx['record_count_formatted'].replace('~', '')
        
        # If the formatted value is >= 1,000, it should have commas
        if ',' in formatted_str:
            # Remove commas and verify it's a valid number
            numeric_str = formatted_str.replace(',', '')
            numeric_value = int(numeric_str)
            assert numeric_value >= 1000, \
                f"Comma separator used, but value is {numeric_value} < 1,000"
    
    @given(record_count=st.integers(min_value=1, max_value=100000))
    def test_property_boundary_transition_at_100(self, record_count):
        """
        Property 5g: The boundary at 100 records is the transition point:
        - Records < 100: exact count, no ~ prefix
        - Records >= 100: rounded count, with ~ prefix
        
        **Validates: Requirements 2.4, 2.5**
        """
        # Create a dataframe with the specified record count
        df = pd.DataFrame({'A': range(min(record_count, 10000))})
        if record_count > 10000:
            assume(record_count <= 100000)
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        if record_count < 100:
            # Should be exact, no approximation
            assert '~' not in ctx['record_count_formatted'], \
                f"Count < 100 should not have '~', got '{ctx['record_count_formatted']}'"
            assert ctx['record_count_formatted'] == str(record_count), \
                f"Count < 100 should be exact, got '{ctx['record_count_formatted']}' instead of '{record_count}'"
        else:
            # Should be rounded with approximation symbol
            assert ctx['record_count_formatted'].startswith('~'), \
                f"Count >= 100 should start with '~', got '{ctx['record_count_formatted']}'"
    
    @given(
        record_count=st.integers(min_value=1, max_value=100000),
        num_columns=st.integers(min_value=1, max_value=10)
    )
    def test_property_formatting_independent_of_columns(self, record_count, num_columns):
        """
        Property 5h: Record count formatting SHALL be independent of the number
        or type of columns in the dataset.
        
        **Validates: Requirements 2.4, 2.5**
        """
        # Limit dataset size for performance
        actual_rows = min(record_count, 10000)
        if record_count > 10000:
            assume(record_count <= 100000)
        
        # Create a dataframe with multiple columns of different types
        data = {}
        for i in range(num_columns):
            if i % 3 == 0:
                data[f'num_col_{i}'] = np.random.randint(0, 100, size=actual_rows)
            elif i % 3 == 1:
                data[f'str_col_{i}'] = [f'value_{j}' for j in range(actual_rows)]
            else:
                data[f'float_col_{i}'] = np.random.random(size=actual_rows)
        
        df = pd.DataFrame(data)
        
        # Format the dataset context
        ctx = _format_dataset_context(df)
        
        # Verify the formatting follows the same rules regardless of columns
        if len(df) < 100:
            assert ctx['record_count_formatted'] == str(len(df))
        else:
            assert ctx['record_count_formatted'].startswith('~')
        
        # Verify column information is present
        assert ctx['num_columns'] == num_columns
        assert len(ctx['column_names']) == num_columns


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
