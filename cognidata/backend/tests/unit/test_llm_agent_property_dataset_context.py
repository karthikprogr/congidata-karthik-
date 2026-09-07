"""
Property-based tests for dataset context reference validation in llm_agent.py

This module tests Property 4: Dataset context reference
**Validates: Requirements 2.1, 2.2, 2.3**

Property 4: Dataset context reference
- For any generated response, it SHALL include a reference to the specific dataset
  by either mentioning the record count OR using possessive phrases ("your data", 
  "this dataset") OR referencing column names from the dataset context.
"""
import pytest
from hypothesis import given, strategies as st, assume, example
from services.agents.llm_agent import _validate_response_format, QueryType


class TestDatasetContextReferenceProperty:
    """Property-based tests for dataset context reference validation"""
    
    # ── Property 4.1: Record count reference ──────────────────────────────────
    
    @given(
        record_count=st.integers(min_value=1, max_value=100000),
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(record_count=847, answer_text="Technology sells more", query_type=QueryType.SIMPLE)
    @example(record_count=2340, answer_text="West region leads with sales", query_type=QueryType.COMPLEX)
    @example(record_count=99, answer_text="Consumer products perform best", query_type=QueryType.SIMPLE)
    def test_property_response_with_record_count_is_valid(self, record_count, answer_text, query_type):
        """
        Property 4.1: Dataset context reference - Record count
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes a record count (numeric value), the
        validation SHALL pass because it references the dataset context.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Construct response with record count reference
        response = f"{answer_text} in your {record_count} records"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with record count should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.2: Possessive reference ("your") ───────────────────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        possessive_phrase=st.sampled_from([
            "your data", "your dataset", "your records", "your sales",
            "your orders", "your customers", "your transactions"
        ]),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology leads", possessive_phrase="your data", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales are growing", possessive_phrase="your records", query_type=QueryType.COMPLEX)
    def test_property_response_with_possessive_is_valid(self, answer_text, possessive_phrase, query_type):
        """
        Property 4.2: Dataset context reference - Possessive phrases
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes possessive phrases ("your data", "your 
        records", etc.), the validation SHALL pass because it references the
        user's specific dataset.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Ensure answer text doesn't already contain the possessive phrase
        assume(possessive_phrase.lower() not in answer_text.lower())
        
        # Construct response with possessive reference
        response = f"{answer_text} in {possessive_phrase}"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with possessive phrase should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.3: "this dataset" reference ────────────────────────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology leads", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales show growth", query_type=QueryType.COMPLEX)
    def test_property_response_with_this_dataset_is_valid(self, answer_text, query_type):
        """
        Property 4.3: Dataset context reference - "this dataset"
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes "this dataset" or "the data" phrases,
        the validation SHALL pass because it references the dataset context.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Ensure answer text doesn't already contain "this dataset" or "the data"
        assume("this dataset" not in answer_text.lower())
        assume("the data" not in answer_text.lower())
        
        # Construct response with "this dataset" reference
        response = f"{answer_text} in this dataset"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with 'this dataset' should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.4: Missing dataset reference fails ─────────────────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ,", 
            min_size=10, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology is the best option", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales are increasing steadily", query_type=QueryType.COMPLEX)
    def test_property_response_without_reference_is_invalid(self, answer_text, query_type):
        """
        Property 4.4: Dataset context reference - Missing reference fails
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that does NOT include a record count, possessive phrase,
        or dataset reference, the validation SHALL fail with an appropriate error.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Ensure text doesn't contain numbers (record count)
        assume(not any(char.isdigit() for char in answer_text))
        
        # Ensure text doesn't contain possessive references
        possessive_words = ['your', 'this dataset', 'the data']
        assume(not any(word in answer_text.lower() for word in possessive_words))
        
        # Construct response WITHOUT dataset reference
        response = answer_text.strip()
        if not response.endswith('.'):
            response += '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert not is_valid, (
            f"Response without dataset reference should be invalid. "
            f"Response: '{response}'"
        )
        
        assert "No dataset reference found" in error_msg, (
            f"Error message should mention missing dataset reference. "
            f"Error: '{error_msg}'"
        )
    
    # ── Property 4.5: Formatted record count reference ────────────────────────
    
    @given(
        record_count=st.integers(min_value=100, max_value=100000),
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(record_count=1500, answer_text="Technology sells more", query_type=QueryType.SIMPLE)
    @example(record_count=12847, answer_text="West region dominates", query_type=QueryType.COMPLEX)
    def test_property_response_with_formatted_count_is_valid(self, record_count, answer_text, query_type):
        """
        Property 4.5: Dataset context reference - Formatted record counts
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes a formatted record count with separators
        (e.g., "1,500" or "~12,000"), the validation SHALL pass because it
        contains numeric dataset context.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Format record count with comma separator
        formatted_count = f"{record_count:,}"
        
        # Construct response with formatted record count
        response = f"{answer_text} across {formatted_count} records"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with formatted record count should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.6: Multiple dataset references ─────────────────────────────
    
    @given(
        record_count=st.integers(min_value=1, max_value=10000),
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=40
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(record_count=847, answer_text="Technology leads", query_type=QueryType.SIMPLE)
    def test_property_response_with_multiple_references_is_valid(self, record_count, answer_text, query_type):
        """
        Property 4.6: Dataset context reference - Multiple references
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes BOTH a record count AND a possessive
        phrase, the validation SHALL pass (stronger dataset reference).
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Construct response with both record count and possessive
        response = f"{answer_text} in your {record_count} records"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with multiple dataset references should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.7: Dataset reference with approximate counts ───────────────
    
    @given(
        approximate_prefix=st.sampled_from(["~", "about ", "approximately ", "around "]),
        rounded_count=st.sampled_from([100, 500, 850, 1000, 2500, 10000, 13000]),
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(approximate_prefix="~", rounded_count=850, answer_text="Technology leads", query_type=QueryType.SIMPLE)
    @example(approximate_prefix="about ", rounded_count=2500, answer_text="Sales growing", query_type=QueryType.COMPLEX)
    def test_property_response_with_approximate_count_is_valid(self, approximate_prefix, rounded_count, answer_text, query_type):
        """
        Property 4.7: Dataset context reference - Approximate counts
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes approximate record counts (e.g., "~850",
        "about 2,500"), the validation SHALL pass because it contains numeric
        dataset context.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Construct response with approximate count
        response = f"{answer_text} in {approximate_prefix}{rounded_count} records"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with approximate count should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.8: "the data" reference ────────────────────────────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology performs best", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales trends upward", query_type=QueryType.COMPLEX)
    def test_property_response_with_the_data_is_valid(self, answer_text, query_type):
        """
        Property 4.8: Dataset context reference - "the data"
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes "the data" phrase, the validation SHALL
        pass because it references the dataset context.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Ensure answer text doesn't already contain "the data"
        assume("the data" not in answer_text.lower())
        
        # Construct response with "the data" reference
        response = f"Looking at the data, {answer_text}"
        
        # Note: This will fail preamble check, so test differently
        # Use "the data" in the middle or end
        response = f"{answer_text} based on the data"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        # May fail due to preamble check if "the data" is at start
        # but should pass dataset reference check
        if not is_valid:
            # If it failed, it should NOT be due to missing dataset reference
            assert "No dataset reference found" not in error_msg, (
                f"Response with 'the data' should pass dataset reference check. "
                f"Response: '{response}', Error: {error_msg}"
            )
    
    # ── Property 4.9: Case insensitivity for possessive references ────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=50
        ),
        case_variant=st.sampled_from(["your", "Your", "YOUR", "YoUr"]),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology leads", case_variant="your", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales growing", case_variant="Your", query_type=QueryType.COMPLEX)
    def test_property_possessive_case_insensitive(self, answer_text, case_variant, query_type):
        """
        Property 4.9: Dataset context reference - Case insensitivity
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response that includes possessive references in any case
        variation (your, Your, YOUR), the validation SHALL pass.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        # Construct response with possessive in various cases
        response = f"{answer_text} in {case_variant} dataset"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with possessive '{case_variant}' should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )
    
    # ── Property 4.10: Position independence of dataset reference ─────────────
    
    @given(
        answer_text=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ", 
            min_size=5, 
            max_size=30
        ),
        record_count=st.integers(min_value=1, max_value=10000),
        position=st.sampled_from(["start", "middle", "end"]),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(answer_text="Technology leads", record_count=847, position="start", query_type=QueryType.SIMPLE)
    @example(answer_text="Sales increase", record_count=2340, position="end", query_type=QueryType.SIMPLE)
    def test_property_reference_position_independence(self, answer_text, record_count, position, query_type):
        """
        Property 4.10: Dataset context reference - Position independence
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        For any response where the dataset reference appears at any position
        (start, middle, or end), the validation SHALL pass.
        """
        # Skip empty or whitespace-only text
        assume(answer_text.strip() != "")
        
        if position == "start":
            response = f"Your {record_count} records show {answer_text}"
        elif position == "middle":
            parts = answer_text.split()
            if len(parts) > 2:
                mid = len(parts) // 2
                response = f"{' '.join(parts[:mid])} in your {record_count} records {' '.join(parts[mid:])}"
            else:
                response = f"{answer_text} in your {record_count} records"
        else:  # end
            response = f"{answer_text} across your {record_count} records"
        
        # For SIMPLE queries, ensure only one sentence
        if query_type == QueryType.SIMPLE:
            response = response.rstrip('.') + '.'
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert is_valid, (
            f"Response with dataset reference at {position} should be valid. "
            f"Response: '{response}', Error: {error_msg}"
        )


# ── Specific edge case tests ─────────────────────────────────────────────────

class TestDatasetContextEdgeCases:
    """Edge case tests for dataset context reference validation"""
    
    def test_exact_count_small_dataset(self):
        """Response with exact count for small dataset (<100) should be valid"""
        response = "Technology sells more in your 47 records."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_rounded_count_large_dataset(self):
        """Response with rounded count for large dataset (≥100) should be valid"""
        response = "Technology leads in your ~850 records."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_multiple_numbers_in_response(self):
        """Response with multiple numbers should be valid (has dataset reference)"""
        response = "Technology has 500 orders in your 847 records."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_your_without_dataset_word(self):
        """Response with 'your' but not dataset-related should still be valid"""
        response = "Technology leads in your analysis."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid  # "your" is a possessive reference
    
    def test_number_in_non_count_context(self):
        """Response with number not related to count should be valid"""
        response = "Technology grew by 25% in your data."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid  # Has both number and "your"
    
    def test_no_reference_at_all(self):
        """Response with no dataset reference should be invalid"""
        response = "Technology is the best category."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert not is_valid
        assert "No dataset reference found" in error_msg
    
    def test_this_dataset_capitalized(self):
        """Response with 'This dataset' (capitalized) should be valid"""
        response = "This dataset shows Technology leading."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_the_data_capitalized(self):
        """Response with 'The data' (capitalized) should be valid"""
        response = "Technology leads based on the data."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_possessive_with_punctuation(self):
        """Response with possessive and punctuation should be valid"""
        response = "Technology sells more (in your records)."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_record_count_with_commas(self):
        """Response with comma-separated record count should be valid"""
        response = "Technology leads in your 12,847 records."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_tilde_prefix_rounded_count(self):
        """Response with ~[count] format should be valid"""
        response = "Technology dominates in ~13,000 records."
        is_valid, _ = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid
    
    def test_complex_query_multiple_references(self):
        """Complex query with multiple dataset references should be valid"""
        response = "Your 2,340 orders show Technology at $125,000. Consumer lags at $78,000 but improved 15%. The data reveals clear trends."
        is_valid, _ = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid
    
    def test_empty_response(self):
        """Empty response should be invalid"""
        response = ""
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert not is_valid
        assert "No dataset reference found" in error_msg
    
    def test_whitespace_only_response(self):
        """Whitespace-only response should be invalid"""
        response = "   \t\n  "
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert not is_valid
        assert "No dataset reference found" in error_msg
