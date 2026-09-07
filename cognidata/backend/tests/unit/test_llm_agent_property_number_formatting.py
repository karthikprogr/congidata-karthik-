"""
Property-based tests for number formatting precision in llm_agent.py

Tests Property 8: Number formatting precision
- For any response containing percentages, they SHALL be rounded to ≤2 decimal places
- For any response containing counts, they SHALL be whole numbers

**Validates: Requirements 4.4, 4.5**
"""
import pytest
import pandas as pd
import numpy as np
import re
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import AsyncMock, patch, MagicMock
from services.agents.llm_agent import run_insight, QueryType


class TestNumberFormattingPrecisionProperty:
    """
    Property-based tests for number formatting precision in responses.
    
    **Property 8: Number formatting precision**
    **Validates: Requirements 4.4, 4.5**
    """
    
    @given(
        record_count=st.integers(min_value=50, max_value=1000),
        percentage_value=st.floats(min_value=0.001, max_value=99.999, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_percentages_max_two_decimals(self, record_count, percentage_value):
        """
        Property 8a: For any response containing percentage values,
        the percentages SHALL be rounded to at most 2 decimal places.
        
        **Validates: Requirement 4.4**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['A', 'B'] * (record_count // 2),
            'Sales': np.random.randint(100, 1000, size=record_count)
        })
        
        # Mock the Gemini response to include a percentage
        mock_response = f"Category A represents {percentage_value:.10f}% of total sales in your {record_count} records."
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="What percentage of sales comes from Category A?"
            )
        
        # Extract all percentage values from the response
        # Pattern matches: number followed by % (including decimals)
        percentage_pattern = r'(\d+\.?\d*)%'
        percentages = re.findall(percentage_pattern, response)
        
        # Verify each percentage has at most 2 decimal places
        for pct_str in percentages:
            if '.' in pct_str:
                decimal_part = pct_str.split('.')[1]
                assert len(decimal_part) <= 2, \
                    f"Percentage {pct_str}% has {len(decimal_part)} decimal places, expected ≤2"
    
    @given(
        record_count=st.integers(min_value=50, max_value=1000),
        count_value=st.integers(min_value=1, max_value=10000)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_counts_are_whole_numbers(self, record_count, count_value):
        """
        Property 8b: For any response containing count values,
        the counts SHALL be whole numbers (no decimal places).
        
        **Validates: Requirement 4.5**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['A', 'B', 'C'] * (record_count // 3 + 1),
            'Sales': np.random.randint(100, 1000, size=record_count)
        })
        df = df.head(record_count)
        
        # Mock the Gemini response to include counts
        mock_response = f"Category A has {count_value} orders across your {record_count} records, with {count_value // 2} being high-value transactions."
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="How many orders does Category A have?"
            )
        
        # Extract all numeric values that represent counts (not percentages)
        # We need to distinguish between counts and percentages
        # Counts are numbers followed by units like "orders", "records", "transactions"
        count_pattern = r'(\d+\.?\d*)\s+(?:orders|records|transactions|items|customers|sales|rows)'
        count_matches = re.findall(count_pattern, response, re.IGNORECASE)
        
        # Also check for standalone numbers that are clearly counts (between "has" or "with" and a unit)
        count_pattern2 = r'(?:has|with|total|count of)\s+(\d+\.?\d*)'
        count_matches2 = re.findall(count_pattern2, response, re.IGNORECASE)
        
        all_counts = count_matches + count_matches2
        
        # Verify each count is a whole number
        for count_str in all_counts:
            # Check if it has a decimal point
            if '.' in count_str:
                # If it has a decimal, the decimal part should be all zeros
                decimal_part = count_str.split('.')[1]
                assert all(c == '0' for c in decimal_part), \
                    f"Count {count_str} is not a whole number, expected no decimal places"
            # Otherwise, it's already a whole number
    
    @given(
        record_count=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_mixed_numbers_formatted_correctly(self, record_count):
        """
        Property 8c: For any response containing both percentages and counts,
        percentages SHALL have ≤2 decimals AND counts SHALL be whole numbers.
        
        **Validates: Requirements 4.4, 4.5**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['A', 'B'] * (record_count // 2),
            'Sales': np.random.randint(100, 1000, size=record_count),
            'Profit': np.random.randint(10, 100, size=record_count)
        })
        
        # Mock a response with both counts and percentages
        mock_response = (
            f"Technology has 247 orders representing 45.67% of revenue, "
            f"while Consumer has 153 orders at 32.1% in your {record_count} records."
        )
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight with a complex query
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="Compare sales across categories with percentages"
            )
        
        # Extract percentages
        percentage_pattern = r'(\d+\.?\d*)%'
        percentages = re.findall(percentage_pattern, response)
        
        # Extract counts (numbers followed by count-related words)
        count_pattern = r'(\d+\.?\d*)\s+(?:orders|records|transactions|items)'
        counts = re.findall(count_pattern, response, re.IGNORECASE)
        
        # Verify percentages have at most 2 decimal places
        for pct_str in percentages:
            if '.' in pct_str:
                decimal_part = pct_str.split('.')[1]
                assert len(decimal_part) <= 2, \
                    f"Percentage {pct_str}% has {len(decimal_part)} decimal places, expected ≤2"
        
        # Verify counts are whole numbers
        for count_str in counts:
            if '.' in count_str:
                decimal_part = count_str.split('.')[1]
                assert all(c == '0' for c in decimal_part), \
                    f"Count {count_str} is not a whole number"
    
    @given(
        record_count=st.integers(min_value=100, max_value=500),
        percentage=st.floats(min_value=0.001, max_value=99.999, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_percentage_rounding_consistent(self, record_count, percentage):
        """
        Property 8d: For any percentage value in the response,
        the rounding SHALL be consistent (always to 2 or fewer decimal places,
        not 3+ decimals in some cases and 2 in others).
        
        **Validates: Requirement 4.4**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['A', 'B'] * (record_count // 2),
            'Value': np.random.randint(100, 1000, size=record_count)
        })
        
        # Mock a response with the given percentage (with many decimals)
        mock_response = f"Category A accounts for {percentage:.6f}% of the total in your {record_count} records."
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="What percentage does Category A represent?"
            )
        
        # Extract all percentages
        percentage_pattern = r'(\d+\.?\d*)%'
        percentages = re.findall(percentage_pattern, response)
        
        # All percentages should follow the same rounding rule
        for pct_str in percentages:
            if '.' in pct_str:
                decimal_part = pct_str.split('.')[1]
                # Consistent rule: at most 2 decimal places
                assert len(decimal_part) <= 2, \
                    f"Inconsistent percentage formatting: {pct_str}% has {len(decimal_part)} decimals"
    
    @given(
        record_count=st.integers(min_value=50, max_value=500),
        float_count=st.floats(min_value=10.5, max_value=999.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_counts_never_have_decimals(self, record_count, float_count):
        """
        Property 8e: For any numeric value representing a count (orders, records, items),
        it SHALL NEVER contain decimal places, even if the source data has decimals.
        
        **Validates: Requirement 4.5**
        """
        # Create a sample dataframe
        df = pd.DataFrame({
            'Category': ['A', 'B', 'C'] * (record_count // 3 + 1),
            'OrderCount': np.random.randint(10, 100, size=record_count)
        })
        df = df.head(record_count)
        
        # Mock a response that might incorrectly include decimal counts
        # The LLM should convert this to a whole number
        mock_response = f"There are {float_count:.2f} orders in category A from your {record_count} records."
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="How many orders in category A?"
            )
        
        # Extract counts (numbers followed by count words, not percentages)
        count_pattern = r'(\d+\.?\d*)\s+(?:orders|records|items|transactions|customers)'
        counts = re.findall(count_pattern, response, re.IGNORECASE)
        
        # Verify each count is a whole number
        for count_str in counts:
            # Should not contain a decimal point with non-zero decimals
            if '.' in count_str:
                parts = count_str.split('.')
                if len(parts) == 2:
                    # If there's a decimal part, it should be removed or all zeros
                    # Actually, counts should NEVER have decimal points at all
                    assert False, \
                        f"Count {count_str} should be a whole number without decimals"
            # Otherwise it's fine (no decimal point)
    
    @given(
        record_count=st.integers(min_value=100, max_value=500)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_numerical_precision_in_complex_queries(self, record_count):
        """
        Property 8f: For any complex query response containing multiple numbers,
        ALL percentages SHALL have ≤2 decimals AND ALL counts SHALL be whole numbers,
        regardless of the number of metrics in the response.
        
        **Validates: Requirements 4.4, 4.5**
        """
        # Create a sample dataframe with multiple categories
        df = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D'] * (record_count // 4),
            'Sales': np.random.randint(1000, 5000, size=record_count),
            'Quantity': np.random.randint(10, 100, size=record_count)
        })
        
        # Mock a complex response with multiple numbers
        mock_response = (
            f"Your {record_count} records show Technology with 342 orders at 45.67%, "
            f"Consumer with 278 orders at 32.15%, Office with 189 orders at 18.9%, "
            f"and Furniture with 91 orders at 3.28%."
        )
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight with a complex query
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="Break down sales by category with percentages"
            )
        
        # Extract all percentages
        percentage_pattern = r'(\d+\.?\d*)%'
        percentages = re.findall(percentage_pattern, response)
        
        # Extract all counts
        count_pattern = r'(\d+\.?\d*)\s+(?:orders|records|items|transactions)'
        counts = re.findall(count_pattern, response, re.IGNORECASE)
        
        # Verify ALL percentages have at most 2 decimal places
        for pct_str in percentages:
            if '.' in pct_str:
                decimal_part = pct_str.split('.')[1]
                assert len(decimal_part) <= 2, \
                    f"Percentage {pct_str}% has {len(decimal_part)} decimal places, expected ≤2"
        
        # Verify ALL counts are whole numbers
        for count_str in counts:
            assert '.' not in count_str, \
                f"Count {count_str} should be a whole number without decimal point"
    
    @given(
        record_count=st.integers(min_value=50, max_value=500),
        num_categories=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_formatting_applies_to_all_numeric_types(self, record_count, num_categories):
        """
        Property 8g: For any response, the formatting rules SHALL apply to all numeric
        values regardless of their context (revenue percentages, growth percentages,
        order counts, customer counts, etc.).
        
        **Validates: Requirements 4.4, 4.5**
        """
        # Create a diverse dataframe
        categories = [chr(65 + i) for i in range(num_categories)]  # A, B, C, etc.
        df = pd.DataFrame({
            'Category': categories * (record_count // num_categories + 1),
            'Revenue': np.random.randint(1000, 10000, size=record_count),
            'CustomerCount': np.random.randint(10, 200, size=record_count)
        })
        df = df.head(record_count)
        
        # Mock a response with various types of numbers
        mock_response = (
            f"In your {record_count} records, revenue grew 23.45% with 1,234 customers "
            f"generating 5,678 orders. Category A leads at 41.2% market share with 456 sales."
        )
        
        # Create a mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.generate_text = AsyncMock(return_value=mock_response)
        
        # Patch the _get_gemini_client function
        with patch('services.agents.llm_agent._get_gemini_client', return_value=mock_gemini):
            # Call run_insight
            response = run_insight(
                df=df,
                api_key="test_key",
                history=[],
                question="What are the key trends?"
            )
        
        # Extract all percentages (growth, market share, etc.)
        percentage_pattern = r'(\d+\.?\d*)%'
        percentages = re.findall(percentage_pattern, response)
        
        # Extract all counts (customers, orders, sales, etc.)
        count_pattern = r'(\d+\.?\d*)\s+(?:customers|orders|sales|records|items|transactions)'
        counts = re.findall(count_pattern, response, re.IGNORECASE)
        
        # Verify percentages (all types) have at most 2 decimal places
        for pct_str in percentages:
            if '.' in pct_str:
                decimal_part = pct_str.split('.')[1]
                assert len(decimal_part) <= 2, \
                    f"Percentage {pct_str}% has {len(decimal_part)} decimals, expected ≤2"
        
        # Verify counts (all types) are whole numbers
        for count_str in counts:
            assert '.' not in count_str, \
                f"Count {count_str} should be a whole number"


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
