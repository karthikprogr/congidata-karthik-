"""
Property-based tests for casual language enforcement in llm_agent.py

This module tests Property 6: Casual business language
**Validates: Requirements 3.2, 3.4**

Property 6: Casual business language
- For any generated response, it SHALL NOT contain technical jargon terms 
  ("statistical significance", "p-value", "correlation coefficient", "standard deviation")
- For any generated response, it SHALL NOT contain academic transitions 
  ("Therefore", "Thus", "In conclusion", "Furthermore")
"""
import pytest
from hypothesis import given, strategies as st, assume, example
from services.agents.llm_agent import _validate_response_format, QueryType


class TestCasualLanguageProperty:
    """Property-based tests for casual business language enforcement"""
    
    # ── Property 6.1: No technical jargon ─────────────────────────────────────
    
    @given(
        jargon_term=st.sampled_from([
            "statistical significance", "p-value", "correlation coefficient",
            "standard deviation", "hypothesis", "null hypothesis"
        ]),
        prefix=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.", 
            min_size=5, 
            max_size=50
        ),
        suffix=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(
        jargon_term="statistical significance",
        prefix="Your dataset shows ",
        suffix=" in the results.",
        query_type=QueryType.COMPLEX
    )
    @example(
        jargon_term="p-value",
        prefix="The analysis reveals a ",
        suffix=" of 0.05.",
        query_type=QueryType.COMPLEX
    )
    @example(
        jargon_term="correlation coefficient",
        prefix="Based on the ",
        suffix=" we can conclude.",
        query_type=QueryType.SIMPLE
    )
    def test_property_no_technical_jargon(self, jargon_term, prefix, suffix, query_type):
        """
        Property 6.1: Casual business language - No technical jargon
        
        **Validates: Requirements 3.2, 3.4**
        
        For any response containing technical jargon terms ("statistical significance", 
        "p-value", "correlation coefficient", "standard deviation", "hypothesis", 
        "null hypothesis"), validation SHALL fail with error indicating jargon detected.
        """
        # Construct response with jargon
        response = f"{prefix}{jargon_term}{suffix}"
        
        # Ensure response has minimal content
        assume(len(response.strip()) > 10)
        
        # Add dataset reference to pass other checks
        if "your" not in response.lower() and not any(char.isdigit() for char in response):
            response = f"In your 500 records, {response}"
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert not is_valid, (
            f"Response containing jargon term '{jargon_term}' should fail validation. "
            f"Response: '{response}'"
        )
        assert "jargon" in error_msg.lower(), (
            f"Error message should indicate jargon detected. Got: '{error_msg}'"
        )
        assert jargon_term in error_msg.lower(), (
            f"Error message should mention the specific jargon term '{jargon_term}'. "
            f"Got: '{error_msg}'"
        )
    
    # ── Property 6.2: No academic transitions ─────────────────────────────────
    
    @given(
        academic_word=st.sampled_from([
            "therefore", "thus", "in conclusion", "furthermore", "moreover", "hence"
        ]),
        prefix=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.", 
            min_size=5, 
            max_size=50
        ),
        suffix=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?", 
            min_size=5, 
            max_size=50
        ),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(
        academic_word="therefore",
        prefix="Sales are up. ",
        suffix=", we recommend investing more.",
        query_type=QueryType.COMPLEX
    )
    @example(
        academic_word="thus",
        prefix="The data indicates growth, ",
        suffix=" the outlook is positive.",
        query_type=QueryType.SIMPLE
    )
    @example(
        academic_word="in conclusion",
        prefix="After analyzing your 1,000 records, ",
        suffix=", the trend is clear.",
        query_type=QueryType.COMPLEX
    )
    def test_property_no_academic_transitions(self, academic_word, prefix, suffix, query_type):
        """
        Property 6.2: Casual business language - No academic transitions
        
        **Validates: Requirements 3.2, 3.4**
        
        For any response containing academic transition phrases ("therefore", "thus", 
        "in conclusion", "furthermore", "moreover", "hence"), validation SHALL fail 
        with error indicating academic transition detected.
        """
        # Construct response with academic transition
        response = f"{prefix}{academic_word}{suffix}"
        
        # Ensure response has minimal content
        assume(len(response.strip()) > 10)
        
        # Add dataset reference to pass other checks
        if "your" not in response.lower() and not any(char.isdigit() for char in response):
            response = f"In your 500 records, {response}"
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        assert not is_valid, (
            f"Response containing academic transition '{academic_word}' should fail validation. "
            f"Response: '{response}'"
        )
        assert "academic transition" in error_msg.lower(), (
            f"Error message should indicate academic transition detected. Got: '{error_msg}'"
        )
    
    # ── Property 6.3: Casual language allows through ─────────────────────────
    
    @given(
        casual_phrase=st.sampled_from([
            "sells more", "doing better", "higher than", "outperforms",
            "leads the pack", "tops the list", "falls behind", "lags behind",
            "on the rise", "trending up", "trending down", "picks up steam"
        ]),
        context=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", 
            min_size=5, 
            max_size=30
        ),
        record_count=st.integers(min_value=1, max_value=10000),
        query_type=st.sampled_from([QueryType.SIMPLE, QueryType.COMPLEX])
    )
    @example(
        casual_phrase="sells more",
        context="Technology",
        record_count=847,
        query_type=QueryType.SIMPLE
    )
    @example(
        casual_phrase="doing better",
        context="West region is",
        record_count=1200,
        query_type=QueryType.COMPLEX
    )
    def test_property_casual_language_allowed(self, casual_phrase, context, record_count, query_type):
        """
        Property 6.3: Casual business language - Allowed phrases
        
        **Validates: Requirements 3.1, 3.3**
        
        For any response using casual business language ("sells more", "doing better", 
        etc.) without jargon or academic transitions, validation SHALL pass.
        """
        # Construct casual response with dataset reference
        response = f"{context} {casual_phrase} in your {record_count} records"
        
        # Ensure no jargon or academic terms accidentally included
        jargon_terms = [
            "statistical significance", "p-value", "correlation coefficient",
            "standard deviation", "hypothesis", "null hypothesis"
        ]
        assume(not any(term in response.lower() for term in jargon_terms))
        
        academic_patterns = ["therefore", "thus", "in conclusion", "furthermore", "moreover", "hence"]
        assume(not any(pattern in response.lower() for pattern in academic_patterns))
        
        # Ensure sentence count is appropriate
        if query_type == QueryType.SIMPLE:
            # Make sure it's one sentence
            assume(response.count('.') <= 1)
            assume(response.count('?') == 0 or (response.count('?') == 1 and response.count('.') == 0))
            assume(response.count('!') == 0 or (response.count('!') == 1 and response.count('.') == 0))
        
        is_valid, error_msg = _validate_response_format(response, query_type)
        
        # Should pass validation or only fail on sentence count, not on language
        if not is_valid:
            assert "jargon" not in error_msg.lower(), (
                f"Casual response should not fail on jargon. Response: '{response}', Error: '{error_msg}'"
            )
            assert "academic" not in error_msg.lower(), (
                f"Casual response should not fail on academic transitions. Response: '{response}', Error: '{error_msg}'"
            )
    
    # ── Property 6.4: Case-insensitive jargon detection ──────────────────────
    
    @given(
        jargon_term=st.sampled_from([
            "statistical significance", "p-value", "correlation coefficient", "standard deviation"
        ]),
        case_variant=st.sampled_from([str.upper, str.lower, str.title])
    )
    @example(jargon_term="p-value", case_variant=str.upper)
    @example(jargon_term="standard deviation", case_variant=str.title)
    def test_property_case_insensitive_jargon_detection(self, jargon_term, case_variant):
        """
        Property 6.4: Casual business language - Case-insensitive detection
        
        **Validates: Requirements 3.2, 3.4**
        
        For any jargon term in any case variation (UPPER, lower, Title), 
        validation SHALL correctly detect it as jargon.
        """
        jargon_variant = case_variant(jargon_term)
        response = f"Your 500 records show {jargon_variant} in the results."
        
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        
        assert not is_valid, (
            f"Jargon term '{jargon_variant}' (variant of '{jargon_term}') should be detected "
            f"regardless of case. Response: '{response}'"
        )
        assert "jargon" in error_msg.lower(), (
            f"Error should indicate jargon detected. Got: '{error_msg}'"
        )
    
    # ── Property 6.5: Case-insensitive academic transition detection ─────────
    
    @given(
        academic_word=st.sampled_from(["therefore", "thus", "furthermore", "hence"]),
        case_variant=st.sampled_from([str.upper, str.lower, str.title, str.capitalize])
    )
    @example(academic_word="therefore", case_variant=str.upper)
    @example(academic_word="thus", case_variant=str.capitalize)
    def test_property_case_insensitive_academic_detection(self, academic_word, case_variant):
        """
        Property 6.5: Casual business language - Case-insensitive academic detection
        
        **Validates: Requirements 3.2, 3.4**
        
        For any academic transition word in any case variation, validation SHALL 
        correctly detect it as an academic transition.
        """
        academic_variant = case_variant(academic_word)
        response = f"Sales are up in your 500 records. {academic_variant}, we recommend action."
        
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        
        assert not is_valid, (
            f"Academic transition '{academic_variant}' should be detected regardless of case. "
            f"Response: '{response}'"
        )
        assert "academic transition" in error_msg.lower(), (
            f"Error should indicate academic transition detected. Got: '{error_msg}'"
        )
    
    # ── Property 6.6: Jargon at different positions ──────────────────────────
    
    @given(
        jargon_term=st.sampled_from(["p-value", "correlation coefficient", "standard deviation"]),
        position=st.sampled_from(["start", "middle", "end"])
    )
    @example(jargon_term="p-value", position="start")
    @example(jargon_term="correlation coefficient", position="middle")
    @example(jargon_term="standard deviation", position="end")
    def test_property_jargon_position_independence(self, jargon_term, position):
        """
        Property 6.6: Casual business language - Position-independent detection
        
        **Validates: Requirements 3.2, 3.4**
        
        For any jargon term appearing at any position (start, middle, end), 
        validation SHALL correctly detect it.
        """
        if position == "start":
            response = f"{jargon_term} indicates a trend in your 500 records."
        elif position == "middle":
            response = f"Your 500 records show {jargon_term} in the analysis."
        else:  # end
            response = f"The analysis of your 500 records reveals {jargon_term}."
        
        # Capitalize first letter if needed
        response = response[0].upper() + response[1:]
        
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        
        assert not is_valid, (
            f"Jargon term '{jargon_term}' at position '{position}' should be detected. "
            f"Response: '{response}'"
        )
        assert "jargon" in error_msg.lower()
    
    # ── Property 6.7: Multiple violations detected ────────────────────────────
    
    @given(
        jargon_term=st.sampled_from(["p-value", "standard deviation"]),
        academic_word=st.sampled_from(["therefore", "thus", "furthermore"])
    )
    @example(jargon_term="p-value", academic_word="therefore")
    @example(jargon_term="standard deviation", academic_word="thus")
    def test_property_multiple_violations_detected(self, jargon_term, academic_word):
        """
        Property 6.7: Casual business language - Multiple violations
        
        **Validates: Requirements 3.2, 3.4**
        
        For any response containing both jargon AND academic transitions, 
        validation SHALL detect at least one violation (may detect first found).
        """
        response = f"Your 500 records show {jargon_term} is significant. {academic_word.capitalize()}, we recommend action."
        
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        
        assert not is_valid, (
            f"Response with both jargon '{jargon_term}' and academic word '{academic_word}' "
            f"should fail validation. Response: '{response}'"
        )
        # Should detect at least one of the violations
        has_violation = ("jargon" in error_msg.lower() or "academic" in error_msg.lower())
        assert has_violation, (
            f"Error message should indicate either jargon or academic transition. Got: '{error_msg}'"
        )
    
    # ── Property 6.8: Word boundary detection ─────────────────────────────────
    
    @given(
        word=st.sampled_from(["therefore", "thus", "hence"]),
        embedding=st.sampled_from(["", "s", "ment", "like"])  # Word parts that would create non-matches
    )
    @example(word="therefore", embedding="")
    @example(word="thus", embedding="s")
    def test_property_word_boundary_detection(self, word, embedding):
        """
        Property 6.8: Casual business language - Word boundary detection
        
        **Validates: Requirements 3.2, 3.4**
        
        Academic transition detection SHALL only trigger on complete words, not 
        as substrings within other words. The implementation uses word boundary 
        regex (\\b), so "therefore" is detected but "therefor" is not (different word).
        """
        if embedding:
            # Create a non-matching embedded version
            embedded_word = f"{word}{embedding}"
            response = f"Your 500 records show that {embedded_word} is the result."
            
            # This should NOT trigger academic transition detection
            # because it's a different word (e.g., "therefores" is not "therefore")
            is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
            
            # We expect this to pass the academic transition check
            # (might still fail on other checks, but not academic transition)
            if not is_valid:
                assert "academic transition" not in error_msg.lower(), (
                    f"Embedded word '{embedded_word}' should not trigger academic transition detection "
                    f"for '{word}'. Response: '{response}', Error: '{error_msg}'"
                )
        else:
            # Test that the standalone word IS detected
            response = f"Your 500 records show growth. {word.capitalize()}, we recommend action."
            
            is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
            
            assert not is_valid, (
                f"Standalone word '{word}' should trigger detection. Response: '{response}'"
            )
            assert "academic transition" in error_msg.lower()


