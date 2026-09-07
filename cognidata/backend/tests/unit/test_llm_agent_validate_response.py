"""
Unit tests for _validate_response_format() function.

Tests validation logic for response format requirements:
- Sentence count limits (1 for SIMPLE, 3 for COMPLEX)
- Preamble detection
- Dataset reference validation
- Technical jargon detection
- Academic transition detection
"""
import pytest
from services.agents.llm_agent import _validate_response_format, QueryType


class TestValidateResponseFormat:
    """Test suite for response format validation"""
    
    # ── Sentence Count Validation ─────────────────────────────────────────────
    
    def test_simple_query_one_sentence_valid(self):
        """Simple query with 1 sentence should pass"""
        response = "Technology sells more in your 847 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_simple_query_two_sentences_invalid(self):
        """Simple query with 2 sentences should fail"""
        response = "Technology leads. Furniture lags."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "Too many sentences" in error_msg
        assert "2 > 1" in error_msg
    
    def test_complex_query_one_sentence_valid(self):
        """Complex query with 1 sentence should pass"""
        response = "Your 2,340 orders show steady growth from Jan to Jun."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is True
        assert error_msg == ""
    
    def test_complex_query_three_sentences_valid(self):
        """Complex query with 3 sentences should pass"""
        response = (
            "Your 2,340 orders show steady growth from Jan to Jun. "
            "Technology drives 45% of revenue at $125,000. "
            "Consumer products improved 15% in Q2."
        )
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is True
        assert error_msg == ""
    
    def test_complex_query_four_sentences_invalid(self):
        """Complex query with 4 sentences should fail"""
        response = (
            "Technology leads. Furniture lags. "
            "Office supplies are stable. Consumer is growing."
        )
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "Too many sentences" in error_msg
        assert "4 > 3" in error_msg
    
    # ── Preamble Detection ────────────────────────────────────────────────────
    
    def test_preamble_based_on_data_invalid(self):
        """Response starting with 'Based on the data' should fail"""
        response = "Based on the data, Technology leads in your 100 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_preamble_based_on_your_data_invalid(self):
        """Response starting with 'Based on your data' should fail"""
        response = "Based on your data, sales are increasing."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_preamble_looking_at_invalid(self):
        """Response starting with 'Looking at' should fail"""
        response = "Looking at the trends, Technology sells more."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_preamble_let_me_analyze_invalid(self):
        """Response starting with 'Let me analyze' should fail"""
        response = "Let me analyze your 500 records and show you the results."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_preamble_i_can_see_invalid(self):
        """Response starting with 'I can see' should fail"""
        response = "I can see that your sales are growing."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_preamble_the_data_shows_invalid(self):
        """Response starting with 'The data shows' should fail"""
        response = "The data shows Technology leading with 100 sales."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "preamble" in error_msg.lower()
    
    def test_no_preamble_direct_answer_valid(self):
        """Response starting directly with answer should pass"""
        response = "Technology sells more in your 847 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    # ── Dataset Reference Validation ──────────────────────────────────────────
    
    def test_dataset_reference_with_number_valid(self):
        """Response with record count should pass"""
        response = "Technology leads in 847 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_dataset_reference_with_your_valid(self):
        """Response with 'your' possessive should pass"""
        response = "Technology sells more in your dataset."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_dataset_reference_with_this_dataset_valid(self):
        """Response with 'this dataset' should pass"""
        response = "Technology leads this dataset with higher sales."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_dataset_reference_with_the_data_valid(self):
        """Response with 'the data' should pass"""
        response = "Technology dominates the data with more sales."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_no_dataset_reference_invalid(self):
        """Response without dataset reference should fail"""
        response = "Technology sells more than Furniture."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "No dataset reference" in error_msg
    
    # ── Technical Jargon Detection ────────────────────────────────────────────
    
    def test_jargon_statistical_significance_invalid(self):
        """Response with 'statistical significance' should fail"""
        response = "Your 100 records show statistical significance in sales."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "jargon" in error_msg.lower()
        assert "statistical significance" in error_msg
    
    def test_jargon_p_value_invalid(self):
        """Response with 'p-value' should fail"""
        response = "The p-value indicates significance in your 200 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "jargon" in error_msg.lower()
        assert "p-value" in error_msg
    
    def test_jargon_correlation_coefficient_invalid(self):
        """Response with 'correlation coefficient' should fail"""
        response = "The correlation coefficient is 0.8 in your dataset."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "jargon" in error_msg.lower()
        assert "correlation coefficient" in error_msg
    
    def test_jargon_standard_deviation_invalid(self):
        """Response with 'standard deviation' should fail"""
        response = "The standard deviation is high across your 500 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "jargon" in error_msg.lower()
        assert "standard deviation" in error_msg
    
    def test_no_jargon_casual_language_valid(self):
        """Response with casual business language should pass"""
        response = "Your 500 records show Technology selling more than Furniture."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is True
        assert error_msg == ""
    
    # ── Academic Transition Detection ─────────────────────────────────────────
    
    def test_academic_therefore_invalid(self):
        """Response with 'Therefore' should fail"""
        response = "Sales increased in Q1. Therefore, your 100 records show growth."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "academic transition" in error_msg.lower()
    
    def test_academic_thus_invalid(self):
        """Response with 'Thus' should fail"""
        response = "Revenue grew in your dataset. Thus, the trend is positive."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "academic transition" in error_msg.lower()
    
    def test_academic_in_conclusion_invalid(self):
        """Response with 'In conclusion' should fail"""
        response = "Sales are up. In conclusion, your 200 records indicate growth."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "academic transition" in error_msg.lower()
    
    def test_academic_furthermore_invalid(self):
        """Response with 'Furthermore' should fail"""
        response = "Technology leads. Furthermore, your data shows Furniture lags."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "academic transition" in error_msg.lower()
    
    def test_academic_moreover_invalid(self):
        """Response with 'Moreover' should fail"""
        response = "Sales grew in Q1. Moreover, your 300 records show continued growth."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is False
        assert "academic transition" in error_msg.lower()
    
    def test_no_academic_transitions_valid(self):
        """Response without academic transitions should pass"""
        response = "Your 500 records show Technology leading with higher sales."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is True
        assert error_msg == ""
    
    # ── Edge Cases ────────────────────────────────────────────────────────────
    
    def test_empty_response_invalid(self):
        """Empty response should fail (no dataset reference)"""
        response = ""
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
    
    def test_sentence_with_multiple_periods_single_sentence(self):
        """Response with abbreviations (e.g., 'U.S.') should count as one sentence"""
        response = "The U.S. region leads in your 500 records."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        # Should pass as single sentence (U.S. doesn't trigger sentence split)
        assert is_valid is True
        assert error_msg == ""
    
    def test_question_mark_as_sentence_terminator(self):
        """Question marks should be recognized as sentence terminators"""
        response = "Why Technology? Because it sells more."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "Too many sentences" in error_msg
    
    def test_exclamation_mark_as_sentence_terminator(self):
        """Exclamation marks should be recognized as sentence terminators"""
        response = "Technology wins! Furniture lags."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is False
        assert "Too many sentences" in error_msg
    
    def test_combined_valid_response_simple(self):
        """Complete valid response for SIMPLE query"""
        response = "Sean Miller leads with the highest order total across your 1,200 transactions."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        assert is_valid is True
        assert error_msg == ""
    
    def test_combined_valid_response_complex(self):
        """Complete valid response for COMPLEX query"""
        response = (
            "Your 2,340 orders show steady growth from Jan to Jun, "
            "with Technology driving 45% of revenue at $125,000. "
            "Consumer products lag at $78,000 but improved 15% in Q2."
        )
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert is_valid is True
        assert error_msg == ""