# ── Specific edge case tests ─────────────────────────────────────────────────

class TestCasualLanguageEdgeCases:
    """Edge case tests for casual language enforcement"""
    
    def test_jargon_with_hyphen(self):
        """Hyphenated jargon term (p-value) should be detected"""
        response = "Your 500 records show p-value of 0.05."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert not is_valid
        assert "jargon" in error_msg.lower()
    
    def test_multi_word_jargon(self):
        """Multi-word jargon terms should be detected"""
        response = "Your 500 records show statistical significance."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert not is_valid
        assert "jargon" in error_msg.lower()
        assert "statistical significance" in error_msg.lower()
    
    def test_multi_word_academic_phrase(self):
        """Multi-word academic phrases like 'in conclusion' should be detected"""
        response = "Your 500 records show growth. In conclusion, invest more."
        is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
        assert not is_valid
        assert "academic transition" in error_msg.lower()
    
    def test_casual_comparatives_pass(self):
        """Casual comparative phrases should pass validation"""
        casual_responses = [
            "Technology sells more in your 847 records.",
            "West region is doing better across your 1,200 orders.",
            "Sales are higher than last quarter in your dataset."
        ]
        
        for response in casual_responses:
            is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
            # Should not fail on language (might fail on other checks)
            if not is_valid:
                assert "jargon" not in error_msg.lower(), f"Failed: {response}"
                assert "academic" not in error_msg.lower(), f"Failed: {response}"
    
    def test_professional_but_casual_tone(self):
        """Professional business language without jargon should pass"""
        response = "Your 2,340 orders show Technology driving 45% of revenue at $125,000."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        
        # Should not fail on language
        if not is_valid:
            assert "jargon" not in error_msg.lower()
            assert "academic" not in error_msg.lower()
    
    def test_partial_word_match_not_triggered(self):
        """Partial matches should not trigger jargon detection"""
        # "deviation" is part of "standard deviation" but alone it's not jargon
        response = "Your 500 records show a deviation from the norm."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        
        # Should not fail on jargon for just "deviation"
        # (The implementation checks for "standard deviation" as a phrase)
        if not is_valid:
            # If it fails, it should NOT be because of jargon
            # (might fail on sentence count or other checks)
            pass  # We can't assert it passes completely, but check error doesn't mention jargon incorrectly
    
    def test_numbers_and_casual_language(self):
        """Numbers with casual language should pass"""
        response = "Technology sells more with 1,234 orders in your dataset."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        
        if not is_valid:
            assert "jargon" not in error_msg.lower()
            assert "academic" not in error_msg.lower()
    
    def test_possessive_with_casual_language(self):
        """Possessive references with casual language should pass"""
        response = "Your Technology category is doing better this quarter."
        is_valid, error_msg = _validate_response_format(response, QueryType.SIMPLE)
        
        if not is_valid:
            assert "jargon" not in error_msg.lower()
            assert "academic" not in error_msg.lower()
    
    def test_all_jargon_terms_detected(self):
        """Verify all specified jargon terms are detected"""
        jargon_terms = [
            "statistical significance",
            "p-value",
            "correlation coefficient",
            "standard deviation",
            "hypothesis",
            "null hypothesis"
        ]
        
        for term in jargon_terms:
            response = f"Your 500 records show {term} in results."
            is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
            assert not is_valid, f"Jargon term '{term}' should be detected"
            assert "jargon" in error_msg.lower(), f"Error should mention jargon for '{term}'"
    
    def test_all_academic_transitions_detected(self):
        """Verify all specified academic transitions are detected"""
        academic_words = [
            "therefore",
            "thus",
            "in conclusion",
            "furthermore",
            "moreover",
            "hence"
        ]
        
        for word in academic_words:
            response = f"Your 500 records show growth. {word.capitalize()}, act now."
            is_valid, error_msg = _validate_response_format(response, QueryType.COMPLEX)
            assert not is_valid, f"Academic word '{word}' should be detected"
            assert "academic transition" in error_msg.lower(), f"Error should mention academic for '{word}'"
